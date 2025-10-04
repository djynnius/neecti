from datetime import datetime
from app import db

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_read = db.Column(db.Boolean, default=False)
    is_saved = db.Column(db.Boolean, default=False)  # If true, message persists after logout
    is_deleted_by_sender = db.Column(db.Boolean, default=False)
    is_deleted_by_recipient = db.Column(db.Boolean, default=False)
    original_language = db.Column(db.String(5), default='en')
    
    def mark_as_read(self):
        """Mark message as read"""
        self.is_read = True
        db.session.commit()
    
    def save_message(self):
        """Save message to persist after logout"""
        self.is_saved = True
        db.session.commit()
    
    def delete_for_user(self, user_id):
        """Delete message for a specific user"""
        if user_id == self.sender_id:
            self.is_deleted_by_sender = True
        elif user_id == self.recipient_id:
            self.is_deleted_by_recipient = True
        
        # If both users deleted, remove from database
        if self.is_deleted_by_sender and self.is_deleted_by_recipient:
            db.session.delete(self)
        
        db.session.commit()
    
    def is_visible_to_user(self, user_id):
        """Check if message is visible to user"""
        if user_id == self.sender_id and self.is_deleted_by_sender:
            return False
        if user_id == self.recipient_id and self.is_deleted_by_recipient:
            return False
        return True
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'sender': self.sender.to_dict() if self.sender else None,
            'recipient': self.recipient.to_dict() if self.recipient else None,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'is_read': self.is_read,
            'is_saved': self.is_saved,
            'original_language': self.original_language
        }
    
    @staticmethod
    def get_conversation(user1_id, user2_id, limit=50):
        """Get conversation between two users"""
        messages = Message.query.filter(
            ((Message.sender_id == user1_id) & (Message.recipient_id == user2_id)) |
            ((Message.sender_id == user2_id) & (Message.recipient_id == user1_id))
        ).filter(
            ~((Message.sender_id == user1_id) & (Message.is_deleted_by_sender == True)) &
            ~((Message.recipient_id == user1_id) & (Message.is_deleted_by_recipient == True))
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        return messages[::-1]  # Reverse to get chronological order
    
    @staticmethod
    def cleanup_ephemeral_messages(user_id):
        """Clean up ephemeral messages for user on logout"""
        ephemeral_messages = Message.query.filter(
            ((Message.sender_id == user_id) | (Message.recipient_id == user_id)) &
            (Message.is_saved == False)
        ).all()
        
        for message in ephemeral_messages:
            message.delete_for_user(user_id)
    
    def __repr__(self):
        return f'<Message {self.id}: {self.sender.handle} -> {self.recipient.handle}>'


class Conversation(db.Model):
    """Model to track conversation metadata"""
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    last_message = db.relationship('Message', foreign_keys=[last_message_id])
    
    def get_other_user(self, current_user_id):
        """Get the other user in the conversation"""
        return self.user2 if self.user1_id == current_user_id else self.user1
    
    def get_unread_count(self, user_id):
        """Get unread message count for user"""
        return Message.query.filter_by(
            recipient_id=user_id,
            is_read=False
        ).filter(
            ((Message.sender_id == self.user1_id) & (Message.recipient_id == self.user2_id)) |
            ((Message.sender_id == self.user2_id) & (Message.recipient_id == self.user1_id))
        ).count()
    
    def to_dict(self, current_user_id):
        """Convert conversation to dictionary"""
        other_user = self.get_other_user(current_user_id)
        return {
            'id': self.id,
            'other_user': other_user.to_dict(),
            'last_message': self.last_message.to_dict() if self.last_message else None,
            'last_activity': self.last_activity.isoformat(),
            'unread_count': self.get_unread_count(current_user_id),
            'created_at': self.created_at.isoformat()
        }
    
    @staticmethod
    def get_or_create(user1_id, user2_id):
        """Get existing conversation or create new one"""
        # Ensure consistent ordering
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        conversation = Conversation.query.filter_by(
            user1_id=user1_id,
            user2_id=user2_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                user1_id=user1_id,
                user2_id=user2_id
            )
            db.session.add(conversation)
            db.session.commit()
        
        return conversation
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.user1.handle} <-> {self.user2.handle}>'
