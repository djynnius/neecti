from flask import request, jsonify
from flask_login import current_user
from app.controllers.translation_service import TranslationService
from app.models import Post, Message
from app import db

class TranslationController:
    
    @staticmethod
    def translate_post(post_id):
        """Translate a specific post"""
        target_lang = request.args.get('lang', 'en')
        
        post = Post.query.filter_by(id=post_id, is_deleted=False).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Get context from parent post if it's a reply
        context = None
        if post.parent:
            context = post.parent.content[:100]  # First 100 chars as context
        
        try:
            translation_service = TranslationService()
            translated_post = translation_service.translate_post(post, target_lang, context)
            
            return jsonify({
                'post': translated_post
            }), 200
            
        except Exception as e:
            return jsonify({'error': 'Translation service error'}), 500
    
    @staticmethod
    def translate_message(message_id):
        """Translate a specific message"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        target_lang = request.args.get('lang', current_user.preferred_language)
        
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Check if user has access to this message
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        if not message.is_visible_to_user(current_user.id):
            return jsonify({'error': 'Message not found'}), 404
        
        try:
            translation_service = TranslationService()
            translated_message = translation_service.translate_message(message, target_lang)
            
            return jsonify({
                'message': translated_message
            }), 200
            
        except Exception as e:
            return jsonify({'error': 'Translation service error'}), 500
    
    @staticmethod
    def translate_text():
        """Translate arbitrary text"""
        data = request.get_json()
        
        content = data.get('content', '').strip()
        source_lang = data.get('source_lang', 'en')
        target_lang = data.get('target_lang', 'en')
        context = data.get('context', '')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        try:
            translation_service = TranslationService()
            result = translation_service.translate_content(
                content=content,
                source_lang=source_lang,
                target_lang=target_lang,
                context=context
            )
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': 'Translation service error'}), 500
    
    @staticmethod
    def get_supported_languages():
        """Get list of supported languages"""
        try:
            translation_service = TranslationService()
            
            languages = {
                'en': 'English',
                'fr': 'French', 
                'pt': 'Portuguese',
                'de': 'German',
                'es': 'Spanish'
            }
            
            supported = []
            for code in translation_service.supported_languages:
                supported.append({
                    'code': code,
                    'name': languages.get(code, code)
                })
            
            return jsonify({
                'supported_languages': supported
            }), 200
            
        except Exception as e:
            return jsonify({'error': 'Service error'}), 500
    
    @staticmethod
    def get_translation_stats():
        """Get translation cache statistics (admin only)"""
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        try:
            translation_service = TranslationService()
            stats = translation_service.get_cache_stats()
            
            return jsonify({
                'stats': stats
            }), 200
            
        except Exception as e:
            return jsonify({'error': 'Service error'}), 500
    
    @staticmethod
    def cleanup_translation_cache():
        """Clean up old translation cache (admin only)"""
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403

        days = request.args.get('days', 30, type=int)

        try:
            translation_service = TranslationService()
            deleted_count = translation_service.cleanup_old_cache(days)

            return jsonify({
                'message': f'Cleaned up {deleted_count} old translations',
                'deleted_count': deleted_count
            }), 200

        except Exception as e:
            return jsonify({'error': 'Service error'}), 500

    @staticmethod
    def test_llm_connection():
        """Test LLM connection and translation service"""
        try:
            translation_service = TranslationService()

            # Test simple translation
            test_result = translation_service.translate_content(
                content="Hello, how are you?",
                source_lang="en",
                target_lang="fr"
            )

            # Test LLM connectivity by checking if we got a real translation
            llm_working = test_result['success'] and not test_result.get('cached', False)

            return jsonify({
                'llm_connected': llm_working,
                'translation_service_available': True,
                'test_translation': test_result,
                'ollama_config': {
                    'host': translation_service.ollama_host,
                    'port': translation_service.ollama_port,
                    'model': translation_service.ollama_model
                },
                'mongodb_connected': True,  # If we get here, MongoDB is working
                'supported_languages': translation_service.supported_languages
            }), 200

        except Exception as e:
            return jsonify({
                'llm_connected': False,
                'translation_service_available': False,
                'error': str(e),
                'ollama_config': {
                    'host': '10.102.109.66',
                    'port': 11434,
                    'model': 'gemma3:1b'
                }
            }), 500
