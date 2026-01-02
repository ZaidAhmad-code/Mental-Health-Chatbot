"""
Predictive Analytics Module for Mental Health Chatbot
Implements ML-based risk prediction, mood forecasting, and pattern detection
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import math
import json

from database import DB_PATH
from error_handler import logger


# ========== Risk Scoring Model ==========

class MentalHealthRiskPredictor:
    """
    Predicts mental health risk based on user patterns
    Uses a weighted scoring system based on clinical indicators
    """
    
    # Risk factor weights (based on clinical research)
    RISK_WEIGHTS = {
        'recent_crisis_events': 3.0,
        'declining_sentiment': 2.5,
        'high_phq9_score': 2.5,
        'high_gad7_score': 2.0,
        'negative_emotion_frequency': 1.5,
        'reduced_engagement': 1.5,
        'sleep_issues_mentioned': 1.0,
        'isolation_indicators': 2.0,
        'hopelessness_language': 3.0
    }
    
    # Keywords indicating specific risk factors
    HOPELESSNESS_KEYWORDS = [
        'no point', 'give up', 'hopeless', 'worthless', 'burden',
        'no future', 'can\'t go on', 'tired of', 'nothing matters',
        'no one cares', 'better off without me'
    ]
    
    ISOLATION_KEYWORDS = [
        'alone', 'lonely', 'isolated', 'no friends', 'nobody',
        'no one to talk to', 'disconnected', 'abandoned'
    ]
    
    SLEEP_KEYWORDS = [
        'can\'t sleep', 'insomnia', 'nightmares', 'sleeping too much',
        'exhausted', 'tired all the time', 'no energy'
    ]
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.risk_factors = {}
        self.risk_score = 0
        self.confidence = 0
    
    def calculate_risk(self, days: int = 14) -> Dict[str, Any]:
        """Calculate comprehensive risk score"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # 1. Recent crisis events
        crisis_score = self._analyze_crisis_history(cursor, since_date)
        
        # 2. Sentiment trends
        sentiment_score = self._analyze_sentiment_trend(cursor, since_date)
        
        # 3. Assessment scores
        assessment_score = self._analyze_assessments(cursor)
        
        # 4. Language patterns in chat
        language_score = self._analyze_language_patterns(cursor, since_date)
        
        # 5. Engagement patterns
        engagement_score = self._analyze_engagement(cursor, since_date)
        
        conn.close()
        
        # Calculate weighted risk score (0-100)
        total_weight = sum(self.RISK_WEIGHTS.values())
        weighted_sum = (
            crisis_score * self.RISK_WEIGHTS['recent_crisis_events'] +
            sentiment_score * self.RISK_WEIGHTS['declining_sentiment'] +
            assessment_score['phq9'] * self.RISK_WEIGHTS['high_phq9_score'] +
            assessment_score['gad7'] * self.RISK_WEIGHTS['high_gad7_score'] +
            language_score['hopelessness'] * self.RISK_WEIGHTS['hopelessness_language'] +
            language_score['isolation'] * self.RISK_WEIGHTS['isolation_indicators'] +
            language_score['sleep'] * self.RISK_WEIGHTS['sleep_issues_mentioned'] +
            engagement_score * self.RISK_WEIGHTS['reduced_engagement']
        )
        
        self.risk_score = min(100, (weighted_sum / total_weight) * 100)
        self.confidence = self._calculate_confidence(cursor)
        
        # Determine risk level
        risk_level = self._get_risk_level()
        
        return {
            'user_id': self.user_id,
            'risk_score': round(self.risk_score, 1),
            'risk_level': risk_level,
            'confidence': round(self.confidence, 2),
            'factors': {
                'crisis_history': round(crisis_score * 10, 1),
                'sentiment_decline': round(sentiment_score * 10, 1),
                'depression_indicators': round(assessment_score['phq9'] * 10, 1),
                'anxiety_indicators': round(assessment_score['gad7'] * 10, 1),
                'hopelessness_language': round(language_score['hopelessness'] * 10, 1),
                'isolation_indicators': round(language_score['isolation'] * 10, 1),
                'sleep_issues': round(language_score['sleep'] * 10, 1),
                'engagement_drop': round(engagement_score * 10, 1)
            },
            'recommendations': self._get_recommendations(risk_level),
            'analysis_period_days': days,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def _analyze_crisis_history(self, cursor, since_date: str) -> float:
        """Analyze recent crisis events"""
        cursor.execute('''
            SELECT COUNT(*), MAX(severity) FROM crisis_events
            WHERE user_id = ? AND created_at >= ?
        ''', (self.user_id, since_date))
        
        result = cursor.fetchone()
        count, max_severity = result[0] or 0, result[1] or 0
        
        # Score based on count and severity
        if count == 0:
            return 0.0
        
        base_score = min(1.0, count / 5)  # Cap at 5 events
        severity_factor = max_severity / 10 if max_severity else 0
        
        return (base_score + severity_factor) / 2
    
    def _analyze_sentiment_trend(self, cursor, since_date: str) -> float:
        """Analyze sentiment trajectory"""
        cursor.execute('''
            SELECT sentiment_score, created_at FROM sentiment_history
            WHERE user_id = ? AND created_at >= ?
            ORDER BY created_at ASC
        ''', (self.user_id, since_date))
        
        results = cursor.fetchall()
        if len(results) < 3:
            return 0.0
        
        scores = [r[0] for r in results]
        
        # Calculate trend (negative slope = declining sentiment)
        n = len(scores)
        if n < 2:
            return 0.0
        
        # Simple linear regression slope
        x_mean = (n - 1) / 2
        y_mean = sum(scores) / n
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Negative slope indicates declining sentiment
        if slope < 0:
            return min(1.0, abs(slope) * 2)  # Scale the decline
        return 0.0
    
    def _analyze_assessments(self, cursor) -> Dict[str, float]:
        """Analyze recent assessment scores"""
        # PHQ-9 (depression)
        cursor.execute('''
            SELECT score FROM assessment_results
            WHERE user_id = ? AND assessment_type = 'phq9'
            ORDER BY created_at DESC LIMIT 1
        ''', (self.user_id,))
        
        phq9_result = cursor.fetchone()
        phq9_score = (phq9_result[0] / 27) if phq9_result else 0  # Normalize to 0-1
        
        # GAD-7 (anxiety)
        cursor.execute('''
            SELECT score FROM assessment_results
            WHERE user_id = ? AND assessment_type = 'gad7'
            ORDER BY created_at DESC LIMIT 1
        ''', (self.user_id,))
        
        gad7_result = cursor.fetchone()
        gad7_score = (gad7_result[0] / 21) if gad7_result else 0  # Normalize to 0-1
        
        return {'phq9': phq9_score, 'gad7': gad7_score}
    
    def _analyze_language_patterns(self, cursor, since_date: str) -> Dict[str, float]:
        """Analyze language patterns in chat messages"""
        cursor.execute('''
            SELECT message FROM chat_history
            WHERE user_id = ? AND created_at >= ?
        ''', (self.user_id, since_date))
        
        messages = [r[0].lower() for r in cursor.fetchall()]
        all_text = ' '.join(messages)
        
        # Count keyword occurrences
        hopelessness_count = sum(1 for kw in self.HOPELESSNESS_KEYWORDS if kw in all_text)
        isolation_count = sum(1 for kw in self.ISOLATION_KEYWORDS if kw in all_text)
        sleep_count = sum(1 for kw in self.SLEEP_KEYWORDS if kw in all_text)
        
        total_messages = max(len(messages), 1)
        
        return {
            'hopelessness': min(1.0, hopelessness_count / (total_messages * 0.5)),
            'isolation': min(1.0, isolation_count / (total_messages * 0.5)),
            'sleep': min(1.0, sleep_count / (total_messages * 0.3))
        }
    
    def _analyze_engagement(self, cursor, since_date: str) -> float:
        """Analyze engagement patterns (drop in activity)"""
        # Get message counts for two periods
        mid_date = (datetime.now() - timedelta(days=7)).isoformat()
        
        cursor.execute('''
            SELECT COUNT(*) FROM chat_history
            WHERE user_id = ? AND created_at >= ? AND created_at < ?
        ''', (self.user_id, since_date, mid_date))
        older_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM chat_history
            WHERE user_id = ? AND created_at >= ?
        ''', (self.user_id, mid_date))
        recent_count = cursor.fetchone()[0]
        
        if older_count == 0:
            return 0.0
        
        # Calculate engagement drop
        if recent_count < older_count * 0.5:  # More than 50% drop
            return min(1.0, (older_count - recent_count) / older_count)
        
        return 0.0
    
    def _calculate_confidence(self, cursor) -> float:
        """Calculate confidence in the risk assessment"""
        # Based on amount of data available
        cursor.execute('''
            SELECT COUNT(*) FROM chat_history WHERE user_id = ?
        ''', (self.user_id,))
        chat_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM assessment_results WHERE user_id = ?
        ''', (self.user_id,))
        assessment_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM sentiment_history WHERE user_id = ?
        ''', (self.user_id,))
        sentiment_count = cursor.fetchone()[0]
        
        # More data = higher confidence
        data_score = min(1.0, (chat_count / 20 + assessment_count / 5 + sentiment_count / 20) / 3)
        
        return data_score
    
    def _get_risk_level(self) -> str:
        """Convert numeric score to risk level"""
        if self.risk_score >= 70:
            return 'CRITICAL'
        elif self.risk_score >= 50:
            return 'HIGH'
        elif self.risk_score >= 30:
            return 'MODERATE'
        elif self.risk_score >= 10:
            return 'LOW'
        return 'MINIMAL'
    
    def _get_recommendations(self, risk_level: str) -> List[str]:
        """Get recommendations based on risk level"""
        recommendations = {
            'CRITICAL': [
                'Immediate professional intervention recommended',
                'Consider contacting crisis hotline',
                'Reach out to trusted support person',
                'Schedule urgent therapy appointment'
            ],
            'HIGH': [
                'Professional support strongly recommended',
                'Daily check-ins with support system',
                'Consider increasing therapy frequency',
                'Practice safety planning'
            ],
            'MODERATE': [
                'Continue regular therapy sessions',
                'Monitor mood patterns closely',
                'Engage in self-care activities',
                'Reach out when feeling overwhelmed'
            ],
            'LOW': [
                'Maintain current support strategies',
                'Continue healthy habits',
                'Stay connected with support system'
            ],
            'MINIMAL': [
                'Continue current wellness practices',
                'Regular self-reflection encouraged'
            ]
        }
        return recommendations.get(risk_level, [])


# ========== Mood Forecasting ==========

class MoodForecaster:
    """
    Predicts likely mood trends based on historical patterns
    Uses time-series analysis and pattern recognition
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    def forecast(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Forecast mood for the next N days"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get historical mood data
        cursor.execute('''
            SELECT mood_score, created_at FROM sentiment_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 30
        ''', (self.user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        if len(results) < 5:
            return {
                'user_id': self.user_id,
                'forecast': [],
                'confidence': 0,
                'message': 'Insufficient data for forecasting (need at least 5 data points)'
            }
        
        scores = [r[0] for r in reversed(results)]  # Oldest first
        
        # Simple moving average forecast
        forecast = self._moving_average_forecast(scores, days_ahead)
        
        # Detect patterns
        patterns = self._detect_patterns(scores)
        
        # Calculate forecast confidence
        confidence = self._calculate_forecast_confidence(scores)
        
        return {
            'user_id': self.user_id,
            'forecast': forecast,
            'patterns': patterns,
            'confidence': round(confidence, 2),
            'current_trend': self._get_trend(scores),
            'insights': self._generate_insights(scores, patterns),
            'generated_at': datetime.now().isoformat()
        }
    
    def _moving_average_forecast(self, scores: List[float], days: int) -> List[Dict]:
        """Simple exponential moving average forecast"""
        if not scores:
            return []
        
        alpha = 0.3  # Smoothing factor
        forecast = []
        last_value = scores[-1]
        ema = sum(scores[-5:]) / min(5, len(scores))  # Start with simple average
        
        for i in range(days):
            # Apply exponential smoothing
            ema = alpha * last_value + (1 - alpha) * ema
            
            # Add some variance based on historical variance
            variance = self._calculate_variance(scores)
            
            forecast_date = (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d')
            
            forecast.append({
                'date': forecast_date,
                'predicted_mood': round(max(-1, min(1, ema)), 2),
                'range_low': round(max(-1, ema - variance), 2),
                'range_high': round(min(1, ema + variance), 2)
            })
            
            last_value = ema
        
        return forecast
    
    def _calculate_variance(self, scores: List[float]) -> float:
        """Calculate variance in scores"""
        if len(scores) < 2:
            return 0.2
        
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return min(0.4, math.sqrt(variance))
    
    def _detect_patterns(self, scores: List[float]) -> Dict[str, Any]:
        """Detect patterns in mood data"""
        if len(scores) < 7:
            return {'weekly_pattern': None, 'trend': 'unknown'}
        
        # Weekly pattern detection (simplified)
        weekly_avg = []
        for i in range(0, len(scores), 7):
            week_scores = scores[i:i+7]
            if week_scores:
                weekly_avg.append(sum(week_scores) / len(week_scores))
        
        # Trend detection
        if len(scores) >= 3:
            recent = sum(scores[-3:]) / 3
            older = sum(scores[:3]) / 3
            
            if recent > older + 0.1:
                trend = 'improving'
            elif recent < older - 0.1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'unknown'
        
        return {
            'weekly_averages': [round(w, 2) for w in weekly_avg],
            'trend': trend,
            'volatility': 'high' if self._calculate_variance(scores) > 0.25 else 'low'
        }
    
    def _get_trend(self, scores: List[float]) -> str:
        """Get current mood trend"""
        if len(scores) < 3:
            return 'unknown'
        
        recent = sum(scores[-3:]) / 3
        if recent > 0.3:
            return 'positive'
        elif recent < -0.3:
            return 'negative'
        return 'neutral'
    
    def _calculate_forecast_confidence(self, scores: List[float]) -> float:
        """Calculate confidence in forecast"""
        # More data and lower variance = higher confidence
        data_factor = min(1.0, len(scores) / 20)
        variance_factor = 1 - min(1.0, self._calculate_variance(scores) * 2)
        
        return (data_factor + variance_factor) / 2
    
    def _generate_insights(self, scores: List[float], patterns: Dict) -> List[str]:
        """Generate human-readable insights"""
        insights = []
        
        if patterns['trend'] == 'improving':
            insights.append("Your mood has been trending upward recently - that's great progress!")
        elif patterns['trend'] == 'declining':
            insights.append("Your mood has been declining - consider reaching out for support")
        
        if patterns.get('volatility') == 'high':
            insights.append("Your mood shows significant variation - tracking triggers may help")
        
        if len(scores) >= 7:
            avg = sum(scores) / len(scores)
            if avg > 0.2:
                insights.append("Overall, your mood has been positive")
            elif avg < -0.2:
                insights.append("Overall, your mood has been challenging - you're not alone")
        
        return insights


# ========== Pattern Detection ==========

class PatternDetector:
    """Detects behavioral and emotional patterns"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    def detect_all_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Detect all patterns for user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        patterns = {
            'time_patterns': self._detect_time_patterns(cursor, since_date),
            'emotion_patterns': self._detect_emotion_patterns(cursor, since_date),
            'topic_patterns': self._detect_topic_patterns(cursor, since_date),
            'improvement_patterns': self._detect_improvement_patterns(cursor),
            'trigger_patterns': self._detect_trigger_patterns(cursor, since_date)
        }
        
        conn.close()
        
        return {
            'user_id': self.user_id,
            'patterns': patterns,
            'analysis_period_days': days,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def _detect_time_patterns(self, cursor, since_date: str) -> Dict:
        """Detect time-based patterns"""
        cursor.execute('''
            SELECT created_at, sentiment_score FROM sentiment_history
            WHERE user_id = ? AND created_at >= ?
        ''', (self.user_id, since_date))
        
        results = cursor.fetchall()
        
        hour_moods = {}
        day_moods = {}
        
        for created_at, score in results:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                hour = dt.hour
                day = dt.strftime('%A')
                
                if hour not in hour_moods:
                    hour_moods[hour] = []
                hour_moods[hour].append(score)
                
                if day not in day_moods:
                    day_moods[day] = []
                day_moods[day].append(score)
            except:
                continue
        
        # Find best and worst times
        hour_avgs = {h: sum(s)/len(s) for h, s in hour_moods.items() if s}
        day_avgs = {d: sum(s)/len(s) for d, s in day_moods.items() if s}
        
        best_hour = max(hour_avgs, key=hour_avgs.get) if hour_avgs else None
        worst_hour = min(hour_avgs, key=hour_avgs.get) if hour_avgs else None
        best_day = max(day_avgs, key=day_avgs.get) if day_avgs else None
        worst_day = min(day_avgs, key=day_avgs.get) if day_avgs else None
        
        return {
            'best_hour': best_hour,
            'worst_hour': worst_hour,
            'best_day': best_day,
            'worst_day': worst_day,
            'hourly_averages': {str(h): round(v, 2) for h, v in hour_avgs.items()},
            'daily_averages': {d: round(v, 2) for d, v in day_avgs.items()}
        }
    
    def _detect_emotion_patterns(self, cursor, since_date: str) -> Dict:
        """Detect emotion frequency patterns"""
        cursor.execute('''
            SELECT emotions FROM sentiment_history
            WHERE user_id = ? AND created_at >= ? AND emotions IS NOT NULL
        ''', (self.user_id, since_date))
        
        all_emotions = []
        for row in cursor.fetchall():
            try:
                emotions = json.loads(row[0]) if row[0] else {}
                for emotion, score in emotions.items():
                    if score > 0.3:  # Significant emotion
                        all_emotions.append(emotion)
            except:
                continue
        
        emotion_counts = Counter(all_emotions)
        total = sum(emotion_counts.values()) or 1
        
        return {
            'most_common': emotion_counts.most_common(5),
            'emotion_distribution': {e: round(c/total, 2) for e, c in emotion_counts.most_common(10)}
        }
    
    def _detect_topic_patterns(self, cursor, since_date: str) -> Dict:
        """Detect common topics discussed"""
        cursor.execute('''
            SELECT message FROM chat_history
            WHERE user_id = ? AND created_at >= ?
        ''', (self.user_id, since_date))
        
        # Topic keywords
        topics = {
            'anxiety': ['anxiety', 'anxious', 'worried', 'panic', 'nervous'],
            'depression': ['depressed', 'depression', 'sad', 'hopeless', 'empty'],
            'sleep': ['sleep', 'insomnia', 'tired', 'exhausted', 'nightmare'],
            'relationships': ['friend', 'family', 'partner', 'relationship', 'lonely'],
            'work_stress': ['work', 'job', 'boss', 'deadline', 'stress'],
            'self_esteem': ['worthless', 'failure', 'ugly', 'hate myself', 'not good enough']
        }
        
        topic_counts = {topic: 0 for topic in topics}
        
        for row in cursor.fetchall():
            message = row[0].lower()
            for topic, keywords in topics.items():
                if any(kw in message for kw in keywords):
                    topic_counts[topic] += 1
        
        return {
            'topic_frequency': topic_counts,
            'primary_concern': max(topic_counts, key=topic_counts.get) if any(topic_counts.values()) else None
        }
    
    def _detect_improvement_patterns(self, cursor) -> Dict:
        """Detect what's associated with improvement"""
        # Compare sentiment before and after certain keywords
        cursor.execute('''
            SELECT message, sentiment_score FROM sentiment_history
            WHERE user_id = ?
            ORDER BY created_at
        ''', (self.user_id,))
        
        results = cursor.fetchall()
        
        # Track what precedes positive sentiment
        positive_associations = []
        
        for i, (message, score) in enumerate(results):
            if score > 0.3 and i > 0:  # Positive sentiment
                # What was discussed before?
                prev_message = results[i-1][0].lower()
                if 'exercise' in prev_message or 'walk' in prev_message:
                    positive_associations.append('physical_activity')
                if 'friend' in prev_message or 'family' in prev_message:
                    positive_associations.append('social_connection')
                if 'sleep' in prev_message and 'well' in prev_message:
                    positive_associations.append('good_sleep')
        
        return {
            'positive_associations': dict(Counter(positive_associations)),
            'sample_size': len(results)
        }
    
    def _detect_trigger_patterns(self, cursor, since_date: str) -> Dict:
        """Detect potential triggers for negative moods"""
        cursor.execute('''
            SELECT message, sentiment_score FROM sentiment_history
            WHERE user_id = ? AND created_at >= ? AND sentiment_score < -0.3
        ''', (self.user_id, since_date))
        
        negative_messages = [row[0].lower() for row in cursor.fetchall()]
        
        # Common trigger keywords
        triggers = {
            'work': ['work', 'job', 'boss', 'meeting', 'deadline'],
            'social': ['friend', 'party', 'people', 'social'],
            'family': ['family', 'parent', 'mom', 'dad', 'sibling'],
            'health': ['sick', 'pain', 'doctor', 'health'],
            'financial': ['money', 'bill', 'debt', 'afford']
        }
        
        trigger_counts = {t: 0 for t in triggers}
        
        for message in negative_messages:
            for trigger, keywords in triggers.items():
                if any(kw in message for kw in keywords):
                    trigger_counts[trigger] += 1
        
        return {
            'likely_triggers': {k: v for k, v in sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True) if v > 0}
        }


# ========== API Functions ==========

def get_risk_prediction(user_id: int, days: int = 14) -> Dict[str, Any]:
    """Get risk prediction for a user"""
    predictor = MentalHealthRiskPredictor(user_id)
    return predictor.calculate_risk(days)


def get_mood_forecast(user_id: int, days_ahead: int = 7) -> Dict[str, Any]:
    """Get mood forecast for a user"""
    forecaster = MoodForecaster(user_id)
    return forecaster.forecast(days_ahead)


def get_user_patterns(user_id: int, days: int = 30) -> Dict[str, Any]:
    """Get detected patterns for a user"""
    detector = PatternDetector(user_id)
    return detector.detect_all_patterns(days)


def get_comprehensive_analysis(user_id: int) -> Dict[str, Any]:
    """Get comprehensive predictive analysis"""
    return {
        'risk': get_risk_prediction(user_id),
        'forecast': get_mood_forecast(user_id),
        'patterns': get_user_patterns(user_id),
        'generated_at': datetime.now().isoformat()
    }
