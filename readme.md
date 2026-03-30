# 🌿 KrishiAI — AI-Powered Farming Assistant

> Smart farming powered by Groq AI · 10 Indian Languages · Voice-to-Voice · Disease Detection · JWT Auth

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎙️ **Voice-to-Voice AI** | Speak in any Indian language → Groq Whisper transcribes → LLaMA answers → gTTS speaks back |
| 🎉 **Welcome Greeting** | Energetic audio welcome *"KrishiAI mein aapka swaaaaagat hai!"* plays on every login |
| 🔬 **Disease Detector** | Upload crop photo or describe symptoms → AI diagnosis with treatment steps |
| 💬 **AI Chat Advisor** | Streaming chat with Groq LLaMA — fertilizers, pests, weather, schemes |
| 🌐 **10 Languages** | Hindi, Marathi, Punjabi, Gujarati, Tamil, Telugu, Kannada, Bengali, Bhojpuri, English |
| 🔐 **JWT Auth** | Secure register/login with bcrypt passwords and JWT tokens |
| 📊 **Analytics** | Yield trends, revenue vs cost charts |
| 💧 **Irrigation Advisor** | Smart irrigation plan based on soil moisture |
| 🌱 **Fertilizer Planner** | Full schedule with cost estimates |
| 📉 **Price Forecast** | Mandi price prediction chart |
| 💰 **Profit Calculator** | Net profit, ROI, break-even price |
| 🏛 **Gov Schemes** | PM-KISAN, Fasal Bima, Krishi Sinchai, Soil Health Card |
| 🗺️ **Nearby Alerts** | District-level disease outbreak alerts |
| 📲 **WhatsApp Alert** | Share disease alert link with nearby farmers |

---

## 🛠️ Tech Stack

```
Frontend  → Streamlit (Python)
Backend   → FastAPI + Uvicorn
Database  → MySQL (pymysql)
AI Chat   → Groq LLaMA 3.3 70B
Vision    → Groq LLaMA 4 Scout / LLaMA 3.2 Vision
STT       → Groq Whisper Large v3
TTS       → gTTS (Google Text-to-Speech)
Auth      → JWT (python-jose) + bcrypt
Search    → Tavily (optional)
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
# Install all dependencies
pip install -r requirements.txt

# OR using Pipenv
pipenv install
pipenv shell
```

### 2. Configure `.env`

```env
# REQUIRED
GROQ_API_KEY=gsk_your_key_here

# DATABASE (MySQL)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=krishiai

# JWT (change this in production!)
JWT_SECRET=your-super-secret-key-change-this

# OPTIONAL
TAVILY_API_KEY=tvly_your_key_here
OPENWEATHER_API_KEY=your_key_here
DATA_GOV_API_KEY=your_key_here
```

Get your free Groq API key → https://console.groq.com

### 3. Setup MySQL

```bash
# Create DB and all tables
python mysql_setup.py
```

### 4. Run Diagnostic

```bash
python test_setup.py
```
Fix any errors it reports before starting.

### 5. Start the App

**Terminal 1 — Backend:**
```bash
python backend.py
# API running at http://127.0.0.1:9999
# Swagger docs at http://127.0.0.1:9999/docs
```

**Terminal 2 — Frontend:**
```bash
streamlit run frontend.py
# App running at http://localhost:8501
```

---

## 🎙️ Voice Setup

Voice features use two libraries. Make sure both are installed:

```bash
pip install gTTS streamlit-mic-recorder
```

**How Voice-to-Voice works:**

```
👨‍🌾 Farmer taps 🎤 Hold & Speak
         ↓
   Records audio in browser
         ↓
  Groq Whisper STT (auto-detects language)
         ↓
  KrishiAI LLaMA 3.3 70B (short energetic reply)
         ↓
  gTTS converts to MP3
         ↓
🔊 Auto-plays in browser
```

**Supported voice languages:** All 10 — Hindi, Marathi, Punjabi, Gujarati, Tamil, Telugu, Kannada, Bengali, Bhojpuri (uses Hindi TTS), English.

---

## 🎉 Welcome Greeting

When a farmer logs in, KrishiAI plays an energetic audio greeting in their language:

- **Hindi:** *"KrishiAI mein aapka swaaaaagat hai! Jai Kisan!"*
- **Marathi:** *"KrishiAI madhe aapale swaaaagat ahe! Jai Kisan!"*
- **Punjabi:** *"KrishiAI wich tuhada swaaaagat hai! Jai Kisan!"*
- ...and 7 more languages

The greeting plays **only once per session** — not on every page reload.

---

## 🗄️ Database Schema

```sql
users           -- id, name, email, phone, password_hash, location, languages, created_at
disease_history -- id, farmer_id(FK), district, crop_name, disease_name, severity, treatment...
disease_alerts  -- id, district, disease_name, crop_name, severity, alert_count, last_seen
chat_history    -- id, farmer_id(FK), role, message, language, sent_at
```

---

## 📁 Project Structure

```
krishi-ai/
├── backend.py          # FastAPI backend (v4) — MySQL, JWT, Groq AI, streaming
├── frontend.py         # Streamlit frontend (v4.1) — Voice AI, all pages
├── mysql_setup.py      # One-time DB setup script
├── test_setup.py       # Diagnostic — checks all dependencies & connections
├── requirements.txt    # pip dependencies
├── Pipfile             # Pipenv dependencies
├── .env                # Your API keys (never commit this!)
└── .env.example        # Template for .env
```

---

## 🔑 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | ❌ | Create new account |
| POST | `/auth/login` | ❌ | Login, get JWT token |
| GET | `/auth/me` | ✅ | Get current user profile |
| POST | `/chat` | ✅ | AI chat (non-streaming) |
| POST | `/chat/stream` | ✅ | AI chat (streaming) |
| GET | `/chat/history` | ✅ | Get chat history |
| POST | `/disease/text` | ✅ | Diagnose by symptoms |
| POST | `/disease/photo` | ✅ | Diagnose by photo |
| GET | `/disease/history` | ✅ | Past disease scans |
| GET | `/disease/nearby-alerts` | ❌ | District alerts |
| GET | `/weather` | ❌ | Weather data |
| GET | `/market` | ❌ | Mandi prices |
| GET | `/schemes` | ❌ | Government schemes |
| GET | `/soil/analyze` | ❌ | Soil health analysis |
| POST | `/irrigation/recommend` | ✅ | Irrigation plan |
| POST | `/planner/fertilizer` | ✅ | Fertilizer schedule |
| POST | `/market/predict` | ✅ | Price forecast |
| POST | `/profit/calc` | ✅ | Profit calculator |
| POST | `/recommend/crop` | ✅ | Crop recommendation |
| GET | `/stats` | ✅ | Dashboard stats |
| GET | `/health` | ❌ | Backend health check |

Full interactive docs: `http://127.0.0.1:9999/docs`

---

## ⚙️ Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | — | Groq API key (get at console.groq.com) |
| `MYSQL_HOST` | ✅ Yes | `localhost` | MySQL host |
| `MYSQL_PORT` | ✅ Yes | `3306` | MySQL port |
| `MYSQL_USER` | ✅ Yes | `root` | MySQL username |
| `MYSQL_PASSWORD` | ✅ Yes | `""` | MySQL password |
| `MYSQL_DATABASE` | ✅ Yes | `krishiai` | MySQL database name |
| `JWT_SECRET` | ✅ Yes | `demo-secret` | **Change in production!** |
| `JWT_ALGORITHM` | ⬜ No | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | ⬜ No | `60` | Token expiry in minutes |
| `TAVILY_API_KEY` | ⬜ No | — | Web search for chat |
| `OPENWEATHER_API_KEY` | ⬜ No | — | Live weather data |
| `DATA_GOV_API_KEY` | ⬜ No | — | Live mandi prices |

---

## 🐛 Common Errors & Fixes

| Error | Fix |
|---|---|
| `GROQ_API_KEY missing` | Add it to `.env` |
| `Error 1364: Field 'username' doesn't have a default value` | Drop old users table and restart backend: `DROP TABLE disease_history; DROP TABLE chat_history; DROP TABLE users;` then `python backend.py` |
| `RuntimeError: Form data requires "python-multipart"` | `pip install python-multipart` |
| `ModuleNotFoundError: No module named 'bcrypt'` | `pip install bcrypt` |
| `Error 401: Could not validate credentials` | JWT expired — logout and login again |
| `Backend Offline` shown in sidebar | Run `python backend.py` in a separate terminal |
| `gTTS error` | Check internet connection (gTTS calls Google TTS API) |
| `Whisper STT error 401` | GROQ_API_KEY is invalid or missing |

---

## 📦 Install All Dependencies at Once

```bash
pip install fastapi uvicorn streamlit python-multipart \
    langchain langchain-community langchain-core langchain-groq \
    langgraph groq pymysql cryptography python-jose[cryptography] \
    passlib[bcrypt] bcrypt gTTS streamlit-mic-recorder \
    python-dotenv httpx requests pydantic pandas tenacity
```

---

## 🌾 Jai Kisan! Jai Hind! 🇮🇳
