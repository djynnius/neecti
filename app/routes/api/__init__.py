from flask import Blueprint
from app.controllers.api_controller import ApiController
from app.controllers.translation_controller import TranslationController
from app.controllers.search_controller import SearchController
from app.controllers.moderation_controller import ModerationController

api_bp = Blueprint('api', __name__, url_prefix='/api')

# General API routes
api_bp.add_url_rule('/stats', 'stats', ApiController.get_stats, methods=['GET'])
api_bp.add_url_rule('/hashtag/<string:hashtag>', 'hashtag_posts', ApiController.get_hashtag_posts, methods=['GET'])
api_bp.add_url_rule('/trending/hashtags', 'trending_hashtags', ApiController.get_trending_hashtags, methods=['GET'])
api_bp.add_url_rule('/cleanup', 'cleanup', ApiController.cleanup_old_data, methods=['POST'])
api_bp.add_url_rule('/create-test-users', 'create_test_users', ApiController.create_test_users, methods=['POST'])

# Moderation routes
api_bp.add_url_rule('/report', 'create_report', ModerationController.create_report, methods=['POST'])
api_bp.add_url_rule('/moderation/reports', 'get_reports', ModerationController.get_reports, methods=['GET'])
api_bp.add_url_rule('/moderation/reports/<int:report_id>', 'get_report', ModerationController.get_report, methods=['GET'])
api_bp.add_url_rule('/moderation/reports/<int:report_id>/resolve', 'resolve_report', ModerationController.resolve_report, methods=['POST'])
api_bp.add_url_rule('/moderation/reports/bulk', 'bulk_action', ModerationController.bulk_action, methods=['POST'])
api_bp.add_url_rule('/moderation/stats', 'moderation_stats', ModerationController.get_moderation_stats, methods=['GET'])
api_bp.add_url_rule('/moderation/content', 'reported_content', ModerationController.get_reported_content, methods=['GET'])

# Search routes
api_bp.add_url_rule('/search', 'global_search', SearchController.global_search, methods=['GET'])
api_bp.add_url_rule('/search/users', 'search_users', SearchController.search_users, methods=['GET'])
api_bp.add_url_rule('/search/posts', 'search_posts', SearchController.search_posts, methods=['GET'])
api_bp.add_url_rule('/search/hashtags', 'search_hashtags', SearchController.search_hashtags, methods=['GET'])
api_bp.add_url_rule('/search/suggestions', 'search_suggestions', SearchController.get_search_suggestions, methods=['GET'])

# Translation routes
api_bp.add_url_rule('/translate/post/<int:post_id>', 'translate_post', TranslationController.translate_post, methods=['GET'])
api_bp.add_url_rule('/translate/message/<int:message_id>', 'translate_message', TranslationController.translate_message, methods=['GET'])
api_bp.add_url_rule('/translate/text', 'translate_text', TranslationController.translate_text, methods=['POST'])
api_bp.add_url_rule('/translate/languages', 'supported_languages', TranslationController.get_supported_languages, methods=['GET'])
api_bp.add_url_rule('/translate/stats', 'translation_stats', TranslationController.get_translation_stats, methods=['GET'])
api_bp.add_url_rule('/translate/cleanup', 'cleanup_translations', TranslationController.cleanup_translation_cache, methods=['POST'])
api_bp.add_url_rule('/translate/test', 'test_llm', TranslationController.test_llm_connection, methods=['GET'])
