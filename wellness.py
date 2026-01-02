"""
Wellness Module - Guided Meditation & Breathing Exercises
Provides interactive breathing exercises, meditation sessions, and progress tracking
"""

from datetime import datetime, timedelta
from database import get_db_connection
import json

# ========== BREATHING EXERCISE DEFINITIONS ==========

BREATHING_EXERCISES = {
    "box_breathing": {
        "id": "box_breathing",
        "name": "Box Breathing",
        "description": "A calming technique used by Navy SEALs. Breathe in a square pattern to reduce stress and improve focus.",
        "icon": "🔲",
        "duration_options": [2, 4, 6, 8],  # minutes
        "default_duration": 4,
        "pattern": {
            "inhale": 4,
            "hold1": 4,
            "exhale": 4,
            "hold2": 4
        },
        "benefits": ["Reduces stress", "Improves focus", "Lowers blood pressure", "Calms anxiety"],
        "difficulty": "beginner",
        "category": "calming"
    },
    "478_breathing": {
        "id": "478_breathing",
        "name": "4-7-8 Breathing",
        "description": "Dr. Andrew Weil's relaxing breath technique. Perfect for falling asleep or calming anxiety.",
        "icon": "😴",
        "duration_options": [2, 4, 6],
        "default_duration": 4,
        "pattern": {
            "inhale": 4,
            "hold1": 7,
            "exhale": 8,
            "hold2": 0
        },
        "benefits": ["Promotes sleep", "Reduces anxiety", "Manages cravings", "Controls anger"],
        "difficulty": "beginner",
        "category": "sleep"
    },
    "energizing_breath": {
        "id": "energizing_breath",
        "name": "Energizing Breath",
        "description": "Quick, powerful breaths to boost energy and alertness. Great for morning or afternoon slump.",
        "icon": "⚡",
        "duration_options": [1, 2, 3],
        "default_duration": 2,
        "pattern": {
            "inhale": 2,
            "hold1": 0,
            "exhale": 2,
            "hold2": 0
        },
        "benefits": ["Increases energy", "Improves alertness", "Boosts mood", "Clears mind"],
        "difficulty": "beginner",
        "category": "energizing"
    },
    "calm_breath": {
        "id": "calm_breath",
        "name": "Calming Breath",
        "description": "Extended exhale breathing to activate your parasympathetic nervous system and feel deeply relaxed.",
        "icon": "🌊",
        "duration_options": [3, 5, 7, 10],
        "default_duration": 5,
        "pattern": {
            "inhale": 4,
            "hold1": 2,
            "exhale": 6,
            "hold2": 2
        },
        "benefits": ["Deep relaxation", "Reduces heart rate", "Calms nervous system", "Eases tension"],
        "difficulty": "intermediate",
        "category": "calming"
    },
    "grounding_breath": {
        "id": "grounding_breath",
        "name": "5-5-5 Grounding",
        "description": "Simple equal breathing combined with grounding awareness. Perfect for panic or dissociation.",
        "icon": "🌳",
        "duration_options": [3, 5, 7],
        "default_duration": 5,
        "pattern": {
            "inhale": 5,
            "hold1": 5,
            "exhale": 5,
            "hold2": 0
        },
        "benefits": ["Grounds anxiety", "Stops panic attacks", "Centers awareness", "Reduces dissociation"],
        "difficulty": "beginner",
        "category": "anxiety"
    }
}

# ========== MEDITATION SESSION DEFINITIONS ==========

MEDITATION_SESSIONS = {
    "body_scan": {
        "id": "body_scan",
        "name": "Body Scan Meditation",
        "description": "Progressively relax each part of your body from head to toe. Great for releasing physical tension.",
        "icon": "🧘",
        "duration_options": [5, 10, 15, 20],
        "default_duration": 10,
        "type": "guided",
        "category": "relaxation",
        "difficulty": "beginner",
        "steps": [
            {"time": 0, "instruction": "Find a comfortable position. Close your eyes and take three deep breaths.", "duration": 30},
            {"time": 30, "instruction": "Bring your attention to the top of your head. Notice any sensations there.", "duration": 20},
            {"time": 50, "instruction": "Move your awareness to your forehead. Let it soften and relax.", "duration": 20},
            {"time": 70, "instruction": "Notice your eyes. Let them feel heavy and relaxed.", "duration": 20},
            {"time": 90, "instruction": "Relax your jaw. Let it drop slightly open.", "duration": 20},
            {"time": 110, "instruction": "Feel your neck and shoulders. Release any tension you find there.", "duration": 30},
            {"time": 140, "instruction": "Bring awareness to your arms and hands. Let them feel heavy and warm.", "duration": 30},
            {"time": 170, "instruction": "Notice your chest rising and falling with each breath.", "duration": 30},
            {"time": 200, "instruction": "Relax your stomach. Let it soften with each exhale.", "duration": 30},
            {"time": 230, "instruction": "Feel your lower back and hips. Release any tightness.", "duration": 30},
            {"time": 260, "instruction": "Bring awareness to your legs. Let them feel heavy and supported.", "duration": 30},
            {"time": 290, "instruction": "Notice your feet. Feel them grounded and relaxed.", "duration": 30},
            {"time": 320, "instruction": "Take a moment to feel your whole body at once. Completely relaxed.", "duration": 40},
            {"time": 360, "instruction": "Slowly wiggle your fingers and toes. Take a deep breath.", "duration": 20},
            {"time": 380, "instruction": "When you're ready, gently open your eyes.", "duration": 20}
        ]
    },
    "loving_kindness": {
        "id": "loving_kindness",
        "name": "Loving Kindness",
        "description": "Cultivate feelings of love and compassion for yourself and others.",
        "icon": "💗",
        "duration_options": [5, 10, 15],
        "default_duration": 10,
        "type": "guided",
        "category": "emotional",
        "difficulty": "beginner",
        "steps": [
            {"time": 0, "instruction": "Close your eyes and take a few deep breaths to settle in.", "duration": 30},
            {"time": 30, "instruction": "Place your hand on your heart. Feel its warmth.", "duration": 20},
            {"time": 50, "instruction": "Think of yourself. Repeat: 'May I be happy. May I be healthy. May I be safe.'", "duration": 45},
            {"time": 95, "instruction": "Picture someone you love. Send them the same wishes.", "duration": 45},
            {"time": 140, "instruction": "Think of someone neutral - a stranger. Extend kindness to them too.", "duration": 45},
            {"time": 185, "instruction": "If you can, think of someone difficult. Try to wish them peace.", "duration": 45},
            {"time": 230, "instruction": "Now extend these wishes to all beings everywhere.", "duration": 45},
            {"time": 275, "instruction": "Feel the warmth of compassion in your heart.", "duration": 30},
            {"time": 305, "instruction": "Take a deep breath. Slowly return to the room.", "duration": 25}
        ]
    },
    "mindful_breathing": {
        "id": "mindful_breathing",
        "name": "Mindful Breathing",
        "description": "Simply observe your breath without trying to change it. The foundation of all meditation.",
        "icon": "🌬️",
        "duration_options": [3, 5, 10, 15],
        "default_duration": 5,
        "type": "guided",
        "category": "focus",
        "difficulty": "beginner",
        "steps": [
            {"time": 0, "instruction": "Find a comfortable seated position. Close your eyes.", "duration": 20},
            {"time": 20, "instruction": "Begin to notice your natural breath. Don't change it.", "duration": 30},
            {"time": 50, "instruction": "Feel the air entering through your nose, cool and fresh.", "duration": 30},
            {"time": 80, "instruction": "Notice the air leaving, warm and soft.", "duration": 30},
            {"time": 110, "instruction": "When your mind wanders, gently return to the breath.", "duration": 30},
            {"time": 140, "instruction": "No judgment. Just notice and return.", "duration": 30},
            {"time": 170, "instruction": "Feel the rhythm of your breathing.", "duration": 30},
            {"time": 200, "instruction": "Each breath, a moment of peace.", "duration": 30},
            {"time": 230, "instruction": "Slowly deepen your breath. Prepare to finish.", "duration": 20},
            {"time": 250, "instruction": "Open your eyes when ready. Carry this calm with you.", "duration": 20}
        ]
    },
    "stress_relief": {
        "id": "stress_relief",
        "name": "Quick Stress Relief",
        "description": "A short but powerful session to release stress and tension quickly.",
        "icon": "🎯",
        "duration_options": [3, 5],
        "default_duration": 3,
        "type": "guided",
        "category": "stress",
        "difficulty": "beginner",
        "steps": [
            {"time": 0, "instruction": "Stop whatever you're doing. Take a moment for yourself.", "duration": 15},
            {"time": 15, "instruction": "Take a big, deep breath in through your nose.", "duration": 10},
            {"time": 25, "instruction": "Hold it for a moment... and release with a sigh.", "duration": 15},
            {"time": 40, "instruction": "Drop your shoulders away from your ears.", "duration": 15},
            {"time": 55, "instruction": "Unclench your jaw. Let your face soften.", "duration": 15},
            {"time": 70, "instruction": "Take another deep breath. Feel the stress leaving.", "duration": 20},
            {"time": 90, "instruction": "Shake out your hands gently.", "duration": 15},
            {"time": 105, "instruction": "Roll your neck slowly in a circle.", "duration": 20},
            {"time": 125, "instruction": "One more deep breath. You've got this.", "duration": 20},
            {"time": 145, "instruction": "Open your eyes. Feel refreshed and ready.", "duration": 15}
        ]
    },
    "sleep_preparation": {
        "id": "sleep_preparation",
        "name": "Sleep Preparation",
        "description": "Wind down your mind and body for restful sleep.",
        "icon": "🌙",
        "duration_options": [10, 15, 20],
        "default_duration": 10,
        "type": "guided",
        "category": "sleep",
        "difficulty": "beginner",
        "steps": [
            {"time": 0, "instruction": "Lie down comfortably. Close your eyes.", "duration": 30},
            {"time": 30, "instruction": "Let go of the day. It's over. You did your best.", "duration": 30},
            {"time": 60, "instruction": "Begin slow, deep breathing. In... and out...", "duration": 40},
            {"time": 100, "instruction": "Imagine a warm, golden light at the top of your head.", "duration": 30},
            {"time": 130, "instruction": "This light slowly moves down, relaxing everything it touches.", "duration": 40},
            {"time": 170, "instruction": "It flows through your face, your neck, melting tension.", "duration": 40},
            {"time": 210, "instruction": "Down through your shoulders, arms, and hands.", "duration": 40},
            {"time": 250, "instruction": "Through your chest and stomach. Warm and peaceful.", "duration": 40},
            {"time": 290, "instruction": "Down through your hips, legs, and feet.", "duration": 40},
            {"time": 330, "instruction": "Your whole body is warm, heavy, and deeply relaxed.", "duration": 40},
            {"time": 370, "instruction": "Continue breathing slowly. Let yourself drift...", "duration": 60},
            {"time": 430, "instruction": "Sleep is coming. You are safe. You are at peace.", "duration": 60}
        ]
    }
}

# ========== DATABASE FUNCTIONS ==========

def init_wellness_tables():
    """Initialize wellness tracking tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Wellness sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wellness_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_type TEXT NOT NULL,
            exercise_id TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            completed BOOLEAN DEFAULT TRUE,
            mood_before INTEGER,
            mood_after INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Wellness streaks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wellness_streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_session_date DATE,
            total_sessions INTEGER DEFAULT 0,
            total_minutes INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ Wellness tables initialized")


def save_wellness_session(user_id: str, session_type: str, exercise_id: str, 
                          duration_seconds: int, completed: bool = True,
                          mood_before: int = None, mood_after: int = None, notes: str = None):
    """Save a completed wellness session"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Save session
    cursor.execute("""
        INSERT INTO wellness_sessions (user_id, session_type, exercise_id, duration_seconds, 
                                       completed, mood_before, mood_after, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, session_type, exercise_id, duration_seconds, completed, 
          mood_before, mood_after, notes))
    
    # Update streak
    today = datetime.now().date()
    cursor.execute("SELECT * FROM wellness_streaks WHERE user_id = ?", (user_id,))
    streak = cursor.fetchone()
    
    if streak:
        last_date = datetime.strptime(streak['last_session_date'], '%Y-%m-%d').date() if streak['last_session_date'] else None
        current = streak['current_streak']
        longest = streak['longest_streak']
        
        if last_date == today:
            # Already did session today, just update totals
            pass
        elif last_date == today - timedelta(days=1):
            # Continue streak
            current += 1
            longest = max(longest, current)
        else:
            # Streak broken, start new
            current = 1
        
        cursor.execute("""
            UPDATE wellness_streaks 
            SET current_streak = ?, longest_streak = ?, last_session_date = ?,
                total_sessions = total_sessions + 1, 
                total_minutes = total_minutes + ?,
                updated_at = datetime('now')
            WHERE user_id = ?
        """, (current, longest, today.isoformat(), duration_seconds // 60, user_id))
    else:
        # First session ever
        cursor.execute("""
            INSERT INTO wellness_streaks (user_id, current_streak, longest_streak, 
                                          last_session_date, total_sessions, total_minutes)
            VALUES (?, 1, 1, ?, 1, ?)
        """, (user_id, today.isoformat(), duration_seconds // 60))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Session saved"}


def get_wellness_stats(user_id: str) -> dict:
    """Get user's wellness statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get streak info
    cursor.execute("SELECT * FROM wellness_streaks WHERE user_id = ?", (user_id,))
    streak = cursor.fetchone()
    
    # Get recent sessions
    cursor.execute("""
        SELECT * FROM wellness_sessions 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    """, (user_id,))
    recent = cursor.fetchall()
    
    # Get favorite exercises
    cursor.execute("""
        SELECT exercise_id, COUNT(*) as count 
        FROM wellness_sessions 
        WHERE user_id = ? 
        GROUP BY exercise_id 
        ORDER BY count DESC 
        LIMIT 5
    """, (user_id,))
    favorites = cursor.fetchall()
    
    # Get mood improvement stats
    cursor.execute("""
        SELECT AVG(mood_after - mood_before) as avg_improvement
        FROM wellness_sessions 
        WHERE user_id = ? AND mood_before IS NOT NULL AND mood_after IS NOT NULL
    """, (user_id,))
    mood_result = cursor.fetchone()
    
    conn.close()
    
    return {
        "streak": {
            "current": streak['current_streak'] if streak else 0,
            "longest": streak['longest_streak'] if streak else 0,
            "last_session": streak['last_session_date'] if streak else None
        },
        "totals": {
            "sessions": streak['total_sessions'] if streak else 0,
            "minutes": streak['total_minutes'] if streak else 0
        },
        "recent_sessions": [dict(r) for r in recent] if recent else [],
        "favorites": [{"exercise_id": f['exercise_id'], "count": f['count']} for f in favorites] if favorites else [],
        "avg_mood_improvement": round(mood_result['avg_improvement'], 1) if mood_result and mood_result['avg_improvement'] else 0
    }


def get_breathing_exercises() -> list:
    """Get all available breathing exercises"""
    return list(BREATHING_EXERCISES.values())


def get_meditation_sessions() -> list:
    """Get all available meditation sessions"""
    return list(MEDITATION_SESSIONS.values())


def get_exercise_by_id(exercise_id: str) -> dict:
    """Get a specific exercise by ID"""
    if exercise_id in BREATHING_EXERCISES:
        return BREATHING_EXERCISES[exercise_id]
    if exercise_id in MEDITATION_SESSIONS:
        return MEDITATION_SESSIONS[exercise_id]
    return None


def get_recommended_exercises(user_id: str, mood: str = None, time_available: int = None) -> list:
    """Get personalized exercise recommendations"""
    recommendations = []
    
    # Based on mood
    if mood:
        mood_lower = mood.lower()
        if mood_lower in ['anxious', 'stressed', 'worried']:
            recommendations.extend([
                BREATHING_EXERCISES['box_breathing'],
                BREATHING_EXERCISES['calm_breath'],
                MEDITATION_SESSIONS['stress_relief']
            ])
        elif mood_lower in ['sad', 'depressed', 'down']:
            recommendations.extend([
                MEDITATION_SESSIONS['loving_kindness'],
                BREATHING_EXERCISES['energizing_breath']
            ])
        elif mood_lower in ['tired', 'sleepy', 'exhausted']:
            recommendations.extend([
                BREATHING_EXERCISES['energizing_breath'],
                MEDITATION_SESSIONS['mindful_breathing']
            ])
        elif mood_lower in ['can\'t sleep', 'insomnia', 'restless']:
            recommendations.extend([
                BREATHING_EXERCISES['478_breathing'],
                MEDITATION_SESSIONS['sleep_preparation']
            ])
        elif mood_lower in ['panic', 'panicking', 'freaking out']:
            recommendations.extend([
                BREATHING_EXERCISES['grounding_breath'],
                MEDITATION_SESSIONS['stress_relief']
            ])
    
    # If no specific recommendations, suggest popular ones
    if not recommendations:
        recommendations = [
            BREATHING_EXERCISES['box_breathing'],
            MEDITATION_SESSIONS['mindful_breathing'],
            MEDITATION_SESSIONS['stress_relief']
        ]
    
    # Filter by time if specified
    if time_available:
        recommendations = [r for r in recommendations 
                          if min(r.get('duration_options', [5])) <= time_available]
    
    return recommendations[:5]  # Return top 5


# Initialize tables on import
try:
    init_wellness_tables()
except:
    pass  # Tables may already exist
