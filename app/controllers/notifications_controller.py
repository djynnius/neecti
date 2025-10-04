from flask import request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Notification, User, Post
from datetime import datetime, timedelta

class NotificationsController:
    
    @staticmethod
    @login_required
    def get_notifications():
        """Get user's notifications with filtering options"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        notification_type = request.args.get('type')  # 'like', 'reply', 'follow', 'share', 'mention'
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        query = current_user.notifications
        
        # Filter by type if specified
        if notification_type:
            query = query.filter_by(type=notification_type)
        
        # Filter by read status if specified
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
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
            'unread_count': current_user.get_notification_count(),
            'filters': {
                'type': notification_type,
                'unread_only': unread_only
            }
        }), 200
    
    @staticmethod
    @login_required
    def mark_notification_read(notification_id):
        """Mark a specific notification as read"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        notification.mark_as_read()
        
        return jsonify({
            'message': 'Notification marked as read',
            'notification': notification.to_dict()
        }), 200
    
    @staticmethod
    @login_required
    def mark_all_notifications_read():
        """Mark all notifications as read"""
        notification_type = request.args.get('type')  # Optional: mark only specific type as read
        
        query = current_user.notifications.filter_by(is_read=False)
        
        if notification_type:
            query = query.filter_by(type=notification_type)
        
        notifications = query.all()
        
        for notification in notifications:
            notification.mark_as_read()
        
        return jsonify({
            'message': f'Marked {len(notifications)} notifications as read',
            'count': len(notifications)
        }), 200
    
    @staticmethod
    @login_required
    def delete_notification(notification_id):
        """Delete a specific notification"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        try:
            db.session.delete(notification)
            db.session.commit()
            
            return jsonify({
                'message': 'Notification deleted successfully'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to delete notification'}), 500
    
    @staticmethod
    @login_required
    def delete_old_notifications():
        """Delete notifications older than specified days"""
        days = request.args.get('days', 10, type=int)
        notification_type = request.args.get('type')  # Optional: delete only specific type
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = current_user.notifications.filter(
            Notification.created_at < cutoff_date
        )
        
        if notification_type:
            query = query.filter_by(type=notification_type)
        
        old_notifications = query.all()
        
        try:
            for notification in old_notifications:
                db.session.delete(notification)
            
            db.session.commit()
            
            return jsonify({
                'message': f'Deleted {len(old_notifications)} old notifications',
                'count': len(old_notifications)
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to delete notifications'}), 500
    
    @staticmethod
    @login_required
    def get_notification_settings():
        """Get user's notification preferences"""
        # This would be extended with user preferences in a real app
        # For now, return default settings
        return jsonify({
            'settings': {
                'email_notifications': True,
                'push_notifications': True,
                'notification_types': {
                    'likes': True,
                    'replies': True,
                    'follows': True,
                    'shares': True,
                    'mentions': True
                },
                'quiet_hours': {
                    'enabled': False,
                    'start_time': '22:00',
                    'end_time': '08:00'
                }
            }
        }), 200
    
    @staticmethod
    @login_required
    def update_notification_settings():
        """Update user's notification preferences"""
        data = request.get_json()
        
        # In a real app, you'd save these to a user preferences table
        # For now, just return success
        
        return jsonify({
            'message': 'Notification settings updated successfully',
            'settings': data
        }), 200
    
    @staticmethod
    @login_required
    def get_notification_stats():
        """Get notification statistics for the user"""
        # Count notifications by type
        stats = {}
        notification_types = ['like', 'reply', 'follow', 'share', 'mention']
        
        for ntype in notification_types:
            total = current_user.notifications.filter_by(type=ntype).count()
            unread = current_user.notifications.filter_by(type=ntype, is_read=False).count()
            stats[ntype] = {
                'total': total,
                'unread': unread
            }
        
        # Get recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = current_user.notifications.filter(
            Notification.created_at >= week_ago
        ).count()
        
        return jsonify({
            'stats': {
                'total_notifications': current_user.notifications.count(),
                'unread_notifications': current_user.get_notification_count(),
                'recent_activity': recent_count,
                'by_type': stats
            }
        }), 200
    
    @staticmethod
    def cleanup_old_notifications():
        """System cleanup of old notifications (admin or cron job)"""
        if current_user.is_authenticated and not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        deleted_count = Notification.cleanup_old_notifications()
        
        return jsonify({
            'message': f'Cleaned up {deleted_count} old notifications',
            'deleted_count': deleted_count
        }), 200
    
    @staticmethod
    @login_required
    def test_notification():
        """Create a test notification (for development/testing)"""
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        notification_type = data.get('type', 'like')
        message = data.get('message', 'This is a test notification')
        
        try:
            notification = Notification(
                user_id=current_user.id,
                type=notification_type,
                message=message
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({
                'message': 'Test notification created',
                'notification': notification.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to create test notification'}), 500
