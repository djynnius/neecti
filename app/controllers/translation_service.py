import requests
import json
import hashlib
import re
from flask import current_app
from datetime import datetime, timedelta
import logging
import time

class TranslationService:

    def __init__(self):
        self.ollama_host = current_app.config.get('OLLAMA_HOST', '10.102.109.66')
        self.ollama_port = current_app.config.get('OLLAMA_PORT', 11434)
        self.ollama_model = current_app.config.get('OLLAMA_MODEL', 'gemma3:1b')
        self.supported_languages = current_app.config.get('SUPPORTED_LANGUAGES', ['en', 'fr', 'pt', 'de', 'es'])

        # Regex patterns for mentions and hashtags
        self.mention_pattern = re.compile(r'@([a-zA-Z0-9_]+)')
        self.hashtag_pattern = re.compile(r'#([a-zA-Z0-9_]+)')

    def _extract_preservable_elements(self, content):
        """
        Extract mentions and hashtags that should be preserved during translation

        Args:
            content (str): The content to analyze

        Returns:
            dict: Contains mentions, hashtags, and content with placeholders
        """
        mentions = self.mention_pattern.findall(content)
        hashtags = self.hashtag_pattern.findall(content)

        # Create placeholders for mentions and hashtags
        placeholder_content = content
        mention_placeholders = {}
        hashtag_placeholders = {}

        # Replace mentions with placeholders
        for i, mention in enumerate(mentions):
            placeholder = f"__MENTION_{i}__"
            mention_placeholders[placeholder] = f"@{mention}"
            placeholder_content = placeholder_content.replace(f"@{mention}", placeholder, 1)

        # Replace hashtags with placeholders
        for i, hashtag in enumerate(hashtags):
            placeholder = f"__HASHTAG_{i}__"
            hashtag_placeholders[placeholder] = f"#{hashtag}"
            placeholder_content = placeholder_content.replace(f"#{hashtag}", placeholder, 1)

        return {
            'mentions': mentions,
            'hashtags': hashtags,
            'placeholder_content': placeholder_content,
            'mention_placeholders': mention_placeholders,
            'hashtag_placeholders': hashtag_placeholders
        }

    def _restore_preservable_elements(self, translated_content, mention_placeholders, hashtag_placeholders):
        """
        Restore mentions and hashtags in the translated content

        Args:
            translated_content (str): The translated content with placeholders
            mention_placeholders (dict): Mapping of placeholders to mentions
            hashtag_placeholders (dict): Mapping of placeholders to hashtags

        Returns:
            str: Content with mentions and hashtags restored
        """
        restored_content = translated_content

        # Restore mentions
        for placeholder, mention in mention_placeholders.items():
            restored_content = restored_content.replace(placeholder, mention)

        # Restore hashtags
        for placeholder, hashtag in hashtag_placeholders.items():
            restored_content = restored_content.replace(placeholder, hashtag)

        return restored_content
    
    def _get_cached_translation(self, content, source_lang, target_lang):
        """Get translation from PostgreSQL cache"""
        try:
            from app.models.translation_cache import TranslationCache

            cached = TranslationCache.get_cached_translation(
                content=content,
                source_lang=source_lang,
                target_lang=target_lang
            )

            if cached:
                return cached.translated_content

            return None

        except Exception as e:
            logging.error(f"Error retrieving cached translation: {e}")
            return None

    def _cache_translation(self, content, source_lang, target_lang, translated_content, translation_time_ms=None):
        """Cache translation in PostgreSQL"""
        try:
            from app.models.translation_cache import TranslationCache

            TranslationCache.cache_translation(
                content=content,
                source_lang=source_lang,
                target_lang=target_lang,
                translated_content=translated_content,
                translation_time_ms=translation_time_ms
            )

        except Exception as e:
            logging.error(f"Error caching translation: {e}")
    
    def _call_ollama_api(self, prompt):
        """Call Ollama API for translation"""
        url = f"http://{self.ollama_host}:{self.ollama_port}/api/generate"
        
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more consistent translations
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama API error: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return None
    
    def _create_translation_prompt(self, content, source_lang, target_lang, context=None, has_placeholders=False):
        """Create a prompt for translation that preserves context"""

        lang_names = {
            'en': 'English',
            'fr': 'French',
            'pt': 'Portuguese',
            'de': 'German',
            'es': 'Spanish'
        }

        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        prompt = f"""You are a professional translator specializing in social media content.
Translate the following {source_name} text to {target_name}, preserving:
- The original tone and style
- Emojis and special characters
- Cultural context and meaning"""

        if has_placeholders:
            prompt += """
- Keep ALL placeholder text EXACTLY as-is (text like __MENTION_0__, __HASHTAG_1__, etc.)
- Do NOT translate or modify any text that looks like __WORD_NUMBER__"""

        prompt += "\n\n"

        if context:
            prompt += f"Context: This is part of a social media conversation. Previous context: {context}\n\n"

        prompt += f"Text to translate: {content}\n\nTranslation:"

        return prompt
    
    def translate_content(self, content, source_lang, target_lang, context=None):
        """
        Translate content from source language to target language
        
        Args:
            content (str): Content to translate
            source_lang (str): Source language code (e.g., 'en')
            target_lang (str): Target language code (e.g., 'fr')
            context (str, optional): Additional context for better translation
            
        Returns:
            dict: Translation result with success status and translated content
        """
        
        # Validate languages
        if source_lang not in self.supported_languages or target_lang not in self.supported_languages:
            return {
                'success': False,
                'error': 'Unsupported language',
                'translated_content': content
            }
        
        # If source and target are the same, return original
        if source_lang == target_lang:
            return {
                'success': True,
                'translated_content': content,
                'cached': False
            }
        
        # Extract mentions and hashtags before translation
        preservable_elements = self._extract_preservable_elements(content)
        content_to_translate = preservable_elements['placeholder_content']
        has_placeholders = bool(preservable_elements['mention_placeholders'] or preservable_elements['hashtag_placeholders'])

        # Check cache first (using original content as cache key)
        cached_translation = self._get_cached_translation(content, source_lang, target_lang)
        if cached_translation:
            return {
                'success': True,
                'translated_content': cached_translation,
                'cached': True
            }

        # Create translation prompt with placeholder content
        prompt = self._create_translation_prompt(content_to_translate, source_lang, target_lang, context, has_placeholders)

        # Call Ollama API with timing
        start_time = time.time()
        translated_content = self._call_ollama_api(prompt)
        end_time = time.time()
        translation_time_ms = int((end_time - start_time) * 1000)

        if translated_content:
            # Restore mentions and hashtags in the translated content
            final_translated_content = self._restore_preservable_elements(
                translated_content,
                preservable_elements['mention_placeholders'],
                preservable_elements['hashtag_placeholders']
            )

            # Cache the translation with timing information (using original content as key)
            self._cache_translation(content, source_lang, target_lang, final_translated_content, translation_time_ms)

            return {
                'success': True,
                'translated_content': final_translated_content,
                'cached': False,
                'translation_time_ms': translation_time_ms,
                'preserved_mentions': preservable_elements['mentions'],
                'preserved_hashtags': preservable_elements['hashtags']
            }
        else:
            return {
                'success': False,
                'error': 'Translation service unavailable',
                'translated_content': content
            }
    
    def translate_post(self, post, target_lang, context=None):
        """
        Translate a post object to target language
        
        Args:
            post: Post object with content and original_language
            target_lang (str): Target language code
            context (str, optional): Additional context
            
        Returns:
            dict: Post data with translated content
        """
        
        result = self.translate_content(
            content=post.content,
            source_lang=post.original_language,
            target_lang=target_lang,
            context=context
        )
        
        post_data = post.to_dict()
        post_data['translated_content'] = result['translated_content']
        post_data['translation_success'] = result['success']
        post_data['translation_cached'] = result.get('cached', False)
        post_data['target_language'] = target_lang
        
        if not result['success']:
            post_data['translation_error'] = result.get('error', 'Unknown error')
        
        return post_data
    
    def translate_message(self, message, target_lang):
        """
        Translate a message object to target language
        
        Args:
            message: Message object with content and original_language
            target_lang (str): Target language code
            
        Returns:
            dict: Message data with translated content
        """
        
        result = self.translate_content(
            content=message.content,
            source_lang=message.original_language,
            target_lang=target_lang
        )
        
        message_data = message.to_dict()
        message_data['translated_content'] = result['translated_content']
        message_data['translation_success'] = result['success']
        message_data['translation_cached'] = result.get('cached', False)
        message_data['target_language'] = target_lang
        
        if not result['success']:
            message_data['translation_error'] = result.get('error', 'Unknown error')
        
        return message_data
    
    def get_cache_stats(self):
        """Get translation cache statistics"""
        total_translations = self.translations_collection.count_documents({})
        
        # Get stats by language pair
        pipeline = [
            {
                '$group': {
                    '_id': {
                        'source_lang': '$source_lang',
                        'target_lang': '$target_lang'
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}}
        ]
        
        language_pairs = list(self.translations_collection.aggregate(pipeline))
        
        return {
            'total_translations': total_translations,
            'language_pairs': language_pairs,
            'supported_languages': self.supported_languages
        }
    
    def cleanup_old_cache(self, days=30):
        """Clean up old cached translations"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = self.translations_collection.delete_many({
            'last_accessed': {'$lt': cutoff_date}
        })
        
        return result.deleted_count
