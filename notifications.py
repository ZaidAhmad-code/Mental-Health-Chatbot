"""
Email Notification Module for Mental Health Chatbot
Implements email notifications for various events
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from jinja2 import Template

from error_handler import logger
from database import DB_PATH
import sqlite3


# ========== Email Configuration ==========

class EmailConfig:
    """Email configuration from environment variables"""
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@mindspace.app')
    FROM_NAME = os.getenv('FROM_NAME', 'MindSpace Mental Health')
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if email is configured"""
        return bool(cls.SMTP_USERNAME and cls.SMTP_PASSWORD)


# ========== Email Templates ==========

TEMPLATES = {
    'welcome': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #9b87f5, #7E69AB); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #9b87f5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Welcome to MindSpace</h1>
        </div>
        <div class="content">
            <h2>Hello {{ first_name or username }}!</h2>
            <p>Welcome to MindSpace, your AI-powered mental health companion. We're here to support you on your journey to better mental wellness.</p>
            
            <h3>What you can do:</h3>
            <ul>
                <li>💬 Chat with our AI counselor anytime</li>
                <li>📊 Take PHQ-9 and GAD-7 assessments</li>
                <li>📈 Track your mental health progress</li>
                <li>🆘 Access crisis resources when needed</li>
            </ul>
            
            <p><strong>Remember:</strong> While MindSpace provides support, it's not a replacement for professional mental health care. Please seek professional help if you're in crisis.</p>
            
            <center>
                <a href="{{ app_url }}" class="button">Start Your Journey</a>
            </center>
        </div>
        <div class="footer">
            <p>If you're in crisis, please call 988 (Suicide Prevention Lifeline) or text HOME to 741741</p>
            <p>© 2025 MindSpace. Take care of your mind. 💜</p>
        </div>
    </div>
</body>
</html>
""",

    'verification': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #9b87f5, #7E69AB); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #9b87f5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }
        .code { background: #e0e0e0; padding: 15px 30px; font-size: 24px; letter-spacing: 5px; border-radius: 5px; display: inline-block; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Verify Your Email</h1>
        </div>
        <div class="content">
            <h2>Hello {{ username }}!</h2>
            <p>Please verify your email address to complete your MindSpace registration.</p>
            
            <center>
                <a href="{{ verification_url }}" class="button">Verify Email</a>
            </center>
            
            <p>Or use this verification code:</p>
            <center>
                <div class="code">{{ verification_code }}</div>
            </center>
            
            <p><small>This link expires in 24 hours. If you didn't create an account, please ignore this email.</small></p>
        </div>
        <div class="footer">
            <p>© 2025 MindSpace. Take care of your mind. 💜</p>
        </div>
    </div>
</body>
</html>
""",

    'password_reset': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #ef4444; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Reset</h1>
        </div>
        <div class="content">
            <h2>Hello {{ username }}!</h2>
            <p>We received a request to reset your MindSpace password.</p>
            
            <center>
                <a href="{{ reset_url }}" class="button">Reset Password</a>
            </center>
            
            <p>This link expires in 24 hours.</p>
            
            <p><strong>Didn't request this?</strong> If you didn't request a password reset, please ignore this email or contact support if you're concerned about your account security.</p>
        </div>
        <div class="footer">
            <p>© 2025 MindSpace. Take care of your mind. 💜</p>
        </div>
    </div>
</body>
</html>
""",

    'crisis_alert': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .alert-box { background: #fee2e2; border: 2px solid #ef4444; border-radius: 10px; padding: 20px; margin: 20px 0; }
        .resources { background: white; border-radius: 10px; padding: 20px; margin: 20px 0; }
        .resource-item { padding: 10px 0; border-bottom: 1px solid #eee; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🆘 Crisis Alert</h1>
        </div>
        <div class="content">
            <div class="alert-box">
                <h2>⚠️ {{ crisis_level }} Level Crisis Detected</h2>
                <p><strong>Time:</strong> {{ timestamp }}</p>
                <p><strong>Triggers:</strong> {{ triggers }}</p>
            </div>
            
            <h3>Immediate Resources:</h3>
            <div class="resources">
                <div class="resource-item">
                    <strong>📞 National Suicide Prevention Lifeline:</strong> 988
                </div>
                <div class="resource-item">
                    <strong>💬 Crisis Text Line:</strong> Text HOME to 741741
                </div>
                <div class="resource-item">
                    <strong>🚨 Emergency Services:</strong> 911
                </div>
            </div>
            
            <p>This alert was generated because concerning content was detected. If you're in crisis, please reach out to one of the resources above immediately.</p>
            
            <p><strong>You are not alone. Help is available.</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated crisis alert from MindSpace.</p>
            <p>© 2025 MindSpace. Take care of your mind. 💜</p>
        </div>
    </div>
</body>
</html>
""",

    'weekly_report': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #9b87f5, #7E69AB); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .stat-box { display: inline-block; background: white; border-radius: 10px; padding: 20px; margin: 10px; text-align: center; min-width: 120px; }
        .stat-number { font-size: 32px; font-weight: bold; color: #9b87f5; }
        .stat-label { font-size: 12px; color: #666; }
        .trend { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .improving { background: #d1fae5; color: #065f46; }
        .stable { background: #dbeafe; color: #1e40af; }
        .worsening { background: #fee2e2; color: #991b1b; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Your Weekly Wellness Report</h1>
            <p>{{ week_start }} - {{ week_end }}</p>
        </div>
        <div class="content">
            <h2>Hello {{ first_name or username }}!</h2>
            <p>Here's your mental wellness summary for this week:</p>
            
            <center>
                <div class="stat-box">
                    <div class="stat-number">{{ conversations }}</div>
                    <div class="stat-label">Conversations</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{{ assessments }}</div>
                    <div class="stat-label">Assessments</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{{ engagement_score }}</div>
                    <div class="stat-label">Engagement</div>
                </div>
            </center>
            
            <h3>📈 Mental Health Trends</h3>
            {% if phq9_trend %}
            <div class="trend {{ 'improving' if phq9_trend == 'improving' else 'stable' if phq9_trend == 'stable' else 'worsening' }}">
                <strong>Depression (PHQ-9):</strong> {{ phq9_trend | capitalize }}
                {% if latest_phq9 %} - Latest score: {{ latest_phq9 }}{% endif %}
            </div>
            {% endif %}
            
            {% if gad7_trend %}
            <div class="trend {{ 'improving' if gad7_trend == 'improving' else 'stable' if gad7_trend == 'stable' else 'worsening' }}">
                <strong>Anxiety (GAD-7):</strong> {{ gad7_trend | capitalize }}
                {% if latest_gad7 %} - Latest score: {{ latest_gad7 }}{% endif %}
            </div>
            {% endif %}
            
            <h3>💡 Wellness Tips</h3>
            <ul>
                {% for tip in tips %}
                <li>{{ tip }}</li>
                {% endfor %}
            </ul>
            
            <p><strong>Keep it up!</strong> Consistency is key to mental wellness.</p>
        </div>
        <div class="footer">
            <p>If you're struggling, please reach out to a mental health professional.</p>
            <p>© 2025 MindSpace. Take care of your mind. 💜</p>
        </div>
    </div>
</body>
</html>
""",

    'assessment_complete': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #9b87f5, #7E69AB); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .result-box { background: white; border-radius: 10px; padding: 20px; margin: 20px 0; text-align: center; }
        .score { font-size: 48px; font-weight: bold; color: #9b87f5; }
        .severity { font-size: 18px; padding: 10px 20px; border-radius: 20px; display: inline-block; margin: 10px 0; }
        .minimal { background: #d1fae5; color: #065f46; }
        .mild { background: #fef3c7; color: #92400e; }
        .moderate { background: #fed7aa; color: #9a3412; }
        .severe { background: #fee2e2; color: #991b1b; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Assessment Complete</h1>
        </div>
        <div class="content">
            <h2>{{ assessment_name }} Results</h2>
            
            <div class="result-box">
                <div class="score">{{ score }}/{{ max_score }}</div>
                <div class="severity {{ severity_class }}">{{ severity }}</div>
            </div>
            
            <h3>What this means:</h3>
            <p>{{ interpretation }}</p>
            
            <h3>Recommendations:</h3>
            <ul>
                {% for rec in recommendations %}
                <li>{{ rec }}</li>
                {% endfor %}
            </ul>
            
            <p><strong>Remember:</strong> This screening is not a diagnosis. Please consult a mental health professional for proper evaluation.</p>
        </div>
        <div class="footer">
            <p>© 2025 MindSpace. Take care of your mind. 💜</p>
        </div>
    </div>
</body>
</html>
"""
}


# ========== Email Sending Functions ==========

class EmailService:
    """Email service for sending notifications"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """
        Send email using SMTP
        Returns True if successful, False otherwise
        """
        if not EmailConfig.is_configured():
            logger.warning("Email not configured - skipping email send")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{EmailConfig.FROM_NAME} <{EmailConfig.FROM_EMAIL}>"
            msg['To'] = to_email
            
            # Add plain text version (fallback)
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            
            # Add HTML version
            msg.attach(MIMEText(html_content, 'html'))
            
            # Connect and send
            with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
                server.starttls()
                server.login(EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD)
                server.sendmail(EmailConfig.FROM_EMAIL, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def render_template(template_name: str, **kwargs) -> str:
        """Render email template with variables"""
        if template_name not in TEMPLATES:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = Template(TEMPLATES[template_name])
        return template.render(**kwargs)
    
    @classmethod
    def send_welcome_email(cls, email: str, username: str, first_name: str = None) -> bool:
        """Send welcome email to new user"""
        html = cls.render_template(
            'welcome',
            username=username,
            first_name=first_name,
            app_url=os.getenv('APP_URL', 'http://localhost:5000')
        )
        return cls.send_email(email, "Welcome to MindSpace! 🧠", html)
    
    @classmethod
    def send_verification_email(cls, email: str, username: str, verification_token: str) -> bool:
        """Send email verification"""
        app_url = os.getenv('APP_URL', 'http://localhost:5000')
        verification_url = f"{app_url}/verify/{verification_token}"
        
        html = cls.render_template(
            'verification',
            username=username,
            verification_url=verification_url,
            verification_code=verification_token[:8].upper()
        )
        return cls.send_email(email, "Verify Your Email - MindSpace", html)
    
    @classmethod
    def send_password_reset_email(cls, email: str, username: str, reset_token: str) -> bool:
        """Send password reset email"""
        app_url = os.getenv('APP_URL', 'http://localhost:5000')
        reset_url = f"{app_url}/reset-password/{reset_token}"
        
        html = cls.render_template(
            'password_reset',
            username=username,
            reset_url=reset_url
        )
        return cls.send_email(email, "Reset Your Password - MindSpace", html)
    
    @classmethod
    def send_crisis_alert(cls, email: str, crisis_level: str, triggers: List[str], timestamp: str = None) -> bool:
        """Send crisis alert email"""
        html = cls.render_template(
            'crisis_alert',
            crisis_level=crisis_level,
            triggers=', '.join(triggers) if triggers else 'Not specified',
            timestamp=timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        return cls.send_email(email, "🆘 Crisis Alert - MindSpace", html)
    
    @classmethod
    def send_weekly_report(cls, email: str, username: str, first_name: str,
                          stats: Dict, trends: Dict, tips: List[str]) -> bool:
        """Send weekly wellness report"""
        from datetime import datetime, timedelta
        
        today = datetime.now()
        week_start = (today - timedelta(days=7)).strftime('%B %d')
        week_end = today.strftime('%B %d, %Y')
        
        html = cls.render_template(
            'weekly_report',
            username=username,
            first_name=first_name,
            week_start=week_start,
            week_end=week_end,
            conversations=stats.get('conversations', 0),
            assessments=stats.get('assessments', 0),
            engagement_score=stats.get('engagement_score', 0),
            phq9_trend=trends.get('phq9_trend'),
            gad7_trend=trends.get('gad7_trend'),
            latest_phq9=trends.get('latest_phq9'),
            latest_gad7=trends.get('latest_gad7'),
            tips=tips
        )
        return cls.send_email(email, "Your Weekly Wellness Report 📊", html)
    
    @classmethod
    def send_assessment_results(cls, email: str, assessment_name: str, score: int,
                               max_score: int, severity: str, interpretation: str,
                               recommendations: List[str]) -> bool:
        """Send assessment results email"""
        severity_class = {
            'Minimal': 'minimal',
            'Mild': 'mild',
            'Moderate': 'moderate',
            'Moderately Severe': 'severe',
            'Severe': 'severe'
        }.get(severity, 'moderate')
        
        html = cls.render_template(
            'assessment_complete',
            assessment_name=assessment_name,
            score=score,
            max_score=max_score,
            severity=severity,
            severity_class=severity_class,
            interpretation=interpretation,
            recommendations=recommendations
        )
        return cls.send_email(email, f"Assessment Results: {assessment_name}", html)


# ========== Notification Queue (for async processing) ==========

def queue_notification(notification_type: str, user_id: int, data: Dict) -> bool:
    """Queue a notification for later processing"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create notifications table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_type TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users_auth(id)
        )
    ''')
    
    import json
    cursor.execute('''
        INSERT INTO notification_queue (notification_type, user_id, data)
        VALUES (?, ?, ?)
    ''', (notification_type, user_id, json.dumps(data)))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Notification queued: {notification_type} for user {user_id}")
    return True


def process_notification_queue() -> int:
    """Process pending notifications, returns count processed"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, notification_type, user_id, data
        FROM notification_queue
        WHERE status = 'pending' AND attempts < 3
        ORDER BY created_at ASC
        LIMIT 10
    ''')
    
    notifications = cursor.fetchall()
    processed = 0
    
    import json
    for notif_id, notif_type, user_id, data_json in notifications:
        data = json.loads(data_json)
        success = False
        
        # Process based on type
        if notif_type == 'welcome':
            success = EmailService.send_welcome_email(
                data['email'], data['username'], data.get('first_name')
            )
        elif notif_type == 'verification':
            success = EmailService.send_verification_email(
                data['email'], data['username'], data['token']
            )
        elif notif_type == 'password_reset':
            success = EmailService.send_password_reset_email(
                data['email'], data['username'], data['token']
            )
        elif notif_type == 'crisis_alert':
            success = EmailService.send_crisis_alert(
                data['email'], data['crisis_level'], data.get('triggers', [])
            )
        
        # Update status
        if success:
            cursor.execute('''
                UPDATE notification_queue
                SET status = 'sent', processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (notif_id,))
            processed += 1
        else:
            cursor.execute('''
                UPDATE notification_queue
                SET attempts = attempts + 1
                WHERE id = ?
            ''', (notif_id,))
    
    conn.commit()
    conn.close()
    
    return processed


# ========== Wellness Tips ==========

WELLNESS_TIPS = [
    "Take a 5-minute breathing break - inhale for 4 counts, hold for 7, exhale for 8.",
    "Try to get outside for at least 15 minutes today. Sunlight can boost your mood.",
    "Reach out to a friend or family member. Connection is important for mental health.",
    "Practice gratitude by writing down three things you're thankful for.",
    "Set a small, achievable goal for today. Small wins build confidence.",
    "Limit social media time to reduce comparison and anxiety.",
    "Stay hydrated - dehydration can affect mood and energy levels.",
    "Try progressive muscle relaxation before bed for better sleep.",
    "Movement is medicine - even a short walk can improve your mood.",
    "Be kind to yourself. Self-compassion is as important as compassion for others.",
    "Consider starting a simple journaling practice to process your thoughts.",
    "Establish a consistent sleep schedule to support your mental health.",
]

def get_wellness_tips(count: int = 3) -> List[str]:
    """Get random wellness tips"""
    import random
    return random.sample(WELLNESS_TIPS, min(count, len(WELLNESS_TIPS)))
