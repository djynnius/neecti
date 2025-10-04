from flask import request, jsonify
from flask_login import current_user
from app.models import Post, User, Notification, Report
from app import db

class ApiController:
    
    @staticmethod
    def get_stats():
        """Get platform statistics"""
        stats = {
            'total_users': User.query.filter_by(is_active=True).count(),
            'total_posts': Post.query.filter_by(is_deleted=False).count(),
            'total_conversations': Post.query.filter_by(is_deleted=False, parent_id=None).count(),
            'active_users_today': User.query.filter(
                User.last_seen >= db.func.current_date()
            ).count()
        }
        
        return jsonify({'stats': stats}), 200
    
    @staticmethod
    def report_content():
        """Report a post or user"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        reason = data.get('reason', '').strip()
        description = data.get('description', '').strip()
        reported_post_id = data.get('post_id')
        reported_user_id = data.get('user_id')
        
        if not reason:
            return jsonify({'error': 'Reason is required'}), 400
        
        if not reported_post_id and not reported_user_id:
            return jsonify({'error': 'Either post_id or user_id is required'}), 400
        
        # Validate reported content exists
        if reported_post_id:
            post = Post.query.get(reported_post_id)
            if not post or post.is_deleted:
                return jsonify({'error': 'Post not found'}), 404
        
        if reported_user_id:
            user = User.query.get(reported_user_id)
            if not user or not user.is_active:
                return jsonify({'error': 'User not found'}), 404
        
        try:
            report = Report(
                reporter_id=current_user.id,
                reported_post_id=reported_post_id,
                reported_user_id=reported_user_id,
                reason=reason,
                description=description
            )
            
            db.session.add(report)
            
            # Mark content as reported
            if reported_post_id:
                post.is_reported = True
            
            db.session.commit()
            
            return jsonify({
                'message': 'Report submitted successfully',
                'report_id': report.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to submit report'}), 500
    
    @staticmethod
    def get_hashtag_posts(hashtag):
        """Get posts with specific hashtag"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        posts = Post.query.filter_by(is_deleted=False)\
                         .filter(Post.hashtags.contains(f'"{hashtag}"'))\
                         .order_by(Post.created_at.desc())\
                         .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'hashtag': hashtag,
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
    def get_trending_hashtags():
        """Get trending hashtags"""
        # This is a simplified implementation
        # In production, you'd want to use a more sophisticated algorithm
        from sqlalchemy import func
        import json
        
        # Get all hashtags from recent posts
        recent_posts = Post.query.filter_by(is_deleted=False)\
                                .filter(Post.created_at >= func.current_date())\
                                .filter(Post.hashtags.isnot(None))\
                                .all()
        
        hashtag_counts = {}
        for post in recent_posts:
            try:
                hashtags = json.loads(post.hashtags)
                for hashtag in hashtags:
                    hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
            except:
                continue
        
        # Sort by count and get top 10
        trending = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            'trending_hashtags': [
                {'hashtag': hashtag, 'count': count} 
                for hashtag, count in trending
            ]
        }), 200
    
    @staticmethod
    def cleanup_old_data():
        """Cleanup old notifications and other temporary data"""
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403

        # Cleanup old notifications
        deleted_notifications = Notification.cleanup_old_notifications()

        return jsonify({
            'message': 'Cleanup completed',
            'deleted_notifications': deleted_notifications
        }), 200

    @staticmethod
    def create_test_users():
        """Create test users for development (admin only)"""
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403

        test_users = [
            {
                'handle': 'alice_dev',
                'email': 'alice@example.com',
                'first_name': 'Alice',
                'last_name': 'Developer',
                'bio': 'Full-stack developer passionate about React and Python'
            },
            {
                'handle': 'bob_designer',
                'email': 'bob@example.com',
                'first_name': 'Bob',
                'last_name': 'Designer',
                'bio': 'UI/UX designer creating beautiful digital experiences'
            },
            {
                'handle': 'charlie_ai',
                'email': 'charlie@example.com',
                'first_name': 'Charlie',
                'last_name': 'AI',
                'bio': 'AI researcher exploring the future of machine learning'
            },
            {
                'handle': 'diana_writer',
                'email': 'diana@example.com',
                'first_name': 'Diana',
                'last_name': 'Writer',
                'bio': 'Technical writer and content creator'
            }
        ]

        created_users = []

        try:
            for user_data in test_users:
                # Check if user already exists
                existing_user = User.query.filter_by(handle=user_data['handle']).first()
                if existing_user:
                    continue

                user = User(
                    handle=user_data['handle'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    bio=user_data['bio']
                )
                user.set_password('testpassword123')

                db.session.add(user)
                created_users.append(user_data['handle'])

            db.session.commit()

            return jsonify({
                'message': f'Created {len(created_users)} test users',
                'created_users': created_users
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to create test users'}), 500
