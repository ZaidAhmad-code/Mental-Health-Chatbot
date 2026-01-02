"""
Streaming Response Module for Mental Health Chatbot
Implements Server-Sent Events (SSE) for real-time response streaming
"""

import json
import time
from typing import Generator, Optional
from flask import Response, stream_with_context
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import BaseCallbackHandler
import os
from queue import Queue
from threading import Thread

from dotenv import load_dotenv
load_dotenv()


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LLM responses"""
    
    def __init__(self, queue: Queue):
        self.queue = queue
        self.is_done = False
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when a new token is generated"""
        self.queue.put({"type": "token", "content": token})
    
    def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM finishes generating"""
        self.queue.put({"type": "end", "content": ""})
        self.is_done = True
    
    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called when LLM errors"""
        self.queue.put({"type": "error", "content": str(error)})
        self.is_done = True


class StreamingLLMChain:
    """Streaming LLM chain with real-time token output"""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    def create_streaming_llm(self, callback_handler: StreamingCallbackHandler):
        """Create a streaming-enabled LLM"""
        return ChatGroq(
            temperature=0.7,
            groq_api_key=self.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            max_tokens=500,
            streaming=True,
            callbacks=[callback_handler]
        )
    
    def stream_response(self, query: str, context: str = "") -> Generator[str, None, None]:
        """Stream response tokens as they're generated"""
        queue = Queue()
        callback_handler = StreamingCallbackHandler(queue)
        
        # Create streaming LLM
        llm = self.create_streaming_llm(callback_handler)
        
        # Build the prompt
        prompt = self._build_prompt(query, context)
        
        # Start LLM in a separate thread
        def run_llm():
            try:
                llm.invoke(prompt)
            except Exception as e:
                queue.put({"type": "error", "content": str(e)})
        
        thread = Thread(target=run_llm)
        thread.start()
        
        # Yield tokens as they come in
        full_response = ""
        while True:
            try:
                item = queue.get(timeout=30)  # 30 second timeout
                
                if item["type"] == "token":
                    full_response += item["content"]
                    yield f"data: {json.dumps({'type': 'token', 'content': item['content']})}\n\n"
                elif item["type"] == "end":
                    yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"
                    break
                elif item["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': item['content']})}\n\n"
                    break
            except:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Timeout'})}\n\n"
                break
        
        thread.join(timeout=1)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the mental health prompt"""
        base_prompt = """You're a knowledgeable mental health companion. Give REAL, SPECIFIC, USEFUL advice - not generic fluff.

Be direct and helpful, like a smart friend who knows their stuff. Give specific, actionable tips.

{context}

User said: {query}

Give helpful, specific advice (be knowledgeable and direct, not preachy):"""
        
        return base_prompt.format(
            context=f"Context: {context}" if context else "",
            query=query
        )


def create_sse_response(generator: Generator) -> Response:
    """Create a Server-Sent Events response"""
    return Response(
        stream_with_context(generator),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )


# Singleton instance
streaming_chain = StreamingLLMChain()


def stream_chat_response(query: str, context: str = "") -> Response:
    """Main function to stream chat responses"""
    return create_sse_response(streaming_chain.stream_response(query, context))
