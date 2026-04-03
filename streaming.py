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

from prompts import build_prompt


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
    """Streaming LLM chain — Groq primary, Gemini 2.5 Flash fallback"""

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

    def create_groq_llm(self, callback_handler: StreamingCallbackHandler, max_tokens: int = 300):
        """Create a streaming-enabled Groq LLM"""
        return ChatGroq(
            temperature=0.7,
            groq_api_key=self.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            max_tokens=max_tokens,
            streaming=True,
            callbacks=[callback_handler]
        )

    def create_gemini_llm(self, callback_handler: StreamingCallbackHandler, max_tokens: int = 300):
        """Create a streaming-enabled Gemini 2.5 Flash LLM"""
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.gemini_api_key,
            temperature=0.7,
            max_output_tokens=max_tokens,
            streaming=True,
            callbacks=[callback_handler]
        )

    def _stream_with_llm(self, llm_factory, prompt: str) -> Generator[str, None, None]:
        """Run a given LLM factory and stream its tokens via a queue."""
        queue = Queue()
        callback_handler = StreamingCallbackHandler(queue)
        llm = llm_factory(callback_handler)

        def run_llm():
            try:
                llm.invoke(prompt)
            except Exception as e:
                queue.put({"type": "error", "content": str(e)})

        thread = Thread(target=run_llm)
        thread.start()

        full_response = ""
        while True:
            try:
                item = queue.get(timeout=30)
                if item["type"] == "token":
                    full_response += item["content"]
                    yield f"data: {json.dumps({'type': 'token', 'content': item['content']})}\n\n"
                elif item["type"] == "end":
                    yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"
                    break
                elif item["type"] == "error":
                    raise RuntimeError(item["content"])
            except RuntimeError:
                raise
            except Exception:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Timeout'})}\n\n"
                break

        thread.join(timeout=1)

    def stream_response(self, query: str, context: str = "") -> Generator[str, None, None]:
        """Stream response — try Groq first, fall back to Gemini on any error."""
        prompt, max_tokens = build_prompt(query, context)

        groq_factory  = lambda cb: self.create_groq_llm(cb, max_tokens)
        gemini_factory = lambda cb: self.create_gemini_llm(cb, max_tokens)

        # ── Try Groq (primary) ────────────────────────────────────────────────
        groq_error = None
        try:
            for chunk in self._stream_with_llm(groq_factory, prompt):
                if '"type": "error"' in chunk:
                    groq_error = chunk
                    break
                yield chunk
            if not groq_error:
                return
        except Exception as e:
            groq_error = str(e)

        # ── Groq failed — fall back to Gemini ────────────────────────────────
        print(f"⚠ Groq streaming failed ({groq_error}), falling back to Gemini…")

        if not self.gemini_api_key:
            yield f"data: {json.dumps({'type': 'error', 'message': str(groq_error)})}\n\n"
            return

        try:
            yield from self._stream_with_llm(gemini_factory, prompt)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
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
