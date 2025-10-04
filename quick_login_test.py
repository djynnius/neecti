#!/usr/bin/env python3
"""
Quick login test for co.nnecti.ng
"""

import time
from app import create_app, db
from app.models import User

def quick_test():
    """Quick test of login components"""
    print("🔍 Quick Login Test")
    print("-" * 30)
    
    app = create_app()
    with app.app_context():
        try:
            print("1. Testing database connection...")
            start = time.time()
            db.session.execute(db.text("SELECT 1"))
            print(f"   ✅ Connected ({time.time() - start:.3f}s)")
            
            print("2. Finding user...")
            start = time.time()
            user = User.query.filter_by(handle='djynnius').first()
            print(f"   ✅ User found ({time.time() - start:.3f}s)")
            
            if user:
                print("3. Checking password...")
                start = time.time()
                valid = user.check_password('Okokomaiko01')
                print(f"   ✅ Password {'valid' if valid else 'invalid'} ({time.time() - start:.3f}s)")
                
                print("4. Updating last_seen...")
                start = time.time()
                from datetime import datetime
                user.last_seen = datetime.utcnow()
                db.session.commit()
                print(f"   ✅ Updated ({time.time() - start:.3f}s)")
                
            print("\n✅ All components working!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    quick_test()
