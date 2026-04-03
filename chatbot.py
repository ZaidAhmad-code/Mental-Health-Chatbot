from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import os

from dotenv import load_dotenv
load_dotenv()

from prompts import build_prompt, classify_message


# ========== MENTAL HEALTH PROMPT (used by RAG QA chain) ==========
MENTAL_HEALTH_PROMPT = """You are Serene, a warm and knowledgeable mental health companion.
Speak like a caring, emotionally intelligent friend — not a therapist reciting a textbook.
Never use clinical jargon. Never give a wall of bullet points unprompted.
Never say: "try deep breathing", "practice self-care", or "I'm just an AI".

Rules:
- Match the length of your reply to the weight of what the user said
- A short message deserves a short reply — don't pad it
- Acknowledge feelings before giving advice
- Be specific and actionable, not vague
- Ask a follow-up question when appropriate

Use this knowledge:
{context}

User said: {question}

Serene:"""


def initialize_llm():
    """Initialize dual LLM system with Groq as primary and Gemini as fallback"""
    try:
        # Primary LLM: Groq (LLaMA-3.3 70B) with higher temperature for natural conversation
        groq_llm = ChatGroq(
            temperature=0.7,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile",
            max_tokens=500  # Enough for helpful advice
        )
        print("✓ Primary LLM initialized: Groq (LLaMA-3.3 70B)")
        
        # Secondary LLM: Google Gemini 2.5 Flash
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key and gemini_api_key != "your_gemini_api_key_here":
            gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=gemini_api_key,
                temperature=0.7,
                max_output_tokens=500
            )
            print("✓ Secondary LLM initialized: Google Gemini 2.5 Flash")
        else:
            gemini_llm = None
            print("⚠ Gemini API key not configured - running with Groq only")
        
        return groq_llm, gemini_llm
    except Exception as e:
        print(f"✗ Error initializing LLMs: {e}")
        return None, None


class DualLLMChain:
    """Wrapper class to handle dual LLM with automatic fallback and conversation history"""
    def __init__(self, primary_chain, secondary_chain=None):
        self.primary_chain = primary_chain
        self.secondary_chain = secondary_chain
        self.primary_failures = 0
        
    def run(self, query, conversation_history=""):
        """Try primary LLM first, fallback to secondary if it fails
        
        Args:
            query: The user's current message (may already include context)
            conversation_history: Formatted string of previous conversation turns (prepended to query)
        """
        # Prepend conversation history to the query if provided
        if conversation_history and conversation_history.strip() and "No previous conversation" not in conversation_history:
            full_query = f"""[CONVERSATION HISTORY - Use this context to provide continuity:
{conversation_history}
]

NOW RESPONDING TO: {query}"""
        else:
            full_query = query
        
        try:
            # Try primary LLM (Groq)
            response = self.primary_chain.run(full_query)
            self.primary_failures = 0  # Reset failure counter on success
            return self._clean_response(response)
        except Exception as primary_error:
            print(f"⚠ Primary LLM (Groq) failed: {primary_error}")
            self.primary_failures += 1
            
            # Fallback to secondary LLM (Gemini)
            if self.secondary_chain:
                try:
                    print("→ Switching to secondary LLM (Gemini)...")
                    response = self.secondary_chain.run(full_query)
                    return self._clean_response(response)
                except Exception as secondary_error:
                    print(f"✗ Secondary LLM (Gemini) also failed: {secondary_error}")
                    return self._get_fallback_response()
            else:
                return self._get_fallback_response()
    
    def _clean_response(self, response):
        """Clean up the response for better presentation"""
        # Remove any repeated phrases or artifacts
        response = response.strip()
        
        # Remove any "Assistant:" or "Chatbot:" prefixes the model might add
        prefixes_to_remove = ["Assistant:", "Chatbot:", "MindSpace:", "Serene:", "Bot:", "Response:"]
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        return response
    
    def _get_fallback_response(self):
        """Return a natural fallback response"""
        import random
        fallbacks = [
            "Hey, I'm so sorry - something glitched on my end for a sec. But I'm here! What were you saying?",
            "Ugh, my bad - I had a little technical hiccup there. I'm back though! Please, keep sharing with me.",
            "Sorry about that! Something went wonky for a moment. I'm listening now - go ahead.",
            "Whoops, had a brief moment there. I'm here for you though - what's on your mind?"
        ]
        return random.choice(fallbacks)


def create_vector_db():
    loader = DirectoryLoader('data/', glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_db = Chroma.from_documents(texts, embeddings, persist_directory='chroma_db')
    vector_db.persist()

    print("Created and data sent")

    return vector_db


def setup_qa_chain(vector_db, llm):
    """Setup QA chain for a given LLM with enhanced mental health prompt"""
    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}  # Retrieve more relevant context
    )
    
    # Use the enhanced mental health prompt
    PROMPT = PromptTemplate(
        template=MENTAL_HEALTH_PROMPT,
        input_variables=["context", "question"]
    )
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={
            "prompt": PROMPT,
        },
        return_source_documents=False
    )

    return qa_chain


def main():

    print("initializing Chatbot !!")
    print("=" * 60)
    
    # Initialize dual LLM system
    groq_llm, gemini_llm = initialize_llm()
    
    if not groq_llm:
        print("✗ Failed to initialize LLMs. Exiting.")
        return

    # Setup vector database
    db_path = 'chroma_db'
    if not os.path.exists(db_path):
        vector_db = create_vector_db()
    else:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)

    # Create QA chains for both LLMs
    print("=" * 60)
    print("Setting up RAG chains...")
    primary_chain = setup_qa_chain(vector_db, groq_llm)
    secondary_chain = setup_qa_chain(vector_db, gemini_llm) if gemini_llm else None
    
    # Create dual LLM chain with automatic fallback
    qa_chain = DualLLMChain(primary_chain, secondary_chain)
    print("✓ Dual LLM system ready!")
    print("=" * 60)
    print("\nChat with the Mental Health Assistant (type 'exit' to quit)\n")

    while True:
        query = input("\nUser: ")
        if query.lower() == "exit":
            print("Chatbot: Goodbye! Take care of yourself.")
            break
        response = qa_chain.run(query)
        print(f"Chatbot: {response}")


if __name__ == "__main__":
    main()