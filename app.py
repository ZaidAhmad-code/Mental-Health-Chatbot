from flask import Flask, render_template, request, jsonify, session
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains import RetrievalQA
import os
import json
from datetime import datetime

# Import your chatbot functions
from chatbot import initialize_llm, create_vector_db, setup_qa_chain, DualLLMChain
from assessments import PHQ9Assessment, GAD7Assessment, get_assessment_by_type, validate_answers
from database import (init_db, save_assessment_result, get_user_assessments, 
                     create_guest_user, save_chat_message, save_crisis_event,
                     get_user_by_email, get_user_by_username, get_user_by_id,
                     save_sentiment, get_sentiment_history,
                     get_mood_trend, get_user_preferences, save_user_preferences,
                     create_chat_session, get_user_chat_sessions, update_chat_session_title,
                     delete_chat_session, get_chat_session, get_chat_history)
from crisis_detection import CrisisDetector, format_crisis_response

# Phase 1 Improvements
from cache_manager import cache, get_cached_llm_response, cache_llm_response
from analytics import (get_user_stats, get_assessment_trends, get_crisis_patterns, 
                      get_engagement_metrics, get_mental_health_trajectory, get_system_analytics)
from conversation_memory import (memory_manager, ConversationContextBuilder, get_memory_stats)
from error_handler import (logger, ErrorHandler, handle_errors, log_performance, 
                           health_monitor, validate_input)

# Phase 2 Improvements
from auth import (init_auth_tables, create_user as auth_create_user, authenticate_user,
                  authenticate_user_by_username, create_session, validate_session, 
                  invalidate_session, login_required,
                  change_password as auth_change_password, generate_reset_token,
                  reset_password_with_token, delete_user_account, get_user_by_id as auth_get_user)
from notifications import EmailService
from sentiment_analysis import SentimentAnalyzer
from api_docs import api_docs_bp

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this!

# Register API documentation blueprint
app.register_blueprint(api_docs_bp, url_prefix='/api/docs')

# Initialize Phase 2 services
init_auth_tables()  # Initialize auth tables
email_service = EmailService()
sentiment_analyzer = SentimentAnalyzer()

# Initialize database
init_db()

# Setup logging
logger.info("=" * 60)
logger.info("Initializing Mental Health Chatbot Web App...")
logger.info("=" * 60)

# Initialize the dual LLM system and vector database
print("=" * 60)
print("Initializing Mental Health Chatbot Web App...")
print("=" * 60)

groq_llm, gemini_llm = initialize_llm()

db_path = 'chroma_db'
if not os.path.exists(db_path):
    vector_db = create_vector_db()
else:
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)

# Create QA chains for both LLMs
primary_chain = setup_qa_chain(vector_db, groq_llm)
secondary_chain = setup_qa_chain(vector_db, gemini_llm) if gemini_llm else None

# Create dual LLM chain with automatic fallback
qa_chain = DualLLMChain(primary_chain, secondary_chain)

print("=" * 60)
print("✓ Dual LLM Mental Health Chatbot Ready!")
print("=" * 60)


def get_user_id():
    """Get or create user ID for session"""
    if 'user_id' not in session:
        session['user_id'] = create_guest_user()
    return session['user_id']


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login')
def login_page():
    return render_template('auth.html')


@app.route('/register')
def register_page():
    return render_template('auth.html')


@app.route('/assessments')
def assessments():
    return render_template('assessments.html')


@app.route('/ask', methods=['POST'])
@handle_errors("Chat endpoint")
@log_performance("Chat query")
def ask():
    start_time = datetime.now()
    user_query = request.form['query']
    chat_session_id = request.form.get('chat_session_id')  # Get current chat session
    user_id = get_user_id()
    
    # Convert chat_session_id to int if provided
    if chat_session_id:
        try:
            chat_session_id = int(chat_session_id)
        except ValueError:
            chat_session_id = None
    
    # Log request
    ErrorHandler.log_request('/ask', user_id, {'query_length': len(user_query)})
    
    # Analyze sentiment (Phase 2)
    sentiment_result = sentiment_analyzer.full_analysis(user_query)
    
    # Save sentiment to database - using correct keys from sentiment result
    try:
        save_sentiment(
            user_id,
            user_query[:500],  # Limit message length
            sentiment_result['sentiment']['score'],
            sentiment_result['sentiment']['sentiment'],  # 'sentiment' not 'label'
            sentiment_result['emotions'],
            sentiment_result['sentiment']['score']  # Use sentiment score as mood
        )
    except Exception as e:
        logger.warning(f"Failed to save sentiment: {e}")
    
    # Check cache first
    cached_response = get_cached_llm_response(user_query.lower().strip())
    if cached_response and not any(word in user_query.lower() for word in ['i', 'my', 'me']):
        logger.info(f"✓ Cache hit for user {user_id}")
        duration = (datetime.now() - start_time).total_seconds()
        ErrorHandler.log_response('/ask', user_id, 'success_cached', duration)
        
        return jsonify({
            'response': cached_response,
            'crisis_detected': False,
            'cached': True,
            'sentiment': sentiment_result
        })
    
    # Detect crisis in user message
    crisis_detector = CrisisDetector()
    crisis_info = crisis_detector.detect_crisis(user_query)
    
    # If crisis detected, log it and prepare crisis response
    if crisis_info['requires_intervention']:
        # Save crisis event to database
        save_crisis_event(
            user_id,
            user_query,
            crisis_info['level'],
            crisis_info['severity'],
            crisis_info['crisis_triggers'] + crisis_info['warning_triggers']
        )
        
        # Get crisis response
        crisis_response = format_crisis_response(crisis_info)
        
        # Get conversation history for context
        conversation_history = ConversationContextBuilder.get_conversation_history(user_id)
        logger.debug(f"Conversation history for user {user_id}: {conversation_history[:200] if conversation_history else 'None'}...")
        
        # Get AI response with conversation context
        ai_response = qa_chain.run(user_query, conversation_history=conversation_history)
        combined_response = crisis_response + "\n\n---\n\n" + ai_response
        
        # Save to database and memory (with session ID)
        save_chat_message(user_id, user_query, combined_response, chat_session_id)
        memory_manager.add_exchange(user_id, user_query, combined_response)
        
        duration = (datetime.now() - start_time).total_seconds()
        ErrorHandler.log_response('/ask', user_id, 'crisis_detected', duration)
        
        return jsonify({
            'response': combined_response,
            'crisis_detected': True,
            'crisis_level': crisis_info['level'],
            'crisis_resources': crisis_detector.get_crisis_resources(),
            'sentiment': sentiment_result,
            'chat_session_id': chat_session_id
        })
    
    # Get conversation history for context-aware responses
    conversation_history = ConversationContextBuilder.get_conversation_history(user_id)
    
    # Build personalized prompt with context
    personalized_query = ConversationContextBuilder.get_personalized_prompt(user_id, user_query)
    
    # Normal conversation with context awareness - pass conversation history
    response = qa_chain.run(personalized_query, conversation_history=conversation_history)
    
    # Save to database and memory (with session ID)
    save_chat_message(user_id, user_query, response, chat_session_id)
    memory_manager.add_exchange(user_id, user_query, response)
    
    # Cache response for non-personal queries (less aggressive caching for mental health)
    if not any(word in user_query.lower() for word in ['i', 'my', 'me', 'myself', 'feel', 'feeling', 'am']):
        cache_llm_response(user_query.lower().strip(), response, ttl=1800)
        logger.info(f"✓ Response cached for query: {user_query[:50]}...")
    
    duration = (datetime.now() - start_time).total_seconds()
    ErrorHandler.log_response('/ask', user_id, 'success', duration)
    
    return jsonify({
        'response': response,
        'crisis_detected': False,
        'cached': False,
        'sentiment': sentiment_result,
        'chat_session_id': chat_session_id
    })


# ==================== CHAT SESSION API ENDPOINTS ====================

@app.route('/api/chats', methods=['GET', 'POST'])
def chat_sessions():
    """Get all chat sessions or create a new one"""
    user_id = get_user_id()
    
    if request.method == 'GET':
        sessions = get_user_chat_sessions(user_id)
        return jsonify({'sessions': sessions})
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        title = data.get('title', 'New Chat')
        
        session_id = create_chat_session(user_id, title)
        
        # Clear memory for new session
        memory_manager.clear_memory(user_id)
        
        return jsonify({
            'id': session_id,
            'title': title,
            'message': 'Chat session created'
        })


@app.route('/api/chats/<int:session_id>', methods=['GET', 'PUT', 'DELETE'])
def chat_session_detail(session_id):
    """Get, update or delete a specific chat session"""
    user_id = get_user_id()
    
    if request.method == 'GET':
        # Get session details and messages
        session = get_chat_session(session_id, user_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        messages = get_chat_history(user_id, chat_session_id=session_id)
        
        return jsonify({
            'session': session,
            'messages': messages
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        title = data.get('title')
        
        if title:
            update_chat_session_title(session_id, title)
            return jsonify({'message': 'Session updated', 'title': title})
        
        return jsonify({'error': 'Title required'}), 400
    
    elif request.method == 'DELETE':
        delete_chat_session(session_id, user_id)
        return jsonify({'message': 'Session deleted'})


@app.route('/api/chats/<int:session_id>/load', methods=['POST'])
def load_chat_session(session_id):
    """Load a chat session into memory for continuation"""
    user_id = get_user_id()
    
    session = get_chat_session(session_id, user_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Load messages into memory
    messages = get_chat_history(user_id, chat_session_id=session_id)
    
    # Clear current memory and reload from this session's messages
    memory_manager.clear_memory(user_id)
    
    # Get or create memory and load messages
    memory = memory_manager.get_or_create_memory(user_id, load_history=False)
    
    # Add messages to memory in order
    for msg in messages:
        memory.add_exchange(msg['message'], msg['response'])
    
    # Store current session in flask session
    session_data = session.copy()
    
    return jsonify({
        'message': 'Session loaded',
        'session': session_data,
        'messages': messages
    })


@app.route('/api/assessment/phq9', methods=['GET', 'POST'])
def phq9_assessment():
    """PHQ-9 Depression Assessment"""
    if request.method == 'GET':
        # Return questions
        return jsonify({
            'title': 'PHQ-9: Depression Screening',
            'description': 'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
            'questions': PHQ9Assessment.QUESTIONS,
            'options': PHQ9Assessment.OPTIONS
        })
    
    elif request.method == 'POST':
        # Process answers
        data = request.get_json()
        answers = data.get('answers', [])
        
        # Validate answers
        valid, message = validate_answers(answers, 'phq9')
        if not valid:
            return jsonify({'error': message}), 400
        
        # Calculate score
        score = PHQ9Assessment.calculate_score(answers)
        interpretation = PHQ9Assessment.interpret_score(score)
        
        # Check for crisis level based on score
        crisis_detector = CrisisDetector()
        crisis_check = crisis_detector.check_assessment_crisis('phq9', score)
        
        # Save to database
        user_id = get_user_id()
        result_id = save_assessment_result(
            user_id, 
            'phq9', 
            score, 
            interpretation['severity'], 
            answers
        )
        
        # If crisis level detected, log it
        if crisis_check['requires_intervention']:
            save_crisis_event(
                user_id,
                f"PHQ-9 Assessment Score: {score}",
                crisis_check['level'],
                score,
                ['high_phq9_score']
            )
        
        return jsonify({
            'id': result_id,
            'score': score,
            'max_score': 27,
            'interpretation': interpretation,
            'crisis_alert': crisis_check if crisis_check['requires_intervention'] else None
        })


@app.route('/api/assessment/gad7', methods=['GET', 'POST'])
def gad7_assessment():
    """GAD-7 Anxiety Assessment"""
    if request.method == 'GET':
        # Return questions
        return jsonify({
            'title': 'GAD-7: Anxiety Screening',
            'description': 'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
            'questions': GAD7Assessment.QUESTIONS,
            'options': GAD7Assessment.OPTIONS
        })
    
    elif request.method == 'POST':
        # Process answers
        data = request.get_json()
        answers = data.get('answers', [])
        
        # Validate answers
        valid, message = validate_answers(answers, 'gad7')
        if not valid:
            return jsonify({'error': message}), 400
        
        # Calculate score
        score = GAD7Assessment.calculate_score(answers)
        interpretation = GAD7Assessment.interpret_score(score)
        
        # Check for crisis level based on score
        crisis_detector = CrisisDetector()
        crisis_check = crisis_detector.check_assessment_crisis('gad7', score)
        
        # Save to database
        user_id = get_user_id()
        result_id = save_assessment_result(
            user_id, 
            'gad7', 
            score, 
            interpretation['severity'], 
            answers
        )
        
        # If crisis level detected, log it
        if crisis_check['requires_intervention']:
            save_crisis_event(
                user_id,
                f"GAD-7 Assessment Score: {score}",
                crisis_check['level'],
                score,
                ['high_gad7_score']
            )
        
        return jsonify({
            'id': result_id,
            'score': score,
            'max_score': 21,
            'interpretation': interpretation,
            'crisis_alert': crisis_check if crisis_check['requires_intervention'] else None
        })


@app.route('/api/assessment/history', methods=['GET'])
def assessment_history():
    """Get user's assessment history"""
    user_id = get_user_id()
    history = get_user_assessments(user_id, limit=20)
    return jsonify({'history': history})


# ========== PHASE 1: Analytics Endpoints ==========

@app.route('/api/analytics/user-stats', methods=['GET'])
@handle_errors("User stats endpoint")
def user_stats():
    """Get comprehensive user statistics"""
    user_id = get_user_id()
    stats = get_user_stats(user_id)
    logger.info(f"User stats requested by user {user_id}")
    return jsonify(stats)


@app.route('/api/analytics/trends/<assessment_type>', methods=['GET'])
@handle_errors("Trends endpoint")
def assessment_trends_endpoint(assessment_type):
    """Get assessment trends over time"""
    user_id = get_user_id()
    days = request.args.get('days', default=30, type=int)
    
    if assessment_type not in ['phq9', 'gad7']:
        return jsonify({'error': 'Invalid assessment type'}), 400
    
    trends = get_assessment_trends(user_id, assessment_type, days)
    return jsonify(trends)


@app.route('/api/analytics/crisis-patterns', methods=['GET'])
@handle_errors("Crisis patterns endpoint")
def crisis_patterns_endpoint():
    """Get crisis event patterns"""
    user_id = get_user_id()
    days = request.args.get('days', default=30, type=int)
    patterns = get_crisis_patterns(user_id, days)
    return jsonify(patterns)


@app.route('/api/analytics/engagement', methods=['GET'])
@handle_errors("Engagement endpoint")
def engagement_endpoint():
    """Get user engagement metrics"""
    user_id = get_user_id()
    metrics = get_engagement_metrics(user_id)
    return jsonify(metrics)


@app.route('/api/analytics/trajectory', methods=['GET'])
@handle_errors("Trajectory endpoint")
def trajectory_endpoint():
    """Get mental health trajectory"""
    user_id = get_user_id()
    trajectory = get_mental_health_trajectory(user_id)
    return jsonify(trajectory)


@app.route('/api/analytics/system', methods=['GET'])
@handle_errors("System analytics endpoint")
def system_analytics_endpoint():
    """Get system-wide analytics (admin view)"""
    # In production, add authentication check here
    analytics = get_system_analytics()
    return jsonify(analytics)


@app.route('/api/analytics/sentiment-history', methods=['GET'])
@handle_errors("Sentiment history analytics endpoint")
def analytics_sentiment_history():
    """Get sentiment history for analytics dashboard"""
    user_id = get_user_id()
    limit = request.args.get('limit', default=10, type=int)
    
    history = get_sentiment_history(user_id, limit)
    return jsonify({'history': history})


@app.route('/api/analytics/mood-trend', methods=['GET'])
@handle_errors("Mood trend analytics endpoint")
def analytics_mood_trend():
    """Get mood trend for analytics dashboard"""
    user_id = get_user_id()
    days = request.args.get('days', default=7, type=int)
    
    trend_data = get_mood_trend(user_id, days)
    # Format trend as a simple string for the dashboard
    trend_label = 'Stable'
    if trend_data:
        avg_score = sum(t.get('avg_score', 0) for t in trend_data) / len(trend_data) if trend_data else 0
        if avg_score > 0.2:
            trend_label = 'Improving'
        elif avg_score < -0.2:
            trend_label = 'Declining'
    
    return jsonify({'trend': trend_label, 'data': trend_data})


# ========== PHASE 1: Memory & Cache Management ==========

@app.route('/api/memory/clear', methods=['POST'])
@handle_errors("Clear memory endpoint")
def clear_memory():
    """Clear conversation memory for current user"""
    user_id = get_user_id()
    memory_manager.clear_memory(user_id)
    logger.info(f"Memory cleared for user {user_id}")
    return jsonify({'status': 'success', 'message': 'Conversation memory cleared'})


@app.route('/api/memory/stats', methods=['GET'])
def memory_stats_endpoint():
    """Get memory statistics"""
    stats = get_memory_stats()
    return jsonify(stats)


@app.route('/api/cache/stats', methods=['GET'])
def cache_stats_endpoint():
    """Get cache statistics"""
    stats = cache.get_stats()
    return jsonify(stats)


@app.route('/api/cache/clear', methods=['POST'])
@handle_errors("Clear cache endpoint")
def clear_cache():
    """Clear all cache (admin only)"""
    # In production, add authentication check here
    cache.clear()
    logger.info("Cache cleared by admin")
    return jsonify({'status': 'success', 'message': 'Cache cleared'})


# ========== PHASE 1: Health & Monitoring ==========

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health = health_monitor.get_health_status()
    
    # Add additional health checks
    health['database'] = 'connected' if os.path.exists('mental_health.db') else 'disconnected'
    health['llm_primary'] = 'available' if groq_llm else 'unavailable'
    health['llm_secondary'] = 'available' if gemini_llm else 'unavailable'
    health['cache_stats'] = cache.get_stats()
    health['memory_stats'] = get_memory_stats()
    
    return jsonify(health)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {str(error)}")
    health_monitor.record_error()
    return jsonify({'error': 'Internal server error'}), 500


# ========== PHASE 2: Authentication Routes ==========

@app.route('/api/auth/register', methods=['POST'])
@handle_errors("Register endpoint")
def register():
    """Register a new user"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    
    # Basic validation
    if not username or len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if not email or '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400
    if not password or len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    result = auth_create_user(username, email, password, first_name, last_name)
    
    if result['success']:
        logger.info(f"New user registered: {username}")
        return jsonify(result)
    else:
        return jsonify(result), 400


@app.route('/api/auth/login', methods=['POST'])
@handle_errors("Login endpoint")
def login():
    """Login user"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    result = authenticate_user_by_username(username, password)
    
    if result['success']:
        # Create session
        session_token = create_session(
            result['user']['id'],
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        # Store user info in Flask session
        session['user_id'] = result['user']['id']
        session['session_token'] = session_token
        session['username'] = result['user']['username']
        
        logger.info(f"User logged in: {username}")
        return jsonify({
            'success': True,
            'user': result['user'],
            'session_token': session_token,
            'message': 'Login successful'
        })
    else:
        logger.warning(f"Failed login attempt for: {username}")
        return jsonify(result), 401


@app.route('/api/auth/logout', methods=['POST'])
@handle_errors("Logout endpoint")
def logout():
    """Logout user"""
    session_token = session.get('session_token')
    user_id = session.get('user_id')
    
    if session_token:
        invalidate_session(session_token)
    
    session.clear()
    
    if user_id:
        logger.info(f"User logged out: {user_id}")
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    
    return jsonify({'success': False, 'message': 'Not logged in'}), 400


@app.route('/api/auth/profile', methods=['GET', 'PUT'])
@handle_errors("Profile endpoint")
def profile():
    """Get or update user profile"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'GET':
        user = get_user_by_id(user_id)
        if user:
            return jsonify({
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'display_name': user.get('display_name', user['username']),
                    'created_at': user['created_at'],
                    'last_login': user['last_login']
                }
            })
        return jsonify({'error': 'User not found'}), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        # Update profile logic here
        return jsonify({'success': True, 'message': 'Profile updated'})


@app.route('/api/auth/preferences', methods=['GET', 'PUT'])
@handle_errors("Auth preferences endpoint")
def auth_preferences():
    """Get or update user preferences (auth version)"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'GET':
        prefs = get_user_preferences(user_id)
        return jsonify({'preferences': prefs or {
            'email_notifications': False,
            'crisis_alerts': True,
            'save_history': True,
            'anonymous_mode': False
        }})
    
    elif request.method == 'PUT':
        data = request.get_json()
        save_user_preferences(user_id, data)
        return jsonify({'success': True, 'message': 'Preferences updated'})


@app.route('/api/auth/change-password', methods=['POST'])
@handle_errors("Change password endpoint")
def change_password_route():
    """Change user password"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password required'}), 400
    
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    
    result = auth_change_password(user_id, current_password, new_password)
    
    if result['success']:
        logger.info(f"Password changed for user: {user_id}")
        return jsonify(result)
    else:
        return jsonify(result), 400


@app.route('/api/auth/reset-password', methods=['POST'])
@handle_errors("Reset password endpoint")
def reset_password_request():
    """Request password reset"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    result = generate_reset_token(email)
    
    # Always return success to prevent email enumeration
    return jsonify({
        'success': True,
        'message': 'If an account exists with this email, a reset link will be sent'
    })


@app.route('/api/auth/delete-account', methods=['DELETE'])
@handle_errors("Delete account endpoint")
def delete_account():
    """Delete user account"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': 'Password required to confirm deletion'}), 400
    
    result = delete_user_account(user_id, password)
    
    if result['success']:
        session.clear()
        logger.info(f"Account deleted: {user_id}")
        return jsonify(result)
    else:
        return jsonify(result), 400


# ========== PHASE 2: Sentiment Analysis Routes ==========

@app.route('/api/sentiment/analyze', methods=['POST'])
@handle_errors("Sentiment analysis endpoint")
def analyze_sentiment_endpoint():
    """Analyze sentiment of text"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'Text required'}), 400
    
    result = sentiment_analyzer.full_analysis(text)
    return jsonify(result)


@app.route('/api/sentiment/history', methods=['GET'])
@handle_errors("Sentiment history endpoint")
def sentiment_history():
    """Get sentiment analysis history"""
    user_id = get_user_id()
    limit = request.args.get('limit', default=50, type=int)
    
    history = get_sentiment_history(user_id, limit)
    return jsonify({'history': history})


@app.route('/api/sentiment/mood-trend', methods=['GET'])
@handle_errors("Mood trend endpoint")
def mood_trend():
    """Get mood trend over time"""
    user_id = get_user_id()
    days = request.args.get('days', default=7, type=int)
    
    trend = get_mood_trend(user_id, days)
    return jsonify({'trend': trend})


# ========== PHASE 2: User Preferences Routes ==========

@app.route('/api/preferences', methods=['GET', 'PUT'])
@handle_errors("Preferences endpoint")
def user_preferences():
    """Get or update user preferences"""
    user_id = get_user_id()
    
    if request.method == 'GET':
        prefs = get_user_preferences(user_id)
        if prefs:
            return jsonify(prefs)
        return jsonify({
            'email_notifications': True,
            'weekly_reports': True,
            'crisis_alerts': True,
            'theme': 'light',
            'language': 'en'
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        save_user_preferences(user_id, data)
        return jsonify({'success': True, 'message': 'Preferences updated'})


# ========== PHASE 2: Notification Routes ==========

@app.route('/api/notifications/test', methods=['POST'])
@handle_errors("Test notification endpoint")
def test_notification():
    """Send a test notification (development only)"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = get_user_by_id(user_id)
    if not user or not user.get('email'):
        return jsonify({'error': 'User email not found'}), 400
    
    # This is for testing - in production, configure SMTP settings
    return jsonify({
        'success': True,
        'message': 'Notification system ready (configure SMTP for actual emails)',
        'email': user['email']
    })


if __name__ == '__main__':
    logger.info("Starting Flask application on http://127.0.0.1:5000")
    logger.info("Phase 2 features enabled: Authentication, Sentiment Analysis, Notifications, API Docs")
    logger.info("API Documentation available at: http://127.0.0.1:5000/api/docs/")
    app.run(debug=True)