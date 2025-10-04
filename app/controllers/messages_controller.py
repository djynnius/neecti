from flask import request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Message, Conversation, User
from app.controllers.socketio_controller import emit_new_notification
from datetime import datetime

class MessagesController:
    
    @staticmethod
    @login_required
    def send_message():
        """Send a private message"""
        data = request.get_json()
        
        recipient_handle = data.get('recipient_handle', '').strip()
        recipient_id = data.get('recipient_id')
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Message content is required'}), 400
        
        # Find recipient by handle or ID
        if recipient_handle:
            recipient = User.query.filter_by(handle=recipient_handle.lower(), is_active=True).first()
        elif recipient_id:
            recipient = User.query.filter_by(id=recipient_id, is_active=True).first()
        else:
            return jsonify({'error': 'Recipient handle or ID is required'}), 400
        
        if not recipient:
            return jsonify({'error': 'Recipient not found'}), 404
        
        if recipient.id == current_user.id:
            return jsonify({'error': 'Cannot send message to yourself'}), 400
        
        try:
            # Create message
            message = Message(
                sender_id=current_user.id,
                recipient_id=recipient.id,
                content=content,
                original_language=current_user.preferred_language
            )
            
            db.session.add(message)
            
            # Update or create conversation
            conversation = Conversation.get_or_create(current_user.id, recipient.id)
            conversation.last_message_id = message.id
            conversation.last_activity = datetime.utcnow()
            
            db.session.commit()
            
            # The real-time notification is handled by SocketIO in socketio_controller.py
            
            return jsonify({
                'message': 'Message sent successfully',
                'message_data': message.to_dict(),
                'conversation_id': conversation.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to send message'}), 500
    
    @staticmethod
    @login_required
    def get_conversations():
        """Get user's conversations"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get conversations where user is participant
        conversations = Conversation.query.filter(
            db.or_(
                Conversation.user1_id == current_user.id,
                Conversation.user2_id == current_user.id
            )
        ).order_by(Conversation.last_activity.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'conversations': [conv.to_dict(current_user.id) for conv in conversations.items],
            'pagination': {
                'page': conversations.page,
                'pages': conversations.pages,
                'per_page': conversations.per_page,
                'total': conversations.total,
                'has_next': conversations.has_next,
                'has_prev': conversations.has_prev
            }
        }), 200
    
    @staticmethod
    @login_required
    def get_conversation_messages(conversation_id):
        """Get messages in a conversation"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Verify user has access to this conversation
        conversation = Conversation.query.filter(
            Conversation.id == conversation_id,
            db.or_(
                Conversation.user1_id == current_user.id,
                Conversation.user2_id == current_user.id
            )
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Get the other user in the conversation
        other_user = conversation.get_other_user(current_user.id)
        
        # Get messages between the two users
        messages = Message.get_conversation(current_user.id, other_user.id, limit=per_page * page)
        
        # Filter messages that are visible to current user
        visible_messages = [
            msg for msg in messages 
            if msg.is_visible_to_user(current_user.id)
        ]
        
        # Paginate manually
        start = (page - 1) * per_page
        end = start + per_page
        paginated_messages = visible_messages[start:end]
        
        return jsonify({
            'conversation': conversation.to_dict(current_user.id),
            'messages': [msg.to_dict() for msg in paginated_messages],
            'pagination': {
                'page': page,
                'total': len(visible_messages),
                'has_next': end < len(visible_messages),
                'has_prev': page > 1
            }
        }), 200
    
    @staticmethod
    @login_required
    def mark_messages_read(conversation_id):
        """Mark messages in conversation as read"""
        # Verify user has access to this conversation
        conversation = Conversation.query.filter(
            Conversation.id == conversation_id,
            db.or_(
                Conversation.user1_id == current_user.id,
                Conversation.user2_id == current_user.id
            )
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        try:
            # Mark all unread messages from the other user as read
            other_user = conversation.get_other_user(current_user.id)
            
            unread_messages = Message.query.filter_by(
                sender_id=other_user.id,
                recipient_id=current_user.id,
                is_read=False
            ).all()
            
            for message in unread_messages:
                message.mark_as_read()
            
            return jsonify({
                'message': f'Marked {len(unread_messages)} messages as read',
                'count': len(unread_messages)
            }), 200
            
        except Exception as e:
            return jsonify({'error': 'Failed to mark messages as read'}), 500
    
    @staticmethod
    @login_required
    def save_message(message_id):
        """Save a message to persist after logout"""
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Check if user has access to this message
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        if not message.is_visible_to_user(current_user.id):
            return jsonify({'error': 'Message not found'}), 404
        
        try:
            message.save_message()
            
            return jsonify({
                'message': 'Message saved successfully',
                'message_data': message.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({'error': 'Failed to save message'}), 500
    
    @staticmethod
    @login_required
    def delete_message(message_id):
        """Delete a message for current user"""
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Check if user has access to this message
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        if not message.is_visible_to_user(current_user.id):
            return jsonify({'error': 'Message not found'}), 404
        
        try:
            message.delete_for_user(current_user.id)
            
            return jsonify({
                'message': 'Message deleted successfully'
            }), 200
            
        except Exception as e:
            return jsonify({'error': 'Failed to delete message'}), 500
    
    @staticmethod
    @login_required
    def search_messages():
        """Search messages"""
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search in messages where user is sender or recipient
        messages = Message.query.filter(
            db.or_(
                Message.sender_id == current_user.id,
                Message.recipient_id == current_user.id
            ),
            Message.content.contains(query)
        ).order_by(Message.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Filter out messages that are not visible to user
        visible_messages = [
            msg for msg in messages.items 
            if msg.is_visible_to_user(current_user.id)
        ]
        
        return jsonify({
            'messages': [msg.to_dict() for msg in visible_messages],
            'pagination': {
                'page': messages.page,
                'pages': messages.pages,
                'per_page': messages.per_page,
                'total': len(visible_messages),
                'has_next': messages.has_next,
                'has_prev': messages.has_prev
            },
            'query': query
        }), 200
    
    @staticmethod
    @login_required
    def get_message_stats():
        """Get user's message statistics"""
        total_sent = Message.query.filter_by(sender_id=current_user.id).count()
        total_received = Message.query.filter_by(recipient_id=current_user.id).count()
        unread_count = current_user.get_unread_message_count()
        
        # Get active conversations count
        active_conversations = Conversation.query.filter(
            db.or_(
                Conversation.user1_id == current_user.id,
                Conversation.user2_id == current_user.id
            )
        ).count()
        
        return jsonify({
            'stats': {
                'total_sent': total_sent,
                'total_received': total_received,
                'unread_count': unread_count,
                'active_conversations': active_conversations
            }
        }), 200
