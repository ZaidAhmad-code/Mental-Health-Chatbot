# 🌿 Serene - AI Mental Health Chatbot

> An AI-powered mental health assistant built with Flask, LangChain, and a dual LLM architecture. Designed as a university project for BSc Computer Science with Artificial Intelligence.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Disclaimer](#disclaimer)

---

## Overview

**Serene** is a context-aware mental health chatbot that uses Retrieval-Augmented Generation (RAG) to provide grounded, evidence-based responses from curated mental health literature. It includes clinical screening tools (PHQ-9 & GAD-7), real-time crisis detection, user authentication, sentiment analysis, and wellness exercises.

---

## Features

- 🤖 **Dual LLM Architecture** — Primary: Groq (LLaMA-3.3 70B), Fallback: Google Gemini Pro
- 📚 **RAG Pipeline** — Responses grounded in mental health PDFs via ChromaDB vector store
- 🏥 **Clinical Assessments** — PHQ-9 (depression) and GAD-7 (anxiety) with scored results
- 🚨 **Crisis Detection** — Real-time keyword-based detection with resource links
- 🔐 **User Authentication** — Register, login, session management
- 💬 **Multi-Session Chat** — Multiple named chat sessions with full history
- 📊 **Sentiment Analysis** — Per-message emotion and mood tracking
- 🧘 **Wellness Module** — Breathing exercises and meditation sessions
- 📈 **Analytics** — User stats, mood trends, assessment history
- 🔒 **Error Handling & Logging** — Rotating logs, structured error tracking

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10, Flask 3.1 |
| AI / LLM | LangChain, Groq (LLaMA-3.3 70B), Google Gemini Pro |
| Vector DB | ChromaDB |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript (Vanilla) |

---

## Project Structure

```
Serene/
├── app.py                   # Main Flask application & all API routes
├── chatbot.py               # Dual LLM chain & RAG setup
├── database.py              # SQLite database models & queries
├── auth.py                  # User registration, login, session management
├── assessments.py           # PHQ-9 & GAD-7 clinical assessment logic
├── crisis_detection.py      # Keyword-based crisis detection
├── sentiment_analysis.py    # Emotion & mood analysis
├── analytics.py             # User stats & engagement metrics
├── predictive_analytics.py  # Risk prediction & mood forecasting
├── conversation_memory.py   # Per-user conversation context
├── cache_manager.py         # In-memory LLM response cache
├── wellness.py              # Breathing & meditation exercises
├── notifications.py         # Email notification service
├── streaming.py             # Server-Sent Events streaming
├── websocket_chat.py        # WebSocket support (Flask-SocketIO)
├── error_handler.py         # Logging & error handling
├── api_docs.py              # OpenAPI / Swagger documentation
├── templates/               # HTML templates
│   ├── index.html           # Main chat UI
│   ├── auth.html            # Login & register
│   ├── assessments.html     # Clinical assessments
│   └── dashboard.html       # User dashboard
├── static/                  # CSS, JS, images
├── data/                    # Mental health PDFs (RAG source)
├── chroma_db/               # ChromaDB vector store (auto-generated)
├── logs/                    # Application logs (auto-generated)
├── requirements.txt
├── .env                     # API keys (not committed to git)
├── Dockerfile
└── docker-compose.yml
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/) (free)
- Optionally a [Google Gemini API key](https://aistudio.google.com/)

### 1. Clone the repository

```bash
git clone https://github.com/ZaidAhmad-code/Mental-Health-Chatbot.git
cd Mental-Health-Chatbot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here   # Optional
SECRET_KEY=your_secret_key_here
```

### 5. Run the application

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

> On first run, the vector database is built automatically from the PDFs in the `data/` folder. This may take a minute.

### Docker (Alternative)

```bash
docker-compose up --build
```

---

## Usage

1. **Register** an account or log in.
2. **Chat** with Serene about anything mental-health related.
3. **Take assessments** (PHQ-9 / GAD-7) via the Assessments page.
4. **Track your mood** and view history on the Dashboard.
5. **Try wellness exercises** — breathing and meditation sessions.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ask` | Send a chat message |
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET/PUT | `/api/auth/profile` | Get or update profile |
| GET/POST | `/api/assessment/phq9` | PHQ-9 assessment |
| GET/POST | `/api/assessment/gad7` | GAD-7 assessment |
| GET | `/api/assessment/history` | Assessment history |
| GET | `/api/analytics/user-stats` | User statistics |
| GET | `/api/analytics/mood-trend` | Mood trend data |
| GET | `/api/wellness/breathing` | Breathing exercises |
| GET | `/api/wellness/meditation` | Meditation sessions |
| GET | `/api/health` | Health check |
| GET | `/api/docs/` | Swagger API documentation |

---

## Disclaimer

> ⚠️ **Serene is not a medical device and is not a replacement for professional mental health care.** It is an academic project developed for educational purposes. If you are in crisis, please contact a mental health professional or call a crisis helpline (e.g. 988 in the US).

---

*Developed by Zaid Ahmad — BSc Computer Science with Artificial Intelligence, 2026*
