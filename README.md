# 🏥 Hospital Bed Management Agent

An intelligent bed management system using **LangGraph + Gemini AI** with a realistic dashboard and chat interface.

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 3: Setup Database
```bash
python scripts/init_data.py
```

### Step 4: Start the Platform
```bash
python start_platform.py
```

This will:
- ✅ Start FastAPI backend on http://localhost:8000
- ✅ Start React frontend on http://localhost:3000
- ✅ Open your browser automatically

## 📊 What You'll See

### Dashboard Features
- **Real-time bed occupancy** metrics
- **Interactive charts** showing trends
- **Color-coded alerts** for capacity issues
- **Auto-refresh** every 30 seconds

### Chat Interface
- **Natural language** queries about bed management
- **AI-powered responses** using Gemini 2.0 Flash
- **Real-time data** integration
- **Suggested questions** to get started

## 🤖 Sample Questions

Try asking the agent:
- "What's the current bed occupancy rate?"
- "Show me available ICU beds"
- "Are there any critical capacity issues?"
- "Who is expected to be discharged today?"

## 🏗️ Tech Stack

- **Agent**: LangGraph + LangChain
- **LLM**: Google Gemini 2.0 Flash
- **Backend**: FastAPI + PostgreSQL
- **Frontend**: React + Vite + Tailwind CSS
- **RAG**: ChromaDB + Sentence Transformers
