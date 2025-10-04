import unittest
import json
from app import create_app, db
from app.models import User

class SearchTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test users
            user1 = User(
                handle='testuser1',
                email='test1@example.com',
                first_name='John',
                last_name='Doe'
            )
            user1.set_password('password123')
            
            user2 = User(
                handle='testuser2',
                email='test2@example.com',
                first_name='Jane',
                last_name='Smith',
                bio='Software developer'
            )
            user2.set_password('password123')
            
            user3 = User(
                handle='inactive_user',
                email='inactive@example.com',
                first_name='Inactive',
                last_name='User',
                is_active=False
            )
            user3.set_password('password123')
            
            db.session.add_all([user1, user2, user3])
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_search_users_by_first_name(self):
        """Test searching users by first name (case-insensitive)"""
        response = self.client.get('/api/search/users?q=john')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 1)
        self.assertEqual(data['users'][0]['handle'], 'testuser1')
    
    def test_search_users_by_last_name(self):
        """Test searching users by last name (case-insensitive)"""
        response = self.client.get('/api/search/users?q=smith')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 1)
        self.assertEqual(data['users'][0]['handle'], 'testuser2')
    
    def test_search_users_by_handle(self):
        """Test searching users by handle"""
        response = self.client.get('/api/search/users?q=testuser1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 1)
        self.assertEqual(data['users'][0]['handle'], 'testuser1')
    
    def test_search_users_by_bio(self):
        """Test searching users by bio content"""
        response = self.client.get('/api/search/users?q=developer')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 1)
        self.assertEqual(data['users'][0]['handle'], 'testuser2')
    
    def test_search_users_case_insensitive(self):
        """Test that search is case-insensitive"""
        response = self.client.get('/api/search/users?q=JOHN')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 1)
        self.assertEqual(data['users'][0]['handle'], 'testuser1')
    
    def test_search_excludes_inactive_users(self):
        """Test that inactive users are excluded from search results"""
        response = self.client.get('/api/search/users?q=inactive')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 0)
    
    def test_search_with_empty_query(self):
        """Test search with empty query returns error"""
        response = self.client.get('/api/search/users?q=')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_global_search_users(self):
        """Test global search for users"""
        response = self.client.get('/api/search?q=john&type=users')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertIn('users', data['results'])
        self.assertEqual(len(data['results']['users']), 1)
        self.assertEqual(data['results']['users'][0]['handle'], 'testuser1')

if __name__ == '__main__':
    unittest.main()
