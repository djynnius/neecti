import unittest
import json
from app import create_app, db
from app.models import User

class AuthTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_user_registration(self):
        """Test user registration"""
        response = self.client.post('/auth/register', 
            data=json.dumps({
                'handle': 'testuser',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'testpassword123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['handle'], 'testuser')
    
    def test_user_login(self):
        """Test user login"""
        # First register a user
        with self.app.app_context():
            user = User(
                handle='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User'
            )
            user.set_password('testpassword123')
            db.session.add(user)
            db.session.commit()
        
        # Then try to login
        response = self.client.post('/auth/login',
            data=json.dumps({
                'login': 'testuser',
                'password': 'testpassword123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = self.client.post('/auth/login',
            data=json.dumps({
                'login': 'nonexistent',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
