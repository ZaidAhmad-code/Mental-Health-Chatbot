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

def initialize_llm():
    """Initialize dual LLM system with Groq as primary and Gemini as fallback"""
    try:
        # Primary LLM: Groq (LLaMA-3.3 70B)
        groq_llm = ChatGroq(
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile"
        )
        print("✓ Primary LLM initialized: Groq (LLaMA-3.3 70B)")
        
        # Secondary LLM: Google Gemini Pro
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key and gemini_api_key != "your_gemini_api_key_here":
            gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=gemini_api_key,
                temperature=0
            )
            print("✓ Secondary LLM initialized: Google Gemini Pro")
        else:
            gemini_llm = None
            print("⚠ Gemini API key not configured - running with Groq only")
        
        return groq_llm, gemini_llm
    except Exception as e:
        print(f"✗ Error initializing LLMs: {e}")
        return None, None


class DualLLMChain:
    """Wrapper class to handle dual LLM with automatic fallback"""
    def __init__(self, primary_chain, secondary_chain=None):
        self.primary_chain = primary_chain
        self.secondary_chain = secondary_chain
        self.primary_failures = 0
        
    def run(self, query):
        """Try primary LLM first, fallback to secondary if it fails"""
        try:
            # Try primary LLM (Groq)
            response = self.primary_chain.run(query)
            self.primary_failures = 0  # Reset failure counter on success
            return response
        except Exception as primary_error:
            print(f"⚠ Primary LLM (Groq) failed: {primary_error}")
            self.primary_failures += 1
            
            # Fallback to secondary LLM (Gemini)
            if self.secondary_chain:
                try:
                    print("→ Switching to secondary LLM (Gemini)...")
                    response = self.secondary_chain.run(query)
                    return response
                except Exception as secondary_error:
                    print(f"✗ Secondary LLM (Gemini) also failed: {secondary_error}")
                    return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment or contact emergency services if you need immediate help."
            else:
                return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment or contact emergency services if you need immediate help."


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
    """Setup QA chain for a given LLM"""
    retriever = vector_db.as_retriever()
    prompt_templates = """ You are a compassionate mental health chatbot. Respond thoughtfully for the following questions
    {context}
    user: {question}
    Chatbot: """
    PROMPT = PromptTemplate(
        template=prompt_templates,
        input_variables=["context", "question"]
    )
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": PROMPT}
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