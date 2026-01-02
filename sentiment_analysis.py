"""
Sentiment Analysis Module for Mental Health Chatbot
Implements sentiment and emotion analysis for user messages
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import Counter

from database import DB_PATH
from error_handler import logger
import sqlite3


# ========== Sentiment Lexicons ==========

# Positive sentiment words
POSITIVE_WORDS = {
    'happy', 'joy', 'joyful', 'glad', 'cheerful', 'delighted', 'pleased', 'content',
    'excited', 'thrilled', 'wonderful', 'amazing', 'great', 'good', 'fantastic',
    'excellent', 'better', 'improving', 'hopeful', 'optimistic', 'grateful',
    'thankful', 'blessed', 'loved', 'supported', 'calm', 'peaceful', 'relaxed',
    'confident', 'proud', 'accomplished', 'motivated', 'energetic', 'positive',
    'beautiful', 'lovely', 'smile', 'laugh', 'enjoy', 'fun', 'comfortable',
    'safe', 'secure', 'strong', 'brave', 'courageous', 'resilient', 'progress',
    'success', 'achieved', 'overcome', 'managing', 'coping', 'healing'
}

# Negative sentiment words
NEGATIVE_WORDS = {
    'sad', 'unhappy', 'depressed', 'depression', 'miserable', 'upset', 'hurt',
    'pain', 'painful', 'suffering', 'anxious', 'anxiety', 'worried', 'nervous',
    'scared', 'afraid', 'fear', 'fearful', 'terrified', 'panic', 'stress',
    'stressed', 'overwhelmed', 'hopeless', 'helpless', 'worthless', 'useless',
    'failure', 'failed', 'lonely', 'alone', 'isolated', 'abandoned', 'rejected',
    'angry', 'frustrated', 'annoyed', 'irritated', 'mad', 'furious', 'hate',
    'terrible', 'awful', 'horrible', 'worst', 'bad', 'worse', 'struggling',
    'difficult', 'hard', 'tough', 'exhausted', 'tired', 'drained', 'numb',
    'empty', 'lost', 'confused', 'uncertain', 'doubt', 'guilty', 'shame',
    'embarrassed', 'regret', 'disappointed', 'devastated', 'broken', 'trauma'
}

# Emotion categories with associated words
EMOTION_LEXICON = {
    'joy': {'happy', 'joy', 'joyful', 'glad', 'cheerful', 'delighted', 'excited', 'thrilled', 'wonderful', 'amazing', 'fantastic', 'great', 'smile', 'laugh'},
    'sadness': {'sad', 'unhappy', 'depressed', 'miserable', 'upset', 'hurt', 'crying', 'tears', 'grief', 'mourning', 'heartbroken', 'devastated', 'lonely', 'empty'},
    'fear': {'afraid', 'scared', 'fear', 'fearful', 'terrified', 'panic', 'anxious', 'nervous', 'worried', 'dread', 'horrified', 'frightened'},
    'anger': {'angry', 'mad', 'furious', 'annoyed', 'irritated', 'frustrated', 'rage', 'hate', 'resentful', 'bitter', 'hostile'},
    'surprise': {'surprised', 'shocked', 'amazed', 'astonished', 'stunned', 'unexpected', 'sudden'},
    'disgust': {'disgusted', 'revolted', 'repulsed', 'sickened', 'grossed'},
    'anxiety': {'anxious', 'anxiety', 'worried', 'nervous', 'stress', 'stressed', 'panic', 'overwhelmed', 'uneasy', 'restless', 'tense'},
    'hope': {'hopeful', 'optimistic', 'better', 'improving', 'progress', 'forward', 'future', 'possibility', 'potential'},
    'gratitude': {'grateful', 'thankful', 'blessed', 'appreciate', 'appreciation', 'thanks'},
    'love': {'love', 'loved', 'caring', 'affection', 'tender', 'warm', 'attached', 'connected'}
}

# Intensity modifiers
INTENSIFIERS = {
    'very': 1.5,
    'extremely': 2.0,
    'incredibly': 2.0,
    'really': 1.3,
    'so': 1.4,
    'absolutely': 1.8,
    'totally': 1.6,
    'completely': 1.7,
    'deeply': 1.6,
    'terribly': 1.8,
    'awfully': 1.7,
    'quite': 1.2,
    'somewhat': 0.8,
    'slightly': 0.6,
    'a bit': 0.7,
    'a little': 0.7,
    'kind of': 0.8,
    'sort of': 0.8
}

# Negation words
NEGATIONS = {'not', "n't", 'no', 'never', 'nothing', 'nowhere', 'neither', 'nobody', 'none', 'hardly', 'barely', 'scarcely'}


# ========== Sentiment Analysis Class ==========

class SentimentAnalyzer:
    """Analyzes sentiment and emotions in text"""
    
    def __init__(self):
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS
        self.emotion_lexicon = EMOTION_LEXICON
        self.intensifiers = INTENSIFIERS
        self.negations = NEGATIONS
    
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation but keep apostrophes for contractions
        text = re.sub(r"[^\w\s']", ' ', text)
        
        # Tokenize
        words = text.split()
        
        return words
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text
        Returns: {
            'sentiment': 'positive'|'negative'|'neutral',
            'score': float (-1 to 1),
            'confidence': float (0 to 1),
            'positive_words': list,
            'negative_words': list
        }
        """
        words = self.preprocess_text(text)
        
        positive_found = []
        negative_found = []
        score = 0.0
        
        # Track negation context (words within 3 tokens of negation)
        negation_window = 0
        
        for i, word in enumerate(words):
            # Check for negation
            if word in self.negations or word.endswith("n't"):
                negation_window = 3
                continue
            
            # Apply intensity modifier if previous word is intensifier
            intensity = 1.0
            if i > 0 and words[i-1] in self.intensifiers:
                intensity = self.intensifiers[words[i-1]]
            
            # Check if negated
            is_negated = negation_window > 0
            
            # Check positive words
            if word in self.positive_words:
                if is_negated:
                    negative_found.append(f"not {word}")
                    score -= 0.5 * intensity
                else:
                    positive_found.append(word)
                    score += 1.0 * intensity
            
            # Check negative words
            elif word in self.negative_words:
                if is_negated:
                    positive_found.append(f"not {word}")
                    score += 0.3 * intensity  # Negated negative is weakly positive
                else:
                    negative_found.append(word)
                    score -= 1.0 * intensity
            
            # Decrement negation window
            if negation_window > 0:
                negation_window -= 1
        
        # Normalize score
        total_sentiment_words = len(positive_found) + len(negative_found)
        if total_sentiment_words > 0:
            normalized_score = score / total_sentiment_words
            # Clamp to -1 to 1
            normalized_score = max(-1, min(1, normalized_score))
        else:
            normalized_score = 0.0
        
        # Determine sentiment category
        if normalized_score > 0.2:
            sentiment = 'positive'
        elif normalized_score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Calculate confidence (based on number of sentiment words found)
        word_count = len(words)
        sentiment_ratio = total_sentiment_words / word_count if word_count > 0 else 0
        confidence = min(sentiment_ratio * 2, 1.0)  # Cap at 1.0
        
        return {
            'sentiment': sentiment,
            'score': round(normalized_score, 3),
            'confidence': round(confidence, 3),
            'positive_words': positive_found,
            'negative_words': negative_found,
            'word_count': word_count,
            'sentiment_word_count': total_sentiment_words
        }
    
    def analyze_emotions(self, text: str) -> Dict:
        """
        Analyze emotions in text
        Returns: {
            'primary_emotion': str,
            'emotions': {emotion: score},
            'emotion_words': {emotion: [words]}
        }
        """
        words = self.preprocess_text(text)
        word_set = set(words)
        
        emotion_scores = {}
        emotion_words = {}
        
        for emotion, lexicon in self.emotion_lexicon.items():
            found_words = word_set.intersection(lexicon)
            if found_words:
                # Score based on number of words found
                score = len(found_words) / len(words) if words else 0
                emotion_scores[emotion] = round(score, 3)
                emotion_words[emotion] = list(found_words)
        
        # Determine primary emotion
        primary_emotion = None
        if emotion_scores:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
        
        return {
            'primary_emotion': primary_emotion,
            'emotions': emotion_scores,
            'emotion_words': emotion_words
        }
    
    def get_mental_health_indicators(self, text: str) -> Dict:
        """
        Analyze text for mental health indicators
        Returns indicators relevant to depression, anxiety, etc.
        """
        text_lower = text.lower()
        words = self.preprocess_text(text)
        
        indicators = {
            'depression_indicators': [],
            'anxiety_indicators': [],
            'crisis_indicators': [],
            'positive_indicators': [],
            'risk_level': 'low'
        }
        
        # Depression indicators
        depression_phrases = [
            'feel empty', 'feel numb', 'no energy', 'cant sleep', "can't sleep",
            'sleep too much', 'no appetite', 'eating too much', 'feel worthless',
            'feel guilty', 'cant concentrate', "can't concentrate", 'no interest',
            'dont care', "don't care", 'whats the point', "what's the point",
            'feel alone', 'no one cares', 'feel hopeless', 'feel helpless'
        ]
        
        for phrase in depression_phrases:
            if phrase in text_lower:
                indicators['depression_indicators'].append(phrase)
        
        # Depression words
        depression_words = {'depressed', 'depression', 'hopeless', 'worthless', 'empty', 'numb'}
        indicators['depression_indicators'].extend(list(set(words) & depression_words))
        
        # Anxiety indicators
        anxiety_phrases = [
            'cant stop worrying', "can't stop worrying", 'feel anxious',
            'panic attack', 'heart racing', 'cant breathe', "can't breathe",
            'feel nervous', 'on edge', 'restless', 'fear of', 'worried about'
        ]
        
        for phrase in anxiety_phrases:
            if phrase in text_lower:
                indicators['anxiety_indicators'].append(phrase)
        
        # Anxiety words
        anxiety_words = {'anxious', 'anxiety', 'worried', 'panic', 'nervous', 'stressed'}
        indicators['anxiety_indicators'].extend(list(set(words) & anxiety_words))
        
        # Crisis indicators (already handled by crisis_detection.py but included here)
        crisis_words = {'suicide', 'suicidal', 'kill myself', 'end my life', 'self-harm', 'hurt myself'}
        for word in crisis_words:
            if word in text_lower:
                indicators['crisis_indicators'].append(word)
        
        # Positive indicators
        positive_phrases = [
            'feeling better', 'getting better', 'making progress', 'feeling good',
            'feeling happy', 'feeling hopeful', 'things are improving', 'im okay', "i'm okay"
        ]
        
        for phrase in positive_phrases:
            if phrase in text_lower:
                indicators['positive_indicators'].append(phrase)
        
        positive_words = {'better', 'improving', 'hopeful', 'progress', 'happy', 'good'}
        indicators['positive_indicators'].extend(list(set(words) & positive_words))
        
        # Determine risk level
        if indicators['crisis_indicators']:
            indicators['risk_level'] = 'critical'
        elif len(indicators['depression_indicators']) >= 3 or len(indicators['anxiety_indicators']) >= 3:
            indicators['risk_level'] = 'high'
        elif indicators['depression_indicators'] or indicators['anxiety_indicators']:
            indicators['risk_level'] = 'moderate'
        elif indicators['positive_indicators']:
            indicators['risk_level'] = 'low'
        
        return indicators
    
    def full_analysis(self, text: str) -> Dict:
        """
        Perform full sentiment and emotion analysis
        Returns comprehensive analysis results
        """
        sentiment = self.analyze_sentiment(text)
        emotions = self.analyze_emotions(text)
        mh_indicators = self.get_mental_health_indicators(text)
        
        return {
            'text_length': len(text),
            'word_count': len(self.preprocess_text(text)),
            'sentiment': sentiment,
            'emotions': emotions,
            'mental_health_indicators': mh_indicators,
            'analyzed_at': datetime.now().isoformat()
        }


# ========== Database Operations ==========

def init_sentiment_table():
    """Initialize sentiment tracking table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_type TEXT DEFAULT 'chat',
            sentiment TEXT NOT NULL,
            sentiment_score REAL NOT NULL,
            primary_emotion TEXT,
            risk_level TEXT,
            analysis_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✓ Sentiment table initialized")


def save_sentiment_analysis(user_id: int, analysis: Dict, message_type: str = 'chat') -> int:
    """Save sentiment analysis to database"""
    import json
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sentiment_history 
        (user_id, message_type, sentiment, sentiment_score, primary_emotion, risk_level, analysis_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        message_type,
        analysis['sentiment']['sentiment'],
        analysis['sentiment']['score'],
        analysis['emotions']['primary_emotion'],
        analysis['mental_health_indicators']['risk_level'],
        json.dumps(analysis)
    ))
    
    conn.commit()
    analysis_id = cursor.lastrowid
    conn.close()
    
    return analysis_id


def get_sentiment_history(user_id: int, limit: int = 20) -> List[Dict]:
    """Get sentiment history for user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sentiment, sentiment_score, primary_emotion, risk_level, created_at
        FROM sentiment_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'sentiment': r[0],
            'score': r[1],
            'primary_emotion': r[2],
            'risk_level': r[3],
            'timestamp': r[4]
        }
        for r in results
    ]


def get_sentiment_trends(user_id: int, days: int = 30) -> Dict:
    """Get sentiment trends over time"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sentiment, sentiment_score, primary_emotion, risk_level, DATE(created_at) as day
        FROM sentiment_history
        WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
        ORDER BY created_at ASC
    ''', (user_id, days))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        return {
            'average_score': 0,
            'sentiment_distribution': {},
            'emotion_distribution': {},
            'risk_distribution': {},
            'trend': 'insufficient_data',
            'data_points': 0
        }
    
    # Calculate distributions
    sentiments = [r[0] for r in results]
    scores = [r[1] for r in results]
    emotions = [r[2] for r in results if r[2]]
    risks = [r[3] for r in results]
    
    # Calculate trend
    if len(scores) >= 3:
        recent_avg = sum(scores[-3:]) / 3
        older_avg = sum(scores[:3]) / 3
        if recent_avg > older_avg + 0.1:
            trend = 'improving'
        elif recent_avg < older_avg - 0.1:
            trend = 'declining'
        else:
            trend = 'stable'
    else:
        trend = 'insufficient_data'
    
    return {
        'average_score': round(sum(scores) / len(scores), 3),
        'sentiment_distribution': dict(Counter(sentiments)),
        'emotion_distribution': dict(Counter(emotions)),
        'risk_distribution': dict(Counter(risks)),
        'trend': trend,
        'data_points': len(results)
    }


# Global analyzer instance
sentiment_analyzer = SentimentAnalyzer()

# Initialize table
init_sentiment_table()
