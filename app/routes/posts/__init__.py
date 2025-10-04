from flask import Blueprint
from app.controllers.posts_controller import PostsController

posts_bp = Blueprint('posts', __name__, url_prefix='/posts')

# Post routes
posts_bp.add_url_rule('/', 'create_post', PostsController.create_post, methods=['POST'])
posts_bp.add_url_rule('/<int:post_id>', 'get_post', PostsController.get_post, methods=['GET'])
posts_bp.add_url_rule('/<int:post_id>', 'delete_post', PostsController.delete_post, methods=['DELETE'])
posts_bp.add_url_rule('/<int:post_id>/like', 'like_post', PostsController.like_post, methods=['POST'])
posts_bp.add_url_rule('/<int:post_id>/share', 'share_post', PostsController.share_post, methods=['POST'])
posts_bp.add_url_rule('/timeline', 'timeline', PostsController.get_timeline, methods=['GET'])
posts_bp.add_url_rule('/trending', 'trending', PostsController.get_trending, methods=['GET'])
posts_bp.add_url_rule('/search', 'search_posts', PostsController.search_posts, methods=['GET'])
