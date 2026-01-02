"""
Conversation Memory Module for Mental Health Chatbot
Implements conversation memory for context-aware conversations
"""

from typing import Dict, List, Optional, Tuple
from database import get_chat_history


class SimpleConversationMemory:
    """Simple conversation memory implementation with enhanced context formatting"""
    
    def __init__(self, max_messages: int = 10):
        """Initialize conversation memory with max message limit"""
        self.max_messages = max_messages
        self.messages: List[Dict[str, str]] = []
    
    def add_exchange(self, user_message: str, bot_response: str):
        """Add a conversation exchange"""
        self.messages.append({
            'role': 'user',
            'content': user_message
        })
        self.messages.append({
            'role': 'assistant',
            'content': bot_response
        })
        
        # Keep only last N messages
        if len(self.messages) > self.max_messages * 2:
            self.messages = self.messages[-(self.max_messages * 2):]
    
    def get_context(self, include_full: bool = False) -> str:
        """Get conversation history as formatted string
        
        Args:
            include_full: If True, include full messages. If False, truncate.
        """
        if not self.messages:
            return "No previous conversation."
        
        context_parts = []
        for msg in self.messages:
            role = "User" if msg['role'] == 'user' else "You (MindSpace)"
            content = msg['content'] if include_full else msg['content'][:200]
            
            # Clean up the content
            content = content.replace('\n\n', ' ').replace('\n', ' ').strip()
            if len(msg['content']) > 200 and not include_full:
                content += "..."
            
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts[-8:])  # Last 4 exchanges (8 messages)
    
    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message"""
        for msg in reversed(self.messages):
            if msg['role'] == 'user':
                return msg['content']
        return None
    
    def get_last_bot_response(self) -> Optional[str]:
        """Get the last bot response"""
        for msg in reversed(self.messages):
            if msg['role'] == 'assistant':
                return msg['content']
        return None
    
    def get_summary(self) -> str:
        """Get a brief summary of the conversation themes"""
        if not self.messages:
            return "New conversation"
        
        user_messages = [m['content'] for m in self.messages if m['role'] == 'user']
        if len(user_messages) <= 2:
            return f"Brief conversation ({len(user_messages)} messages from user)"
        return f"Ongoing conversation ({len(user_messages)} messages from user)"
    
    def clear(self):
        """Clear all messages"""
        self.messages.clear()
    
    def load_from_database(self, history: List[Dict]):
        """Load history from database"""
        self.messages.clear()
        for entry in reversed(history):  # Oldest first
            self.messages.append({
                'role': 'user',
                'content': entry['message']
            })
            self.messages.append({
                'role': 'assistant',
                'content': entry['response']
            })


class ConversationMemoryManager:
    """Manages conversation memory for context-aware responses"""
    
    def __init__(self):
        """Initialize conversation memory manager"""
        self.user_memories: Dict[int, SimpleConversationMemory] = {}
        
    def get_or_create_memory(self, user_id: int, load_history: bool = True) -> SimpleConversationMemory:
        """Get existing memory or create new one for user"""
        if user_id not in self.user_memories:
            memory = SimpleConversationMemory(max_messages=5)
            
            # Load recent chat history from database
            if load_history:
                history = get_chat_history(user_id, limit=5)
                memory.load_from_database(history)
            
            self.user_memories[user_id] = memory
        
        return self.user_memories[user_id]
    
    def add_exchange(self, user_id: int, user_message: str, bot_response: str):
        """Add a conversation exchange to memory"""
        memory = self.get_or_create_memory(user_id, load_history=False)
        memory.add_exchange(user_message, bot_response)
    
    def get_conversation_context(self, user_id: int) -> str:
        """Get conversation history as formatted string"""
        memory = self.get_or_create_memory(user_id)
        return memory.get_context()
    
    def clear_memory(self, user_id: int):
        """Clear memory for a specific user"""
        if user_id in self.user_memories:
            self.user_memories[user_id].clear()
    
    def clear_all_memories(self):
        """Clear all user memories"""
        self.user_memories.clear()


class ConversationContextBuilder:
    """Builds rich conversation context for better responses"""
    
    @staticmethod
    def build_context(user_id: int, current_query: str) -> str:
        """Build conversation context including history and user data"""
        from database import get_user_assessments, get_crisis_events
        
        context_parts = []
        
        # Add recent chat history from memory manager
        memory = memory_manager.get_or_create_memory(user_id)
        chat_context = memory.get_context()
        if chat_context and chat_context != "No previous conversation.":
            context_parts.append("=== Recent Conversation ===")
            context_parts.append(chat_context)
        
        # Add recent assessment results for context
        assessments = get_user_assessments(user_id, limit=1)
        if assessments:
            context_parts.append("\n=== User's Recent Assessment ===")
            for assessment in assessments:
                context_parts.append(
                    f"Assessment: {assessment['type'].upper()} - {assessment['severity']} "
                    f"(score: {assessment['score']})"
                )
        
        # Add crisis history (if any) - important context
        crises = get_crisis_events(user_id, limit=1)
        if crises:
            context_parts.append("\n=== Important Note ===")
            context_parts.append("User has previously expressed distress. Respond with extra care.")
        
        return "\n".join(context_parts) if context_parts else "New user, first conversation."
    
    @staticmethod
    def get_conversation_history(user_id: int) -> str:
        """Get formatted conversation history for the prompt"""
        memory = memory_manager.get_or_create_memory(user_id)
        return memory.get_context()
    
    @staticmethod
    def get_personalized_prompt(user_id: int, base_query: str) -> str:
        """Generate personalized prompt with user context and conversation history"""
        from database import get_user_assessments
        
        # Get conversation history
        memory = memory_manager.get_or_create_memory(user_id)
        conversation_history = memory.get_context()
        
        # Get latest assessment to understand user's state
        assessments = get_user_assessments(user_id, limit=1)
        
        context_notes = []
        
        if assessments:
            latest = assessments[0]
            severity = latest['severity']
            assessment_type = latest['type'].upper()
            
            # Add assessment context
            if severity in ['Severe', 'Moderately Severe']:
                context_notes.append(f"[Note: User's recent {assessment_type} assessment indicates {severity.lower()} symptoms. Be especially gentle and supportive.]")
            elif severity in ['Moderate']:
                context_notes.append(f"[Note: User's recent {assessment_type} shows moderate symptoms. Offer supportive guidance.]")
        
        # Build the full query with context
        parts = []
        
        # Add conversation history if exists
        if conversation_history and conversation_history != "No previous conversation.":
            parts.append(f"[Conversation History:\n{conversation_history}]")
        
        # Add context notes
        if context_notes:
            parts.append("\n".join(context_notes))
        
        # Add the current query
        parts.append(f"\nUser's current message: {base_query}")
        
        return "\n\n".join(parts)


# Global memory manager instance
memory_manager = ConversationMemoryManager()


def get_memory_stats() -> Dict[str, int]:
    """Get memory usage statistics"""
    return {
        'active_conversations': len(memory_manager.user_memories),
        'total_memories': sum(
            len(mem.messages)
            for mem in memory_manager.user_memories.values()
        )
    }
