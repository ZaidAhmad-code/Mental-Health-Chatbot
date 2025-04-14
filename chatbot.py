from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings  # New package
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq.chat_models import ChatGroq
import os

from dotenv import load_dotenv
load_dotenv()

def initialize_llm():
  llm = ChatGroq(
      temperature=0,
      groq_api_key=os.getenv("GROQ_API_KEY"),  # Read from .env
      model_name="llama-3.3-70b-versatile"
  )
  return llm


def create_vector_db():
    loader = DirectoryLoader('data/', glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    embeddings = HuggingFaceBgeEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-V2")
    vector_db = Chroma.from_documents(texts, embeddings, persist_directory='chroma_db')
    vector_db.persist()

    print("Created and data sent")

    return vector_db


def setup_qa_chain(vector_db, llm):
    retriever = vector_db.as_retriever()
    prompt_templates = """ You are a compassionate mental health chatbot. Respond thougfully for the following questions
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
    llm = initialize_llm()

    db_path = 'chroma_db'
    if not os.path.exists(db_path):
        vector_db = create_vector_db()
    else:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-V2")
        vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)

    qa_chain = setup_qa_chain(vector_db, llm)

    while True:
        query = input("\nUser: ")
        if query.lower() == "exit":
            print("Chatbot: Goodbye!")
            break
        response = qa_chain.run(query)
        print(f"Chatbot: {response}")


if __name__ == "__main__":
    main()