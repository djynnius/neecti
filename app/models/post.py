from datetime import datetime
from app import db

# Association tables
post_likes = db.Table('post_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
)

post_shares = db.Table('post_shares',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('shared_at', db.DateTime, default=datetime.utcnow)
)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Conversation branching fields
    parent_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    conversation_root_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    branch_level = db.Column(db.Integer, default=0)  # 0 = root post, 1 = reply, 2 = reply to reply, etc.
    is_branch_root = db.Column(db.Boolean, default=False)  # True if this starts a new branch
    
    # Content metadata
    original_language = db.Column(db.String(5), default='en')
    hashtags = db.Column(db.Text)  # JSON string of hashtags
    mentions = db.Column(db.Text)  # JSON string of mentioned users
    
    # Engagement metrics
    likes_count = db.Column(db.Integer, default=0)
    replies_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # Moderation
    is_deleted = db.Column(db.Boolean, default=False)
    is_reported = db.Column(db.Boolean, default=False)
    
    # Self-referential relationships for conversation tree
    parent = db.relationship('Post', foreign_keys=[parent_id], remote_side=[id], backref='replies')
    conversation_root = db.relationship('Post', foreign_keys=[conversation_root_id], remote_side=[id])
    
    # Other relationships
    images = db.relationship('PostImage', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    # Many-to-many relationships
    liked_by = db.relationship('User', secondary=post_likes, backref='liked_posts')
    shared_by = db.relationship('User', secondary=post_shares, backref='shared_posts')
    
    def get_conversation_tree(self, max_depth=5):
        """Get the conversation tree starting from this post"""
        if self.branch_level >= max_depth:
            return []
        
        replies = Post.query.filter_by(parent_id=self.id, is_deleted=False)\
                           .order_by(Post.created_at.asc()).all()
        
        tree = []
        for reply in replies:
            reply_data = reply.to_dict()
            reply_data['replies'] = reply.get_conversation_tree(max_depth)
            tree.append(reply_data)
        
        return tree
    
    def get_conversation_path(self):
        """Get the path from root to this post"""
        path = []
        current = self
        
        while current:
            path.insert(0, current)
            current = current.parent
        
        return path
    
    def create_branch(self, user, content):
        """Create a new branch from this post"""
        branch_post = Post(
            content=content,
            user_id=user.id,
            parent_id=self.id,
            conversation_root_id=self.conversation_root_id or self.id,
            branch_level=self.branch_level + 1,
            is_branch_root=True,
            original_language=user.preferred_language
        )
        return branch_post
    
    def add_reply(self, user, content):
        """Add a reply to this post"""
        reply = Post(
            content=content,
            user_id=user.id,
            parent_id=self.id,
            conversation_root_id=self.conversation_root_id or self.id,
            branch_level=self.branch_level + 1,
            is_branch_root=False,
            original_language=user.preferred_language
        )
        return reply
    
    def like(self, user):
        """Like this post"""
        if user not in self.liked_by:
            self.liked_by.append(user)
            self.likes_count += 1
    
    def unlike(self, user):
        """Unlike this post"""
        if user in self.liked_by:
            self.liked_by.remove(user)
            self.likes_count -= 1
    
    def is_liked_by(self, user):
        """Check if post is liked by user"""
        return user in self.liked_by
    
    def share(self, user):
        """Share this post"""
        if user not in self.shared_by:
            self.shared_by.append(user)
            self.shares_count += 1
    
    def get_trending_score(self):
        """Calculate trending score based on engagement"""
        # Simple trending algorithm - can be improved
        time_factor = (datetime.utcnow() - self.created_at).total_seconds() / 3600  # hours
        engagement = self.likes_count + (self.replies_count * 2) + (self.shares_count * 3)
        return engagement / (time_factor + 1)

    def delete_with_children(self):
        """Delete this post and all its child posts (replies) recursively"""
        from app import db

        # Mark all posts for deletion recursively
        self._mark_for_deletion()

        # Commit all changes at once
        db.session.commit()

    def _mark_for_deletion(self):
        """Recursively mark this post and all children for deletion"""
        # Get all direct replies to this post
        direct_replies = Post.query.filter_by(parent_id=self.id, is_deleted=False).all()

        # Recursively mark all child posts for deletion first
        for reply in direct_replies:
            reply._mark_for_deletion()

        # Mark this post as deleted
        self.is_deleted = True

        # Update parent's reply count if this post has a parent
        if self.parent_id:
            parent_post = Post.query.get(self.parent_id)
            if parent_post and parent_post.replies_count > 0:
                parent_post.replies_count -= 1
    
    def to_dict(self, include_replies=False):
        """Convert post to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'content': self.content,
            'user_id': self.user_id,
            'author': self.author.to_dict() if self.author else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'parent_id': self.parent_id,
            'conversation_root_id': self.conversation_root_id,
            'branch_level': self.branch_level,
            'is_branch_root': self.is_branch_root,
            'original_language': self.original_language,
            'likes_count': self.likes_count,
            'replies_count': self.replies_count,
            'shares_count': self.shares_count,
            'views_count': self.views_count,
            'images': [img.to_dict() for img in self.images],
            'trending_score': self.get_trending_score()
        }
        
        if include_replies:
            data['replies'] = self.get_conversation_tree()
        
        return data
    
    def __repr__(self):
        return f'<Post {self.id}: {self.content[:50]}...>'


class PostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<PostImage {self.id}: {self.filename}>'
