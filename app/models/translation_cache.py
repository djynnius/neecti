from app import db
from datetime import datetime, timedelta
import hashlib


class TranslationCache(db.Model):
    """
    Model for caching translation results to improve performance
    and reduce API calls to the LLM service
    """
    __tablename__ = 'translation_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Content identification
    content_hash = db.Column(db.String(64), nullable=False, index=True)
    original_content = db.Column(db.Text, nullable=False)
    
    # Language information
    source_language = db.Column(db.String(5), nullable=False, index=True)
    target_language = db.Column(db.String(5), nullable=False, index=True)
    
    # Translation result
    translated_content = db.Column(db.Text, nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Optional context for better cache matching
    context = db.Column(db.String(255), nullable=True)
    
    # Performance tracking
    translation_time_ms = db.Column(db.Integer, nullable=True)
    
    # Composite index for efficient lookups
    __table_args__ = (
        db.Index('idx_translation_lookup', 'content_hash', 'source_language', 'target_language'),
        db.Index('idx_language_pair', 'source_language', 'target_language'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    @staticmethod
    def generate_content_hash(content, source_lang, target_lang, context=None):
        """
        Generate a unique hash for the content and translation parameters
        
        Args:
            content (str): The content to translate
            source_lang (str): Source language code
            target_lang (str): Target language code
            context (str, optional): Additional context
            
        Returns:
            str: SHA-256 hash of the content and parameters
        """
        # Create a string that uniquely identifies this translation request
        hash_input = f"{content}|{source_lang}|{target_lang}"
        if context:
            hash_input += f"|{context}"
        
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    @classmethod
    def get_cached_translation(cls, content, source_lang, target_lang, context=None):
        """
        Retrieve a cached translation if it exists
        
        Args:
            content (str): The content to translate
            source_lang (str): Source language code
            target_lang (str): Target language code
            context (str, optional): Additional context
            
        Returns:
            TranslationCache or None: The cached translation if found
        """
        content_hash = cls.generate_content_hash(content, source_lang, target_lang, context)
        
        return cls.query.filter_by(
            content_hash=content_hash,
            source_language=source_lang,
            target_language=target_lang
        ).first()
    
    @classmethod
    def cache_translation(cls, content, source_lang, target_lang, translated_content, 
                         context=None, translation_time_ms=None):
        """
        Cache a new translation result
        
        Args:
            content (str): The original content
            source_lang (str): Source language code
            target_lang (str): Target language code
            translated_content (str): The translated content
            context (str, optional): Additional context
            translation_time_ms (int, optional): Time taken for translation
            
        Returns:
            TranslationCache: The created cache entry
        """
        content_hash = cls.generate_content_hash(content, source_lang, target_lang, context)
        
        # Check if already exists (shouldn't happen, but just in case)
        existing = cls.query.filter_by(
            content_hash=content_hash,
            source_language=source_lang,
            target_language=target_lang
        ).first()
        
        if existing:
            # Update existing entry
            existing.translated_content = translated_content
            existing.updated_at = datetime.utcnow()
            if translation_time_ms is not None:
                existing.translation_time_ms = translation_time_ms
            db.session.commit()
            return existing
        
        # Create new cache entry
        cache_entry = cls(
            content_hash=content_hash,
            original_content=content,
            source_language=source_lang,
            target_language=target_lang,
            translated_content=translated_content,
            context=context,
            translation_time_ms=translation_time_ms
        )
        
        db.session.add(cache_entry)
        db.session.commit()
        
        return cache_entry
    
    @classmethod
    def get_cache_stats(cls):
        """
        Get statistics about the translation cache
        
        Returns:
            dict: Cache statistics
        """
        total_entries = cls.query.count()
        
        # Get language pair statistics
        language_pairs = db.session.query(
            cls.source_language,
            cls.target_language,
            db.func.count(cls.id).label('count')
        ).group_by(cls.source_language, cls.target_language).all()
        
        # Get recent activity (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_entries = cls.query.filter(cls.created_at >= recent_cutoff).count()
        
        return {
            'total_entries': total_entries,
            'language_pairs': [
                {
                    'source': pair.source_language,
                    'target': pair.target_language,
                    'count': pair.count
                }
                for pair in language_pairs
            ],
            'recent_entries_24h': recent_entries
        }
    
    @classmethod
    def cleanup_old_entries(cls, days_old=30):
        """
        Clean up old cache entries to prevent database bloat
        
        Args:
            days_old (int): Remove entries older than this many days
            
        Returns:
            int: Number of entries removed
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        old_entries = cls.query.filter(cls.created_at < cutoff_date)
        count = old_entries.count()
        old_entries.delete()
        db.session.commit()
        
        return count
    
    def to_dict(self):
        """
        Convert the cache entry to a dictionary
        
        Returns:
            dict: Dictionary representation of the cache entry
        """
        return {
            'id': self.id,
            'content_hash': self.content_hash,
            'original_content': self.original_content,
            'source_language': self.source_language,
            'target_language': self.target_language,
            'translated_content': self.translated_content,
            'context': self.context,
            'translation_time_ms': self.translation_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<TranslationCache {self.source_language}->{self.target_language}: {self.original_content[:30]}...>'
