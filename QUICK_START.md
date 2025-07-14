# 🚀 Hospital Bed Management Agent - Quick Start

## One-Command Setup
```bash
python start_platform.py
```

## Manual Setup (if needed)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2. Initialize Database
```bash
python scripts/init_data.py
```

### 3. Start Backend
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start Frontend (new terminal)
```bash
cd frontend && npm run dev
```

## Access the Platform
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Features
- 📊 **Real-time Dashboard** with bed occupancy metrics
- 💬 **AI Chat Interface** powered by Gemini 2.0 Flash
- 🏥 **16 Sample Beds** across ICU, General, Emergency wards
- 👥 **8 Sample Patients** with realistic medical data
- 📈 **Interactive Charts** and trend analysis

## Sample Chat Questions
- "What's the current bed occupancy rate?"
- "Show me available ICU beds"
- "Are there any critical capacity issues?"
- "Who is expected to be discharged today?"

---
**🎉 Ready to optimize hospital bed management with AI!**
