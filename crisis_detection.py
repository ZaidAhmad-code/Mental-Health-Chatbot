"""
Crisis Detection System for Mental Health Chatbot
Detects potential crisis situations through keyword analysis and sentiment detection
"""

import re
from typing import Dict, List, Tuple

class CrisisDetector:
    """Detects crisis situations in user messages"""
    
    # High-risk keywords indicating immediate danger
    CRISIS_KEYWORDS = [
        # Suicide/Self-harm
        'suicide', 'suicidal', 'kill myself', 'end my life', 'want to die', 
        'better off dead', 'no reason to live', 'take my own life',
        'self harm', 'self-harm', 'cut myself', 'hurt myself', 'harm myself',
        
        # Hopelessness
        'no way out', 'no hope', 'hopeless', 'give up', 'can\'t go on',
        'nothing left', 'end it all', 'no point', 'tired of living',
        
        # Violence to others
        'hurt someone', 'kill someone', 'harm others', 'violent thoughts',
        
        # Substance abuse crisis
        'overdose', 'too many pills', 'substance abuse crisis',
        
        # Emergency situations
        'emergency', 'crisis', 'help me now', 'urgent help'
    ]
    
    # Medium-risk keywords indicating serious concern
    WARNING_KEYWORDS = [
        'depressed', 'depression', 'anxious', 'anxiety', 'panic attack',
        'can\'t cope', 'overwhelmed', 'breaking down', 'falling apart',
        'scared', 'terrified', 'alone', 'lonely', 'isolated',
        'worthless', 'useless', 'failure', 'burden', 'hate myself',
        'self-hatred', 'disgust myself', 'no one cares', 'nobody cares',
        'crying', 'can\'t stop crying', 'can\'t sleep', 'nightmares'
    ]
    
    @staticmethod
    def detect_crisis(message: str) -> Dict:
        """
        Analyze message for crisis indicators
        
        Args:
            message: User's message text
            
        Returns:
            Dictionary with crisis detection results
        """
        message_lower = message.lower()
        
        # Check for crisis keywords
        crisis_triggers = []
        warning_triggers = []
        
        for keyword in CrisisDetector.CRISIS_KEYWORDS:
            if keyword in message_lower:
                crisis_triggers.append(keyword)
        
        for keyword in CrisisDetector.WARNING_KEYWORDS:
            if keyword in message_lower:
                warning_triggers.append(keyword)
        
        # Determine crisis level
        if crisis_triggers:
            level = 'CRITICAL'
            severity = 10
            message_type = 'crisis'
        elif len(warning_triggers) >= 3:
            level = 'HIGH'
            severity = 7
            message_type = 'warning'
        elif warning_triggers:
            level = 'MODERATE'
            severity = 5
            message_type = 'concern'
        else:
            level = 'NORMAL'
            severity = 0
            message_type = 'normal'
        
        return {
            'is_crisis': level == 'CRITICAL',
            'is_warning': level in ['CRITICAL', 'HIGH'],
            'level': level,
            'severity': severity,
            'type': message_type,
            'crisis_triggers': crisis_triggers,
            'warning_triggers': warning_triggers,
            'requires_intervention': level in ['CRITICAL', 'HIGH'],
            'recommendation': CrisisDetector._get_recommendation(level)
        }
    
    @staticmethod
    def _get_recommendation(level: str) -> str:
        """Get recommendation based on crisis level"""
        recommendations = {
            'CRITICAL': 'IMMEDIATE_HELP_NEEDED',
            'HIGH': 'PROFESSIONAL_SUPPORT_RECOMMENDED',
            'MODERATE': 'MONITORING_SUGGESTED',
            'NORMAL': 'CONTINUE_CONVERSATION'
        }
        return recommendations.get(level, 'CONTINUE_CONVERSATION')
    
    @staticmethod
    def get_crisis_resources() -> Dict:
        """Get emergency resources and hotlines"""
        return {
            'emergency': {
                'title': '🆘 Immediate Emergency',
                'description': 'If you are in immediate danger, please call emergency services.',
                'contacts': [
                    {'name': 'Emergency Services', 'number': '911', 'available': '24/7'},
                    {'name': 'National Suicide Prevention Lifeline (US)', 'number': '988', 'available': '24/7'},
                    {'name': 'Crisis Text Line', 'number': 'Text HOME to 741741', 'available': '24/7'}
                ]
            },
            'international': {
                'title': '🌍 International Hotlines',
                'contacts': [
                    {'country': 'UK', 'name': 'Samaritans', 'number': '116 123'},
                    {'country': 'Australia', 'name': 'Lifeline', 'number': '13 11 14'},
                    {'country': 'Canada', 'name': 'Crisis Services Canada', 'number': '1-833-456-4566'},
                    {'country': 'India', 'name': 'AASRA', 'number': '91-9820466726'}
                ]
            },
            'online_support': {
                'title': '💬 Online Crisis Support',
                'resources': [
                    {'name': 'Crisis Text Line', 'link': 'https://www.crisistextline.org'},
                    {'name': 'International Association for Suicide Prevention', 'link': 'https://www.iasp.info/resources/Crisis_Centres/'},
                    {'name': 'Befrienders Worldwide', 'link': 'https://www.befrienders.org'}
                ]
            }
        }
    
    @staticmethod
    def check_assessment_crisis(assessment_type: str, score: int) -> Dict:
        """
        Check if assessment score indicates crisis level
        
        Args:
            assessment_type: 'phq9' or 'gad7'
            score: Assessment score
            
        Returns:
            Dictionary with crisis assessment
        """
        if assessment_type == 'phq9':
            # PHQ-9: 20-27 is severe depression
            if score >= 20:
                return {
                    'is_crisis': True,
                    'level': 'CRITICAL',
                    'message': 'Your PHQ-9 score indicates severe depression. Please seek immediate professional help.',
                    'requires_intervention': True
                }
            elif score >= 15:
                return {
                    'is_crisis': False,
                    'level': 'HIGH',
                    'message': 'Your PHQ-9 score indicates moderately severe depression. Professional help is strongly recommended.',
                    'requires_intervention': True
                }
        
        elif assessment_type == 'gad7':
            # GAD-7: 15-21 is severe anxiety
            if score >= 15:
                return {
                    'is_crisis': True,
                    'level': 'CRITICAL',
                    'message': 'Your GAD-7 score indicates severe anxiety. Please consider seeking professional help.',
                    'requires_intervention': True
                }
            elif score >= 10:
                return {
                    'is_crisis': False,
                    'level': 'HIGH',
                    'message': 'Your GAD-7 score indicates moderate anxiety. Professional support is recommended.',
                    'requires_intervention': True
                }
        
        return {
            'is_crisis': False,
            'level': 'NORMAL',
            'message': 'Continue monitoring your mental health.',
            'requires_intervention': False
        }


def format_crisis_response(crisis_info: Dict) -> str:
    """
    Format a crisis response message
    
    Args:
        crisis_info: Crisis detection results
        
    Returns:
        Formatted response message
    """
    if crisis_info['level'] == 'CRITICAL':
        return """
🆘 **CRISIS ALERT**

I'm very concerned about what you've shared. Your safety is the top priority.

**IMMEDIATE ACTIONS:**
• If you are in immediate danger, please call 911 or your local emergency services
• National Suicide Prevention Lifeline: 988 (US) - Available 24/7
• Crisis Text Line: Text HOME to 741741

**You are not alone.** Professional help is available right now, and people care about you.

Please reach out to one of these resources immediately. They are trained to help in situations like this.
"""
    
    elif crisis_info['level'] == 'HIGH':
        return """
⚠️ **Important: Professional Support Recommended**

I hear that you're going through a very difficult time. While I'm here to support you, I strongly encourage you to reach out to a mental health professional who can provide the specialized help you need.

**Support Resources:**
• National Suicide Prevention Lifeline: 988 (US)
• Crisis Text Line: Text HOME to 741741
• Your doctor or local mental health services

Would you like to talk about what's troubling you? I'm here to listen, but please also consider reaching out to professional support.
"""
    
    return ""


# Example usage and testing
if __name__ == "__main__":
    detector = CrisisDetector()
    
    # Test cases
    test_messages = [
        "I want to kill myself",
        "I'm feeling really depressed and anxious",
        "How can I improve my mood?",
        "I'm so overwhelmed and can't cope anymore, feeling hopeless and worthless"
    ]
    
    print("Crisis Detection System - Test Results")
    print("=" * 60)
    
    for msg in test_messages:
        result = detector.detect_crisis(msg)
        print(f"\nMessage: {msg}")
        print(f"Level: {result['level']}")
        print(f"Severity: {result['severity']}/10")
        print(f"Crisis: {result['is_crisis']}")
        print(f"Triggers: {result['crisis_triggers'] + result['warning_triggers']}")
        print(f"Recommendation: {result['recommendation']}")
        print("-" * 60)
