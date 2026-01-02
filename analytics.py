"""
Analytics Module for Mental Health Chatbot
Provides user insights, trends, and engagement metrics
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from database import DB_PATH


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Get comprehensive user statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total conversations
    cursor.execute('''
        SELECT COUNT(*) FROM chat_history WHERE user_id = ?
    ''', (user_id,))
    total_conversations = cursor.fetchone()[0]
    
    # Total assessments
    cursor.execute('''
        SELECT COUNT(*) FROM assessment_results WHERE user_id = ?
    ''', (user_id,))
    total_assessments = cursor.fetchone()[0]
    
    # Crisis events
    cursor.execute('''
        SELECT COUNT(*) FROM crisis_events WHERE user_id = ?
    ''', (user_id,))
    crisis_count = cursor.fetchone()[0]
    
    # Latest PHQ-9 score
    cursor.execute('''
        SELECT score, created_at FROM assessment_results
        WHERE user_id = ? AND assessment_type = 'phq9'
        ORDER BY created_at DESC LIMIT 1
    ''', (user_id,))
    latest_phq9 = cursor.fetchone()
    
    # Latest GAD-7 score
    cursor.execute('''
        SELECT score, created_at FROM assessment_results
        WHERE user_id = ? AND assessment_type = 'gad7'
        ORDER BY created_at DESC LIMIT 1
    ''', (user_id,))
    latest_gad7 = cursor.fetchone()
    
    # First interaction
    cursor.execute('''
        SELECT MIN(created_at) FROM chat_history WHERE user_id = ?
    ''', (user_id,))
    first_interaction = cursor.fetchone()[0]
    
    # Last interaction
    cursor.execute('''
        SELECT MAX(created_at) FROM chat_history WHERE user_id = ?
    ''', (user_id,))
    last_interaction = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'user_id': user_id,
        'total_conversations': total_conversations,
        'total_assessments': total_assessments,
        'crisis_events': crisis_count,
        'latest_phq9': {
            'score': latest_phq9[0] if latest_phq9 else None,
            'date': latest_phq9[1] if latest_phq9 else None
        },
        'latest_gad7': {
            'score': latest_gad7[0] if latest_gad7 else None,
            'date': latest_gad7[1] if latest_gad7 else None
        },
        'first_interaction': first_interaction,
        'last_interaction': last_interaction,
        'days_active': _calculate_days_active(first_interaction, last_interaction)
    }


def get_assessment_trends(user_id: int, assessment_type: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get assessment score trends over time"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    since_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    cursor.execute('''
        SELECT score, severity, created_at
        FROM assessment_results
        WHERE user_id = ? AND assessment_type = ? AND created_at >= ?
        ORDER BY created_at ASC
    ''', (user_id, assessment_type, since_date))
    
    results = cursor.fetchall()
    conn.close()
    
    trends = []
    for score, severity, timestamp in results:
        trends.append({
            'score': score,
            'severity': severity,
            'date': timestamp
        })
    
    # Calculate trend direction
    if len(trends) >= 2:
        recent_avg = sum(t['score'] for t in trends[-3:]) / min(3, len(trends[-3:]))
        older_avg = sum(t['score'] for t in trends[:3]) / min(3, len(trends[:3]))
        trend_direction = 'improving' if recent_avg < older_avg else 'worsening' if recent_avg > older_avg else 'stable'
    else:
        trend_direction = 'insufficient_data'
    
    return {
        'assessment_type': assessment_type,
        'data': trends,
        'trend_direction': trend_direction,
        'total_assessments': len(trends)
    }


def get_crisis_patterns(user_id: int, days: int = 30) -> Dict[str, Any]:
    """Analyze crisis event patterns"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    since_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    cursor.execute('''
        SELECT crisis_level, severity, triggers, created_at
        FROM crisis_events
        WHERE user_id = ? AND created_at >= ?
        ORDER BY created_at DESC
    ''', (user_id, since_date))
    
    events = cursor.fetchall()
    conn.close()
    
    if not events:
        return {
            'total_events': 0,
            'severity_distribution': {},
            'common_triggers': [],
            'recent_events': []
        }
    
    # Analyze severity distribution
    severity_counts = {}
    all_triggers = []
    
    for level, severity, triggers, timestamp in events:
        severity_counts[level] = severity_counts.get(level, 0) + 1
        if triggers:
            all_triggers.extend(triggers.split(','))
    
    # Count trigger frequency
    trigger_counts = {}
    for trigger in all_triggers:
        trigger = trigger.strip()
        if trigger:
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
    
    # Sort triggers by frequency
    common_triggers = sorted(
        trigger_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    return {
        'total_events': len(events),
        'severity_distribution': severity_counts,
        'common_triggers': [{'trigger': t[0], 'count': t[1]} for t in common_triggers],
        'recent_events': [
            {
                'level': e[0],
                'severity': e[1],
                'date': e[3]
            } for e in events[:5]
        ]
    }


def get_engagement_metrics(user_id: int) -> Dict[str, Any]:
    """Calculate user engagement metrics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Messages per day (last 7 days)
    cursor.execute('''
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM chat_history
        WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
        GROUP BY day
        ORDER BY day ASC
    ''', (user_id,))
    
    daily_messages = cursor.fetchall()
    
    # Average message length
    cursor.execute('''
        SELECT AVG(LENGTH(message)) FROM chat_history WHERE user_id = ?
    ''', (user_id,))
    avg_message_length = cursor.fetchone()[0] or 0
    
    # Response sentiment (basic keyword analysis)
    cursor.execute('''
        SELECT message FROM chat_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 50
    ''', (user_id,))
    recent_messages = cursor.fetchall()
    
    conn.close()
    
    # Calculate engagement score (0-100)
    engagement_score = _calculate_engagement_score(
        len(recent_messages),
        daily_messages,
        avg_message_length
    )
    
    return {
        'engagement_score': engagement_score,
        'daily_activity': [{'date': day, 'messages': count} for day, count in daily_messages],
        'avg_message_length': round(avg_message_length, 2),
        'total_recent_messages': len(recent_messages)
    }


def get_mental_health_trajectory(user_id: int) -> Dict[str, Any]:
    """Calculate overall mental health trajectory"""
    phq9_trends = get_assessment_trends(user_id, 'phq9', days=90)
    gad7_trends = get_assessment_trends(user_id, 'gad7', days=90)
    crisis_data = get_crisis_patterns(user_id, days=90)
    
    # Calculate trajectory score (0-100, higher is better)
    trajectory_score = _calculate_trajectory_score(phq9_trends, gad7_trends, crisis_data)
    
    return {
        'trajectory_score': trajectory_score,
        'phq9_trend': phq9_trends['trend_direction'],
        'gad7_trend': gad7_trends['trend_direction'],
        'crisis_frequency': crisis_data['total_events'],
        'overall_status': _get_status_label(trajectory_score)
    }


def get_system_analytics() -> Dict[str, Any]:
    """Get system-wide analytics (admin view)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # Total conversations
    cursor.execute('SELECT COUNT(*) FROM chat_history')
    total_conversations = cursor.fetchone()[0]
    
    # Total assessments
    cursor.execute('SELECT COUNT(*) FROM assessment_results')
    total_assessments = cursor.fetchone()[0]
    
    # Total crisis events
    cursor.execute('SELECT COUNT(*) FROM crisis_events')
    total_crises = cursor.fetchone()[0]
    
    # Active users (last 7 days)
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM chat_history
        WHERE created_at >= datetime('now', '-7 days')
    ''')
    active_users = cursor.fetchone()[0]
    
    # Most common assessment severity
    cursor.execute('''
        SELECT severity, COUNT(*) as count
        FROM assessment_results
        GROUP BY severity
        ORDER BY count DESC
        LIMIT 1
    ''')
    most_common_severity = cursor.fetchone()
    
    conn.close()
    
    return {
        'total_users': total_users,
        'active_users_7d': active_users,
        'total_conversations': total_conversations,
        'total_assessments': total_assessments,
        'total_crisis_events': total_crises,
        'avg_conversations_per_user': round(total_conversations / total_users, 2) if total_users > 0 else 0,
        'most_common_severity': most_common_severity[0] if most_common_severity else 'N/A'
    }


# Helper functions

def _calculate_days_active(first_date: Optional[str], last_date: Optional[str]) -> int:
    """Calculate days between first and last interaction"""
    if not first_date or not last_date:
        return 0
    
    first = datetime.fromisoformat(first_date)
    last = datetime.fromisoformat(last_date)
    return (last - first).days


def _calculate_engagement_score(total_messages: int, daily_activity: List, avg_length: float) -> int:
    """Calculate engagement score (0-100)"""
    # Simple scoring algorithm
    message_score = min(total_messages * 2, 40)  # Max 40 points
    consistency_score = min(len(daily_activity) * 10, 40)  # Max 40 points
    depth_score = min(avg_length / 10, 20)  # Max 20 points
    
    return round(message_score + consistency_score + depth_score)


def _calculate_trajectory_score(phq9_data: Dict, gad7_data: Dict, crisis_data: Dict) -> int:
    """Calculate mental health trajectory score (0-100, higher is better)"""
    score = 50  # Start at neutral
    
    # Adjust based on trends
    if phq9_data['trend_direction'] == 'improving':
        score += 15
    elif phq9_data['trend_direction'] == 'worsening':
        score -= 15
    
    if gad7_data['trend_direction'] == 'improving':
        score += 15
    elif gad7_data['trend_direction'] == 'worsening':
        score -= 15
    
    # Adjust based on crisis events
    score -= min(crisis_data['total_events'] * 5, 20)
    
    # Ensure score is in range
    return max(0, min(100, score))


def _get_status_label(trajectory_score: int) -> str:
    """Convert trajectory score to status label"""
    if trajectory_score >= 70:
        return 'Improving'
    elif trajectory_score >= 40:
        return 'Stable'
    else:
        return 'Needs Attention'
