#!/usr/bin/env python3
"""
Debug script for login issues in co.nnecti.ng
"""

import time
import traceback
from app import create_app, db
from app.models import User

def test_database_connection():
    """Test database connectivity and performance"""
    print("🔍 Testing database connection...")
    
    app = create_app()
    with app.app_context():
        try:
            start_time = time.time()
            
            # Test basic connection
            result = db.session.execute(db.text("SELECT 1")).fetchone()
            connection_time = time.time() - start_time
            print(f"✅ Database connection successful ({connection_time:.3f}s)")
            
            # Test user table access
            start_time = time.time()
            user_count = User.query.count()
            query_time = time.time() - start_time
            print(f"✅ User table accessible - {user_count} users ({query_time:.3f}s)")
            
            # Test specific user lookup (like login does)
            start_time = time.time()
            test_user = User.query.filter_by(handle='djynnius').first()
            lookup_time = time.time() - start_time
            
            if test_user:
                print(f"✅ User lookup successful ({lookup_time:.3f}s)")
                
                # Test password check
                start_time = time.time()
                password_valid = test_user.check_password('Okokomaiko01')
                password_time = time.time() - start_time
                print(f"✅ Password check: {'Valid' if password_valid else 'Invalid'} ({password_time:.3f}s)")
                
            else:
                print("❌ Test user 'djynnius' not found")
                
            return True
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            traceback.print_exc()
            return False

def test_login_endpoint():
    """Test the login endpoint directly"""
    print("\n🔍 Testing login endpoint...")
    
    app = create_app()
    with app.test_client() as client:
        try:
            start_time = time.time()
            
            response = client.post('/auth/login', 
                                 json={'login': 'djynnius', 'password': 'Okokomaiko01'},
                                 headers={'Content-Type': 'application/json'})
            
            request_time = time.time() - start_time
            
            print(f"📊 Login request completed in {request_time:.3f}s")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📊 Response: {response.get_json() if response.is_json else response.data}")
            
            if request_time > 10:
                print("⚠️  WARNING: Login taking longer than 10 seconds!")
                
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Login endpoint error: {e}")
            traceback.print_exc()
            return False

def check_system_resources():
    """Check system resource usage"""
    print("\n🔍 Checking system resources...")
    
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"💻 CPU Usage: {cpu_percent}%")
        
        # Memory usage
        memory = psutil.virtual_memory()
        print(f"🧠 Memory Usage: {memory.percent}% ({memory.used // (1024**2)}MB / {memory.total // (1024**2)}MB)")
        
        # Disk usage
        disk = psutil.disk_usage('/')
        print(f"💾 Disk Usage: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)")
        
        if cpu_percent > 80:
            print("⚠️  WARNING: High CPU usage detected!")
        if memory.percent > 80:
            print("⚠️  WARNING: High memory usage detected!")
        if disk.percent > 90:
            print("⚠️  WARNING: Low disk space!")
            
    except ImportError:
        print("📦 psutil not installed - run 'pip install psutil' for system monitoring")
    except Exception as e:
        print(f"❌ System check error: {e}")

def main():
    """Run all diagnostic tests"""
    print("🚀 co.nnecti.ng Login Diagnostics")
    print("=" * 50)
    
    # Test database
    db_ok = test_database_connection()
    
    # Test login endpoint
    login_ok = test_login_endpoint()
    
    # Check system resources
    check_system_resources()
    
    print("\n📋 Summary:")
    print(f"Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"Login: {'✅ OK' if login_ok else '❌ FAILED'}")
    
    if not db_ok:
        print("\n🔧 Database Issues Detected:")
        print("- Check database server is running")
        print("- Verify connection credentials in .env")
        print("- Check network connectivity to database")
        
    if not login_ok:
        print("\n🔧 Login Issues Detected:")
        print("- Check Flask application logs")
        print("- Verify user exists in database")
        print("- Check password hashing is working")

if __name__ == "__main__":
    main()
