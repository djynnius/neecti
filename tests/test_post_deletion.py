import unittest
import json
from app import create_app, db
from app.models import User, Post
from flask_login import login_user

class PostDeletionTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test users
            self.user1 = User(
                handle='user1',
                email='user1@example.com',
                first_name='User',
                last_name='One'
            )
            self.user1.set_password('password123')
            
            self.user2 = User(
                handle='user2',
                email='user2@example.com',
                first_name='User',
                last_name='Two'
            )
            self.user2.set_password('password123')
            
            db.session.add(self.user1)
            db.session.add(self.user2)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def login_user(self, handle):
        """Helper method to login a user"""
        return self.client.post('/auth/login',
            data=json.dumps({
                'login': handle,
                'password': 'password123'
            }),
            content_type='application/json'
        )
    
    def test_delete_simple_post(self):
        """Test deleting a simple post without replies"""
        with self.app.app_context():
            # Login user1
            self.login_user('user1')

            # Get user1 from database
            user1 = User.query.filter_by(handle='user1').first()

            # Create a post
            post = Post(
                content="This is a test post",
                user_id=user1.id
            )
            db.session.add(post)
            db.session.commit()
            post_id = post.id

            # Delete the post
            response = self.client.delete(f'/posts/{post_id}')
            self.assertEqual(response.status_code, 200)

            # Verify post is marked as deleted
            deleted_post = Post.query.get(post_id)
            self.assertTrue(deleted_post.is_deleted)
    
    def test_delete_post_with_replies(self):
        """Test deleting a post with replies (cascading delete)"""
        with self.app.app_context():
            # Login user1
            self.login_user('user1')

            # Get users from database
            user1 = User.query.filter_by(handle='user1').first()
            user2 = User.query.filter_by(handle='user2').first()

            # Create parent post
            parent_post = Post(
                content="Parent post",
                user_id=user1.id
            )
            db.session.add(parent_post)
            db.session.commit()

            # Create child posts (replies)
            child1 = Post(
                content="First reply",
                user_id=user2.id,
                parent_id=parent_post.id,
                conversation_root_id=parent_post.id,
                branch_level=1
            )

            child2 = Post(
                content="Second reply",
                user_id=user1.id,
                parent_id=parent_post.id,
                conversation_root_id=parent_post.id,
                branch_level=1
            )

            # Add and commit child posts first to get their IDs
            db.session.add_all([child1, child2])
            db.session.commit()

            # Create grandchild post (reply to reply)
            grandchild = Post(
                content="Reply to first reply",
                user_id=user1.id,
                parent_id=child1.id,
                conversation_root_id=parent_post.id,
                branch_level=2
            )

            db.session.add(grandchild)
            db.session.commit()
            
            parent_id = parent_post.id
            child1_id = child1.id
            child2_id = child2.id
            grandchild_id = grandchild.id
            
            # Delete the parent post
            response = self.client.delete(f'/posts/{parent_id}')
            self.assertEqual(response.status_code, 200)
            
            # Verify all posts are marked as deleted
            parent = Post.query.get(parent_id)
            child1_deleted = Post.query.get(child1_id)
            child2_deleted = Post.query.get(child2_id)
            grandchild_deleted = Post.query.get(grandchild_id)

            self.assertTrue(parent.is_deleted)
            self.assertTrue(child1_deleted.is_deleted)
            self.assertTrue(child2_deleted.is_deleted)
            self.assertTrue(grandchild_deleted.is_deleted)
    
    def test_delete_unauthorized_post(self):
        """Test that users cannot delete posts they don't own"""
        with self.app.app_context():
            # Login user1 and create a post
            self.login_user('user1')

            user1 = User.query.filter_by(handle='user1').first()

            post = Post(
                content="User1's post",
                user_id=user1.id
            )
            db.session.add(post)
            db.session.commit()
            post_id = post.id

            # Logout and login as user2
            self.client.post('/auth/logout')
            self.login_user('user2')

            # Try to delete user1's post
            response = self.client.delete(f'/posts/{post_id}')
            self.assertEqual(response.status_code, 404)  # Not found or not authorized

            # Verify post is not deleted
            post = Post.query.get(post_id)
            self.assertFalse(post.is_deleted)
    
    def test_delete_nonexistent_post(self):
        """Test deleting a post that doesn't exist"""
        with self.app.app_context():
            self.login_user('user1')

            response = self.client.delete('/posts/99999')
            self.assertEqual(response.status_code, 404)

    def test_delete_already_deleted_post(self):
        """Test deleting a post that's already deleted"""
        with self.app.app_context():
            self.login_user('user1')

            user1 = User.query.filter_by(handle='user1').first()

            # Create and delete a post
            post = Post(
                content="Test post",
                user_id=user1.id,
                is_deleted=True
            )
            db.session.add(post)
            db.session.commit()
            post_id = post.id

            # Try to delete it again
            response = self.client.delete(f'/posts/{post_id}')
            self.assertEqual(response.status_code, 404)

    def test_delete_without_authentication(self):
        """Test deleting a post without being logged in"""
        with self.app.app_context():
            user1 = User.query.filter_by(handle='user1').first()

            # Create a post
            post = Post(
                content="Test post",
                user_id=user1.id
            )
            db.session.add(post)
            db.session.commit()
            post_id = post.id

            # Try to delete without login
            response = self.client.delete(f'/posts/{post_id}')
            self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_reply_count_update_on_deletion(self):
        """Test that parent post reply count is updated when child is deleted"""
        with self.app.app_context():
            self.login_user('user1')

            user1 = User.query.filter_by(handle='user1').first()

            # Create parent post
            parent_post = Post(
                content="Parent post",
                user_id=user1.id,
                replies_count=2
            )
            db.session.add(parent_post)
            db.session.commit()

            # Create child post
            child_post = Post(
                content="Child post",
                user_id=user1.id,
                parent_id=parent_post.id,
                conversation_root_id=parent_post.id,
                branch_level=1
            )
            db.session.add(child_post)
            db.session.commit()

            child_id = child_post.id
            parent_id = parent_post.id

            # Delete child post
            response = self.client.delete(f'/posts/{child_id}')
            self.assertEqual(response.status_code, 200)

            # Verify parent's reply count is decremented
            parent = Post.query.get(parent_id)
            self.assertEqual(parent.replies_count, 1)

if __name__ == '__main__':
    unittest.main()
