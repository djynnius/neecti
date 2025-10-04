from flask import request, jsonify
from flask_login import current_user
from app import db
from app.models import User, Post, Notification
import json
import re
from datetime import datetime, timedelta

class SearchController:
    
    @staticmethod
    def global_search():
        """Global search across users, posts, and hashtags"""
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')  # 'all', 'users', 'posts', 'hashtags'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        results = {}
        
        if search_type in ['all', 'users']:
            # Search users (case-insensitive)
            users = User.query.filter_by(is_active=True).filter(
                db.or_(
                    User.handle.contains(query.lower()),
                    db.func.lower(User.first_name).contains(query.lower()),
                    db.func.lower(User.last_name).contains(query.lower()),
                    db.and_(User.bio.isnot(None), db.func.lower(User.bio).contains(query.lower()))
                )
            ).limit(per_page if search_type == 'users' else 5).all()
            
            results['users'] = [user.to_dict() for user in users]
        
        if search_type in ['all', 'posts']:
            # Search posts (case-insensitive)
            posts_query = Post.query.filter_by(is_deleted=False).filter(
                db.or_(
                    db.func.lower(Post.content).contains(query.lower()),
                    db.and_(Post.hashtags.isnot(None), db.func.lower(Post.hashtags).contains(query.lower())),
                    db.and_(Post.mentions.isnot(None), db.func.lower(Post.mentions).contains(query.lower()))
                )
            ).order_by(Post.created_at.desc())
            
            if search_type == 'posts':
                posts = posts_query.paginate(
                    page=page, per_page=per_page, error_out=False
                )
                results['posts'] = [post.to_dict() for post in posts.items]
                results['pagination'] = {
                    'page': posts.page,
                    'pages': posts.pages,
                    'per_page': posts.per_page,
                    'total': posts.total,
                    'has_next': posts.has_next,
                    'has_prev': posts.has_prev
                }
            else:
                posts = posts_query.limit(5).all()
                results['posts'] = [post.to_dict() for post in posts]
        
        if search_type in ['all', 'hashtags']:
            # Search hashtags
            hashtag_results = SearchController._search_hashtags(query)
            results['hashtags'] = hashtag_results
        
        return jsonify({
            'query': query,
            'search_type': search_type,
            'results': results
        }), 200
    
    @staticmethod
    def _search_hashtags(query):
        """Search for hashtags in posts"""
        # Get posts with hashtags containing the query (case-insensitive)
        posts = Post.query.filter_by(is_deleted=False)\
                         .filter(Post.hashtags.isnot(None))\
                         .filter(db.func.lower(Post.hashtags).contains(query.lower()))\
                         .all()
        
        hashtag_counts = {}
        for post in posts:
            try:
                hashtags = json.loads(post.hashtags)
                for hashtag in hashtags:
                    if query.lower() in hashtag.lower():
                        hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
            except:
                continue
        
        # Sort by count and return top results
        sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [
            {'hashtag': hashtag, 'count': count}
            for hashtag, count in sorted_hashtags
        ]
    
    @staticmethod
    def search_users():
        """Advanced user search with filters"""
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort', 'relevance')  # 'relevance', 'followers', 'recent'
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Base query (case-insensitive)
        users_query = User.query.filter_by(is_active=True).filter(
            db.or_(
                User.handle.contains(query.lower()),
                db.func.lower(User.first_name).contains(query.lower()),
                db.func.lower(User.last_name).contains(query.lower()),
                db.and_(User.bio.isnot(None), db.func.lower(User.bio).contains(query.lower()))
            )
        )
        
        # Apply sorting
        if sort_by == 'followers':
            # This would require a subquery to count followers
            # For simplicity, we'll use created_at as a proxy
            users_query = users_query.order_by(User.created_at.desc())
        elif sort_by == 'recent':
            users_query = users_query.order_by(User.created_at.desc())
        else:  # relevance - prioritize exact handle matches
            users_query = users_query.order_by(
                User.handle.like(f'{query.lower()}%').desc(),
                User.created_at.desc()
            )
        
        users = users_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            },
            'query': query,
            'sort_by': sort_by
        }), 200
    
    @staticmethod
    def search_posts():
        """Advanced post search with filters"""
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort', 'recent')  # 'recent', 'popular', 'relevant'
        date_filter = request.args.get('date')  # 'today', 'week', 'month'
        user_id = request.args.get('user_id', type=int)  # Search within specific user's posts
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Base query (case-insensitive)
        posts_query = Post.query.filter_by(is_deleted=False).filter(
            db.or_(
                db.func.lower(Post.content).contains(query.lower()),
                db.and_(Post.hashtags.isnot(None), db.func.lower(Post.hashtags).contains(query.lower())),
                db.and_(Post.mentions.isnot(None), db.func.lower(Post.mentions).contains(query.lower()))
            )
        )
        
        # Apply user filter
        if user_id:
            posts_query = posts_query.filter_by(user_id=user_id)
        
        # Apply date filter
        if date_filter:
            now = datetime.utcnow()
            if date_filter == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_filter == 'week':
                start_date = now - timedelta(days=7)
            elif date_filter == 'month':
                start_date = now - timedelta(days=30)
            else:
                start_date = None
            
            if start_date:
                posts_query = posts_query.filter(Post.created_at >= start_date)
        
        # Apply sorting
        if sort_by == 'popular':
            # Sort by engagement (likes + replies + shares)
            posts_query = posts_query.order_by(
                (Post.likes_count + Post.replies_count + Post.shares_count).desc(),
                Post.created_at.desc()
            )
        elif sort_by == 'relevant':
            # Prioritize posts with query in content over hashtags/mentions
            posts_query = posts_query.order_by(
                Post.content.contains(query).desc(),
                Post.created_at.desc()
            )
        else:  # recent
            posts_query = posts_query.order_by(Post.created_at.desc())
        
        posts = posts_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'posts': [post.to_dict() for post in posts.items],
            'pagination': {
                'page': posts.page,
                'pages': posts.pages,
                'per_page': posts.per_page,
                'total': posts.total,
                'has_next': posts.has_next,
                'has_prev': posts.has_prev
            },
            'query': query,
            'filters': {
                'sort_by': sort_by,
                'date_filter': date_filter,
                'user_id': user_id
            }
        }), 200
    
    @staticmethod
    def search_hashtags():
        """Search and get trending hashtags"""
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        time_period = request.args.get('period', 'week')  # 'day', 'week', 'month', 'all'
        
        # Set time filter
        now = datetime.utcnow()
        if time_period == 'day':
            start_date = now - timedelta(days=1)
        elif time_period == 'week':
            start_date = now - timedelta(days=7)
        elif time_period == 'month':
            start_date = now - timedelta(days=30)
        else:  # all
            start_date = None
        
        # Base query for posts with hashtags
        posts_query = Post.query.filter_by(is_deleted=False)\
                                .filter(Post.hashtags.isnot(None))
        
        if start_date:
            posts_query = posts_query.filter(Post.created_at >= start_date)
        
        if query:
            posts_query = posts_query.filter(db.func.lower(Post.hashtags).contains(query.lower()))
        
        posts = posts_query.all()
        
        # Count hashtag occurrences
        hashtag_counts = {}
        for post in posts:
            try:
                hashtags = json.loads(post.hashtags)
                for hashtag in hashtags:
                    if not query or query.lower() in hashtag.lower():
                        hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
            except:
                continue
        
        # Sort by count and limit results
        sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return jsonify({
            'hashtags': [
                {'hashtag': hashtag, 'count': count}
                for hashtag, count in sorted_hashtags
            ],
            'query': query,
            'time_period': time_period,
            'total_found': len(sorted_hashtags)
        }), 200
    
    @staticmethod
    def get_search_suggestions():
        """Get search suggestions based on query"""
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'suggestions': []}), 200
        
        suggestions = []
        
        # User suggestions (handles and names) - case-insensitive
        users = User.query.filter_by(is_active=True).filter(
            db.or_(
                User.handle.like(f'{query.lower()}%'),
                db.func.lower(User.first_name).like(f'{query.lower()}%'),
                db.func.lower(User.last_name).like(f'{query.lower()}%')
            )
        ).limit(5).all()
        
        for user in users:
            suggestions.append({
                'type': 'user',
                'text': f'@{user.handle}',
                'display': f'{user.full_name} (@{user.handle})',
                'id': user.id
            })
        
        # Hashtag suggestions
        hashtag_results = SearchController._search_hashtags(query)[:5]
        for hashtag_data in hashtag_results:
            suggestions.append({
                'type': 'hashtag',
                'text': f"#{hashtag_data['hashtag']}",
                'display': f"#{hashtag_data['hashtag']} ({hashtag_data['count']} posts)",
                'count': hashtag_data['count']
            })
        
        return jsonify({
            'suggestions': suggestions,
            'query': query
        }), 200
