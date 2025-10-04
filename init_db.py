#!/usr/bin/env python3
"""
Database initialization script for co.nnecti.ng
"""

from app import create_app, db
from app.models import User, Post, Message, Conversation, Notification, Report, PostImage

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Created tables: {', '.join(tables)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Initializing co.nnecti.ng database...")
    success = init_database()
    
    if success:
        print("🎉 Database initialization completed!")
        print("\n📝 Next steps:")
        print("1. Start the Flask application: python app.py")
        print("2. Start the React frontend: cd frontend && npm start")
        print("3. Register your first user account")
    else:
        print("💥 Database initialization failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Check PostgreSQL is running on 10.102.109.141:5432")
        print("2. Verify database credentials in .env file")
        print("3. Ensure 'connecting' database exists")
