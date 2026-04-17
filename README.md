# 🌿 Serene — AI Mental Health Companion

> A full-stack, three-platform AI mental health companion built with Flask, LangChain, Next.js, and Flutter. Features a dual-LLM architecture with automatic fallback, Retrieval-Augmented Generation grounded in clinical literature, real-time crisis detection, and validated clinical screening tools (PHQ-9 & GAD-7).
>
> *BSc Computer Science with Artificial Intelligence — Final Year Project, 2026*

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the System](#running-the-system)
- [API Endpoints](#api-endpoints)
- [Safety & Crisis Detection](#safety--crisis-detection)
- [Clinical Assessments](#clinical-assessments)
- [Disclaimer](#disclaimer)

---

## Overview

**Serene** is a context-aware mental health companion that uses Retrieval-Augmented Generation (RAG) to provide grounded, evidence-based responses from curated clinical mental health literature. It combines a conversational AI with real clinical screening tools, a real-time safety engine, mood tracking, and wellness exercises — accessible on both web and Android.

The system is built across three platforms:
- **Flask backend** — the core API, AI pipeline, and database
- **Next.js web app** — browser-based interface with real-time streaming chat
- **Flutter Android app** — native mobile client with full feature parity

---

## System Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Next.js Web App   │     │  Flutter Android App │
│   (port 3000)       │     │  (serene_app/)       │
└────────┬────────────┘     └──────────┬───────────┘
         │  HTTP / SSE                 │  HTTP / SSE
         ▼                             ▼
┌─────────────────────────────────────────────────┐
│              Flask Backend (port 5000)           │
│                                                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │  Auth &  │  │    RAG    │  │    Crisis    │  │
│  │ Sessions │  │ Pipeline  │  │  Detection   │  │
│  └──────────┘  └─────┬─────┘  └──────────────┘  │
│                      │                           │
│  ┌───────────────────▼──────────────────────┐   │
│  │          Dual LLM Architecture           │   │
│  │  Primary: Groq LLaMA-3.3 70B            │   │
│  │  Fallback: Google Gemini 2.5 Flash      │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────┐  ┌───────────┐  ┌──────────┐   │
│  │  ChromaDB   │  │  SQLite   │  │Sentiment │   │
│  │ Vector Store│  │    DB     │  │ Analysis │   │
│  └─────────────┘  └───────────┘  └──────────┘   │
└─────────────────────────────────────────────────┘
```

---

## Features

### 🤖 AI & Chat
- **Dual LLM Architecture** — Primary: Groq LLaMA-3.3 70B · Fallback: Google Gemini 2.5 Flash (automatic, transparent)
- **RAG Pipeline** — Responses grounded in 4 clinical mental health PDFs via ChromaDB + `all-MiniLM-L6-v2` embeddings
- **Context-Aware Prompting** — 8 message types (greeting, venting, crisis, question, etc.) each with a dedicated system prompt and token budget
- **Real-Time Streaming** — Server-Sent Events (SSE) for live token-by-token chat responses
- **Multi-Session Memory** — Multiple named chat sessions, full history, per-session conversation context

### 🚨 Safety
- **Crisis Detection Engine** — 4 severity levels (NORMAL / MODERATE / HIGH / CRITICAL) with emergency resource surfacing
- **Assessment-Integrated Safety** — PHQ-9 score ≥ 20 automatically triggers CRITICAL crisis flag

### 🏥 Clinical Tools
- **PHQ-9** — 9-question depression screening, 0–27 score, 5 severity bands
- **GAD-7** — 7-question anxiety screening, 0–21 score, 4 severity bands
- **Assessment History** — All results stored and displayed on dashboard

### 📊 Wellbeing Tracking
- **Sentiment Analysis** — Per-message mood scoring stored longitudinally
- **Dashboard** — Mood trend graphs, usage stats, assessment history
- **Predictive Analytics** — Risk scoring and mood forecasting
- **Wellness Module** — Breathing, meditation, grounding, and journaling exercises

### 🔐 Infrastructure
- **User Authentication** — Register, login, session management with Werkzeug password hashing
- **Response Caching** — In-memory cache for common queries (instant responses, no LLM call)
- **Structured Logging** — Rotating logs, per-module error tracking
- **OpenAPI Docs** — Swagger UI at `/api/docs/`
- **Docker Support** — `Dockerfile` + `docker-compose.yml` included

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10, Flask 3.1 |
| LLM Orchestration | LangChain |
| Primary LLM | Groq — LLaMA-3.3 70B |
| Fallback LLM | Google Gemini 2.5 Flash |
| Vector Database | ChromaDB |
| Embeddings | HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Database | SQLite |
| Web Frontend | Next.js (React), TypeScript |
| Mobile App | Flutter (Dart), Android |
| Streaming | Server-Sent Events (SSE) |
| Auth | Flask Sessions, Werkzeug |
| Containerisation | Docker, Docker Compose |

---

## Project Structure

```
Mental-Health-Chatbot/          ← Flask backend
├── app.py                      # Entry point — all 30+ API routes
├── chatbot.py                  # RAG chain, dual LLM initialisation
├── streaming.py                # SSE streaming with Groq→Gemini fallback
├── prompts.py                  # Context-aware message classifier & prompt builder
├── database.py                 # SQLite schema & queries
├── auth.py                     # Registration, login, session management
├── assessments.py              # PHQ-9 & GAD-7 scoring logic
├── crisis_detection.py         # 4-level crisis detection engine
├── sentiment_analysis.py       # Per-message emotion scoring
├── analytics.py                # Usage stats & mood trend aggregation
├── predictive_analytics.py     # Risk scoring & mood forecasting
├── conversation_memory.py      # Per-session conversation history
├── cache_manager.py            # In-memory LLM response cache
├── wellness.py                 # Wellness exercise content
├── notifications.py            # Email notification service
├── error_handler.py            # Logging & structured error handling
├── api_docs.py                 # OpenAPI / Swagger docs
├── websocket_chat.py           # WebSocket support (Flask-SocketIO)
├── data/                       # Clinical PDFs (RAG knowledge base)
│   ├── depression-in-adults-treatment-and-management.pdf
│   ├── mental_health_Document.pdf
│   ├── mhgap1.pdf
│   └── The-Anxiety-and-Phobia-Workbook-Edmund-J.-Bourne.pdf
├── chroma_db/                  # ChromaDB vector store (auto-generated)
├── logs/                       # Application logs (auto-generated)
├── templates/                  # Flask HTML templates (legacy)
├── static/                     # Static assets
├── requirements.txt
├── .env                        # API keys — NOT committed
├── Dockerfile
└── docker-compose.yml
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/) — free tier available
- A [Google Gemini API key](https://aistudio.google.com/) — free tier available (used as fallback)
- Node.js 18+ and `pnpm` (for the Next.js web frontend)
- Flutter SDK (for the Android app — optional)

---

### 1. Clone the repository

```bash
git clone https://github.com/ZaidAhmad-code/Mental-Health-Chatbot.git
cd Mental-Health-Chatbot
```

### 2. Create and activate a virtual environment

```bash
python3.10 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=any_long_random_string_here
```

---

## Running the System

### Backend (Flask)

```bash
source .venv/bin/activate
python app.py
```

The backend starts on **http://0.0.0.0:5000** and is accessible from any device on the same network.

> **First run:** The vector database is built automatically from the PDFs in `data/`. This takes ~1–2 minutes. Subsequent starts are instant.

---

### Web Frontend (Next.js)

```bash
cd ../Serene-Frontend
pnpm install
pnpm dev
```

Visit **http://localhost:3000**

---

### Android App (Flutter)

```bash
cd ../serene_app
flutter pub get
flutter run
```

On first launch, enter the backend IP address (e.g. `http://10.1.1.187:5000` on a local network, or `http://10.0.2.2:5000` for an Android emulator).

---

### Docker (All-in-one)

```bash
docker-compose up --build
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET/PUT | `/api/auth/profile` | Get or update user profile |
| PUT | `/api/auth/change-password` | Change password |
| DELETE | `/api/auth/delete-account` | Delete account |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ask` | Standard chat (non-streaming) |
| GET | `/api/chat/stream` | SSE streaming chat |
| GET | `/api/chats` | List all chat sessions |
| POST | `/api/chats` | Create a new chat session |
| GET | `/api/chats/<id>/messages` | Get messages for a session |
| DELETE | `/api/chats/<id>` | Delete a session |

### Assessments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/assessment/phq9` | PHQ-9 depression screening |
| GET/POST | `/api/assessment/gad7` | GAD-7 anxiety screening |
| GET | `/api/assessment/history` | All past assessment results |

### Dashboard & Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Summary stats |
| GET | `/api/analytics/user-stats` | Detailed user statistics |
| GET | `/api/analytics/mood-trend` | Mood trend over time |
| GET | `/api/predictive/risk-score` | Predictive risk assessment |
| GET | `/api/predictive/mood-forecast` | Mood forecast |

### Wellness
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wellness/breathing` | Breathing exercises |
| GET | `/api/wellness/meditation` | Meditation sessions |
| GET | `/api/wellness/grounding` | Grounding techniques |
| GET | `/api/wellness/journal` | Journal prompts |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/docs/` | Swagger / OpenAPI documentation |

---

## Safety & Crisis Detection

Every message passes through the crisis detection engine **before** the LLM generates a response.

| Severity | Score | Trigger |
|---|---|---|
| NORMAL | 0 | No risk indicators |
| MODERATE | 5 | 1–2 warning keywords detected |
| HIGH | 7 | 3+ warning keywords detected |
| CRITICAL | 10 | Any crisis-level keyword detected, or PHQ-9 ≥ 20 |

When CRITICAL or HIGH severity is detected, the interface immediately surfaces emergency crisis resources including international helplines.

---

## Clinical Assessments

### PHQ-9 (Patient Health Questionnaire)
9 questions · Score range 0–27

| Score | Severity |
|---|---|
| 0–4 | Minimal |
| 5–9 | Mild |
| 10–14 | Moderate |
| 15–19 | Moderately Severe |
| 20–27 | Severe → auto-triggers CRITICAL crisis flag |

### GAD-7 (Generalised Anxiety Disorder scale)
7 questions · Score range 0–21

| Score | Severity |
|---|---|
| 0–4 | Minimal |
| 5–9 | Mild |
| 10–14 | Moderate |
| 15–21 | Severe |

---

## Disclaimer

> ⚠️ **Serene is not a medical device and is not a substitute for professional mental health care.** It is an academic project developed for educational purposes only. If you or someone you know is in crisis, please contact a qualified mental health professional or a crisis helpline:

---

