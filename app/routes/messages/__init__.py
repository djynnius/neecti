from flask import Blueprint
from app.controllers.messages_controller import MessagesController

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

# Message routes
messages_bp.add_url_rule('/', 'send_message', MessagesController.send_message, methods=['POST'])
messages_bp.add_url_rule('/conversations', 'conversations', MessagesController.get_conversations, methods=['GET'])
messages_bp.add_url_rule('/conversations/<int:conversation_id>', 'conversation_messages', MessagesController.get_conversation_messages, methods=['GET'])
messages_bp.add_url_rule('/conversations/<int:conversation_id>/read', 'mark_messages_read', MessagesController.mark_messages_read, methods=['POST'])
messages_bp.add_url_rule('/<int:message_id>/save', 'save_message', MessagesController.save_message, methods=['POST'])
messages_bp.add_url_rule('/<int:message_id>', 'delete_message', MessagesController.delete_message, methods=['DELETE'])
messages_bp.add_url_rule('/search', 'search_messages', MessagesController.search_messages, methods=['GET'])
messages_bp.add_url_rule('/stats', 'message_stats', MessagesController.get_message_stats, methods=['GET'])
