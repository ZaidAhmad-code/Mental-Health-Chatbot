from flask import Flask, render_template, request, jsonify, session, Response, redirect, url_for
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
                     delete_chat_session, get_chat_session, get_chat_history, update_user_profile)
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

# Phase 3 Improvements - Advanced Features
from streaming import streaming_chain, stream_chat_response
from predictive_analytics import (get_risk_prediction, get_mood_forecast, 
                                   get_user_patterns, get_comprehensive_analysis)

# Phase 4 - Wellness Features
from wellness import (get_breathing_exercises, get_meditation_sessions, get_exercise_by_id,
                      save_wellness_session, get_wellness_stats, get_recommended_exercises,
                      init_wellness_tables)

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
    # Check if user is logged in
    session_token = session.get('session_token')
    if session_token:
        # Validate session
        user_data = validate_session(session_token)
        if user_data:
            return render_template('index.html')
    
    # Not logged in, redirect to login page
    return redirect(url_for('login_page'))


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


# ==================== DASHBOARD API ENDPOINTS ====================

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics for the current user"""
    user_id = get_user_id()
    
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total chats
        cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE user_id = ?", (user_id,))
        total_chats = cursor.fetchone()[0]
        
        # Get total messages
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
        total_messages = cursor.fetchone()[0]
        
        # Calculate streak (days with activity)
        cursor.execute("""
            SELECT COUNT(DISTINCT DATE(timestamp)) 
            FROM conversations 
            WHERE user_id = ? 
            AND DATE(timestamp) >= DATE('now', '-7 days')
        """, (user_id,))
        streak_days = cursor.fetchone()[0]
        
        # Get recent activity
        cursor.execute("""
            SELECT cs.title, c.timestamp
            FROM conversations c
            JOIN chat_sessions cs ON c.chat_session_id = cs.id
            WHERE c.user_id = ?
            ORDER BY c.timestamp DESC
            LIMIT 5
        """, (user_id,))
        
        recent_activity = []
        for row in cursor.fetchall():
            title, timestamp = row
            recent_activity.append({
                'title': title or 'Chat Session',
                'description': 'Message sent',
                'time': format_timestamp(timestamp)
            })
        
        conn.close()
        
        return jsonify({
            'total_chats': total_chats,
            'total_messages': total_messages // 2 if total_messages > 0 else 0,  # Divide by 2 (user + bot messages)
            'streak_days': streak_days,
            'recent_activity': recent_activity
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({
            'total_chats': 0,
            'total_messages': 0,
            'streak_days': 0,
            'recent_activity': []
        }), 200  # Return empty data instead of error


@app.route('/api/dashboard/mood', methods=['POST'])
def save_mood():
    """Save user mood to database"""
    user_id = get_user_id()
    data = request.get_json() or {}
    mood = data.get('mood')
    
    if not mood:
        return jsonify({'error': 'Mood is required'}), 400
    
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Save mood entry
        cursor.execute("""
            INSERT INTO mood_tracker (user_id, mood, timestamp)
            VALUES (?, ?, datetime('now'))
        """, (user_id, mood))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Mood saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving mood: {e}")
        return jsonify({'error': 'Failed to save mood'}), 500


@app.route('/api/chats/clear', methods=['DELETE'])
def clear_all_chats():
    """Clear all chat history for the current user"""
    user_id = get_user_id()
    
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete all conversations
        cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        
        # Delete all chat sessions
        cursor.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'All chats cleared successfully'})
        
    except Exception as e:
        logger.error(f"Error clearing chats: {e}")
        return jsonify({'error': 'Failed to clear chats'}), 500


def format_timestamp(timestamp_str):
    """Format timestamp to human-readable format"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes}m ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return dt.strftime("%b %d")
    except:
        return "Recently"


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


# ========== PHASE 3: Streaming Chat ==========

@app.route('/api/chat/stream', methods=['POST'])
@handle_errors("Streaming chat endpoint")
def stream_chat():
    """Stream chat response using Server-Sent Events with crisis detection"""
    import json
    
    user_id = get_user_id()
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    chat_session_id = data.get('chat_session_id')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Check for crisis FIRST before streaming
    crisis_detector = CrisisDetector()
    crisis_info = crisis_detector.detect_crisis(query)
    
    def generate():
        """Generator function for SSE streaming with crisis info at end"""
        try:
            # Get conversation context
            conversation_history = ConversationContextBuilder.get_conversation_history(user_id)
            context = f"Conversation history:\n{conversation_history}" if conversation_history else ""
            
            # If crisis detected, add crisis context
            if crisis_info['is_crisis']:
                context += "\n[IMPORTANT: User may be in crisis. Provide empathetic support and include crisis resources.]"
            
            # Get streaming response from LLM
            from streaming import StreamingLLMChain
            streaming_chain = StreamingLLMChain()
            
            full_response = ""
            for chunk in streaming_chain.stream_response(query, context):
                # Parse the SSE format to extract content
                if 'data: ' in chunk:
                    try:
                        data_str = chunk.replace('data: ', '').strip()
                        if data_str:
                            data_obj = json.loads(data_str)
                            if data_obj.get('type') == 'token':
                                full_response += data_obj.get('content', '')
                                yield chunk
                            elif data_obj.get('type') == 'done':
                                # Don't yield the done, we'll send our own with crisis info
                                pass
                            else:
                                yield chunk
                    except:
                        yield chunk
            
            # Save conversation to database
            try:
                if chat_session_id:
                    from database import get_db_connection
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Update sentiment analysis
                    sentiment = sentiment_analyzer.analyze(query) if hasattr(sentiment_analyzer, 'analyze') else None
                    
                    cursor.execute("""
                        INSERT INTO conversations (user_id, message, response, chat_session_id, sentiment_score, sentiment_label)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        user_id, query, full_response, chat_session_id,
                        sentiment.get('score') if sentiment else 0,
                        sentiment.get('label') if sentiment else 'neutral'
                    ))
                    
                    # Update session timestamp
                    cursor.execute("UPDATE chat_sessions SET updated_at = datetime('now') WHERE id = ?", (chat_session_id,))
                    conn.commit()
                    conn.close()
            except Exception as e:
                logger.error(f"Failed to save streaming conversation: {e}")
            
            # Send final done message with crisis info
            done_data = {
                'type': 'done',
                'crisis_detected': crisis_info['is_crisis'],
                'crisis_level': crisis_info.get('severity'),
                'crisis_resources': crisis_detector.get_crisis_resources() if crisis_info['is_crisis'] else None,
                'full_response': full_response
            }
            yield f"data: {json.dumps(done_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    logger.info(f"Streaming response for user {user_id}")
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


# ========== PHASE 3: Predictive Analytics ==========

@app.route('/api/predictive/risk', methods=['GET'])
@handle_errors("Risk prediction endpoint")
def risk_prediction():
    """Get mental health risk prediction for user"""
    user_id = get_user_id()
    days = request.args.get('days', default=14, type=int)
    
    prediction = get_risk_prediction(user_id, days)
    logger.info(f"Risk prediction generated for user {user_id}: {prediction.get('risk_level')}")
    
    return jsonify(prediction)


@app.route('/api/predictive/forecast', methods=['GET'])
@handle_errors("Mood forecast endpoint")
def mood_forecast():
    """Get mood forecast for user"""
    user_id = get_user_id()
    days_ahead = request.args.get('days', default=7, type=int)
    
    forecast = get_mood_forecast(user_id, days_ahead)
    return jsonify(forecast)


@app.route('/api/predictive/patterns', methods=['GET'])
@handle_errors("Pattern detection endpoint")
def pattern_detection():
    """Get detected patterns for user"""
    user_id = get_user_id()
    days = request.args.get('days', default=30, type=int)
    
    patterns = get_user_patterns(user_id, days)
    return jsonify(patterns)


@app.route('/api/predictive/comprehensive', methods=['GET'])
@handle_errors("Comprehensive analysis endpoint")
def comprehensive_analysis():
    """Get comprehensive predictive analysis"""
    user_id = get_user_id()
    
    analysis = get_comprehensive_analysis(user_id)
    logger.info(f"Comprehensive analysis generated for user {user_id}")
    
    return jsonify(analysis)


# ========== PHASE 4: Wellness - Meditation & Breathing ==========

@app.route('/api/wellness/breathing', methods=['GET'])
@handle_errors("Get breathing exercises")
def get_breathing():
    """Get all available breathing exercises"""
    exercises = get_breathing_exercises()
    return jsonify({'exercises': exercises})


@app.route('/api/wellness/meditation', methods=['GET'])
@handle_errors("Get meditation sessions")
def get_meditation():
    """Get all available meditation sessions"""
    sessions = get_meditation_sessions()
    return jsonify({'sessions': sessions})


@app.route('/api/wellness/exercise/<exercise_id>', methods=['GET'])
@handle_errors("Get exercise details")
def get_exercise(exercise_id):
    """Get details for a specific exercise"""
    exercise = get_exercise_by_id(exercise_id)
    if not exercise:
        return jsonify({'error': 'Exercise not found'}), 404
    return jsonify(exercise)


@app.route('/api/wellness/recommend', methods=['GET'])
@handle_errors("Get recommendations")
def get_recommendations():
    """Get personalized exercise recommendations"""
    user_id = get_user_id()
    mood = request.args.get('mood')
    time_available = request.args.get('time', type=int)
    
    recommendations = get_recommended_exercises(user_id, mood, time_available)
    return jsonify({'recommendations': recommendations})


@app.route('/api/wellness/session', methods=['POST'])
@handle_errors("Save wellness session")
def save_session():
    """Save a completed wellness session"""
    user_id = get_user_id()
    data = request.get_json() or {}
    
    session_type = data.get('session_type')  # 'breathing' or 'meditation'
    exercise_id = data.get('exercise_id')
    duration_seconds = data.get('duration_seconds', 0)
    completed = data.get('completed', True)
    mood_before = data.get('mood_before')
    mood_after = data.get('mood_after')
    notes = data.get('notes')
    
    if not session_type or not exercise_id:
        return jsonify({'error': 'session_type and exercise_id are required'}), 400
    
    result = save_wellness_session(
        user_id, session_type, exercise_id, duration_seconds,
        completed, mood_before, mood_after, notes
    )
    
    logger.info(f"Wellness session saved for user {user_id}: {exercise_id}")
    return jsonify(result)


@app.route('/api/wellness/stats', methods=['GET'])
@handle_errors("Get wellness stats")
def wellness_stats():
    """Get user's wellness statistics and streaks"""
    user_id = get_user_id()
    stats = get_wellness_stats(user_id)
    return jsonify(stats)


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
                    'bio': user.get('bio', ''),
                    'avatar_config': user.get('avatar_config', ''),
                    'created_at': user['created_at'],
                    'last_login': user['last_login']
                }
            })
        return jsonify({'error': 'User not found'}), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        # Extract fields to update
        update_fields = {}
        if 'display_name' in data:
            update_fields['display_name'] = data['display_name']
        if 'email' in data:
            update_fields['email'] = data['email']
        if 'bio' in data:
            update_fields['bio'] = data['bio']
        if 'avatar_config' in data:
            update_fields['avatar_config'] = data['avatar_config']
        
        # Update profile
        if update_user_profile(user_id, **update_fields):
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        else:
            return jsonify({'error': 'No valid fields to update'}), 400


@app.route('/api/auth/avatar', methods=['POST'])
@handle_errors("Avatar upload endpoint")
def upload_avatar():
    """Upload user avatar"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['avatar']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    filename = file.filename.lower()
    if not any(filename.endswith('.' + ext) for ext in allowed_extensions):
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
    
    try:
        # Create avatars directory if it doesn't exist
        avatars_dir = os.path.join('static', 'avatars')
        os.makedirs(avatars_dir, exist_ok=True)
        
        # Save with user_id as filename
        file_ext = filename.rsplit('.', 1)[1]
        avatar_filename = f"{user_id}.{file_ext}"
        avatar_path = os.path.join(avatars_dir, avatar_filename)
        
        file.save(avatar_path)
        
        logger.info(f"Avatar uploaded for user {user_id}: {avatar_filename}")
        
        return jsonify({
            'success': True,
            'message': 'Avatar uploaded successfully',
            'avatar_url': f'/static/avatars/{avatar_filename}'
        })
        
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        return jsonify({'error': 'Failed to upload avatar'}), 500


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