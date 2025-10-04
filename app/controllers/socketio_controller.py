from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask import request
from app import socketio, db
from app.models import User, Message, Conversation, Notification
from datetime import datetime
import json

# Store active connections
active_users = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        # Update user's last seen
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Store user's session
        active_users[current_user.id] = request.sid
        
        # Join user's personal room for notifications
        join_room(f"user_{current_user.id}")
        
        # Join timeline room
        join_room("timeline")
        
        emit('connected', {
            'message': 'Connected successfully',
            'user_id': current_user.id
        })
        
        # Notify followers that user is online
        emit('user_online', {
            'user_id': current_user.id,
            'handle': current_user.handle
        }, room='timeline')
        
        print(f"User {current_user.handle} connected")
    else:
        # Allow anonymous users to join timeline
        join_room("timeline")
        emit('connected', {'message': 'Connected as guest'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        # Remove from active users
        if current_user.id in active_users:
            del active_users[current_user.id]
        
        # Update last seen
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Notify followers that user is offline
        emit('user_offline', {
            'user_id': current_user.id,
            'handle': current_user.handle
        }, room='timeline')
        
        print(f"User {current_user.handle} disconnected")

@socketio.on('join_conversation')
def handle_join_conversation(data):
    """Join a conversation room for real-time messaging"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    other_user_id = data.get('user_id')
    if not other_user_id:
        emit('error', {'message': 'User ID required'})
        return
    
    # Create conversation room name (consistent ordering)
    room_name = f"conversation_{min(current_user.id, other_user_id)}_{max(current_user.id, other_user_id)}"
    join_room(room_name)
    
    emit('joined_conversation', {
        'room': room_name,
        'other_user_id': other_user_id
    })

@socketio.on('leave_conversation')
def handle_leave_conversation(data):
    """Leave a conversation room"""
    if not current_user.is_authenticated:
        return
    
    other_user_id = data.get('user_id')
    if not other_user_id:
        return
    
    room_name = f"conversation_{min(current_user.id, other_user_id)}_{max(current_user.id, other_user_id)}"
    leave_room(room_name)
    
    emit('left_conversation', {'room': room_name})

@socketio.on('send_message')
def handle_send_message(data):
    """Send a real-time message"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    recipient_id = data.get('recipient_id')
    content = data.get('content', '').strip()
    
    if not recipient_id or not content:
        emit('error', {'message': 'Recipient and content required'})
        return
    
    # Validate recipient exists
    recipient = User.query.get(recipient_id)
    if not recipient or not recipient.is_active:
        emit('error', {'message': 'Recipient not found'})
        return
    
    try:
        # Create message
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content,
            original_language=current_user.preferred_language
        )
        
        db.session.add(message)
        
        # Update or create conversation
        conversation = Conversation.get_or_create(current_user.id, recipient_id)
        conversation.last_message_id = message.id
        conversation.last_activity = datetime.utcnow()
        
        db.session.commit()
        
        # Send to conversation room
        room_name = f"conversation_{min(current_user.id, recipient_id)}_{max(current_user.id, recipient_id)}"
        emit('new_message', {
            'message': message.to_dict(),
            'conversation_id': conversation.id
        }, room=room_name)
        
        # Send notification to recipient if they're online
        if recipient_id in active_users:
            emit('message_notification', {
                'sender': current_user.to_dict(),
                'preview': content[:50] + '...' if len(content) > 50 else content,
                'conversation_id': conversation.id
            }, room=f"user_{recipient_id}")
        
        emit('message_sent', {
            'message': message.to_dict(),
            'conversation_id': conversation.id
        })
        
    except Exception as e:
        db.session.rollback()
        emit('error', {'message': 'Failed to send message'})

@socketio.on('typing_start')
def handle_typing_start(data):
    """Handle typing indicator start"""
    if not current_user.is_authenticated:
        return
    
    other_user_id = data.get('user_id')
    if not other_user_id:
        return
    
    room_name = f"conversation_{min(current_user.id, other_user_id)}_{max(current_user.id, other_user_id)}"
    emit('user_typing', {
        'user_id': current_user.id,
        'handle': current_user.handle,
        'typing': True
    }, room=room_name, include_self=False)

@socketio.on('typing_stop')
def handle_typing_stop(data):
    """Handle typing indicator stop"""
    if not current_user.is_authenticated:
        return
    
    other_user_id = data.get('user_id')
    if not other_user_id:
        return
    
    room_name = f"conversation_{min(current_user.id, other_user_id)}_{max(current_user.id, other_user_id)}"
    emit('user_typing', {
        'user_id': current_user.id,
        'handle': current_user.handle,
        'typing': False
    }, room=room_name, include_self=False)

@socketio.on('mark_messages_read')
def handle_mark_messages_read(data):
    """Mark messages as read"""
    if not current_user.is_authenticated:
        return
    
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return
    
    try:
        # Mark all unread messages in conversation as read
        messages = Message.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).join(Conversation).filter(Conversation.id == conversation_id).all()
        
        for message in messages:
            message.mark_as_read()
        
        emit('messages_marked_read', {
            'conversation_id': conversation_id,
            'count': len(messages)
        })
        
    except Exception as e:
        emit('error', {'message': 'Failed to mark messages as read'})

# Helper functions to emit real-time updates from other parts of the app

def emit_new_post(post):
    """Emit new post to timeline"""
    socketio.emit('new_post', {
        'post': post.to_dict()
    }, room='timeline')

def emit_new_notification(user_id, notification):
    """Emit new notification to user"""
    socketio.emit('new_notification', {
        'notification': notification.to_dict()
    }, room=f"user_{user_id}")

def emit_post_update(post):
    """Emit post update (likes, shares, etc.)"""
    socketio.emit('post_updated', {
        'post': post.to_dict()
    }, room='timeline')

def emit_post_deleted(post_id):
    """Emit post deletion to timeline"""
    socketio.emit('post_deleted', {
        'post_id': post_id
    }, room='timeline')

def emit_user_status(user_id, status):
    """Emit user status change"""
    socketio.emit('user_status_changed', {
        'user_id': user_id,
        'status': status
    }, room='timeline')

def is_user_online(user_id):
    """Check if user is currently online"""
    return user_id in active_users
