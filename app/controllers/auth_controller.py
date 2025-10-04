from flask import request, jsonify, session
from flask_login import login_user, logout_user, current_user
from app import db
from app.models import User
import re

class AuthController:
    
    @staticmethod
    def register():
        """Handle user registration"""
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['handle', 'email', 'first_name', 'last_name', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        handle = data['handle'].lower().strip()
        email = data['email'].lower().strip()
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()
        password = data['password']
        phone_number = data.get('phone_number', '').strip()
        preferred_language = data.get('preferred_language', 'en')

        # Validate handle format (alphanumeric and underscores only)
        if not handle:
            return jsonify({'error': 'Handle is required'}), 400
        if not re.match(r'^[a-zA-Z0-9_]{3,50}$', handle):
            return jsonify({'error': 'Handle must be 3-50 characters, alphanumeric and underscores only'}), 400
        
        # Validate email format
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Check if user already exists
        if User.query.filter_by(handle=handle).first():
            return jsonify({'error': 'Handle already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        if phone_number and User.query.filter_by(phone_number=phone_number).first():
            return jsonify({'error': 'Phone number already exists'}), 400
        
        # Create new user
        try:
            user = User(
                handle=handle,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number if phone_number else None,
                preferred_language=preferred_language
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Log in the user
            login_user(user, remember=True)
            
            return jsonify({
                'message': 'Registration successful',
                'user': user.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Registration failed'}), 500
    
    @staticmethod
    def login():
        """Handle user login"""
        import time
        import logging

        start_time = time.time()
        logging.info(f"Login attempt started for request from {request.remote_addr}")

        try:
            data = request.get_json()

            login_field = data.get('login', '').strip()  # Can be email, phone, or handle
            password = data.get('password', '')
            remember_me = data.get('remember_me', False)

            if not login_field or not password:
                return jsonify({'error': 'Login and password are required'}), 400
        
            # Try to find user by email, phone, or handle
            user = None
            lookup_start = time.time()

            if '@' in login_field:
                # Email login
                user = User.query.filter_by(email=login_field.lower()).first()
            elif login_field.isdigit() or '+' in login_field:
                # Phone number login
                user = User.query.filter_by(phone_number=login_field).first()
            else:
                # Handle login
                user = User.query.filter_by(handle=login_field.lower()).first()

            lookup_time = time.time() - lookup_start
            logging.info(f"User lookup completed in {lookup_time:.3f}s")

            if not user:
                logging.warning(f"Login failed: User '{login_field}' not found")
                return jsonify({'error': 'Invalid credentials'}), 401

            # Check password
            password_start = time.time()
            if not user.check_password(password):
                logging.warning(f"Login failed: Invalid password for user '{login_field}'")
                return jsonify({'error': 'Invalid credentials'}), 401

            password_time = time.time() - password_start
            logging.info(f"Password check completed in {password_time:.3f}s")

            if not user.is_active:
                logging.warning(f"Login failed: Account '{login_field}' is deactivated")
                return jsonify({'error': 'Account is deactivated'}), 401

            # Update last seen
            update_start = time.time()
            from datetime import datetime
            user.last_seen = datetime.utcnow()
            db.session.commit()
            update_time = time.time() - update_start
            logging.info(f"Database update completed in {update_time:.3f}s")

            # Log in the user
            login_user(user, remember=remember_me)

            total_time = time.time() - start_time
            logging.info(f"Login successful for '{login_field}' in {total_time:.3f}s")

            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict()
            }), 200

        except Exception as e:
            total_time = time.time() - start_time
            logging.error(f"Login error after {total_time:.3f}s: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Login failed due to server error'}), 500
    
    @staticmethod
    def logout():
        """Handle user logout"""
        if current_user.is_authenticated:
            # Clean up ephemeral messages
            from app.models.message import Message
            Message.cleanup_ephemeral_messages(current_user.id)
            
            logout_user()
            return jsonify({'message': 'Logout successful'}), 200
        
        return jsonify({'error': 'Not logged in'}), 400
    
    @staticmethod
    def get_current_user():
        """Get current user info"""
        if current_user.is_authenticated:
            return jsonify({'user': current_user.to_dict()}), 200
        
        return jsonify({'error': 'Not authenticated'}), 401
    
    @staticmethod
    def change_password():
        """Change user password"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            
            return jsonify({'message': 'Password changed successfully'}), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to change password'}), 500
    
    @staticmethod
    def update_profile():
        """Update user profile"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        # Fields that can be updated
        updatable_fields = ['first_name', 'last_name', 'bio', 'preferred_language', 'dark_mode']
        
        try:
            for field in updatable_fields:
                if field in data:
                    if field in ['first_name', 'last_name', 'bio']:
                        setattr(current_user, field, data[field].strip() if data[field] else None)
                    else:
                        setattr(current_user, field, data[field])
            
            db.session.commit()
            
            return jsonify({
                'message': 'Profile updated successfully',
                'user': current_user.to_dict()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to update profile'}), 500
    
    @staticmethod
    def delete_account():
        """Delete user account"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password is required to delete account'}), 400
        
        if not current_user.check_password(password):
            return jsonify({'error': 'Incorrect password'}), 400
        
        try:
            # Clean up user data
            from app.models.message import Message
            Message.cleanup_ephemeral_messages(current_user.id)
            
            # Deactivate account instead of deleting to preserve data integrity
            current_user.is_active = False
            current_user.email = f"deleted_{current_user.id}@deleted.com"
            current_user.handle = f"deleted_{current_user.id}"
            
            db.session.commit()
            logout_user()
            
            return jsonify({'message': 'Account deleted successfully'}), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to delete account'}), 500
