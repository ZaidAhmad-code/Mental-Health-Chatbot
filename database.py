import sqlite3
from datetime import datetime
import os

DB_PATH = 'mental_health.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table (simple version for now)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
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


def save_chat_message(user_id, message, response):
    """Save chat message to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chat_history (user_id, message, response)
        VALUES (?, ?, ?)
    ''', (user_id, message, response))
    
    conn.commit()
    conn.close()


def get_chat_history(user_id, limit=50):
    """Get chat history for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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


# Initialize database on import
if not os.path.exists(DB_PATH):
    init_db()
