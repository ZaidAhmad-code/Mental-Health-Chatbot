from flask import Flask, render_template, request, jsonify, session
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains import RetrievalQA
import os
import json

# Import your chatbot functions
from chatbot import initialize_llm, create_vector_db, setup_qa_chain, DualLLMChain
from assessments import PHQ9Assessment, GAD7Assessment, get_assessment_by_type, validate_answers
from database import init_db, save_assessment_result, get_user_assessments, create_guest_user, save_chat_message

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this!

# Initialize database
init_db()

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


@app.route('/assessments')
def assessments():
    return render_template('assessments.html')


@app.route('/ask', methods=['POST'])
def ask():
    user_query = request.form['query']
    response = qa_chain.run(user_query)
    
    # Save to database
    user_id = get_user_id()
    save_chat_message(user_id, user_query, response)
    
    return jsonify({'response': response})


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
        
        # Save to database
        user_id = get_user_id()
        result_id = save_assessment_result(
            user_id, 
            'phq9', 
            score, 
            interpretation['severity'], 
            answers
        )
        
        return jsonify({
            'id': result_id,
            'score': score,
            'max_score': 27,
            'interpretation': interpretation
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
        
        # Save to database
        user_id = get_user_id()
        result_id = save_assessment_result(
            user_id, 
            'gad7', 
            score, 
            interpretation['severity'], 
            answers
        )
        
        return jsonify({
            'id': result_id,
            'score': score,
            'max_score': 21,
            'interpretation': interpretation
        })


@app.route('/api/assessment/history', methods=['GET'])
def assessment_history():
    """Get user's assessment history"""
    user_id = get_user_id()
    history = get_user_assessments(user_id, limit=20)
    return jsonify({'history': history})


if __name__ == '__main__':
    app.run(debug=True)