#!/usr/bin/env python3
"""
User management script for co.nnecti.ng
"""

from app import create_app, db
from app.models import User, Post, Message, Conversation, Notification, Report, PostImage
from app.models.user import followers

def drop_all_users():
    """Drop all users and related data from the database"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🗑️  Starting user cleanup...")
            
            # Delete all data in order to respect foreign key constraints
            print("   Deleting reports...")
            Report.query.delete()
            
            print("   Deleting notifications...")
            Notification.query.delete()
            
            print("   Deleting post images...")
            PostImage.query.delete()
            
            print("   Deleting posts...")
            Post.query.delete()
            
            print("   Deleting conversations...")
            Conversation.query.delete()
            
            print("   Deleting messages...")
            Message.query.delete()
            
            print("   Deleting follower relationships...")
            db.session.execute(followers.delete())
            
            print("   Deleting users...")
            User.query.delete()
            
            db.session.commit()
            print("✅ All users and related data deleted successfully!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deleting users: {e}")
            return False

def create_user(first_name, last_name, handle, email, password, preferred_language='en'):
    """Create a new user"""
    app = create_app()
    
    with app.app_context():
        try:
            print(f"👤 Creating user: {first_name} {last_name} (@{handle})...")
            
            # Check if user already exists
            existing_user = User.query.filter_by(handle=handle.lower()).first()
            if existing_user:
                print(f"❌ User with handle @{handle} already exists!")
                return False
            
            existing_email = User.query.filter_by(email=email.lower()).first()
            if existing_email:
                print(f"❌ User with email {email} already exists!")
                return False
            
            # Create new user
            user = User(
                handle=handle.lower(),
                email=email.lower(),
                first_name=first_name,
                last_name=last_name,
                preferred_language=preferred_language
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            print(f"✅ User created successfully!")
            print(f"   Name: {user.full_name}")
            print(f"   Handle: @{user.handle}")
            print(f"   Email: {user.email}")
            print(f"   ID: {user.id}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating user: {e}")
            return False

def main():
    """Main function"""
    print("🚀 User Management Script for co.nnecti.ng")
    print("=" * 50)
    
    # Drop all users
    print("\n1. Dropping all existing users...")
    if not drop_all_users():
        print("💥 Failed to drop users. Exiting.")
        return
    
    # Create new user
    print("\n2. Creating new user...")
    success = create_user(
        first_name="Sunday",
        last_name="Ikpe", 
        handle="djynnius",
        email="sunday.ikpe@example.com",  # You may want to provide a real email
        password="Okokomaiko01",
        preferred_language="en"
    )
    
    if success:
        print("\n🎉 User management completed successfully!")
        print("\n📝 Next steps:")
        print("1. You can now log in with:")
        print("   Handle: djynnius")
        print("   Password: Okokomaiko01")
        print("2. Start the Flask application if not running: python app.py")
        print("3. Start the React frontend: cd frontend && npm start")
    else:
        print("\n💥 User creation failed!")

if __name__ == "__main__":
    main()
