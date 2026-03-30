from dotenv import load_dotenv
load_dotenv()

import os, logging, json, base64, datetime
from typing import List, Optional
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

# ------------------------------------------------------------
# 1️⃣  Core libs
# ------------------------------------------------------------
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages.ai import AIMessage
from langchain_core.messages import SystemMessage, HumanMessage as LCHuman
from langgraph.prebuilt import create_react_agent

# ------------------------------------------------------------
# 2️⃣  ENV SETTINGS
# ------------------------------------------------------------
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY  = os.getenv("TAVILY_API_KEY", "")
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
MARKET_API_KEY  = os.getenv("DATA_GOV_API_KEY", "")
SARVAM_API_KEY  = os.getenv("SARVAM_API_KEY", "")

MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB       = os.getenv("MYSQL_DATABASE", "krishiai")

JWT_SECRET     = os.getenv("JWT_SECRET", "demo-secret-change-me")
JWT_ALGORITHM  = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing – add it to .env")

# ------------------------------------------------------------
# 3️⃣  MySQL helper
# ------------------------------------------------------------
import pymysql
import pymysql.cursors

def get_db():
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DB,
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            name          VARCHAR(128) NOT NULL,
            email         VARCHAR(255) UNIQUE,
            phone         VARCHAR(20)  UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            location      VARCHAR(255),
            languages     JSON,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS disease_history (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            farmer_id     INT NOT NULL,
            district      VARCHAR(128) NOT NULL DEFAULT 'Pune',
            crop_name     VARCHAR(128),
            symptoms      TEXT,
            disease_name  VARCHAR(255),
            confidence    VARCHAR(32),
            severity      VARCHAR(64),
            treatment     JSON,
            organic_opt   TEXT,
            yield_impact  TEXT,
            prevention    TEXT,
            detected_at   DATETIME NOT NULL,
            image_name    VARCHAR(255) DEFAULT '',
            source        ENUM('text','photo') DEFAULT 'text',
            whatsapp_sent TINYINT(1)   DEFAULT 0,
            FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS disease_alerts (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            district      VARCHAR(128) NOT NULL,
            disease_name  VARCHAR(255) NOT NULL,
            crop_name     VARCHAR(128) NOT NULL,
            severity      VARCHAR(64),
            alert_count   INT DEFAULT 1,
            last_seen     DATETIME NOT NULL,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_alert (district, disease_name, crop_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            farmer_id  INT NOT NULL,
            role       ENUM('user','bot') NOT NULL,
            message    TEXT NOT NULL,
            language   VARCHAR(8) NOT NULL,
            sent_at    DATETIME NOT NULL,
            FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    cur.close()
    conn.close()
    log.info("All MySQL tables ready.")

try:
    init_db()
except Exception as _e:
    log.error("init_db() failed – MySQL may be unavailable: %s", _e)

# ------------------------------------------------------------
# 4️⃣  JWT + password (direct bcrypt, no passlib)
# ------------------------------------------------------------
from jose import JWTError, jwt
import bcrypt as _bcrypt

bearer = HTTPBearer()

def hash_password(pw: str) -> str:
    pw_bytes = pw.encode("utf-8")[:72]
    return _bcrypt.hashpw(pw_bytes, _bcrypt.gensalt()).decode("utf-8")

def verify_password(pw: str, hashed: str) -> bool:
    pw_bytes = pw.encode("utf-8")[:72]
    return _bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=JWT_EXPIRE_MIN))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub", 0))
        if not user_id:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Could not validate credentials")
    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
    finally:
        if cur: cur.close()
        if conn: conn.close()
    if not user:
        raise HTTPException(404, "User not found")
    return user

# ------------------------------------------------------------
# 5️⃣  Pydantic Schemas
# ------------------------------------------------------------
class ChatRequest(BaseModel):
    model_name:   str  = Field(default="llama-3.3-70b-versatile")
    messages:     List[str] = Field(..., min_length=1)
    allow_search: bool = Field(default=True)
    language:     str  = Field(default="en")
    farmer_name:  str  = Field(default="Farmer")
    location:     str  = Field(default="Pune, Maharashtra")

    @field_validator("model_name")
    @classmethod
    def check_model(cls, v):
        allowed = ["llama-3.3-70b-versatile","llama3-70b-8192","mixtral-8x7b-32768","gemma2-9b-it"]
        if v not in allowed:
            raise ValueError(f"Model '{v}' not supported.")
        return v

class DiseaseTextRequest(BaseModel):
    crop_name: str = Field(default="crop")
    symptoms:  str = Field(default="yellow leaves with brown spots")
    language:  str = Field(default="en")
    location:  str = Field(default="Pune, Maharashtra")
    district:  str = Field(default="Pune")

class AlertRequest(BaseModel):
    disease_name: str
    crop_name:    str
    district:     str
    severity:     str
    farmer_phone: Optional[str] = None

class IrrigationRequest(BaseModel):
    crop: str = Field(default="Wheat")
    soil_moisture: float = Field(default=45.0, ge=0, le=100)
    lat: float = Field(default=18.5204)
    lon: float = Field(default=73.8567)
    language: str = Field(default="hi")

class FertilizerPlannerRequest(BaseModel):
    crop: str = Field(default="Wheat")
    stage: str = Field(default="Tillering")
    area: float = Field(default=1.0)
    unit: str = Field(default="acre")
    ph: float = Field(default=6.9)
    nitrogen: int = Field(default=45)
    phosphorus: int = Field(default=30)
    potassium: int = Field(default=180)
    organic_only: bool = Field(default=False)
    language: str = Field(default="hi")

class MarketPredictionRequest(BaseModel):
    state: str = Field(default="Maharashtra")
    crop: str = Field(default="Tomato")
    days: int = Field(default=7, ge=1, le=15)
    language: str = Field(default="hi")

class ProfitCalculatorRequest(BaseModel):
    crop: str = Field(default="Wheat")
    area: float = Field(default=1.0)
    unit: str = Field(default="acre")
    seed_cost: float = Field(default=1200.0)
    fertilizer_cost: float = Field(default=1800.0)
    pesticide_cost: float = Field(default=600.0)
    labor_cost: float = Field(default=2000.0)
    irrigation_cost: float = Field(default=500.0)
    misc_cost: float = Field(default=400.0)
    expected_yield_q: float = Field(default=10.0)
    expected_price_per_q: float = Field(default=2300.0)
    transport_cost: float = Field(default=0.0)
    language: str = Field(default="hi")

class CropRecommendationRequest(BaseModel):
    location: str = Field(default="Pune, Maharashtra")
    soil_type: str = Field(default="Black")
    season: str = Field(default="Kharif")
    language: str = Field(default="hi")

class RegisterRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str
    location: Optional[str] = None
    languages: List[str] = Field(default_factory=lambda: ["hi","mr"])

class LoginRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str

# ------------------------------------------------------------
# 6️⃣  Helpers
# ------------------------------------------------------------
SUPPORTED_LANGS = {
    "en":"English","hi":"Hindi","mr":"Marathi","pa":"Punjabi","gu":"Gujarati",
    "ta":"Tamil","te":"Telugu","kn":"Kannada","bn":"Bengali","bh":"Bhojpuri",
}

def build_system_prompt(language: str, farmer_name: str, location: str) -> str:
    lang_name = SUPPORTED_LANGS.get(language, "English")
    bhoj_note = " Use simple rural Bhojpuri dialect." if language == "bh" else ""

    if language == "en":
        lang_rule = "Respond in clear, simple English."
    else:
        lang_rule = (
            f"Detect the language the farmer used and reply in THAT SAME language. "
            f"If they write in English, reply in English. If Hindi, reply in Hindi. "
            f"If {lang_name}, reply in {lang_name}.{bhoj_note} Default if unclear: {lang_name}."
        )

    return (
        f"You are KrishiAI — a friendly, expert agricultural assistant for Indian farmers.\n"
        f"Farmer: {farmer_name} | Location: {location}\n\n"
        f"LANGUAGE RULE: {lang_rule}\n\n"
        "EXPERTISE: crop diseases & pests with exact treatment doses, fertilizer NPK ratios & timing, "
        "irrigation scheduling, weather impact on crops, government schemes (PM-KISAN, Fasal Bima Yojana, "
        "PM Krishi Sinchai Yojana, Soil Health Card), mandi prices & selling windows, "
        "soil health improvement, seasonal crop planning (Kharif/Rabi/Summer).\n\n"
        "RESPONSE STYLE:\n"
        "- Give SPECIFIC, ACTIONABLE advice with exact quantities, doses, timings\n"
        "- Use simple language a farmer can understand — avoid jargon\n"
        "- Use numbered steps for multi-step instructions\n"
        "- Be warm, supportive and encouraging\n"
        "- End every reply with a short encouraging line\n"
        "- If uncertain, say so honestly and suggest consulting a local agronomist"
    )

def save_chat_message(user_id: int, role: str, message: str, language: str):
    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_history (farmer_id,role,message,language,sent_at) VALUES (%s,%s,%s,%s,%s)",
            (user_id, role, message, language, datetime.datetime.utcnow()),
        )
        conn.commit()
    except Exception as e:
        log.warning("save_chat_message failed: %s", e)
    finally:
        if cur: cur.close()
        if conn: conn.close()

# ------------------------------------------------------------
# 7️⃣  FastAPI app + CORS
# ------------------------------------------------------------
app = FastAPI(
    title="KrishiAI Backend v4",
    description="Groq AI · 10 Languages · Photo Disease Detection · MySQL · JWT · Streaming",
    version="4.0.0",
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ------------------------------------------------------------
# 8️⃣  AUTH ENDPOINTS
# ------------------------------------------------------------
@app.post("/auth/register")
def register_user(req: RegisterRequest):
    langs = set(req.languages)
    if "hi" not in langs or "mr" not in langs:
        raise HTTPException(400, "Hindi (hi) and Marathi (mr) must be selected")
    if not req.password or len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if not req.email and not req.phone:
        raise HTTPException(400, "Provide at least email or phone")

    pw_hash = hash_password(req.password)
    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        if req.email:
            cur.execute("SELECT id FROM users WHERE email=%s", (req.email,))
            if cur.fetchone():
                raise HTTPException(400, "Email already registered")
        if req.phone:
            cur.execute("SELECT id FROM users WHERE phone=%s", (req.phone,))
            if cur.fetchone():
                raise HTTPException(400, "Phone already registered")
        cur.execute(
            "INSERT INTO users (name,email,phone,password_hash,location,languages) VALUES (%s,%s,%s,%s,%s,%s)",
            (req.name, req.email or None, req.phone or None, pw_hash, req.location, json.dumps(list(langs))),
        )
        conn.commit()
        user_id = cur.lastrowid
        token = create_access_token({"sub": str(user_id)})
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        if conn: conn.rollback()
        raise
    except pymysql.err.IntegrityError as e:
        if conn: conn.rollback()
        msg = str(e).lower()
        if "email" in msg: raise HTTPException(400, "Email already registered")
        if "phone" in msg: raise HTTPException(400, "Phone already registered")
        raise HTTPException(400, f"DB integrity error: {e}")
    except Exception as e:
        if conn: conn.rollback()
        log.error("Register error: %s", e, exc_info=True)
        raise HTTPException(500, f"Registration failed: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

@app.post("/auth/login")
def login_user(req: LoginRequest):
    if not (req.email or req.phone):
        raise HTTPException(400, "Provide email or phone")
    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        if req.email:
            cur.execute("SELECT * FROM users WHERE email=%s", (req.email,))
        else:
            cur.execute("SELECT * FROM users WHERE phone=%s", (req.phone,))
        user = cur.fetchone()
    except Exception as e:
        log.error("Login DB error: %s", e, exc_info=True)
        raise HTTPException(500, f"Login failed: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": str(user["id"])})
    return {"access_token": token, "token_type": "bearer"}

# ------------------------------------------------------------
# 8️⃣b  USER PROFILE ENDPOINT
# ------------------------------------------------------------
@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id":        current_user["id"],
        "name":      current_user["name"],
        "email":     current_user.get("email"),
        "phone":     current_user.get("phone"),
        "location":  current_user.get("location"),
        "languages": json.loads(current_user["languages"]) if isinstance(current_user.get("languages"), str) else (current_user.get("languages") or ["en","hi","mr"]),
        "created_at": str(current_user.get("created_at","")),
    }

# ------------------------------------------------------------
# 9️⃣  CHAT ENDPOINTS
# ------------------------------------------------------------
_SEARCH_KEYWORDS = [
    "price","rate","mandi","weather","news","today","current","scheme","yojana",
    "forecast","market","latest","2024","2025","भाव","मौसम","आज","ताज़ा","किमत",
]

def _needs_search(messages: list) -> bool:
    last = messages[-1] if messages else ""
    text = (last if isinstance(last, str) else str(last)).lower()
    return any(kw in text for kw in _SEARCH_KEYWORDS)

@app.post("/chat")
def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    system_prompt = build_system_prompt(req.language, current_user["name"], req.location)
    try:
        llm = ChatGroq(model=req.model_name)
        use_search = req.allow_search and TAVILY_API_KEY and _needs_search(req.messages)
        if use_search:
            tools = [TavilySearchResults(max_results=1)]
            agent = create_react_agent(model=llm, tools=tools, state_modifier=system_prompt)
            resp  = agent.invoke({"messages": req.messages})
            ai_msgs = [m.content for m in resp.get("messages", []) if isinstance(m, AIMessage) and m.content]
            answer = ai_msgs[-1] if ai_msgs else ""
        else:
            lc_msgs = [SystemMessage(content=system_prompt)] + [
                LCHuman(content=m) if isinstance(m, str) else m for m in req.messages
            ]
            result = llm.invoke(lc_msgs)
            answer = result.content or ""
    except Exception as e:
        log.error("Chat error: %s", e, exc_info=True)
        err_str = str(e)
        # Give a friendly message for common errors
        if "api_key" in err_str.lower() or "authentication" in err_str.lower():
            raise HTTPException(500, "GROQ_API_KEY is invalid or missing. Check your .env file.")
        if "model" in err_str.lower():
            raise HTTPException(500, f"Model error: {err_str}")
        if "rate" in err_str.lower() or "429" in err_str:
            raise HTTPException(429, "Rate limit reached. Please wait a moment and try again.")
        raise HTTPException(500, f"AI error: {err_str}")

    if not answer:
        raise HTTPException(500, "AI returned an empty response. Please try again.")

    save_chat_message(user_id, "user", req.messages[-1], req.language)
    save_chat_message(user_id, "bot", answer, req.language)
    return {"response": answer, "model_used": req.model_name, "language": req.language}

@app.post("/chat/stream")
def chat_stream(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    system_prompt = build_system_prompt(req.language, current_user["name"], req.location)

    # Validate before streaming so we can return a proper HTTP error
    if not GROQ_API_KEY:
        raise HTTPException(500, "GROQ_API_KEY is missing. Add it to your .env file.")

    try:
        llm = ChatGroq(model=req.model_name, streaming=True)
    except Exception as e:
        raise HTTPException(500, f"Could not initialise AI model: {e}")

    lc_msgs = [SystemMessage(content=system_prompt)] + [
        LCHuman(content=m) if isinstance(m, str) else m for m in req.messages
    ]

    def token_generator():
        full = []
        try:
            for chunk in llm.stream(lc_msgs):
                token = chunk.content
                if token:
                    full.append(token)
                    yield token
        except Exception as e:
            log.error("Streaming error: %s", e, exc_info=True)
            err = str(e)
            if "rate" in err.lower() or "429" in err:
                yield "\n\n⚠️ Rate limit reached. Please wait a moment and try again."
            elif "api_key" in err.lower() or "authentication" in err.lower():
                yield "\n\n⚠️ GROQ API key error. Please check your .env file."
            else:
                yield f"\n\n⚠️ Error: {err}"
        finally:
            answer = "".join(full)
            if answer and not answer.startswith("\n\n⚠️"):
                save_chat_message(user_id, "user", req.messages[-1], req.language)
                save_chat_message(user_id, "bot",  answer, req.language)

    return StreamingResponse(token_generator(), media_type="text/plain")

@app.get("/chat/history")
def get_chat_history(limit: int = 50, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT role,message,language,sent_at FROM chat_history WHERE farmer_id=%s ORDER BY sent_at DESC LIMIT %s",
            (user_id, limit),
        )
        rows = cur.fetchall()
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return {"history": list(reversed(rows)), "count": len(rows)}

# ------------------------------------------------------------
# 🔟  DISEASE ENDPOINTS
# ------------------------------------------------------------
@app.post("/disease/text")
def disease_from_text(req: DiseaseTextRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    llm = ChatGroq(model="llama-3.3-70b-versatile")
    lang_name = SUPPORTED_LANGS.get(req.language, "English")
    prompt = (
        f"Plant disease expert for Indian farms.\n"
        f"Crop: {req.crop_name} | Location: {req.location} | Symptoms: {req.symptoms}\n"
        f"Respond ONLY as valid JSON in {lang_name} (no markdown, no extra text):\n"
        '{{"disease_name":"...","confidence":"94%","severity":"Early/Moderate/Severe",'
        '"affected_area":"30% of leaves","treatment_steps":["step1","step2","step3","step4"],'
        '"organic_option":"...","yield_impact":"...% loss if untreated","followup_days":10,'
        '"prevention":"one prevention tip"}}'
    )
    result = llm.invoke(prompt)
    text = result.content.strip()
    start, end = text.find("{"), text.rfind("}") + 1
    if start == -1 or end == 0:
        raise HTTPException(500, "Invalid JSON from LLM")
    data = json.loads(text[start:end])
    data["crop_name"] = req.crop_name
    data["symptoms"]  = req.symptoms

    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO disease_history
            (farmer_id,district,crop_name,symptoms,disease_name,confidence,severity,
             treatment,organic_opt,yield_impact,prevention,detected_at,source)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'text')""",
            (user_id, req.district, data.get("crop_name"), data.get("symptoms"),
             data.get("disease_name"), data.get("confidence"), data.get("severity"),
             json.dumps(data.get("treatment_steps", [])), data.get("organic_option"),
             data.get("yield_impact"), data.get("prevention")),
        )
        cur.execute(
            """INSERT INTO disease_alerts (district,disease_name,crop_name,severity,alert_count,last_seen)
            VALUES (%s,%s,%s,%s,1,NOW())
            ON DUPLICATE KEY UPDATE alert_count=alert_count+1,last_seen=NOW()""",
            (req.district, data.get("disease_name"), data.get("crop_name"), data.get("severity")),
        )
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        log.warning("disease_from_text DB save failed: %s", e)
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return {**data, "language": req.language, "saved": True}

@app.post("/disease/photo")
async def disease_from_photo(
    crop_name: str = Form(default="crop"),
    language:  str = Form(default="en"),
    location:  str = Form(default="Pune, Maharashtra"),
    district:  str = Form(default="Pune"),
    photo: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    image_bytes = await photo.read()

    # Validate file size (max 10MB)
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large. Please upload an image under 10MB.")

    # Validate it's actually an image
    if not image_bytes[:4] in (b"\x89PNG", b"\xff\xd8") and image_bytes[:4] != b"RIFF":
        # Check JPEG more carefully
        if image_bytes[:2] != b"\xff\xd8":
            log.warning("Possibly non-image upload, proceeding anyway")

    image_b64   = base64.b64encode(image_bytes).decode("utf-8")
    image_name  = photo.filename or "upload.jpg"

    try:
        data = analyze_image_with_groq(image_b64, crop_name, language, location)
    except HTTPException:
        raise
    except Exception as e:
        log.error("Disease photo unexpected error: %s", e, exc_info=True)
        raise HTTPException(500, f"Photo analysis failed: {str(e)}")
    data["crop_name"] = crop_name
    data["symptoms"]  = data.get("symptoms_observed", f"Photo: {image_name}")
    data["source"]    = "photo"

    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO disease_history
            (farmer_id,district,crop_name,symptoms,disease_name,confidence,severity,
             treatment,organic_opt,yield_impact,prevention,detected_at,image_name,source)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s)""",
            (user_id, district, data.get("crop_name"), data.get("symptoms"),
             data.get("disease_name"), data.get("confidence"), data.get("severity"),
             json.dumps(data.get("treatment_steps", [])), data.get("organic_option"),
             data.get("yield_impact"), data.get("prevention"), image_name, "photo"),
        )
        cur.execute(
            """INSERT INTO disease_alerts (district,disease_name,crop_name,severity,alert_count,last_seen)
            VALUES (%s,%s,%s,%s,1,NOW())
            ON DUPLICATE KEY UPDATE alert_count=alert_count+1,last_seen=NOW()""",
            (district, data.get("disease_name"), data.get("crop_name"), data.get("severity")),
        )
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        log.warning("disease_from_photo DB save failed: %s", e)
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return {**data, "language": language, "saved": True, "image_received": True, "image_name": image_name}

@app.get("/disease/history")
def get_disease_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM disease_history WHERE farmer_id=%s ORDER BY detected_at DESC LIMIT %s",
            (current_user["id"], limit),
        )
        rows = cur.fetchall()
    finally:
        if cur: cur.close()
        if conn: conn.close()
    for r in rows:
        r["treatment_steps"] = json.loads(r.get("treatment") or "[]")
    return {"history": rows, "count": len(rows)}

@app.get("/disease/nearby-alerts")
def get_nearby_alerts(district: str = "Pune", limit: int = 5):
    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """SELECT disease_name,crop_name,severity,alert_count,last_seen
            FROM disease_alerts WHERE district=%s
            ORDER BY alert_count DESC, last_seen DESC LIMIT %s""",
            (district, limit),
        )
        rows = cur.fetchall()
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return {"alerts": rows, "district": district, "count": len(rows)}

# ------------------------------------------------------------
# 1️⃣1️⃣  OTHER ENDPOINTS
# ------------------------------------------------------------
@app.post("/alert/whatsapp")
def generate_whatsapp_alert(req: AlertRequest):
    import urllib.parse
    msg = (f"🚨 *KrishiAI रोग अलर्ट*\n\n{req.district} जिले में *{req.crop_name}* में "
           f"*{req.disease_name}* पाया गया है। गंभीरता: {req.severity}\n\n"
           "⚠️ अपने खेत की जांच करें!\n\n_KrishiAI से जानकारी_")
    return {"whatsapp_link": f"https://wa.me/?text={urllib.parse.quote(msg)}", "message_preview": msg}

@app.get("/weather")
async def get_weather(lat: float=18.5204, lon: float=73.8567, district: str="Pune", language: str="en"):
    return {
        "temp_c": 28.0, "condition": "Partly Cloudy", "humidity": 64,
        "wind_kmh": 12.0, "rain_chance": 20, "emoji": "⛅", "district": district,
        "tip": "Check wind direction before spraying pesticides.",
    }

@app.get("/market")
async def get_market(state: str="Maharashtra", language: str="en"):
    return {"prices": [
        {"crop":"Wheat",  "emoji":"🌾","mandi":"Pune Mandi",   "price":"₹2,340","change":"+₹80", "direction":"up"},
        {"crop":"Tomato", "emoji":"🍅","mandi":"Nashik Market","price":"₹1,120","change":"-₹40", "direction":"down"},
        {"crop":"Onion",  "emoji":"🧅","mandi":"Lasalgaon",    "price":"₹890", "change":"+₹120","direction":"up"},
    ], "source": "demo", "state": state}

@app.get("/schemes")
def get_schemes(language: str="en"):
    return {"schemes": [
        {"icon":"🏦","name":"PM-KISAN","description":"₹6,000/year direct support in 3 installments.",
         "benefit":"₹6,000/year","tag":"Income Support","apply_url":"https://pmkisan.gov.in"},
        {"icon":"🛡️","name":"Fasal Bima Yojana","description":"Subsidized crop insurance against drought, flood, pest.",
         "benefit":"Up to ₹2L","tag":"Insurance","apply_url":"https://pmfby.gov.in"},
        {"icon":"💧","name":"PM Krishi Sinchai Yojana","description":"Irrigation support – drip and sprinkler subsidy.",
         "benefit":"55–90% subsidy","tag":"Irrigation","apply_url":"https://pmksy.gov.in"},
        {"icon":"🌱","name":"Soil Health Card","description":"Free soil testing and recommendations every 2 years.",
         "benefit":"Free","tag":"Soil","apply_url":"https://soilhealth.dac.gov.in"},
    ], "language": language}

@app.get("/soil/analyze")
def analyze_soil(ph: float=6.9, nitrogen: int=45, phosphorus: int=30, potassium: int=180, crop: str="Wheat", language: str="en"):
    score = min(100, int((ph / 7.5) * 40 + (nitrogen / 100) * 20 + (phosphorus / 80) * 20 + (potassium / 300) * 20))
    status = "Good" if score >= 80 else "Moderate" if score >= 60 else "Poor"
    recs = []
    if ph < 6.0:  recs.append("Apply lime to raise pH")
    if ph > 7.5:  recs.append("Apply gypsum/sulphur to lower pH")
    if nitrogen < 40:   recs.append("Nitrogen is low – add urea or FYM")
    if phosphorus < 20: recs.append("Phosphorus is low – add DAP or SSP")
    if potassium < 100: recs.append("Potassium is low – add MOP")
    if not recs: recs.append("Soil health is good – maintain organic matter")
    return {"health_score": score, "status": status, "recommendations": recs,
            "fertilizer_advice": "Apply DAP 50kg/acre + Urea 25kg/acre based on soil deficit",
            "next_test_months": 6, "language": language}

@app.get("/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    conn, cur = None, None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM disease_history WHERE farmer_id=%s", (current_user["id"],))
        total = cur.fetchone()["c"]
        cur.execute("SELECT disease_name FROM disease_history WHERE farmer_id=%s ORDER BY detected_at DESC LIMIT 1", (current_user["id"],))
        recent = cur.fetchone()
        cur.execute("SELECT SUM(alert_count) AS c FROM disease_alerts")
        nearby = cur.fetchone()["c"] or 0
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return {"total_scans": total, "recent_disease": recent["disease_name"] if recent else None, "nearby_alerts": nearby}

# ------------------------------------------------------------
# 1️⃣2️⃣  PRACTICAL ENDPOINTS
# ------------------------------------------------------------
@app.post("/recommend/crop")
def recommend_crop(req: CropRecommendationRequest, current_user: dict = Depends(get_current_user)):
    mapping = {
        "kharif": ["Rice","Cotton","Soybean","Maize","Sugarcane"],
        "rabi":   ["Wheat","Chickpea","Mustard","Barley"],
        "summer": ["Pulses","Fodder","Watermelon","Vegetables"],
    }
    suggested = mapping.get(req.season.lower(), mapping["kharif"])
    return {"location": req.location, "season": req.season, "soil_type": req.soil_type,
            "recommended_crops": suggested[:4], "expected_yield_range_q_per_acre": "15–25",
            "sowing_time": f"{req.season} window", "language": req.language}

@app.post("/irrigation/recommend")
def irrigation_recommend(req: IrrigationRequest, current_user: dict = Depends(get_current_user)):
    deficit = max(0.0, 60.0 - req.soil_moisture)
    method  = "drip" if req.crop.lower() in ["tomato","cotton","sugarcane","onion","grape"] else ("flood" if req.soil_moisture < 35 else "drip")
    eff     = 0.6 if method == "flood" else 0.85
    mm      = round((deficit * 1.5) / eff, 1)
    liters  = round(mm * 4046.86, 0)
    schedule = [(datetime.date.today() + datetime.timedelta(days=7*i)).isoformat() for i in range(4)]
    return {"why": f"Soil moisture {req.soil_moisture}% is {deficit:.1f}% below optimal (60%).",
            "method": method, "amount_mm": mm, "amount_l_per_acre": liters,
            "schedule": schedule, "language": req.language}

def _parse_area(val: float, unit: str) -> float:
    return val * 2.471 if unit.lower().startswith("hec") else val

def _unit_label(unit: str) -> str:
    return "acre" if unit.lower().startswith("ac") else "hectare"

@app.post("/planner/fertilizer")
def planner_fertilizer(req: FertilizerPlannerRequest, current_user: dict = Depends(get_current_user)):
    area = _parse_area(req.area, req.unit)
    base = ([
        {"stage":"Basal","days":0,"items":[{"name":"FYM/Compost","dose":"10 t/acre","cost":4000},{"name":"Neem Cake","dose":"100 kg/acre","cost":800}]},
        {"stage":"Tillering","days":21,"items":[{"name":"Jeevamrut","dose":"500 L/acre","cost":1200}]},
    ] if req.organic_only else [
        {"stage":"Basal","days":0,"items":[{"name":"DAP","dose":"50 kg/acre","cost":1800},{"name":"MOP","dose":"25 kg/acre","cost":900}]},
        {"stage":"Tillering","days":21,"items":[{"name":"Urea","dose":"25 kg/acre","cost":500}]},
        {"stage":"Flowering","days":60,"items":[{"name":"Urea","dose":"30 kg/acre","cost":600}]},
    ])
    today, schedule, total = datetime.date.today(), [], 0.0
    for row in base:
        items = []
        for it in row["items"]:
            cost = it["cost"] * area; total += cost
            items.append({"name": it["name"], "dose": f"{it['dose']} / {_unit_label(req.unit)}", "cost_estimate": f"₹{cost:,.0f}"})
        schedule.append({"date": (today + datetime.timedelta(days=row["days"])).isoformat(),
                         "stage": row["stage"], "items": items,
                         "safety": "Use gloves/mask; avoid over-application; follow label."})
    return {"crop": req.crop, "area": f"{req.area} {_unit_label(req.unit)}",
            "total_cost_estimate": f"₹{total:,.0f}", "schedule": schedule,
            "organic_only": req.organic_only, "language": req.language}

@app.post("/market/predict")
def market_predict(req: MarketPredictionRequest, current_user: dict = Depends(get_current_user)):
    today = datetime.date.today()
    step, base, prices = (40.0 if req.crop.lower() in ["tomato","onion"] else 20.0), 1000.0, []
    for i in range(req.days):
        d = today + datetime.timedelta(days=i)
        base = max(200.0, base + (step if d.weekday() in (0,2,4) else -step))
        prices.append({"date": d.isoformat(), "price": int(base)})
    best = max(prices, key=lambda x: x["price"])["date"]
    return {"crop": req.crop, "state": req.state, "window_days": req.days,
            "prices": prices, "best_selling_window": best,
            "note": "Prediction is indicative; check live mandi rates before selling.",
            "language": req.language}

@app.post("/profit/calc")
def profit_calc(req: ProfitCalculatorRequest, current_user: dict = Depends(get_current_user)):
    area  = _parse_area(req.area, req.unit)
    total = (req.seed_cost + req.fertilizer_cost + req.pesticide_cost + req.labor_cost +
             req.irrigation_cost + req.misc_cost + req.transport_cost) * area
    expected_yield = req.expected_yield_q * area
    revenue = expected_yield * req.expected_price_per_q
    profit  = revenue - total
    roi     = round((profit / total) * 100.0, 1) if total else 0.0
    be      = round(total / expected_yield, 0) if expected_yield else 0.0
    def m(x): return f"₹{x:,.0f}"
    return {"area": f"{req.area} {_unit_label(req.unit)}", "crop": req.crop,
            "total_cost": m(total), "expected_yield_q": round(expected_yield, 1),
            "revenue": m(revenue), "profit": m(profit), "roi_percent": roi,
            "break_even_price_per_q": m(be), "language": req.language}

# ------------------------------------------------------------
# 1️⃣3️⃣  Health
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "version": "4.0.0",
            "models": ["llama-3.3-70b-versatile","llama3-70b-8192","mixtral-8x7b-32768","gemma2-9b-it"],
            "languages": SUPPORTED_LANGS,
            "features": ["streaming_chat","photo_disease","disease_history","chat_history",
                         "nearby_alerts","whatsapp_alert","crop_recommendation","irrigation_advisor",
                         "fertilizer_planner","market_prediction","profit_calculator"],
            "services": {"weather": bool(WEATHER_API_KEY), "market": bool(MARKET_API_KEY), "search": bool(TAVILY_API_KEY)}}

# ------------------------------------------------------------
# 1️⃣4️⃣  Vision helper
# ------------------------------------------------------------
# Groq vision models (in order of preference — first available wins)
VISION_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.2-90b-vision-preview",
    "llama-3.2-11b-vision-preview",
]
# Cache the working model so we don't query the API every request
_vision_model_cache: dict = {}

def _get_vision_llm():
    """Return a working vision LLM. Probes once then caches result."""
    if _vision_model_cache.get("model"):
        return ChatGroq(model=_vision_model_cache["model"]), _vision_model_cache["model"]
    try:
        from groq import Groq
        client  = Groq(api_key=GROQ_API_KEY)
        available = {m.id for m in client.models.list().data}
        for m in VISION_MODELS:
            if m in available:
                _vision_model_cache["model"] = m
                log.info("Vision model selected: %s", m)
                return ChatGroq(model=m), m
    except Exception as e:
        log.warning("Could not probe models list: %s — falling back to default", e)
    # Fallback: use first model without checking
    m = VISION_MODELS[0]
    _vision_model_cache["model"] = m
    log.info("Vision model fallback: %s", m)
    return ChatGroq(model=m), m

def _detect_mime(image_base64: str) -> str:
    """Detect image MIME type from base64 header bytes."""
    try:
        # Decode enough bytes to check magic numbers
        raw = base64.b64decode(image_base64[:16] + "==")
        if raw[:4] == b"\x89PNG":
            return "image/png"
        if raw[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if raw[:4] in (b"RIFF", b"WEBP"):
            return "image/webp"
    except Exception:
        pass
    return "image/jpeg"

def analyze_image_with_groq(image_base64: str, crop_name: str, language: str, location: str) -> dict:
    from langchain_core.messages import HumanMessage

    lang_name = SUPPORTED_LANGS.get(language, "English")
    mime      = _detect_mime(image_base64)
    image_url = f"data:{mime};base64,{image_base64}"

    try:
        vision_llm, model_used = _get_vision_llm()
        log.info("Disease photo — model: %s | crop: %s", model_used, crop_name)
    except Exception as e:
        raise HTTPException(500, f"Vision model unavailable: {e}")

    json_schema = """{
  "disease_name": "name of disease or Healthy",
  "confidence": "85%",
  "severity": "Healthy or Early or Moderate or Severe",
  "affected_area": "e.g. 40% of leaves",
  "symptoms_observed": "describe visible symptoms in detail",
  "treatment_steps": ["step 1", "step 2", "step 3", "step 4"],
  "organic_option": "organic/natural treatment option",
  "yield_impact": "e.g. 30% loss if untreated",
  "followup_days": 7,
  "prevention": "one key prevention tip"
}"""

    prompt = (
        f"You are an expert plant pathologist. Carefully examine this crop image.\n"
        f"Crop: {crop_name} | Location: {location}\n\n"
        f"If this is NOT a plant/crop image, respond with exactly: NOT_A_PLANT\n\n"
        f"If it IS a plant, diagnose any disease or confirm it is healthy.\n"
        f"Respond ONLY in {lang_name} with valid JSON matching this exact structure "
        f"(no markdown, no code fences, no extra text):\n{json_schema}"
    )

    try:
        resp = vision_llm.invoke([HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text",      "text": prompt},
        ])])
    except Exception as e:
        log.error("Vision invoke error: %s", e, exc_info=True)
        err = str(e)
        if "429" in err or "rate" in err.lower():
            raise HTTPException(429, "Rate limit reached. Please wait 30 seconds and try again.")
        if "404" in err or "model" in err.lower():
            # Clear cache so next request re-probes
            _vision_model_cache.clear()
            raise HTTPException(500, f"Vision model not available ({model_used}). Try again in a moment.")
        raise HTTPException(500, f"Photo analysis failed: {err}")

    raw = resp.content.strip()
    log.info("Vision raw response (first 300 chars): %s", raw[:300])

    # Handle non-plant response
    if "NOT_A_PLANT" in raw.upper():
        raise HTTPException(400, "Image does not appear to show a plant or crop. Please upload a clear crop photo.")

    # Strip markdown fences if model added them
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    # Extract JSON object
    s = raw.find("{")
    e = raw.rfind("}") + 1
    if s == -1 or e == 0:
        log.error("No JSON in vision response: %s", raw[:500])
        raise HTTPException(500, "Vision model returned unexpected response. Please try again.")

    try:
        result = json.loads(raw[s:e])
    except json.JSONDecodeError as je:
        # Try to fix common issues like trailing commas
        import re
        cleaned = re.sub(r",\s*([}\]])", r"\1", raw[s:e])
        try:
            result = json.loads(cleaned)
        except Exception:
            log.error("JSON parse failed: %s | raw: %s", je, raw[s:e][:300])
            raise HTTPException(500, "Could not parse AI response. Please try again.")

    # Ensure required fields exist with defaults
    result.setdefault("disease_name",    "Unknown")
    result.setdefault("confidence",      "—")
    result.setdefault("severity",        "—")
    result.setdefault("affected_area",   "—")
    result.setdefault("treatment_steps", ["Consult a local agronomist"])
    result.setdefault("organic_option",  "—")
    result.setdefault("yield_impact",    "—")
    result.setdefault("followup_days",   7)
    result.setdefault("prevention",      "—")

    return result




# ------------------------------------------------------------
# Sarvam TTS Proxy — Indian voices ke liye
# Browser directly Sarvam call nahi kar sakta (CORS block)
# So backend proxy karta hai
# ------------------------------------------------------------
import httpx, re as _re

class TTSRequest(BaseModel):
    text: str
    language: str = "hi"

SARVAM_LANG_MAP = {
    "hi": ("hi-IN", "meera"), "mr": ("mr-IN", "meera"),
    "en": ("en-IN", "anushka"), "pa": ("pa-IN", "anushka"),
    "gu": ("gu-IN", "anushka"), "ta": ("ta-IN", "anushka"),
    "te": ("te-IN", "anushka"), "kn": ("kn-IN", "anushka"),
    "bn": ("bn-IN", "anushka"), "bh": ("hi-IN", "anushka"),
}

@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    if not SARVAM_API_KEY:
        raise HTTPException(status_code=503, detail="SARVAM_API_KEY not set in .env")
    clean = _re.sub(r'\*\*|\*|_|`|>|#+\s', '', req.text)
    clean = _re.sub(r'\n+', '. ', clean).strip()[:500]
    lang_code, speaker = SARVAM_LANG_MAP.get(req.language, ("hi-IN", "meera"))
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={"Content-Type":"application/json","api-subscription-key":SARVAM_API_KEY},
                json={"inputs":[clean],"target_language_code":lang_code,"speaker":speaker,
                      "model":"bulbul:v3","pace":0.9,"output_audio_codec":"wav","speech_sample_rate":22050}
            )
        if res.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Sarvam error {res.status_code}: {res.text[:200]}")
        data = res.json()
        audio_b64 = data.get("audios",[None])[0]
        if not audio_b64:
            raise HTTPException(status_code=502, detail="Sarvam returned no audio")
        return {"audio_base64": audio_b64, "format": "wav", "language": lang_code, "speaker": speaker}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Sarvam timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------
# 1️⃣5️⃣  Run
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="127.0.0.1", port=9999, reload=True)
