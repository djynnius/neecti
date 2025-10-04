from flask import Blueprint
from app.controllers.users_controller import UsersController
from app.controllers.notifications_controller import NotificationsController

users_bp = Blueprint('users', __name__, url_prefix='/users')

# User routes
users_bp.add_url_rule('/search', 'search_users', UsersController.search_users, methods=['GET'])
users_bp.add_url_rule('/suggested', 'suggested_users', UsersController.get_suggested_users, methods=['GET'])

# Notification routes
users_bp.add_url_rule('/notifications', 'notifications', NotificationsController.get_notifications, methods=['GET'])
users_bp.add_url_rule('/notifications/read-all', 'mark_all_notifications_read', NotificationsController.mark_all_notifications_read, methods=['POST'])
users_bp.add_url_rule('/notifications/<int:notification_id>/read', 'mark_notification_read', NotificationsController.mark_notification_read, methods=['POST'])
users_bp.add_url_rule('/notifications/<int:notification_id>', 'delete_notification', NotificationsController.delete_notification, methods=['DELETE'])
users_bp.add_url_rule('/notifications/cleanup', 'delete_old_notifications', NotificationsController.delete_old_notifications, methods=['DELETE'])
users_bp.add_url_rule('/notifications/settings', 'notification_settings', NotificationsController.get_notification_settings, methods=['GET'])
users_bp.add_url_rule('/notifications/settings', 'update_notification_settings', NotificationsController.update_notification_settings, methods=['PUT'])
users_bp.add_url_rule('/notifications/stats', 'notification_stats', NotificationsController.get_notification_stats, methods=['GET'])
users_bp.add_url_rule('/notifications/test', 'test_notification', NotificationsController.test_notification, methods=['POST'])

# Profile routes
users_bp.add_url_rule('/@<string:handle>', 'user_profile', UsersController.get_user_profile, methods=['GET'])
users_bp.add_url_rule('/@<string:handle>/follow', 'follow_user', UsersController.follow_user, methods=['POST'])
users_bp.add_url_rule('/@<string:handle>/unfollow', 'unfollow_user', UsersController.unfollow_user, methods=['POST'])
users_bp.add_url_rule('/@<string:handle>/followers', 'followers', UsersController.get_followers, methods=['GET'])
users_bp.add_url_rule('/@<string:handle>/following', 'following', UsersController.get_following, methods=['GET'])
