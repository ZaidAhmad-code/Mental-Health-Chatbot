from flask import Flask, render_template, request, jsonify
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings  # New package
from langchain.chains import RetrievalQA
import os

# Import your chatbot functions
from chatbot import initialize_llm, create_vector_db, setup_qa_chain

app = Flask(__name__)

# Initialize the LLM and vector database
llm = initialize_llm()
db_path = 'chroma_db'
if not os.path.exists(db_path):
    vector_db = create_vector_db()
else:
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-V2")
    vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)

qa_chain = setup_qa_chain(vector_db, llm)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_query = request.form['query']
    response = qa_chain.run(user_query)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)