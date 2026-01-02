import sqlite3
from datetime import datetime
import os

DB_PATH = 'mental_health.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table with authentication fields (Phase 2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT,
            token TEXT,
            token_expiry TIMESTAMP,
            is_verified BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Assessment results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            assessment_type TEXT NOT NULL,
            score INTEGER NOT NULL,
            severity TEXT NOT NULL,
            answers TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Chat history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Crisis events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crisis_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            crisis_level TEXT NOT NULL,
            severity INTEGER NOT NULL,
            triggers TEXT,
            intervention_shown BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Sentiment history table (Phase 2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            sentiment_score REAL NOT NULL,
            sentiment_label TEXT NOT NULL,
            emotions TEXT,
            mood_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # User preferences table (Phase 2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            email_notifications BOOLEAN DEFAULT 1,
            weekly_reports BOOLEAN DEFAULT 1,
            crisis_alerts BOOLEAN DEFAULT 1,
            theme TEXT DEFAULT 'light',
            language TEXT DEFAULT 'en',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Chat sessions table (for multiple conversations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Add chat_session_id to chat_history if not exists
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'chat_session_id' not in columns:
        cursor.execute('ALTER TABLE chat_history ADD COLUMN chat_session_id INTEGER')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")


def save_assessment_result(user_id, assessment_type, score, severity, answers):
    """Save assessment result to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Convert answers list to comma-separated string
    answers_str = ','.join(map(str, answers))
    
    cursor.execute('''
        INSERT INTO assessment_results (user_id, assessment_type, score, severity, answers)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, assessment_type, score, severity, answers_str))
    
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()
    
    return result_id


def get_user_assessments(user_id, assessment_type=None, limit=10):
    """Get assessment history for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if assessment_type:
        cursor.execute('''
            SELECT id, assessment_type, score, severity, created_at
            FROM assessment_results
            WHERE user_id = ? AND assessment_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, assessment_type, limit))
    else:
        cursor.execute('''
            SELECT id, assessment_type, score, severity, created_at
            FROM assessment_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': r[0],
            'type': r[1],
            'score': r[2],
            'severity': r[3],
            'date': r[4]
        }
        for r in results
    ]


def save_chat_message(user_id, message, response, chat_session_id=None):
    """Save chat message to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chat_history (user_id, message, response, chat_session_id)
        VALUES (?, ?, ?, ?)
    ''', (user_id, message, response, chat_session_id))
    
    # Update session's updated_at
    if chat_session_id:
        cursor.execute('''
            UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (chat_session_id,))
    
    conn.commit()
    conn.close()


def get_chat_history(user_id, limit=50, chat_session_id=None):
    """Get chat history for a user, optionally filtered by session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if chat_session_id:
        cursor.execute('''
            SELECT message, response, created_at
            FROM chat_history
            WHERE user_id = ? AND chat_session_id = ?
            ORDER BY created_at ASC
        ''', (user_id, chat_session_id))
    else:
        cursor.execute('''
            SELECT message, response, created_at
            FROM chat_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'message': r[0],
            'response': r[1],
            'timestamp': r[2]
        }
        for r in results
    ]


# ==================== CHAT SESSION FUNCTIONS ====================

def create_chat_session(user_id, title="New Chat"):
    """Create a new chat session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chat_sessions (user_id, title)
        VALUES (?, ?)
    ''', (user_id, title))
    
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    
    return session_id


def get_user_chat_sessions(user_id, limit=20):
    """Get all chat sessions for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT cs.id, cs.title, cs.created_at, cs.updated_at,
               (SELECT COUNT(*) FROM chat_history WHERE chat_session_id = cs.id) as message_count
        FROM chat_sessions cs
        WHERE cs.user_id = ?
        ORDER BY cs.updated_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': r[0],
            'title': r[1],
            'created_at': r[2],
            'updated_at': r[3],
            'message_count': r[4]
        }
        for r in results
    ]


def update_chat_session_title(session_id, title):
    """Update a chat session's title"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (title, session_id))
    
    conn.commit()
    conn.close()


def delete_chat_session(session_id, user_id):
    """Delete a chat session and its messages"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete messages first
    cursor.execute('DELETE FROM chat_history WHERE chat_session_id = ? AND user_id = ?', 
                   (session_id, user_id))
    
    # Delete session
    cursor.execute('DELETE FROM chat_sessions WHERE id = ? AND user_id = ?', 
                   (session_id, user_id))
    
    conn.commit()
    conn.close()


def get_chat_session(session_id, user_id):
    """Get a single chat session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        WHERE id = ? AND user_id = ?
    ''', (session_id, user_id))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'title': result[1],
            'created_at': result[2],
            'updated_at': result[3]
        }
    return None


def create_guest_user():
    """Create a guest user for demo purposes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email)
            VALUES (?, ?)
        ''', ('guest', 'guest@example.com'))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Guest user already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', ('guest',))
        user_id = cursor.fetchone()[0]
    
    conn.close()
    return user_id


def save_crisis_event(user_id, message, crisis_level, severity, triggers):
    """Save crisis event to database for tracking and monitoring"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    triggers_str = ','.join(triggers) if triggers else ''
    
    cursor.execute('''
        INSERT INTO crisis_events (user_id, message, crisis_level, severity, triggers)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, message, crisis_level, severity, triggers_str))
    
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    
    return event_id


def get_crisis_events(user_id, limit=10):
    """Get crisis event history for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT crisis_level, severity, triggers, created_at
        FROM crisis_events
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'level': r[0],
            'severity': r[1],
            'triggers': r[2].split(',') if r[2] else [],
            'timestamp': r[3]
        }
        for r in results
    ]


# ========== PHASE 2: Authentication Functions ==========

def get_user_by_email(email):
    """Get user by email address"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        columns = ['id', 'username', 'email', 'password_hash', 'token', 
                   'token_expiry', 'is_verified', 'is_active', 'last_login', 'created_at']
        return dict(zip(columns, user))
    return None


def get_user_by_username(username):
    """Get user by username"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        columns = ['id', 'username', 'email', 'password_hash', 'token', 
                   'token_expiry', 'is_verified', 'is_active', 'last_login', 'created_at']
        return dict(zip(columns, user))
    return None


def get_user_by_id(user_id):
    """Get user by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        columns = ['id', 'username', 'email', 'password_hash', 'token', 
                   'token_expiry', 'is_verified', 'is_active', 'last_login', 'created_at']
        return dict(zip(columns, user))
    return None


def create_user(username, email, password_hash):
    """Create a new user with authentication"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError as e:
        conn.close()
        if 'username' in str(e):
            raise ValueError("Username already exists")
        elif 'email' in str(e):
            raise ValueError("Email already exists")
        raise ValueError("User creation failed")


def update_user_token(user_id, token, token_expiry):
    """Update user authentication token"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET token = ?, token_expiry = ?, last_login = ?
        WHERE id = ?
    ''', (token, token_expiry, datetime.now().isoformat(), user_id))
    
    conn.commit()
    conn.close()


def update_user_password(user_id, password_hash):
    """Update user password"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET password_hash = ? WHERE id = ?
    ''', (password_hash, user_id))
    
    conn.commit()
    conn.close()


def clear_user_token(user_id):
    """Clear user token on logout"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET token = NULL, token_expiry = NULL WHERE id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()


def delete_user(user_id):
    """Delete a user and all their data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete related data
    cursor.execute('DELETE FROM assessment_results WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM crisis_events WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM sentiment_history WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM user_preferences WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    conn.commit()
    conn.close()


# ========== PHASE 2: Sentiment Functions ==========

def save_sentiment(user_id, message, sentiment_score, sentiment_label, emotions, mood_score):
    """Save sentiment analysis result"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    import json
    emotions_str = json.dumps(emotions) if emotions else '{}'
    
    cursor.execute('''
        INSERT INTO sentiment_history (user_id, message, sentiment_score, sentiment_label, emotions, mood_score)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, message, sentiment_score, sentiment_label, emotions_str, mood_score))
    
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()
    
    return result_id


def get_sentiment_history(user_id, limit=50):
    """Get sentiment history for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sentiment_score, sentiment_label, emotions, mood_score, created_at
        FROM sentiment_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    import json
    return [
        {
            'sentiment_score': r[0],
            'sentiment_label': r[1],
            'emotions': json.loads(r[2]) if r[2] else {},
            'mood_score': r[3],
            'timestamp': r[4]
        }
        for r in results
    ]


def get_mood_trend(user_id, days=7):
    """Get mood trend over specified days"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DATE(created_at) as date, AVG(mood_score) as avg_mood, COUNT(*) as count
        FROM sentiment_history
        WHERE user_id = ? AND created_at >= datetime('now', ?)
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    ''', (user_id, f'-{days} days'))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'date': r[0],
            'avg_mood': round(r[1], 2) if r[1] else None,
            'message_count': r[2]
        }
        for r in results
    ]


# ========== PHASE 2: User Preferences ==========

def get_user_preferences(user_id):
    """Get user preferences"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
    prefs = cursor.fetchone()
    conn.close()
    
    if prefs:
        return {
            'email_notifications': bool(prefs[2]),
            'weekly_reports': bool(prefs[3]),
            'crisis_alerts': bool(prefs[4]),
            'theme': prefs[5],
            'language': prefs[6]
        }
    return None


def save_user_preferences(user_id, preferences):
    """Save or update user preferences"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO user_preferences (user_id, email_notifications, weekly_reports, crisis_alerts, theme, language)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            email_notifications = excluded.email_notifications,
            weekly_reports = excluded.weekly_reports,
            crisis_alerts = excluded.crisis_alerts,
            theme = excluded.theme,
            language = excluded.language,
            updated_at = CURRENT_TIMESTAMP
    ''', (
        user_id,
        preferences.get('email_notifications', True),
        preferences.get('weekly_reports', True),
        preferences.get('crisis_alerts', True),
        preferences.get('theme', 'light'),
        preferences.get('language', 'en')
    ))
    
    conn.commit()
    conn.close()


# Initialize database on import
if not os.path.exists(DB_PATH):
    init_db()
