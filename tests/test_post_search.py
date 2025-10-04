import unittest
import json
from app import create_app, db
from app.models import User, Post
from app.controllers.search_controller import SearchController


class PostSearchTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create test user
        self.test_user = User(
            handle='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password_hash='dummy_hash',
            is_active=True
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        # Create test posts
        self.test_posts = [
            Post(
                content='Hello world! This is my first post #hello #world',
                user_id=self.test_user.id,
                original_language='en',
                hashtags='["hello", "world"]',
                mentions=None
            ),
            Post(
                content='Working on a new Python project #python #coding @djynnius',
                user_id=self.test_user.id,
                original_language='en',
                hashtags='["python", "coding"]',
                mentions='["djynnius"]'
            ),
            Post(
                content='Beautiful sunset today #nature #photography #sunset',
                user_id=self.test_user.id,
                original_language='en',
                hashtags='["nature", "photography", "sunset"]',
                mentions=None
            ),
            Post(
                content='Thanks @debzdebola for the great advice! #grateful',
                user_id=self.test_user.id,
                original_language='en',
                hashtags='["grateful"]',
                mentions='["debzdebola"]'
            ),
            Post(
                content='Post with null hashtags and mentions',
                user_id=self.test_user.id,
                original_language='en',
                hashtags=None,
                mentions=None
            )
        ]
        
        for post in self.test_posts:
            db.session.add(post)
        db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        self.app_context.pop()

    def test_search_posts_by_content(self):
        """Test searching posts by content (case-insensitive)"""
        # Test lowercase
        posts = Post.query.filter_by(is_deleted=False).filter(
            db.func.lower(Post.content).contains('python')
        ).all()
        self.assertEqual(len(posts), 1)
        self.assertIn('Python', posts[0].content)
        
        # Test uppercase
        posts = Post.query.filter_by(is_deleted=False).filter(
            db.func.lower(Post.content).contains('HELLO')
        ).all()
        self.assertEqual(len(posts), 1)
        self.assertIn('Hello', posts[0].content)

    def test_search_posts_by_hashtags(self):
        """Test searching posts by hashtags (case-insensitive)"""
        posts = Post.query.filter_by(is_deleted=False).filter(
            db.and_(Post.hashtags.isnot(None), db.func.lower(Post.hashtags).contains('python'))
        ).all()
        self.assertEqual(len(posts), 1)
        self.assertIn('python', posts[0].hashtags)

    def test_search_posts_by_mentions(self):
        """Test searching posts by mentions (case-insensitive)"""
        posts = Post.query.filter_by(is_deleted=False).filter(
            db.and_(Post.mentions.isnot(None), db.func.lower(Post.mentions).contains('djynnius'))
        ).all()
        self.assertEqual(len(posts), 1)
        self.assertIn('djynnius', posts[0].mentions)

    def test_search_posts_with_null_fields(self):
        """Test that search handles null hashtags and mentions properly"""
        # This should not crash even though some posts have null hashtags/mentions
        posts = Post.query.filter_by(is_deleted=False).filter(
            db.or_(
                db.func.lower(Post.content).contains('null'),
                db.and_(Post.hashtags.isnot(None), db.func.lower(Post.hashtags).contains('null')),
                db.and_(Post.mentions.isnot(None), db.func.lower(Post.mentions).contains('null'))
            )
        ).all()
        self.assertEqual(len(posts), 1)
        self.assertIn('null', posts[0].content)

    def test_hashtag_search_case_insensitive(self):
        """Test hashtag search is case-insensitive"""
        # Test with different cases
        test_cases = ['nature', 'NATURE', 'Nature', 'nAtUrE']
        
        for query in test_cases:
            hashtag_results = SearchController._search_hashtags(query)
            self.assertGreater(len(hashtag_results), 0)
            # Should find the 'nature' hashtag
            found_nature = any(h['hashtag'] == 'nature' for h in hashtag_results)
            self.assertTrue(found_nature, f"Failed to find 'nature' hashtag with query '{query}'")

    def test_global_search_posts(self):
        """Test global search for posts"""
        with self.app.test_request_context('/?q=python&type=posts'):
            response, status = SearchController.global_search()
            self.assertEqual(status, 200)
            
            result = response.get_json()
            posts = result['results']['posts']
            self.assertGreater(len(posts), 0)
            
            # Should find the Python post
            found_python = any('Python' in post['content'] for post in posts)
            self.assertTrue(found_python)


if __name__ == '__main__':
    unittest.main()
