from datetime import datetime, timedelta
from app import db

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'like', 'reply', 'follow', 'share', 'mention'
    message = db.Column(db.Text, nullable=False)
    related_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # User who triggered the notification
    related_post_id = db.Column(db.Integer, db.ForeignKey('post.id'))  # Related post if applicable
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    related_post = db.relationship('Post', foreign_keys=[related_post_id])
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        db.session.commit()
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'related_user': self.related_user.to_dict() if self.related_user else None,
            'related_post': self.related_post.to_dict() if self.related_post else None,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }
    
    @staticmethod
    def create_like_notification(post, liker):
        """Create notification for post like"""
        if post.author.id != liker.id:  # Don't notify self
            notification = Notification(
                user_id=post.author.id,
                type='like',
                message=f'{liker.handle} liked your post',
                related_user_id=liker.id,
                related_post_id=post.id
            )
            db.session.add(notification)
            db.session.commit()

            # Emit real-time notification
            try:
                from app.controllers.socketio_controller import emit_new_notification
                emit_new_notification(post.author.id, notification)
            except ImportError:
                pass  # SocketIO not available

            return notification
    
    @staticmethod
    def create_reply_notification(post, replier):
        """Create notification for post reply"""
        if post.author.id != replier.id:  # Don't notify self
            notification = Notification(
                user_id=post.author.id,
                type='reply',
                message=f'{replier.handle} replied to your post',
                related_user_id=replier.id,
                related_post_id=post.id
            )
            db.session.add(notification)
            db.session.commit()
            return notification
    
    @staticmethod
    def create_follow_notification(followed_user, follower):
        """Create notification for new follower"""
        notification = Notification(
            user_id=followed_user.id,
            type='follow',
            message=f'{follower.handle} started following you',
            related_user_id=follower.id
        )
        db.session.add(notification)
        db.session.commit()

        # Emit real-time notification
        try:
            from app.controllers.socketio_controller import emit_new_notification
            emit_new_notification(followed_user.id, notification)
        except ImportError:
            pass  # SocketIO not available

        return notification
    
    @staticmethod
    def create_share_notification(post, sharer):
        """Create notification for post share"""
        if post.author.id != sharer.id:  # Don't notify self
            notification = Notification(
                user_id=post.author.id,
                type='share',
                message=f'{sharer.handle} shared your post',
                related_user_id=sharer.id,
                related_post_id=post.id
            )
            db.session.add(notification)
            db.session.commit()
            return notification
    
    @staticmethod
    def create_mention_notification(post, mentioned_user):
        """Create notification for mention in post"""
        if post.author.id != mentioned_user.id:  # Don't notify self
            notification = Notification(
                user_id=mentioned_user.id,
                type='mention',
                message=f'{post.author.handle} mentioned you in a post',
                related_user_id=post.author.id,
                related_post_id=post.id
            )
            db.session.add(notification)
            db.session.commit()
            return notification
    
    @staticmethod
    def cleanup_old_notifications():
        """Clean up notifications older than 10 days"""
        cutoff_date = datetime.utcnow() - timedelta(days=10)
        old_notifications = Notification.query.filter(
            Notification.created_at < cutoff_date
        ).all()
        
        for notification in old_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        return len(old_notifications)
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.type} for {self.user.handle}>'


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reported_post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    reason = db.Column(db.String(100), nullable=False)  # 'spam', 'harassment', 'inappropriate', etc.
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'reviewed', 'resolved', 'dismissed'
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    
    def resolve(self, admin_user, notes=None):
        """Mark report as resolved"""
        self.status = 'resolved'
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by_id = admin_user.id
        if notes:
            self.admin_notes = notes
        db.session.commit()
    
    def dismiss(self, admin_user, notes=None):
        """Dismiss report"""
        self.status = 'dismissed'
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by_id = admin_user.id
        if notes:
            self.admin_notes = notes
        db.session.commit()
    
    def to_dict(self):
        """Convert report to dictionary"""
        return {
            'id': self.id,
            'reporter': self.reporter.to_dict() if self.reporter else None,
            'reported_user': self.reported_user.to_dict() if self.reported_user else None,
            'reported_post': self.reported_post.to_dict() if self.reported_post else None,
            'reason': self.reason,
            'description': self.description,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by.to_dict() if self.reviewed_by else None
        }
    
    def __repr__(self):
        return f'<Report {self.id}: {self.reason} by {self.reporter.handle}>'
