"""
User Authentication Module for Mental Health Chatbot
Implements user registration, login, and session management
"""

import sqlite3
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from functools import wraps
from flask import session, request, jsonify

from database import DB_PATH
from error_handler import logger


# ========== Password Hashing ==========

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash password with salt using SHA-256
    Returns: (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(32)
    
    # Combine password and salt
    salted_password = password + salt
    
    # Hash using SHA-256
    hashed = hashlib.sha256(salted_password.encode()).hexdigest()
    
    return hashed, salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verify a password against its hash"""
    test_hash, _ = hash_password(password, salt)
    return test_hash == hashed_password


# ========== Database Operations ==========

def init_auth_tables():
    """Initialize authentication tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Update users table with authentication fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_auth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            display_name TEXT,
            first_name TEXT,
            last_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 0,
            verification_token TEXT,
            reset_token TEXT,
            reset_token_expires TIMESTAMP,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users_auth(id)
        )
    ''')
    
    # User preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            theme TEXT DEFAULT 'dark',
            notifications_enabled BOOLEAN DEFAULT 1,
            email_notifications BOOLEAN DEFAULT 1,
            weekly_reports BOOLEAN DEFAULT 1,
            crisis_alerts BOOLEAN DEFAULT 1,
            language TEXT DEFAULT 'en',
            timezone TEXT DEFAULT 'UTC',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users_auth(id)
        )
    ''')
    
    # Add display_name column if it doesn't exist (migration for existing databases)
    try:
        cursor.execute("ALTER TABLE users_auth ADD COLUMN display_name TEXT")
    except:
        pass  # Column already exists
    
    conn.commit()
    conn.close()
    logger.info("✓ Authentication tables initialized")


def create_user(username: str, email: str, password: str, 
                first_name: str = None, last_name: str = None) -> Dict:
    """
    Create a new user account - stores password in plain text
    Returns: {'success': bool, 'user_id': int, 'message': str}
    """
    # Validate inputs
    if not validate_email(email):
        return {'success': False, 'message': 'Invalid email format'}
    
    if len(password) < 3:  # Simplified validation
        return {'success': False, 'message': 'Password must be at least 3 characters'}
    
    if len(username) < 3:
        return {'success': False, 'message': 'Username must be at least 3 characters'}
    
    # Store password in plain text (no hashing)
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users_auth (username, email, password_hash, password_salt, 
                                   first_name, last_name, verification_token)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email.lower(), password, '', first_name, last_name, verification_token))  # Plain text password, empty salt
        
        user_id = cursor.lastrowid
        
        # Create default preferences
        cursor.execute('''
            INSERT INTO user_preferences (user_id)
            VALUES (?)
        ''', (user_id,))
        
        # Also create entry in original users table for compatibility
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, username, email, password_hash)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, email.lower(), password))  # Plain text password
        
        conn.commit()
        
        logger.info(f"New user created: {username} (ID: {user_id})")
        
        return {
            'success': True,
            'user_id': user_id,
            'verification_token': verification_token,
            'message': 'Account created successfully'
        }
        
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return {'success': False, 'message': 'Username already exists'}
        elif 'email' in str(e):
            return {'success': False, 'message': 'Email already registered'}
        return {'success': False, 'message': 'Registration failed'}
    
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Dict:
    """
    Authenticate user with email and password - plain text comparison
    Returns: {'success': bool, 'user': dict, 'message': str}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, email, password_hash, password_salt, 
               first_name, last_name, is_active, is_verified
        FROM users_auth
        WHERE email = ?
    ''', (email.lower(),))
    
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return {'success': False, 'message': 'Invalid email or password'}
    
    user_id, username, email, password_hash, salt, first_name, last_name, is_active, is_verified = user
    
    if not is_active:
        conn.close()
        return {'success': False, 'message': 'Account is deactivated'}
    
    # Direct password comparison (plain text)
    if password != password_hash:
        conn.close()
        return {'success': False, 'message': 'Invalid email or password'}
    
    # Update last login
    cursor.execute('''
        UPDATE users_auth SET last_login = CURRENT_TIMESTAMP WHERE id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()
    
    logger.info(f"User logged in: {username} (ID: {user_id})")
    
    return {
        'success': True,
        'user': {
            'id': user_id,
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'is_verified': is_verified
        },
        'message': 'Login successful'
    }


def authenticate_user_by_username(username: str, password: str) -> Dict:
    """
    Authenticate user with username and password - plain text comparison
    Returns: {'success': bool, 'user': dict, 'message': str}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, email, password_hash, password_salt, 
               first_name, last_name, is_active, is_verified
        FROM users_auth
        WHERE username = ?
    ''', (username,))
    
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return {'success': False, 'message': 'Invalid username or password'}
    
    user_id, username, email, password_hash, salt, first_name, last_name, is_active, is_verified = user
    
    if not is_active:
        conn.close()
        return {'success': False, 'message': 'Account is deactivated'}
    
    # Direct password comparison (plain text)
    if password != password_hash:
        conn.close()
        return {'success': False, 'message': 'Invalid username or password'}
    
    # Update last login
    cursor.execute('''
        UPDATE users_auth SET last_login = CURRENT_TIMESTAMP WHERE id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()
    
    logger.info(f"User logged in by username: {username} (ID: {user_id})")
    
    return {
        'success': True,
        'user': {
            'id': user_id,
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'is_verified': is_verified
        },
        'message': 'Login successful'
    }


def create_session(user_id: int, ip_address: str = None, user_agent: str = None) -> str:
    """Create a new session for user, returns session token"""
    session_token = secrets.token_urlsafe(64)
    expires_at = datetime.now() + timedelta(days=7)  # 7 day session
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, session_token, ip_address, user_agent, expires_at))
    
    conn.commit()
    conn.close()
    
    return session_token


def validate_session(session_token: str) -> Optional[Dict]:
    """Validate session token and return user info if valid"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.user_id, s.expires_at, u.username, u.email, u.first_name, u.last_name
        FROM user_sessions s
        JOIN users_auth u ON s.user_id = u.id
        WHERE s.session_token = ? AND u.is_active = 1
    ''', (session_token,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    user_id, expires_at, username, email, first_name, last_name = result
    
    # Check expiration
    if datetime.fromisoformat(expires_at) < datetime.now():
        return None
    
    return {
        'user_id': user_id,
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name
    }


def invalidate_session(session_token: str):
    """Invalidate a session (logout)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
    conn.commit()
    conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, email, first_name, last_name, is_verified, created_at, last_login, display_name
        FROM users_auth WHERE id = ?
    ''', (user_id,))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return None
    
    return {
        'id': user[0],
        'username': user[1],
        'email': user[2],
        'first_name': user[3],
        'last_name': user[4],
        'is_verified': user[5],
        'created_at': user[6],
        'last_login': user[7],
        'display_name': user[8]
    }


def update_user_profile(user_id: int, **kwargs) -> bool:
    """Update user profile fields"""
    allowed_fields = ['first_name', 'last_name', 'email']
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
    
    if not updates:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [user_id]
    
    cursor.execute(f'''
        UPDATE users_auth SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?
    ''', values)
    
    conn.commit()
    conn.close()
    
    logger.info(f"User profile updated: {user_id}")
    return True


def change_password(user_id: int, current_password: str, new_password: str) -> Dict:
    """Change user password"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current password hash
    cursor.execute('''
        SELECT password_hash, password_salt FROM users_auth WHERE id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return {'success': False, 'message': 'User not found'}
    
    current_hash, salt = result
    
    # Verify current password
    if not verify_password(current_password, current_hash, salt):
        conn.close()
        return {'success': False, 'message': 'Current password is incorrect'}
    
    # Validate new password
    if not validate_password(new_password):
        conn.close()
        return {'success': False, 'message': 'New password does not meet requirements'}
    
    # Hash new password
    new_hash, new_salt = hash_password(new_password)
    
    # Update password
    cursor.execute('''
        UPDATE users_auth SET password_hash = ?, password_salt = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_hash, new_salt, user_id))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Password changed for user: {user_id}")
    return {'success': True, 'message': 'Password changed successfully'}


def generate_reset_token(email: str) -> Optional[str]:
    """Generate password reset token"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT id FROM users_auth WHERE email = ?', (email.lower(),))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return None
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=24)
    
    cursor.execute('''
        UPDATE users_auth SET reset_token = ?, reset_token_expires = ?
        WHERE email = ?
    ''', (reset_token, expires_at, email.lower()))
    
    conn.commit()
    conn.close()
    
    return reset_token


def reset_password_with_token(token: str, new_password: str) -> Dict:
    """Reset password using reset token"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, reset_token_expires FROM users_auth WHERE reset_token = ?
    ''', (token,))
    
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return {'success': False, 'message': 'Invalid reset token'}
    
    user_id, expires_at = result
    
    if datetime.fromisoformat(expires_at) < datetime.now():
        conn.close()
        return {'success': False, 'message': 'Reset token has expired'}
    
    if not validate_password(new_password):
        conn.close()
        return {'success': False, 'message': 'Password does not meet requirements'}
    
    # Hash new password
    new_hash, new_salt = hash_password(new_password)
    
    # Update password and clear reset token
    cursor.execute('''
        UPDATE users_auth 
        SET password_hash = ?, password_salt = ?, reset_token = NULL, reset_token_expires = NULL
        WHERE id = ?
    ''', (new_hash, new_salt, user_id))
    
    conn.commit()
    conn.close()
    
    return {'success': True, 'message': 'Password reset successfully'}


def get_user_preferences(user_id: int) -> Optional[Dict]:
    """Get user preferences"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT theme, notifications_enabled, email_notifications, weekly_reports,
               crisis_alerts, language, timezone
        FROM user_preferences WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    return {
        'theme': result[0],
        'notifications_enabled': bool(result[1]),
        'email_notifications': bool(result[2]),
        'weekly_reports': bool(result[3]),
        'crisis_alerts': bool(result[4]),
        'language': result[5],
        'timezone': result[6]
    }


def update_user_preferences(user_id: int, **kwargs) -> bool:
    """Update user preferences"""
    allowed_fields = ['theme', 'notifications_enabled', 'email_notifications', 
                      'weekly_reports', 'crisis_alerts', 'language', 'timezone']
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [user_id]
    
    cursor.execute(f'''
        UPDATE user_preferences SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', values)
    
    conn.commit()
    conn.close()
    return True


# ========== Validation Helpers ==========

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> bool:
    """
    Validate password strength:
    - At least 8 characters
    - At least one uppercase
    - At least one lowercase
    - At least one digit
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True


# ========== Decorators ==========

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Optionally validate session token
        if 'session_token' in session:
            user = validate_session(session['session_token'])
            if not user:
                return jsonify({'error': 'Session expired'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges (placeholder for future)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # TODO: Add admin check
        # For now, allow all authenticated users
        
        return f(*args, **kwargs)
    return decorated_function


def delete_user_account(user_id: int, password: str) -> Dict:
    """
    Delete a user account after verifying password
    Returns: {'success': bool, 'message': str}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get user to verify password
    cursor.execute('''
        SELECT password_hash, password_salt FROM users_auth WHERE id = ?
    ''', (user_id,))
    
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return {'success': False, 'message': 'User not found'}
    
    password_hash, salt = user
    
    if not verify_password(password, password_hash, salt):
        conn.close()
        return {'success': False, 'message': 'Incorrect password'}
    
    try:
        # Delete all user data
        cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_preferences WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM assessment_results WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM crisis_events WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM sentiment_history WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        cursor.execute('DELETE FROM users_auth WHERE id = ?', (user_id,))
        
        conn.commit()
        logger.info(f"User account deleted: {user_id}")
        return {'success': True, 'message': 'Account deleted successfully'}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return {'success': False, 'message': 'Failed to delete account'}
    
    finally:
        conn.close()


# Initialize auth tables on import
init_auth_tables()
