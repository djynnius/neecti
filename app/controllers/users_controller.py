from flask import request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import User, Post, Notification

class UsersController:
    
    @staticmethod
    def get_user_profile(handle):
        """Get user profile by handle"""
        user = User.query.filter_by(handle=handle.lower(), is_active=True).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's posts
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        posts = Post.query.filter_by(user_id=user.id, is_deleted=False, parent_id=None)\
                         .order_by(Post.created_at.desc())\
                         .paginate(page=page, per_page=per_page, error_out=False)
        
        profile_data = user.to_dict()
        profile_data.update({
            'posts': [post.to_dict() for post in posts.items],
            'pagination': {
                'page': posts.page,
                'pages': posts.pages,
                'per_page': posts.per_page,
                'total': posts.total,
                'has_next': posts.has_next,
                'has_prev': posts.has_prev
            }
        })
        
        # Add follow status if user is authenticated
        if current_user.is_authenticated:
            profile_data['is_following'] = current_user.is_following(user)
            profile_data['is_followed_by'] = user.is_following(current_user)
        
        return jsonify({'user': profile_data}), 200
    
    @staticmethod
    @login_required
    def follow_user(handle):
        """Follow a user"""
        user = User.query.filter_by(handle=handle.lower(), is_active=True).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot follow yourself'}), 400
        
        if current_user.is_following(user):
            return jsonify({'error': 'Already following this user'}), 400
        
        current_user.follow(user)
        db.session.commit()
        
        # Create notification
        Notification.create_follow_notification(user, current_user)
        
        return jsonify({
            'message': f'Now following @{user.handle}',
            'is_following': True
        }), 200
    
    @staticmethod
    @login_required
    def unfollow_user(handle):
        """Unfollow a user"""
        user = User.query.filter_by(handle=handle.lower(), is_active=True).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not current_user.is_following(user):
            return jsonify({'error': 'Not following this user'}), 400
        
        current_user.unfollow(user)
        db.session.commit()
        
        return jsonify({
            'message': f'Unfollowed @{user.handle}',
            'is_following': False
        }), 200
    
    @staticmethod
    def get_followers(handle):
        """Get user's followers"""
        user = User.query.filter_by(handle=handle.lower(), is_active=True).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        followers = user.followers.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'followers': [follower.to_dict() for follower in followers.items],
            'pagination': {
                'page': followers.page,
                'pages': followers.pages,
                'per_page': followers.per_page,
                'total': followers.total,
                'has_next': followers.has_next,
                'has_prev': followers.has_prev
            }
        }), 200
    
    @staticmethod
    def get_following(handle):
        """Get users that this user is following"""
        user = User.query.filter_by(handle=handle.lower(), is_active=True).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        following = user.followed.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'following': [followed.to_dict() for followed in following.items],
            'pagination': {
                'page': following.page,
                'pages': following.pages,
                'per_page': following.per_page,
                'total': following.total,
                'has_next': following.has_next,
                'has_prev': following.has_prev
            }
        }), 200
    
    @staticmethod
    def search_users():
        """Search users by handle, name, or bio"""
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        users = User.query.filter_by(is_active=True).filter(
            db.or_(
                User.handle.contains(query.lower()),
                db.func.lower(User.first_name).contains(query.lower()),
                db.func.lower(User.last_name).contains(query.lower()),
                db.and_(User.bio.isnot(None), db.func.lower(User.bio).contains(query.lower()))
            )
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            },
            'query': query
        }), 200
    
    @staticmethod
    def get_suggested_users():
        """Get suggested users to follow"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        # Simple suggestion algorithm: users with most followers that current user isn't following
        # We'll use a subquery to count followers for ordering
        from sqlalchemy import func
        from app.models.user import followers

        follower_count = db.session.query(
            followers.c.followed_id,
            func.count(followers.c.follower_id).label('follower_count')
        ).group_by(followers.c.followed_id).subquery()

        suggested = User.query.filter_by(is_active=True)\
                             .filter(User.id != current_user.id)\
                             .filter(~User.followers.any(id=current_user.id))\
                             .outerjoin(follower_count, User.id == follower_count.c.followed_id)\
                             .order_by(follower_count.c.follower_count.desc().nullslast())\
                             .limit(10).all()

        return jsonify({
            'suggested_users': [user.to_dict() for user in suggested]
        }), 200
    
    @staticmethod
    @login_required
    def get_notifications():
        """Get user's notifications"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        notifications = current_user.notifications.order_by(
            Notification.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications.items],
            'pagination': {
                'page': notifications.page,
                'pages': notifications.pages,
                'per_page': notifications.per_page,
                'total': notifications.total,
                'has_next': notifications.has_next,
                'has_prev': notifications.has_prev
            },
            'unread_count': current_user.get_notification_count()
        }), 200
    
    @staticmethod
    @login_required
    def mark_notifications_read():
        """Mark notifications as read"""
        notification_ids = request.get_json().get('notification_ids', [])
        
        if notification_ids:
            # Mark specific notifications as read
            notifications = Notification.query.filter(
                Notification.id.in_(notification_ids),
                Notification.user_id == current_user.id
            ).all()
        else:
            # Mark all notifications as read
            notifications = current_user.notifications.filter_by(is_read=False).all()
        
        for notification in notifications:
            notification.mark_as_read()
        
        return jsonify({
            'message': f'Marked {len(notifications)} notifications as read'
        }), 200
