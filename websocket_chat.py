"""
WebSocket Chat Module for Mental Health Chatbot
Implements real-time bidirectional communication using Flask-SocketIO
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request, session
import json
from datetime import datetime
from typing import Dict, Optional
import threading

from database import save_chat_message, get_chat_history
from conversation_memory import memory_manager, ConversationContextBuilder
from sentiment_analysis import SentimentAnalyzer
from crisis_detection import CrisisDetector
from error_handler import logger


# Initialize SocketIO (will be attached to app in app.py)
socketio = None


def init_socketio(app, cors_allowed_origins="*"):
    """Initialize SocketIO with the Flask app"""
    global socketio
    socketio = SocketIO(
        app, 
        cors_allowed_origins=cors_allowed_origins,
        async_mode='threading',
        ping_timeout=60,
        ping_interval=25
    )
    register_handlers()
    return socketio


def register_handlers():
    """Register all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        user_id = session.get('user_id', 'anonymous')
        logger.info(f"WebSocket connected: user {user_id}")
        
        # Join user's personal room
        join_room(f"user_{user_id}")
        
        emit('connected', {
            'status': 'connected',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        user_id = session.get('user_id', 'anonymous')
        logger.info(f"WebSocket disconnected: user {user_id}")
        leave_room(f"user_{user_id}")
    
    @socketio.on('join_chat')
    def handle_join_chat(data):
        """Handle joining a specific chat session"""
        chat_session_id = data.get('chat_session_id')
        user_id = session.get('user_id')
        
        if chat_session_id:
            room = f"chat_{chat_session_id}"
            join_room(room)
            
            emit('joined_chat', {
                'chat_session_id': chat_session_id,
                'status': 'joined'
            })
            
            logger.info(f"User {user_id} joined chat room {room}")
    
    @socketio.on('leave_chat')
    def handle_leave_chat(data):
        """Handle leaving a chat session"""
        chat_session_id = data.get('chat_session_id')
        if chat_session_id:
            leave_room(f"chat_{chat_session_id}")
    
    @socketio.on('send_message')
    def handle_message(data):
        """Handle incoming chat message"""
        user_id = session.get('user_id')
        message = data.get('message', '').strip()
        chat_session_id = data.get('chat_session_id')
        
        if not message:
            emit('error', {'message': 'Empty message'})
            return
        
        # Emit typing indicator
        emit('typing_start', {'status': 'processing'})
        
        try:
            # Import here to avoid circular imports
            from app import qa_chain, sentiment_analyzer
            
            # Analyze sentiment
            sentiment_result = sentiment_analyzer.full_analysis(message)
            
            # Check for crisis
            crisis_detector = CrisisDetector()
            crisis_info = crisis_detector.detect_crisis(message)
            
            # Get conversation context
            conversation_history = ConversationContextBuilder.get_conversation_history(user_id)
            
            # Get AI response
            response = qa_chain.run(message, conversation_history=conversation_history)
            
            # Save to database
            save_chat_message(user_id, message, response, chat_session_id)
            
            # Update memory
            memory_manager.add_exchange(user_id, message, response)
            
            # Stop typing indicator
            emit('typing_stop', {})
            
            # Send response
            emit('message_response', {
                'response': response,
                'sentiment': sentiment_result,
                'crisis_detected': crisis_info['requires_intervention'],
                'crisis_level': crisis_info.get('level'),
                'timestamp': datetime.now().isoformat()
            })
            
            # If crisis detected, send alert
            if crisis_info['requires_intervention']:
                emit('crisis_alert', {
                    'level': crisis_info['level'],
                    'resources': crisis_detector.get_crisis_resources()
                })
            
        except Exception as e:
            logger.error(f"WebSocket message error: {e}")
            emit('typing_stop', {})
            emit('error', {'message': 'Failed to process message. Please try again.'})
    
    @socketio.on('typing')
    def handle_typing(data):
        """Handle typing indicator from client"""
        user_id = session.get('user_id')
        chat_session_id = data.get('chat_session_id')
        is_typing = data.get('is_typing', False)
        
        if chat_session_id:
            room = f"chat_{chat_session_id}"
            emit('user_typing', {
                'user_id': user_id,
                'is_typing': is_typing
            }, room=room, include_self=False)
    
    @socketio.on('request_history')
    def handle_history_request(data):
        """Handle request for chat history"""
        user_id = session.get('user_id')
        chat_session_id = data.get('chat_session_id')
        limit = data.get('limit', 50)
        
        history = get_chat_history(user_id, limit=limit, chat_session_id=chat_session_id)
        
        emit('chat_history', {
            'messages': history,
            'chat_session_id': chat_session_id
        })


class RealtimeNotifier:
    """Send real-time notifications to connected users"""
    
    @staticmethod
    def notify_user(user_id: int, event: str, data: dict):
        """Send notification to specific user"""
        if socketio:
            room = f"user_{user_id}"
            socketio.emit(event, data, room=room)
    
    @staticmethod
    def broadcast(event: str, data: dict):
        """Broadcast to all connected users"""
        if socketio:
            socketio.emit(event, data)
    
    @staticmethod
    def send_crisis_alert(user_id: int, crisis_level: str, resources: list):
        """Send crisis alert to user"""
        RealtimeNotifier.notify_user(user_id, 'crisis_alert', {
            'level': crisis_level,
            'resources': resources,
            'timestamp': datetime.now().isoformat()
        })
    
    @staticmethod
    def send_reminder(user_id: int, reminder_type: str, message: str):
        """Send reminder notification"""
        RealtimeNotifier.notify_user(user_id, 'reminder', {
            'type': reminder_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    @staticmethod
    def send_insight(user_id: int, insight: dict):
        """Send personalized insight"""
        RealtimeNotifier.notify_user(user_id, 'insight', {
            'insight': insight,
            'timestamp': datetime.now().isoformat()
        })


# Export notifier instance
notifier = RealtimeNotifier()
