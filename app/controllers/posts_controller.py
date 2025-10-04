from flask import request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Post, PostImage, User, Notification
import json
import re
from datetime import datetime

class PostsController:
    
    @staticmethod
    @login_required
    def create_post():
        """Create a new post"""
        data = request.get_json()
        
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        is_branch = data.get('is_branch', False)
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        if len(content) > 250:
            return jsonify({'error': 'Content must be 250 characters or less'}), 400
        
        try:
            # Extract hashtags and mentions
            hashtags = re.findall(r'#(\w+)', content)
            mentions = re.findall(r'@(\w+)', content)
            
            # Create post
            post = Post(
                content=content,
                user_id=current_user.id,
                original_language=current_user.preferred_language,
                hashtags=json.dumps(hashtags) if hashtags else None,
                mentions=json.dumps(mentions) if mentions else None
            )
            
            # Handle replies and branches
            if parent_id:
                parent_post = Post.query.get(parent_id)
                if not parent_post:
                    return jsonify({'error': 'Parent post not found'}), 404
                
                if is_branch:
                    # Create a new branch
                    post.parent_id = parent_post.id
                    post.conversation_root_id = parent_post.conversation_root_id or parent_post.id
                    post.branch_level = parent_post.branch_level + 1
                    post.is_branch_root = True
                else:
                    # Regular reply
                    post.parent_id = parent_post.id
                    post.conversation_root_id = parent_post.conversation_root_id or parent_post.id
                    post.branch_level = parent_post.branch_level + 1
                    post.is_branch_root = False
                
                # Update parent's reply count
                parent_post.replies_count += 1
                
                # Create notification for parent author
                Notification.create_reply_notification(parent_post, current_user)
            
            db.session.add(post)
            db.session.commit()

            # Create notifications for mentioned users
            for mention in mentions:
                mentioned_user = User.query.filter_by(handle=mention.lower()).first()
                if mentioned_user:
                    Notification.create_mention_notification(post, mentioned_user)

            # Emit real-time event for new post
            from app.controllers.socketio_controller import emit_new_post
            emit_new_post(post)

            return jsonify({
                'message': 'Post created successfully',
                'post': post.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to create post'}), 500
    
    @staticmethod
    def get_post(post_id):
        """Get a specific post with conversation tree"""
        post = Post.query.filter_by(id=post_id, is_deleted=False).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Increment view count
        post.views_count += 1
        db.session.commit()
        
        return jsonify({
            'post': post.to_dict(include_replies=True)
        }), 200
    
    @staticmethod
    def get_timeline():
        """Get user's timeline"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if current_user.is_authenticated:
            # Get posts from followed users and own posts
            posts = current_user.get_timeline_posts()
        else:
            # Get trending posts for anonymous users
            posts = Post.query.filter_by(is_deleted=False, parent_id=None)
        
        posts = posts.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'posts': [post.to_dict() for post in posts.items],
            'pagination': {
                'page': posts.page,
                'pages': posts.pages,
                'per_page': posts.per_page,
                'total': posts.total,
                'has_next': posts.has_next,
                'has_prev': posts.has_prev
            }
        }), 200
    
    @staticmethod
    def get_trending():
        """Get trending posts"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get posts from last 24 hours, ordered by trending score
        posts = Post.query.filter_by(is_deleted=False, parent_id=None)\
                         .filter(Post.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0))\
                         .all()
        
        # Sort by trending score
        posts.sort(key=lambda x: x.get_trending_score(), reverse=True)
        
        # Manual pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_posts = posts[start:end]
        
        return jsonify({
            'posts': [post.to_dict() for post in paginated_posts],
            'pagination': {
                'page': page,
                'total': len(posts),
                'has_next': end < len(posts),
                'has_prev': page > 1
            }
        }), 200
    
    @staticmethod
    @login_required
    def like_post(post_id):
        """Like or unlike a post"""
        post = Post.query.filter_by(id=post_id, is_deleted=False).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        if post.is_liked_by(current_user):
            post.unlike(current_user)
            action = 'unliked'
        else:
            post.like(current_user)
            action = 'liked'
            # Create notification
            Notification.create_like_notification(post, current_user)
        
        db.session.commit()

        # Emit real-time update for post engagement
        from app.controllers.socketio_controller import emit_post_update
        emit_post_update(post)

        return jsonify({
            'message': f'Post {action}',
            'likes_count': post.likes_count,
            'is_liked': post.is_liked_by(current_user)
        }), 200
    
    @staticmethod
    @login_required
    def share_post(post_id):
        """Share a post"""
        post = Post.query.filter_by(id=post_id, is_deleted=False).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        if current_user not in post.shared_by:
            post.share(current_user)
            # Create notification
            Notification.create_share_notification(post, current_user)
            db.session.commit()
            
            return jsonify({
                'message': 'Post shared',
                'shares_count': post.shares_count
            }), 200
        else:
            return jsonify({'error': 'Post already shared'}), 400
    
    @staticmethod
    @login_required
    def delete_post(post_id):
        """Delete a post and all its child posts (cascading delete)"""
        post = Post.query.filter_by(id=post_id, user_id=current_user.id, is_deleted=False).first()
        if not post:
            return jsonify({'error': 'Post not found or not authorized'}), 404

        try:
            # Use the cascading delete method
            post.delete_with_children()

            # Emit real-time update for post deletion
            from app.controllers.socketio_controller import emit_post_deleted
            emit_post_deleted(post_id)

            return jsonify({
                'message': 'Post and all replies deleted successfully',
                'deleted_post_id': post_id
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to delete post'}), 500
    
    @staticmethod
    def search_posts():
        """Search posts by content, hashtags, or mentions"""
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search in content, hashtags, and mentions (case-insensitive)
        posts = Post.query.filter_by(is_deleted=False).filter(
            db.or_(
                db.func.lower(Post.content).contains(query.lower()),
                db.and_(Post.hashtags.isnot(None), db.func.lower(Post.hashtags).contains(query.lower())),
                db.and_(Post.mentions.isnot(None), db.func.lower(Post.mentions).contains(query.lower()))
            )
        ).order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'posts': [post.to_dict() for post in posts.items],
            'pagination': {
                'page': posts.page,
                'pages': posts.pages,
                'per_page': posts.per_page,
                'total': posts.total,
                'has_next': posts.has_next,
                'has_prev': posts.has_prev
            },
            'query': query
        }), 200
