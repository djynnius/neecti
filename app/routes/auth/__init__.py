from flask import Blueprint
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Authentication routes
auth_bp.add_url_rule('/register', 'register', AuthController.register, methods=['POST'])
auth_bp.add_url_rule('/login', 'login', AuthController.login, methods=['POST'])
auth_bp.add_url_rule('/logout', 'logout', AuthController.logout, methods=['POST'])
auth_bp.add_url_rule('/me', 'current_user', AuthController.get_current_user, methods=['GET'])
auth_bp.add_url_rule('/change-password', 'change_password', AuthController.change_password, methods=['POST'])
auth_bp.add_url_rule('/profile', 'update_profile', AuthController.update_profile, methods=['PUT'])
auth_bp.add_url_rule('/delete-account', 'delete_account', AuthController.delete_account, methods=['DELETE'])
