# frontend.py — KrishiAI v4.1
# New in v4.1: Voice-to-Voice AI · Groq Whisper STT · gTTS TTS · Energetic Welcome Greeting
import streamlit as st
import streamlit.components.v1 as components
import requests, json, datetime, os, base64, re, tempfile
from io import BytesIO

API_BASE = "http://127.0.0.1:9999"

st.set_page_config(page_title="KrishiAI", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")

LANGS = {
    "en": {"name": "English",   "flag": "🇬🇧", "tts": "en-US"},
    "hi": {"name": "हिन्दी",   "flag": "🇮🇳", "tts": "hi-IN"},
    "mr": {"name": "मराठी",    "flag": "🌿",   "tts": "mr-IN"},
    "pa": {"name": "ਪੰਜਾਬੀ",   "flag": "🇮🇳", "tts": "pa-IN"},
    "gu": {"name": "ગુજરાતી",  "flag": "🇮🇳", "tts": "gu-IN"},
    "ta": {"name": "தமிழ்",    "flag": "🇮🇳", "tts": "ta-IN"},
    "te": {"name": "తెలుగు",   "flag": "🇮🇳", "tts": "te-IN"},
    "kn": {"name": "ಕನ್ನಡ",    "flag": "🇮🇳", "tts": "kn-IN"},
    "bn": {"name": "বাংলা",    "flag": "🇧🇩", "tts": "bn-IN"},
    "bh": {"name": "भोजपुरी",  "flag": "🌾",   "tts": "hi-IN"},  # Bhojpuri → Hindi TTS
}

# gTTS language codes
TTS_LANG_MAP = {
    "en":"en","hi":"hi","mr":"mr","pa":"pa","gu":"gu",
    "ta":"ta","te":"te","kn":"kn","bn":"bn","bh":"hi",
}

# Energetic farmer greeting per language
ENERGY_PREFIX = {
    "hi": "अरे भाई! सुनो! ",
    "mr": "अरे दादा! ऐका! ",
    "pa": "ਓਏ ਯਾਰ! ਸੁਣੋ! ",
    "gu": "અરે ભાઈ! સાંભળો! ",
    "ta": "அண்ணா! கேளுங்க! ",
    "te": "అన్నా! వినండి! ",
    "kn": "ಅಣ್ಣ! ಕೇಳಿ! ",
    "bn": "ভাই! শোনো! ",
    "bh": "अरे भाई! सुनऽ! ",
    "en": "Hey farmer! Listen up! ",
}

UI = dict(
    app_tagline="Smart farming powered by AI",
    login_title="KrishiAI",
    register_btn="Create Account",
    login_btn="Login",
    logout_btn="Logout",
    dashboard="Dashboard", chat="AI Advisor", disease="Disease Detector",
    market="Market Prices", schemes="Gov Schemes", soil="Soil Health",
    irrigation="Irrigation", planner="Fertilizer Planner", predict="Price Forecast",
    profit="Profit Calculator", analytics="Analytics", calendar="Calendar",
    voice_page="🎙️ Voice AI",
    voice_toggle="🔊 Voice", send="Send ➤", type_q="Ask your farming question...",
    analyzing="Analyzing…", disease_title="Disease Detector",
    upload_photo="📷 Upload or Take Photo", symptoms_label="Or describe symptoms:",
    analyze_btn="🔬 Analyse", result_tab="Result", history_tab="History",
    nearby_tab="Nearby Alerts", no_history="No scans yet.", no_alerts="No alerts in your area.",
    confidence="Confidence", severity="Severity", affected="Affected Area",
    treatment="Treatment Steps", organic="Organic Option", yield_impact="Yield Impact",
    prevention="Prevention", soil_title="Soil Health", analyze_soil="🧪 Analyse Soil",
    market_title="Mandi Prices", apply_online="Apply Online →", crop_label="Select Crop",
    schemes_title="Government Schemes",
)

def t(key): return UI.get(key, key)

# ── Session state ─────────────────────────────────────────────────────────────
DEFAULTS = dict(
    screen="login", jwt=None, user=None, chat_msgs=[], dis_result=None,
    soil_data=None, voice_on=False, last_reply="", page="dashboard",
    is_typing=False, auth_error="", auth_success="",
    welcomed=False, voice_history=[], chat_voice_text="", disease_voice_text="",
)
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Outfit:wght@300;400;500;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;}
html,body,[class*="css"]{font-family:'Outfit',sans-serif!important;background:#060a0d!important;color:#e4edf4!important;cursor:default!important;}
input,textarea,select{cursor:text!important;caret-color:#aaff44!important;}
button,[role="button"],a{cursor:pointer!important;}
#MainMenu,footer{visibility:hidden;height:0!important;}
header[data-testid="stHeader"],[data-testid="stToolbar"],.stAppDeployButton,div[data-testid="stDecoration"]{display:none!important;}
.block-container{padding:1.2rem 1.6rem!important;max-width:100%!important;padding-top:0.6rem!important;}
section[data-testid="stSidebar"]{background:rgba(6,10,13,.97)!important;border-right:1px solid rgba(255,255,255,.06)!important;backdrop-filter:blur(24px)!important;}
section[data-testid="stSidebar"] *{color:#e4edf4!important;}
[data-testid="metric-container"]{background:rgba(255,255,255,.03)!important;border:1px solid rgba(255,255,255,.06)!important;border-radius:12px!important;padding:10px 14px!important;}
body::before{content:'';position:fixed;width:700px;height:700px;background:radial-gradient(circle,rgba(170,255,68,.11) 0%,transparent 70%);border-radius:50%;top:-250px;left:-150px;animation:aur1 13s ease-in-out infinite;pointer-events:none;z-index:0;}
body::after{content:'';position:fixed;width:600px;height:600px;background:radial-gradient(circle,rgba(0,212,170,.09) 0%,transparent 70%);border-radius:50%;bottom:-180px;right:-120px;animation:aur2 16s ease-in-out infinite;pointer-events:none;z-index:0;}
.blob-amber{position:fixed;width:450px;height:450px;background:radial-gradient(circle,rgba(255,181,71,.07),transparent 70%);border-radius:50%;top:45%;left:55%;transform:translate(-50%,-50%);animation:aur3 19s ease-in-out infinite;pointer-events:none;z-index:0;}
@keyframes aur1{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(70px,50px) scale(1.1)}66%{transform:translate(-40px,70px) scale(.95)}}
@keyframes aur2{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(-90px,-60px) scale(1.15)}}
@keyframes aur3{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:.8}50%{transform:translate(-42%,-62%) scale(1.2);opacity:1}}
@keyframes pageEnter{from{opacity:0;transform:translateX(28px)}to{opacity:1;transform:translateX(0)}}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
@keyframes welcomePulse{0%{box-shadow:0 0 0 0 rgba(170,255,68,.5)}70%{box-shadow:0 0 0 20px rgba(170,255,68,0)}100%{box-shadow:0 0 0 0 rgba(170,255,68,0)}}
.k-card{background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.075);border-radius:20px;padding:22px;margin-bottom:14px;backdrop-filter:blur(14px);position:relative;overflow:hidden;transition:all .3s ease;}
.k-card:hover{border-color:rgba(170,255,68,.14);box-shadow:0 10px 36px rgba(0,0,0,.32);transform:translateY(-1px);}
.sec-head{font-family:'Syne',sans-serif;font-size:21px;font-weight:700;margin-bottom:5px;}
.sec-sub{font-size:12px;color:#7a93a8;margin-bottom:18px;}
.chip{display:inline-block;font-size:10px;font-weight:600;padding:3px 10px;border-radius:100px;margin:3px;}
.chip-lime{background:rgba(170,255,68,.12);color:#aaff44;border:1px solid rgba(170,255,68,.2);}
.chip-amber{background:rgba(255,181,71,.12);color:#ffb547;border:1px solid rgba(255,181,71,.2);}
.chip-rose{background:rgba(255,107,107,.10);color:#ff6b6b;border:1px solid rgba(255,107,107,.18);}
.chip-teal{background:rgba(0,212,170,.10);color:#00d4aa;border:1px solid rgba(0,212,170,.18);}
.chip-sky{background:rgba(96,184,255,.10);color:#60b8ff;border:1px solid rgba(96,184,255,.18);}
.lime{color:#aaff44;}.amber{color:#ffb547;}.teal{color:#00d4aa;}.sky{color:#60b8ff;}.rose{color:#ff6b6b;}
button[kind="primary"]{background:linear-gradient(135deg,#aaff44,#55cc00)!important;color:#0a1a00!important;border:none!important;font-weight:700!important;border-radius:12px!important;box-shadow:0 4px 16px rgba(170,255,68,.22)!important;transition:all .22s!important;}
button[kind="primary"]:hover{transform:translateY(-2px)!important;box-shadow:0 8px 28px rgba(170,255,68,.38)!important;}
button[kind="secondary"]{background:rgba(255,255,255,.04)!important;border:1px solid rgba(255,255,255,.1)!important;color:#e4edf4!important;border-radius:12px!important;transition:all .2s!important;}
.msg-bot{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:16px 16px 16px 4px;padding:14px 18px;margin:8px 0;font-size:14px;line-height:1.75;backdrop-filter:blur(8px);animation:fadeUp .3s ease;}
.msg-bot-latest::after{content:'▋';display:inline-block;color:#aaff44;animation:blink .9s step-end infinite;margin-left:3px;font-size:11px;vertical-align:middle;}
.msg-user{background:linear-gradient(135deg,rgba(170,255,68,.09),rgba(0,212,170,.05));border:1px solid rgba(170,255,68,.17);border-radius:16px 16px 4px 16px;padding:14px 18px;margin:8px 0;font-size:14px;text-align:right;animation:fadeUp .3s ease;}
.res-card{background:rgba(255,181,71,.04);border:1px solid rgba(255,181,71,.18);border-radius:16px;padding:18px;backdrop-filter:blur(8px);}
.res-name{font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:#ffb547;}
.hist-item{display:flex;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:13px;}
.hist-name{font-weight:600;color:#ffb547;}.hist-meta{color:#7a93a8;font-size:11px;margin-top:3px;}
.na-item{background:rgba(255,107,107,.04);border:1px solid rgba(255,107,107,.14);border-radius:12px;padding:14px;margin-bottom:8px;}
.na-name{color:#ff6b6b;font-weight:600;}
.logo-icon{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#aaff44,#55aa00);display:flex;align-items:center;justify-content:center;font-size:22px;box-shadow:0 4px 18px rgba(170,255,68,.28);flex-shrink:0;}
.soil-bar-wrap{background:rgba(255,255,255,.06);border-radius:6px;height:9px;margin-top:7px;}
.soil-bar{height:9px;border-radius:6px;background:linear-gradient(90deg,#00d4aa,#aaff44);transition:width .8s ease;}
.auth-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);border-radius:24px;padding:40px 36px;backdrop-filter:blur(18px);animation:fadeUp .5s ease;width:100%;max-width:480px;}
.auth-logo{text-align:center;margin-bottom:32px;}
.auth-logo-icon{width:72px;height:72px;border-radius:22px;background:linear-gradient(135deg,#aaff44,#55aa00);display:inline-flex;align-items:center;justify-content:center;font-size:36px;box-shadow:0 8px 28px rgba(170,255,68,.35);margin-bottom:14px;}
.auth-title{font-family:'Syne',sans-serif;font-size:32px;font-weight:800;color:#aaff44;}
.auth-sub{font-size:13px;color:#7a93a8;margin-top:4px;}
.voice-bubble-q{background:rgba(170,255,68,.06);border:1px solid rgba(170,255,68,.18);border-radius:16px 16px 16px 4px;padding:14px 18px;margin:8px 0;font-size:15px;}
.voice-bubble-a{background:rgba(0,183,171,.06);border:1px solid rgba(0,183,171,.18);border-radius:16px 16px 4px 16px;padding:14px 18px;margin:8px 0;font-size:15px;line-height:1.7;}
.welcome-banner{background:linear-gradient(135deg,#0d2b0d,#0a1f1a);border:2px solid #aaff44;border-radius:20px;padding:28px;text-align:center;margin-bottom:20px;animation:welcomePulse 1.5s ease-out;}
</style>
<div class="blob-amber"></div>
""", unsafe_allow_html=True)

# ── API helpers ───────────────────────────────────────────────────────────────
def api_headers():
    h = {"Content-Type": "application/json"}
    if st.session_state.jwt:
        h["Authorization"] = f"Bearer {st.session_state.jwt}"
    return h

def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, headers=api_headers(), timeout=10)
        if not r.ok:
            try: detail = r.json().get("detail", r.text)
            except: detail = r.text
            return None, f"Error {r.status_code}: {detail}"
        return r.json(), None
    except Exception as e:
        return None, str(e)

def api_post(path, data=None, files=None):
    try:
        if files:
            h = {"Authorization": f"Bearer {st.session_state.jwt}"} if st.session_state.jwt else {}
            r = requests.post(f"{API_BASE}{path}", data=data, files=files, headers=h, timeout=60)
        else:
            r = requests.post(f"{API_BASE}{path}", json=data, headers=api_headers(), timeout=30)
        if not r.ok:
            try: detail = r.json().get("detail", r.text)
            except: detail = r.text
            return None, f"Error {r.status_code}: {detail}"
        return r.json(), None
    except Exception as e:
        return None, str(e)

def user_lang():
    if st.session_state.get("chat_lang"):
        return st.session_state.chat_lang
    if st.session_state.user:
        langs = st.session_state.user.get("languages", ["en"])
        return "en" if "en" in langs else (langs[0] if langs else "en")
    return "en"

# ══════════════════════════════════════════════════════════════════════════════
# VOICE ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _clean_for_tts(text: str) -> str:
    """Remove markdown, emojis, limit length for natural TTS."""
    clean = re.sub(r'[*_`#\[\]()\->]', '', text)
    clean = re.sub(r'https?://\S+', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:500]

def _play_audio_b64(audio_b64: str):
    """Inject autoplay audio into the page."""
    st.markdown(f"""
    <audio autoplay style="display:none">
        <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)

def speak_gtts(text: str, language: str):
    """Convert text to speech using gTTS and auto-play."""
    try:
        from gtts import gTTS
        tts_lang = TTS_LANG_MAP.get(language, "hi")
        clean = _clean_for_tts(text)
        if not clean:
            return
        buf = BytesIO()
        gTTS(text=clean, lang=tts_lang, slow=False).write_to_fp(buf)
        buf.seek(0)
        _play_audio_b64(base64.b64encode(buf.read()).decode())
    except Exception as e:
        st.warning(f"🔊 TTS error: {e}")

def speak(text: str):
    """Legacy browser TTS (Web Speech API) — used when voice_on toggle is ON."""
    if not text or not st.session_state.voice_on:
        return
    tts = LANGS.get(user_lang(), LANGS["en"])["tts"]
    payload = json.dumps(str(text)[:500])
    components.html(f"""<script>(function(){{
        var sp=window.parent.speechSynthesis||window.speechSynthesis;
        if(!sp)return; sp.cancel();
        var u=new(window.parent.SpeechSynthesisUtterance||SpeechSynthesisUtterance)({payload});
        u.lang='{tts}';u.rate=0.85;u.pitch=1.0;
        var v=sp.getVoices();
        if(v.length===0){{sp.onvoiceschanged=function(){{sp.speak(u);}};}}else{{sp.speak(u);}}
    }})();</script>""", height=1)

def transcribe_audio(audio_bytes: bytes) -> str:
    """Send audio bytes to Groq Whisper and return transcript."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        st.error("GROQ_API_KEY missing in .env")
        return ""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp = f.name
    try:
        import httpx
        with open(tmp, "rb") as f:
            r = httpx.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {groq_key}"},
                data={"model": "whisper-large-v3"},
                files={"file": ("audio.wav", f, "audio/wav")},
                timeout=25,
            )
        if r.status_code == 200:
            return r.json().get("text", "").strip()
        else:
            st.error(f"Whisper error {r.status_code}: {r.text[:200]}")
            return ""
    except Exception as e:
        st.error(f"STT error: {e}")
        return ""
    finally:
        os.unlink(tmp)

def get_ai_voice_response(question: str, language: str, farmer_name: str, location: str) -> str:
    """Get a short, energetic AI response optimised for voice output."""
    lang_name = LANGS.get(language, LANGS["en"])["name"]
    prefix    = ENERGY_PREFIX.get(language, "")
    system = (
        f"You are KrishiAI — a high-energy, warm farming advisor speaking to {farmer_name} in {location}.\n"
        f"CRITICAL: Respond ONLY in {lang_name}. Max 3-4 sentences — this is a voice reply.\n"
        f"Start your reply with '{prefix}' to sound energetic and friendly.\n"
        f"Give ONE clear, specific action the farmer can take TODAY.\n"
        f"Use very simple words. End with a short encouraging phrase."
    )
    try:
        import groq as groq_sdk
        client = groq_sdk.Groq(api_key=os.getenv("GROQ_API_KEY", ""))
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": question},
            ],
            max_tokens=200,
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"माफ करो भाई, कुछ गड़बड़ हो गई। फिर कोशिश करो। ({e})"

def play_welcome_greeting(farmer_name: str, lang: str = "hi"):
    """Play energetic welcome audio + show animated banner. Runs only once per session."""
    greetings = {
        "hi": f"KrishiAI mein aapka swaaaaagat hai! Jai Kisan! Kya haal hai {farmer_name} bhai! Aaj hum milke kheti ko aur behtar banayenge!",
        "mr": f"KrishiAI madhe aapale swaaaagat ahe! Jai Kisan! Kasa aahaat {farmer_name} dada! Aaj aaplyala shetat kaam karayche ahe!",
        "pa": f"KrishiAI wich tuhada swaaaagat hai! Jai Kisan! Ki haal hai {farmer_name} veere! Aj assi kheti nu hor changi kariye!",
        "gu": f"KrishiAI maa tamaro swaaaagat chhe! Jai Kisan! Kem chho {farmer_name} bhai! Aaj aaude kheti ne sundar banaaviye!",
        "ta": f"KrishiAI il ungal swaaagatam! Jai Kisan! Eppadi irukkingal {farmer_name} anna! Indru vivasayam seyalaam!",
        "te": f"KrishiAI lo mee swaaagatam! Jai Kisan! Ela unnaru {farmer_name} anna! Ee roju vallakadu pani cheddham!",
        "kn": f"KrishiAI ge nimage swaaaagata! Jai Kisan! Hege iddira {farmer_name} anna! Idu naavirali krushi madona!",
        "bn": f"KrishiAI te aapnar swaaaagoto! Jai Kisan! Kemon aachhen {farmer_name} bhai! Aaj aamar shathe chashi korbo!",
        "bh": f"KrishiAI mein aapan ke swaaaagat baa! Jai Kisan! Kaise bani {farmer_name} bhai! Aaj kheti ke baat kari!",
        "en": f"Weeeelcome to KrishiAI! Jai Kisan! How are you {farmer_name}! Today we grow stronger together!",
    }
    text = greetings.get(lang, greetings["hi"])

    # Play audio
    speak_gtts(text, lang)

    # Animated banner
    st.markdown(f"""
    <div class="welcome-banner">
        <div style="font-size:52px;margin-bottom:8px">🌾🎉🌾</div>
        <div style="font-family:'Syne',sans-serif;font-size:24px;font-weight:800;color:#aaff44">
            KrishiAI में आपका स्वागत है!
        </div>
        <div style="font-size:16px;color:#e4edf4;margin-top:10px">
            नमस्ते <b>{farmer_name}</b> जी! आज का दिन शुभ हो! 🙏
        </div>
        <div style="font-size:13px;color:#7a93a8;margin-top:8px">
            Jai Kisan 🌱 Jai Hind 🇮🇳
        </div>
    </div>
    """, unsafe_allow_html=True)

def mic_component():
    """Browser Web Speech API mic button (legacy voice toggle)."""
    if not st.session_state.user: return
    tl = LANGS.get(user_lang(), LANGS["en"])["tts"]
    components.html(f"""
    <style>
    .mb{{background:linear-gradient(135deg,#aaff44,#55cc00);border:none;border-radius:50%;
    width:44px;height:44px;font-size:19px;cursor:pointer;display:flex;align-items:center;
    justify-content:center;box-shadow:0 4px 16px rgba(170,255,68,.35);transition:all .3s;}}
    .mb.rec{{background:linear-gradient(135deg,#ff6b6b,#cc2222);box-shadow:0 4px 20px rgba(255,107,107,.5);animation:pulse .8s infinite;}}
    @keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.1)}}}}
    .ms{{font-size:10px;color:#7a93a8;text-align:center;margin-top:3px;}}
    </style>
    <div><button class="mb" id="mb" onclick="tog()">🎙</button>
    <div class="ms" id="ms">Tap</div></div>
    <script>
    var rc=null,ir=false;
    function ini(){{
      var S=window.SpeechRecognition||window.webkitSpeechRecognition;
      if(!S){{document.getElementById('ms').innerText='❌ N/A';return null;}}
      var r=new S();r.continuous=false;r.interimResults=false;r.lang='{tl}';
      r.onstart=function(){{document.getElementById("mb").classList.add("rec");document.getElementById("mb").innerText="⏹";document.getElementById("ms").innerText="🎙 Listening...";}};
      r.onresult=function(e){{var txt=Array.from(e.results).map(function(x){{return x[0].transcript;}}).join(" ").trim();document.getElementById("ms").innerText="✓ "+txt.substring(0,18)+"...";var url=new URL(window.parent.location.href);url.searchParams.set("voice_input",txt);window.parent.location.replace(url.toString());}};
      r.onerror=function(e){{document.getElementById("ms").innerText="⚠ "+e.error;rc=null;ir=false;document.getElementById("mb").classList.remove("rec");document.getElementById("mb").innerText="🎙";}};
      r.onend=function(){{ir=false;document.getElementById("mb").classList.remove("rec");document.getElementById("mb").innerText="🎙";}};
      return r;
    }}
    function tog(){{if(!rc)rc=ini();if(!rc)return;if(ir){{rc.stop();ir=false;}}else{{try{{rc.start();ir=true;}}catch(e){{document.getElementById("ms").innerText="⚠ "+e.message;}}}}}}
    </script>""", height=70)

def groq_mic_button(key: str) -> str | None:
    """Streamlit mic recorder → Groq Whisper transcription. Returns text or None."""
    try:
        from streamlit_mic_recorder import mic_recorder
        audio = mic_recorder(
            start_prompt="🎤 Tap to speak",
            stop_prompt="⏹ Stop",
            key=key,
            use_container_width=True,
        )
        if audio and audio.get("bytes"):
            with st.spinner("🧠 Transcribing…"):
                return transcribe_audio(audio["bytes"])
    except ImportError:
        st.caption("Install `streamlit-mic-recorder` for Whisper mic")
    except Exception as e:
        st.warning(f"Mic error: {e}")
    return None

def inject_anim():
    components.html("""<script>(function(){var a=0;function r(){var d=window.parent.document,
    e=d.querySelector('.main .block-container');
    if(e){e.style.animation='none';e.offsetHeight;e.style.animation='pageEnter .38s cubic-bezier(.25,.46,.45,.94) both';}
    else if(++a<10)setTimeout(r,60);}r();})();</script>""", height=0)

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN / REGISTER
# ══════════════════════════════════════════════════════════════════════════════
def screen_login():
    inject_anim()
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""<div class="auth-card">
          <div class="auth-logo">
            <div class="auth-logo-icon">🌿</div>
            <div class="auth-title">KrishiAI</div>
            <div class="auth-sub">Smart farming powered by AI</div>
          </div>
        </div>""", unsafe_allow_html=True)

        if st.session_state.auth_error:
            st.error(st.session_state.auth_error); st.session_state.auth_error = ""
        if st.session_state.auth_success:
            st.success(st.session_state.auth_success); st.session_state.auth_success = ""

        tab_login, tab_signup = st.tabs(["🔑  Login", "🌱  Register"])

        with tab_login:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                li_email = st.text_input("📧 Email", placeholder="your@email.com")
                li_phone = st.text_input("📱 Phone (if no email)", placeholder="9876543210")
                li_pw    = st.text_input("🔒 Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Login →", type="primary", use_container_width=True)
            if submitted:
                email, phone, pw = li_email.strip(), li_phone.strip(), li_pw
                if not email and not phone:
                    st.error("❌ Enter your email or phone number.")
                elif not pw:
                    st.error("❌ Enter your password.")
                else:
                    payload = {"password": pw}
                    if email: payload["email"] = email
                    if phone: payload["phone"] = phone
                    data, err = api_post("/auth/login", payload)
                    if err:
                        st.error(f"❌ {err}")
                    else:
                        st.session_state.jwt = data["access_token"]
                        me, _ = api_get("/auth/me")
                        st.session_state.user = me if me else {"languages": ["en","hi","mr"], "name": "Farmer"}
                        st.session_state.chat_lang  = "en"
                        st.session_state.screen     = "app"
                        st.session_state.welcomed   = False  # reset so greeting plays
                        st.rerun()

        with tab_signup:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=False):
                rg_name  = st.text_input("👤 Full Name *",              placeholder="Ramesh Kumar")
                rg_email = st.text_input("📧 Email *",                  placeholder="your@email.com")
                rg_phone = st.text_input("📱 Phone Number *",           placeholder="9876543210")
                rg_pw    = st.text_input("🔒 Password * (min 6 chars)", placeholder="••••••••", type="password")
                rg_loc   = st.text_input("📍 District / Location",      placeholder="Pune, Maharashtra")
                st.markdown("<div style='margin:14px 0 8px;font-size:13px;color:#7a93a8'>🌐 AI Response Languages <span style='color:#ff6b6b;font-size:11px'>(Hindi & Marathi required)</span></div>", unsafe_allow_html=True)
                lang_cols = st.columns(5)
                lang_checks = {}
                for i, (code, info) in enumerate(LANGS.items()):
                    with lang_cols[i % 5]:
                        if code in ("hi","mr"):
                            st.checkbox(f"{info['flag']} {info['name']}", value=True, disabled=True, key=f"rg_lck_{code}")
                            lang_checks[code] = True
                        else:
                            lang_checks[code] = st.checkbox(f"{info['flag']} {info['name']}", value=False, key=f"rg_lck_{code}")
                submitted_reg = st.form_submit_button("Create Account →", type="primary", use_container_width=True)
            if submitted_reg:
                name  = rg_name.strip()
                email = rg_email.strip()
                phone = rg_phone.strip()
                pw    = rg_pw
                loc   = rg_loc.strip()
                chosen_langs = {code for code, checked in lang_checks.items() if checked} | {"hi","mr"}
                if not name:
                    st.error("❌ Full name is required.")
                elif not email and not phone:
                    st.error("❌ Provide at least an email or phone number.")
                elif not pw or len(pw) < 6:
                    st.error("❌ Password must be at least 6 characters.")
                else:
                    payload = {"name": name, "email": email or None, "phone": phone or None,
                               "password": pw, "location": loc or None, "languages": list(chosen_langs)}
                    data, err = api_post("/auth/register", payload)
                    if err:
                        st.error(f"❌ {err}")
                    else:
                        st.session_state.jwt    = data["access_token"]
                        st.session_state.user   = {"languages": list(chosen_langs), "name": name}
                        st.session_state.screen = "app"
                        st.session_state.welcomed = False
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def sidebar():
    with st.sidebar:
        st.markdown("""<div style="display:flex;align-items:center;gap:12px;padding:14px 0 22px">
          <div class="logo-icon">🌿</div>
          <div>
            <div style="font-family:'Syne',sans-serif;font-size:17px;font-weight:800;color:#aaff44">KrishiAI</div>
            <div style="font-size:11px;color:#7a93a8">v4.1 · Groq AI · Voice</div>
          </div>
        </div>""", unsafe_allow_html=True)

        if st.session_state.user:
            name = st.session_state.user.get("name","Farmer")
            st.markdown(f"""<div style="background:rgba(170,255,68,.06);border:1px solid rgba(170,255,68,.15);
            border-radius:10px;padding:8px 12px;font-size:12px;margin-bottom:10px;color:#aaff44">
            👨‍🌾 {name}</div>""", unsafe_allow_html=True)

        ok = False
        try:
            health, _ = api_get("/health")
            ok = health and health.get("status") == "ok"
        except: pass
        col  = "#aaff44" if ok else "#ff6b6b"
        bg   = "rgba(170,255,68,.06)" if ok else "rgba(255,107,107,.06)"
        bd   = "rgba(170,255,68,.18)" if ok else "rgba(255,107,107,.18)"
        st.markdown(f"""<div style="background:{bg};border:1px solid {bd};border-radius:10px;
            padding:7px 12px;font-size:11px;margin-bottom:14px;color:{col}">
            {'🟢 Backend Online' if ok else '🔴 Backend Offline – start backend.py'}</div>""", unsafe_allow_html=True)

        pages = [
            ("dashboard","⊞",t("dashboard")),  ("chat","💬",t("chat")),
            ("disease","🔬",t("disease")),       ("voice","🎙️",t("voice_page")),
            ("market","📈",t("market")),         ("schemes","🏛",t("schemes")),
            ("soil","🧪",t("soil")),             ("irrigation","💧",t("irrigation")),
            ("planner","🌱",t("planner")),       ("predict","📉",t("predict")),
            ("profit","💰",t("profit")),         ("analytics","📊",t("analytics")),
            ("calendar","📅",t("calendar")),
        ]
        for pid, icon, label in pages:
            active = st.session_state.page == pid
            if st.button(f"{icon}  {label}", key=f"nav_{pid}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.page = pid
                st.rerun()

        st.markdown("<div style='height:1px;background:rgba(255,255,255,.06);margin:14px 0'></div>", unsafe_allow_html=True)
        st.session_state.voice_on = st.toggle(t("voice_toggle"), value=st.session_state.voice_on, key="voice_switch")
        if st.button(t("logout_btn"), use_container_width=True, key="do_logout"):
            for k in list(st.session_state.keys()):
                st.session_state[k] = DEFAULTS.get(k, None)
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    inject_anim()

    # ── Welcome greeting (plays once per login) ───────────────────────────────
    if not st.session_state.welcomed and st.session_state.user:
        name = st.session_state.user.get("name", "Kisan")
        lang = user_lang()
        play_welcome_greeting(name, lang)
        st.session_state.welcomed = True

    name = st.session_state.user.get("name","Farmer") if st.session_state.user else "Farmer"
    st.markdown(f"<div class='sec-head'>⊞ Good day, {name}! 🌿</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Crops", "4", "+1")
    c2.metric("Field Temp", "28°C", "-2°C")
    c3.metric("Soil Moisture", "62%", "+4%")
    c4.metric("Est. Revenue", "₹84k", "+₹6k")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    wc, mc = st.columns(2)
    with wc:
        w, _ = api_get("/weather")
        if w:
            st.markdown(f"""<div class="k-card">
            <div style="font-size:13px;color:#7a93a8;margin-bottom:8px">🌤 Weather · {w.get('district','')}</div>
            <div style="font-family:'Syne',sans-serif;font-size:52px;font-weight:800;color:#60b8ff;line-height:1">{w.get('temp_c',0):.0f}°C</div>
            <div style="font-size:14px;color:#7a93a8;margin-top:4px">{w.get('emoji','')} {w.get('condition','')} · 💧{w.get('humidity',0)}% · 💨{w.get('wind_kmh',0)} km/h</div>
            <div style="background:rgba(170,255,68,.06);border:1px solid rgba(170,255,68,.12);border-radius:10px;padding:10px 14px;font-size:13px;color:#aaff44;margin-top:12px">💡 {w.get('tip','')}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div class='k-card'><div style='color:#7a93a8;font-size:13px'>🌤 Weather unavailable</div></div>", unsafe_allow_html=True)
    with mc:
        mk, _ = api_get("/market")
        if mk:
            rows_html = "".join([
                f"<div style='display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.05)'>"
                f"<span>{p['emoji']} {p['crop']}</span><span style='font-weight:700'>{p['price']}/q</span>"
                f"<span style='color:{'#aaff44' if p['direction']=='up' else '#ff6b6b'}'>{p['change']}</span></div>"
                for p in mk.get("prices",[])
            ])
            st.markdown(f"<div class='k-card'><div style='font-size:13px;color:#7a93a8;margin-bottom:12px'>📊 Live Mandi Prices</div>{rows_html}</div>", unsafe_allow_html=True)

    stats, _ = api_get("/stats")
    if stats:
        s1, s2, s3 = st.columns(3)
        s1.metric("Total Scans",   stats.get("total_scans", 0))
        s2.metric("Last Disease",  stats.get("recent_disease") or "—")
        s3.metric("Nearby Alerts", stats.get("nearby_alerts", 0))

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:13px;color:#7a93a8;margin-bottom:10px'>⚡ Quick Actions</div>", unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    if q1.button("🔬 Scan Disease",    use_container_width=True): st.session_state.page="disease"; st.rerun()
    if q2.button("💬 Ask AI Advisor",  use_container_width=True): st.session_state.page="chat";    st.rerun()
    if q3.button("🎙️ Voice AI",        use_container_width=True): st.session_state.page="voice";   st.rerun()
    if q4.button("💰 Profit Calc",     use_container_width=True): st.session_state.page="profit";  st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# CHAT
# ══════════════════════════════════════════════════════════════════════════════
def _send_chat(text: str):
    st.session_state.chat_msgs.append({"role":"user","text":text})
    st.session_state.is_typing = True
    st.rerun()

def _stream_last_message():
    msgs = st.session_state.chat_msgs
    last_user = next((m["text"] for m in reversed(msgs) if m["role"]=="user"), None)
    if not last_user:
        st.session_state.is_typing = False
        return

    payload = {"model_name":"llama-3.3-70b-versatile","messages":[last_user],
               "allow_search":True,"language":user_lang()}
    headers = {"Content-Type":"application/json"}
    if st.session_state.jwt:
        headers["Authorization"] = f"Bearer {st.session_state.jwt}"

    reply_box = st.empty()
    collected = []

    try:
        with requests.post(
            f"{API_BASE}/chat/stream", json=payload, headers=headers,
            stream=True, timeout=60
        ) as r:
            if r.status_code == 404:
                raise ValueError("stream_not_found")
            if not r.ok:
                try:   err = r.json().get("detail", r.text)
                except: err = r.text
                reply_box.markdown(f"<div class='msg-bot'>🌿 ⚠️ {err}</div>", unsafe_allow_html=True)
                st.session_state.chat_msgs.append({"role":"bot","text":f"⚠️ {err}"})
                st.session_state.is_typing = False
                return
            for chunk in r.iter_content(chunk_size=None):
                if chunk:
                    collected.append(chunk.decode("utf-8","ignore"))
                    current = "".join(collected)
                    reply_box.markdown(f"<div class='msg-bot msg-bot-latest'>🌿 {current}</div>", unsafe_allow_html=True)
        final = "".join(collected)
        if final:
            st.session_state.chat_msgs.append({"role":"bot","text":final})
            st.session_state.last_reply = final
            st.session_state.is_typing  = False
            return
        raise ValueError("empty_stream")
    except ValueError:
        pass
    except Exception:
        pass

    reply_box.markdown("<div class='msg-bot msg-bot-latest'>🌿 ▋</div>", unsafe_allow_html=True)
    data, err = api_post("/chat", payload)
    if err:
        friendly = err
        if "401" in err: friendly = "Session expired. Please logout and login again."
        elif "429" in err: friendly = "Too many requests. Please wait a moment and try again."
        elif "Connection" in err or "timed out" in err.lower():
            friendly = "Cannot reach the backend. Make sure backend.py is running on port 9999."
        reply_box.markdown(
            f"<div class='msg-bot' style='border-color:rgba(255,107,107,.3);background:rgba(255,107,107,.05)'>"
            f"<span style='color:#ff6b6b'>⚠️ {friendly}</span></div>", unsafe_allow_html=True)
        st.session_state.chat_msgs.append({"role":"bot","text":f"⚠️ {friendly}"})
    else:
        answer = data.get("response","")
        reply_box.markdown(f"<div class='msg-bot'>🌿 {answer}</div>", unsafe_allow_html=True)
        st.session_state.chat_msgs.append({"role":"bot","text":answer})
        st.session_state.last_reply = answer
    st.session_state.is_typing = False

def page_chat():
    inject_anim()
    st.markdown(f"<div class='sec-head'>💬 {t('chat')}</div>", unsafe_allow_html=True)

    lc1, lc2 = st.columns([3, 1])
    with lc1:
        st.markdown("<div class='sec-sub'>Ask anything about farming — diseases, fertilizers, weather, schemes</div>", unsafe_allow_html=True)
    with lc2:
        lang_options = list(LANGS.keys())
        lang_labels  = [f"{LANGS[k]['flag']} {LANGS[k]['name']}" for k in lang_options]
        current_lang = st.session_state.get("chat_lang", user_lang())
        sel_idx = lang_options.index(current_lang) if current_lang in lang_options else 0
        chosen = st.selectbox("Language", lang_labels, index=sel_idx, key="chat_lang_sel", label_visibility="collapsed")
        st.session_state.chat_lang = lang_options[lang_labels.index(chosen)]

    qp = st.query_params
    if "voice_input" in qp:
        vi = qp.get("voice_input","").strip()
        st.query_params.clear()
        if vi: _send_chat(vi); return

    if not st.session_state.chat_msgs:
        st.markdown("<div style='color:#7a93a8;font-size:12px;margin-bottom:8px'>💡 Try asking:</div>", unsafe_allow_html=True)
        sq1, sq2, sq3 = st.columns(3)
        suggestions = [
            ("🌾 Best crop for summer?",  "Which crop is best to grow in summer season in Maharashtra?"),
            ("🦠 Yellow leaves on wheat?", "My wheat leaves are turning yellow with brown spots, what disease is this?"),
            ("💊 Fertilizer for tomato?",  "What fertilizer should I apply for tomato crop at flowering stage?"),
        ]
        for col, (label, q) in zip([sq1, sq2, sq3], suggestions):
            if col.button(label, use_container_width=True, key=f"sq_{label}"):
                _send_chat(q)

    msgs_to_show = [m for m in st.session_state.chat_msgs if m["role"]=="user"] if st.session_state.get("is_typing") else st.session_state.chat_msgs
    for idx, msg in enumerate(msgs_to_show):
        if msg["role"] == "user":
            st.markdown(f"<div class='msg-user'>👨‍🌾 {msg['text']}</div>", unsafe_allow_html=True)
        else:
            cls = "msg-bot msg-bot-latest" if idx == len(msgs_to_show)-1 else "msg-bot"
            st.markdown(f"<div class='{cls}'>🌿 {msg['text']}</div>", unsafe_allow_html=True)

    if st.session_state.get("is_typing"):
        _stream_last_message(); st.rerun(); return

    # ── Input row: mic (legacy) | Whisper mic | text input | send ─────────────
    c_mic, c_wmik, c_inp = st.columns([1, 1, 10])
    with c_mic:
        mic_component()
    with c_wmik:
        # Groq Whisper mic button
        transcript = groq_mic_button("chat_whisper_mic")
        if transcript:
            st.session_state.chat_voice_text = transcript
            st.rerun()

    with c_inp:
        # Pre-fill with voice text if available
        voice_prefill = st.session_state.get("chat_voice_text", "")
        with st.form("chat_form", clear_on_submit=True):
            ui = st.text_input("Message", value=voice_prefill,
                               placeholder=t("type_q"), label_visibility="collapsed")
            if st.form_submit_button(t("send"), type="primary") and ui.strip():
                st.session_state.chat_voice_text = ""
                _send_chat(ui.strip())

    if st.session_state.chat_msgs:
        if st.button("🗑 Clear Chat", key="clear_chat"):
            st.session_state.chat_msgs = []
            st.rerun()

    if st.session_state.last_reply and st.session_state.voice_on:
        speak(st.session_state.last_reply)
    st.session_state.last_reply = ""

# ══════════════════════════════════════════════════════════════════════════════
# VOICE AI PAGE (full voice-to-voice)
# ══════════════════════════════════════════════════════════════════════════════
def page_voice():
    inject_anim()
    lang         = st.session_state.get("chat_lang", user_lang())
    farmer_name  = st.session_state.user.get("name", "Farmer") if st.session_state.user else "Farmer"
    location     = st.session_state.user.get("location", "Pune, Maharashtra") if st.session_state.user else "Pune, Maharashtra"

    st.markdown("""
    <div style='text-align:center;padding:24px 0 8px'>
        <div style='font-size:72px'>🎙️</div>
        <div style='font-family:"Syne",sans-serif;font-size:26px;font-weight:800;color:#aaff44'>Voice AI Advisor</div>
        <div style='font-size:14px;color:#7a93a8;margin-top:6px'>बोलो — AI सुनेगा, समझेगा और जवाब देगा 🌾</div>
    </div>
    """, unsafe_allow_html=True)

    # Language selector
    lang_options = list(LANGS.keys())
    lang_labels  = [f"{LANGS[k]['flag']} {LANGS[k]['name']}" for k in lang_options]
    sel_idx = lang_options.index(lang) if lang in lang_options else 0
    chosen = st.selectbox("भाषा चुनें / Choose Language", lang_labels, index=sel_idx, key="voice_lang_sel")
    active_lang = lang_options[lang_labels.index(chosen)]
    st.session_state.chat_lang = active_lang

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Mic recorder ──────────────────────────────────────────────────────────
    try:
        from streamlit_mic_recorder import mic_recorder
        st.markdown("<div style='text-align:center'>", unsafe_allow_html=True)
        audio = mic_recorder(
            start_prompt="🎤 Hold & Speak",
            stop_prompt="⏹ Done — Sending to AI...",
            key="voice_page_recorder",
            use_container_width=False,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    except ImportError:
        st.error("Install `streamlit-mic-recorder`: `pip install streamlit-mic-recorder`")
        return

    # ── Process recording ─────────────────────────────────────────────────────
    if audio and audio.get("bytes"):
        with st.spinner("🎙️ Transcribing your voice…"):
            question = transcribe_audio(audio["bytes"])

        if not question:
            st.error("❌ आवाज़ नहीं सुनी। फिर से बोलो।")
            return

        # Show what was heard
        st.markdown(f"""
        <div class='voice-bubble-q'>
            <div style='font-size:10px;color:#aaff44;font-weight:700;margin-bottom:6px'>🎤 YOU SAID</div>
            <div style='font-size:16px'>{question}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("🧠 KrishiAI सोच रहा है…"):
            answer = get_ai_voice_response(question, active_lang, farmer_name, location)

        # Show AI response
        st.markdown(f"""
        <div class='voice-bubble-a'>
            <div style='font-size:10px;color:#00d4aa;font-weight:700;margin-bottom:6px'>🌿 KRISHIAI SAYS</div>
            <div style='font-size:16px'>{answer}</div>
        </div>
        """, unsafe_allow_html=True)

        # Auto-play response
        speak_gtts(answer, active_lang)

        # Save to history
        if "voice_history" not in st.session_state:
            st.session_state.voice_history = []
        st.session_state.voice_history.append({
            "q": question, "a": answer, "lang": active_lang,
            "time": datetime.datetime.now().strftime("%H:%M")
        })

    # ── Voice history ─────────────────────────────────────────────────────────
    if st.session_state.get("voice_history"):
        st.markdown("---")
        st.markdown("<div style='font-size:13px;color:#7a93a8;margin-bottom:8px'>🕐 Voice History</div>", unsafe_allow_html=True)
        for item in reversed(st.session_state.voice_history[-6:]):
            with st.expander(f"🎤 {item['q'][:55]}…  [{item.get('time','')}]"):
                st.write(item["a"])
                c1, c2 = st.columns([1, 6])
                with c1:
                    if st.button("🔊", key=f"replay_{item['time']}_{item['q'][:8]}"):
                        speak_gtts(item["a"], item["lang"])

        if st.button("🗑 Clear Voice History", key="clear_voice_hist"):
            st.session_state.voice_history = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# DISEASE DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
def page_disease():
    inject_anim()
    st.markdown(f"<div class='sec-head'>🔬 {t('disease_title')}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Upload a crop photo or describe symptoms for AI diagnosis</div>", unsafe_allow_html=True)

    CROPS = ["Wheat","Rice","Tomato","Onion","Cotton","Maize","Soybean","Potato","Sugarcane","Groundnut"]
    cf, cr = st.columns([1, 1])
    with cf:
        crop  = st.selectbox(t("crop_label"), CROPS, key="d_crop")
        photo = st.file_uploader(t("upload_photo"), type=["jpg","jpeg","png","webp"])
        if photo: st.image(photo, use_container_width=True)
        st.markdown("<div style='text-align:center;color:#7a93a8;font-size:12px;margin:8px 0'>— or describe symptoms below —</div>", unsafe_allow_html=True)

        # Symptoms input with Whisper mic
        sym_col, mic_col = st.columns([9, 1])
        with sym_col:
            voice_sym_prefill = st.session_state.get("disease_voice_text", "")
            sym = st.text_area(t("symptoms_label"),
                               value=voice_sym_prefill,
                               placeholder="e.g. yellow leaves, brown spots, wilting…",
                               height=90, key="d_sym")
        with mic_col:
            st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
            disease_transcript = groq_mic_button("disease_whisper_mic")
            if disease_transcript:
                st.session_state.disease_voice_text = disease_transcript
                st.rerun()

        # Clear voice prefill once user edits
        if sym and sym != st.session_state.get("disease_voice_text", ""):
            st.session_state.disease_voice_text = ""

        btn = st.button(t("analyze_btn"), type="primary", disabled=(not photo and not sym.strip()), key="d_btn")
        if btn:
            with st.spinner(t("analyzing")):
                lang = user_lang()
                if photo:
                    data, err = api_post("/disease/photo",
                        data={"crop_name":crop,"language":lang,"location":"Maharashtra","district":"Pune"},
                        files={"photo":(photo.name,photo.getvalue(),photo.type)})
                else:
                    data, err = api_post("/disease/text",
                        {"crop_name":crop,"symptoms":sym,"language":lang,"location":"Maharashtra","district":"Pune"})
            if data:
                st.session_state.dis_result = data
                st.session_state.disease_voice_text = ""
                if st.session_state.voice_on:
                    txt = f"रोग: {data.get('disease_name','अज्ञात')}. "
                    if data.get("severity"): txt += f"गंभीरता: {data['severity']}. "
                    if data.get("treatment_steps"): txt += "उपचार: " + ", ".join(data["treatment_steps"][:2]) + "."
                    speak(txt)
                # Auto-play gTTS result
                dis_summary = f"{data.get('disease_name','')} detected. Severity: {data.get('severity','')}."
                speak_gtts(dis_summary, lang)
            else:
                st.error(err or "Error analysing")

    with cr:
        t1, t2, t3 = st.tabs([t("result_tab"), t("history_tab"), t("nearby_tab")])
        with t1:
            r = st.session_state.dis_result
            if r:
                symptoms_html = (
                    f'<div style="font-size:12px;color:#7a93a8;margin-top:8px;padding:8px;background:rgba(255,255,255,.03);border-radius:8px">👁 {r["symptoms_observed"]}</div>'
                    if r.get("symptoms_observed") else ""
                )
                st.markdown(f"""<div class="res-card">
                <div class="res-name">🦠 {r.get('disease_name','—')}</div>
                <div style="margin:10px 0">
                <span class="chip chip-amber">{t('confidence')}: {r.get('confidence','—')}</span>
                <span class="chip chip-rose">{t('severity')}: {r.get('severity','—')}</span>
                <span class="chip chip-teal">{t('affected')}: {r.get('affected_area','—')}</span>
                </div>
                {symptoms_html}
                </div>""", unsafe_allow_html=True)
                if r.get("treatment_steps"):
                    st.markdown(f"**🩺 {t('treatment')}**")
                    for i, s in enumerate(r["treatment_steps"], 1):
                        st.markdown(f"{i}. {s}")
                if r.get("organic_option"):
                    st.success(f"🌿 **Organic:** {r['organic_option']}")
                if r.get("yield_impact"):
                    st.warning(f"⚠️ **{t('yield_impact')}:** {r['yield_impact']}")
                if r.get("prevention"):
                    st.info(f"💡 **{t('prevention')}:** {r['prevention']}")
                if r.get("followup_days"):
                    st.markdown(f"<div style='font-size:12px;color:#7a93a8;margin-top:8px'>🔁 Re-check in {r['followup_days']} days</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#7a93a8;font-size:13px;text-align:center;padding:40px 20px'>📸 Upload a photo or describe symptoms to start diagnosis</div>", unsafe_allow_html=True)
        with t2:
            hdata, _ = api_get("/disease/history", {"limit": 15})
            if hdata and hdata.get("history"):
                for h in hdata["history"]:
                    ic = "📷" if h.get("source")=="photo" else "📝"
                    st.markdown(f"""<div class="hist-item"><div style="font-size:22px">{ic}</div>
                    <div><div class="hist-name">🦠 {h.get('disease_name','—')}</div>
                    <div class="hist-meta">🌾 {h.get('crop_name','—')} · 🔴 {h.get('severity','—')}</div>
                    <div class="hist-meta">🕐 {str(h.get('detected_at','—'))[:16]}</div></div></div>""", unsafe_allow_html=True)
            else:
                st.info(t("no_history"))
        with t3:
            adata, _ = api_get("/disease/nearby-alerts", {"district":"Pune"})
            if adata and adata.get("alerts"):
                for a in adata["alerts"]:
                    st.markdown(f"""<div class="na-item"><div class="na-name">⚠️ {a.get('disease_name','—')}</div>
                    <div style="font-size:12px;color:#7a93a8;margin-top:3px">🌾 {a.get('crop_name','—')} · {a.get('severity','—')} ·
                    <span style="color:#ff6b6b">{a.get('alert_count',0)} reports</span></div>
                    <div style="font-size:11px;color:#7a93a8;margin-top:2px">Last: {str(a.get('last_seen','—'))[:16]}</div></div>""", unsafe_allow_html=True)
            else:
                st.info(t("no_alerts"))

# ══════════════════════════════════════════════════════════════════════════════
# MARKET
# ══════════════════════════════════════════════════════════════════════════════
def page_market():
    inject_anim()
    st.markdown(f"<div class='sec-head'>📈 {t('market_title')}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Live mandi prices from Maharashtra</div>", unsafe_allow_html=True)
    data, err = api_get("/market")
    if err: st.error(err); return
    for p in data.get("prices",[]):
        clr = "#aaff44" if p["direction"]=="up" else "#ff6b6b"
        arr = "↑" if p["direction"]=="up" else "↓"
        st.markdown(f"""<div class="k-card" style="padding:16px 20px">
        <div style="display:flex;align-items:center;gap:14px">
          <div style="font-size:36px">{p['emoji']}</div>
          <div style="flex:1">
            <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700">{p['crop']}</div>
            <div style="font-size:11px;color:#7a93a8">📍 {p['mandi']}</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:20px;font-weight:800;color:#e4edf4">{p['price']}<span style="font-size:11px;color:#7a93a8">/q</span></div>
            <div style="font-size:12px;color:{clr};font-weight:600">{arr} {p['change']}</div>
          </div>
        </div></div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SCHEMES
# ══════════════════════════════════════════════════════════════════════════════
def page_schemes():
    inject_anim()
    st.markdown(f"<div class='sec-head'>🏛 {t('schemes_title')}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Government schemes available for farmers</div>", unsafe_allow_html=True)
    data, err = api_get("/schemes")
    if err: st.error(err); return
    for s in data.get("schemes",[]):
        with st.expander(f"{s['icon']} {s['name']} — {s['benefit']}"):
            st.write(s["description"])
            st.markdown(f"**💰 Benefit:** {s['benefit']}")
            st.link_button(t("apply_online"), s.get("apply_url","#"))

# ══════════════════════════════════════════════════════════════════════════════
# SOIL
# ══════════════════════════════════════════════════════════════════════════════
def page_soil():
    inject_anim()
    st.markdown(f"<div class='sec-head'>🧪 {t('soil_title')}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Enter your soil test values for AI-powered recommendations</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        ph   = st.slider("pH", 5.0, 9.0, 6.9, 0.1)
        n    = st.slider("Nitrogen (mg/kg)", 10, 100, 45)
        p    = st.slider("Phosphorus (mg/kg)", 5, 80, 30)
        k    = st.slider("Potassium (mg/kg)", 50, 300, 180)
        crop = st.selectbox("Crop", ["Wheat","Rice","Tomato","Cotton","Maize"])
        if st.button(t("analyze_soil"), type="primary"):
            data, err = api_get("/soil/analyze", {"ph":ph,"nitrogen":n,"phosphorus":p,"potassium":k,"crop":crop})
            if err: st.error(err)
            else:   st.session_state.soil_data = data
    with c2:
        sd = st.session_state.get("soil_data")
        if sd:
            sc  = sd.get("health_score", 0)
            clr = "#aaff44" if sc >= 80 else "#ffb547" if sc >= 60 else "#ff6b6b"
            st.markdown(f"""<div class="k-card" style="text-align:center;padding:28px">
            <div style="font-family:'Syne',sans-serif;font-size:64px;font-weight:800;color:{clr};line-height:1">{sc}</div>
            <div style="font-size:14px;color:#7a93a8;margin-top:4px">/ 100 — {sd.get('status','')}</div></div>""", unsafe_allow_html=True)
            for nm, val, mx in [("Nitrogen (N)", n, 100),("Phosphorus (P)", p, 80),("Potassium (K)", k, 300)]:
                pct = int(val / mx * 100)
                st.markdown(f"""<div style="margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;font-size:13px"><span>{nm}</span><span style="color:#aaff44">{val} mg/kg</span></div>
                <div class="soil-bar-wrap"><div class="soil-bar" style="width:{pct}%"></div></div></div>""", unsafe_allow_html=True)
            st.markdown("**🌱 Recommendations:**")
            for rec in sd.get("recommendations", []):
                st.markdown(f"• {rec}")
            if sd.get("fertilizer_advice"):
                st.success(f"💊 {sd['fertilizer_advice']}")
        else:
            st.markdown("<div style='color:#7a93a8;font-size:13px;text-align:center;padding:60px 20px'>🧪 Enter soil values and click Analyse</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# IRRIGATION
# ══════════════════════════════════════════════════════════════════════════════
def page_irrigation():
    inject_anim()
    st.markdown("<div class='sec-head'>💧 Irrigation Advisor</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Get a smart irrigation plan based on soil moisture and crop type</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        crop = st.selectbox("Crop", ["Wheat","Rice","Tomato","Onion","Cotton","Maize","Sugarcane"])
        soil = st.slider("Soil moisture (%)", 10, 90, 45)
        st.markdown(f"<div style='font-size:12px;color:{'#aaff44' if soil>=60 else '#ffb547' if soil>=40 else '#ff6b6b'}'>{'✅ Optimal' if soil>=60 else '⚠️ Below optimal' if soil>=40 else '🔴 Low – irrigate soon'}</div>", unsafe_allow_html=True)
    with c2:
        if st.button("💧 Get Irrigation Plan", type="primary"):
            data, err = api_post("/irrigation/recommend",
                {"crop":crop,"soil_moisture":soil,"language":user_lang()})
            if err: st.error(err)
            else:
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Method",   data.get("method","").title())
                mc2.metric("Amount",   f"{data.get('amount_mm',0)} mm")
                mc3.metric("Per Acre", f"{int(data.get('amount_l_per_acre',0)):,} L")
                st.info(f"ℹ️ {data.get('why','')}")
                if data.get("schedule"):
                    st.markdown("**📅 Irrigation Schedule:**")
                    for d in data["schedule"]:
                        st.markdown(f"  • {d}")

# ══════════════════════════════════════════════════════════════════════════════
# FERTILIZER PLANNER
# ══════════════════════════════════════════════════════════════════════════════
def page_planner():
    inject_anim()
    st.markdown("<div class='sec-head'>🌱 Fertilizer Planner</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Generate a full fertilizer schedule with cost estimates</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        crop    = st.selectbox("Crop", ["Wheat","Rice","Tomato","Cotton","Maize","Onion","Soybean"])
        stage   = st.selectbox("Growth Stage", ["Seedling","Tillering","Vegetative","Flowering","Grain filling","Maturity"])
        area    = st.number_input("Area", 1.0, step=0.1)
        unit    = st.selectbox("Unit", ["acre","hectare"])
    with c2:
        organic = st.toggle("🌿 Organic Only", False)
        ph_val  = st.slider("Soil pH", 5.0, 9.0, 6.9, 0.1)
    if st.button("🌱 Generate Plan", type="primary"):
        data, err = api_post("/planner/fertilizer",
            {"crop":crop,"stage":stage,"area":area,"unit":unit,"organic_only":organic,
             "ph":ph_val,"language":user_lang()})
        if err: st.error(err)
        else:
            st.metric("💰 Total Cost Estimate", data.get("total_cost_estimate",""))
            for sched in data.get("schedule",[]):
                with st.expander(f"📅 {sched['date']} — {sched['stage']}"):
                    for item in sched.get("items",[]):
                        st.markdown(f"• **{item['name']}** · {item['dose']} · {item['cost_estimate']}")
                    st.caption(f"⚠️ {sched.get('safety','')}")

# ══════════════════════════════════════════════════════════════════════════════
# PRICE FORECAST
# ══════════════════════════════════════════════════════════════════════════════
def page_predict():
    inject_anim()
    st.markdown("<div class='sec-head'>📉 Price Forecast</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Indicative mandi price prediction for selling decisions</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        crop  = st.selectbox("Crop", ["Wheat","Tomato","Onion","Cotton","Soybean","Maize"])
        state = st.text_input("State", "Maharashtra")
        days  = st.slider("Days Ahead", 1, 15, 7)
    with c2:
        if st.button("📊 Predict Prices", type="primary"):
            data, err = api_post("/market/predict",
                {"crop":crop,"state":state,"days":days,"language":user_lang()})
            if err: st.error(err)
            else:
                st.success(f"🏆 Best selling window: **{data.get('best_selling_window','')}**")
                import pandas as pd
                df = pd.DataFrame(data.get("prices",[]))
                if not df.empty:
                    df["date"] = pd.to_datetime(df["date"])
                    st.line_chart(df.set_index("date")["price"], height=220)
                st.caption(f"⚠️ {data.get('note','')}")

# ══════════════════════════════════════════════════════════════════════════════
# PROFIT CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
def page_profit():
    inject_anim()
    st.markdown("<div class='sec-head'>💰 Profit Calculator</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Calculate net profit, ROI and break-even price for your crop</div>", unsafe_allow_html=True)
    crop  = st.text_input("Crop", "Wheat")
    a1, a2 = st.columns(2)
    area  = a1.number_input("Area", 1.0, step=0.1)
    unit  = a2.selectbox("Unit", ["acre","hectare"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Cost Inputs (per acre)**")
        seed  = st.number_input("Seed cost (₹)",        1200.0, step=100.0)
        fert  = st.number_input("Fertilizer (₹)",       1800.0, step=100.0)
        pest  = st.number_input("Pesticide (₹)",         600.0, step=50.0)
        labor = st.number_input("Labor (₹)",             2000.0, step=100.0)
    with c2:
        st.markdown("**Revenue Inputs**")
        irrig = st.number_input("Irrigation (₹)",        500.0, step=50.0)
        misc  = st.number_input("Misc (₹)",              400.0, step=50.0)
        yld   = st.number_input("Expected yield (q/acre)", 10.0, step=0.5)
        price = st.number_input("Expected price (₹/q)", 2300.0, step=50.0)
    trans = st.number_input("Transport (₹/acre)", 0.0, step=50.0)
    if st.button("💰 Calculate Profit", type="primary"):
        data, err = api_post("/profit/calc",
            {"crop":crop,"area":area,"unit":unit,"seed_cost":seed,"fertilizer_cost":fert,
             "pesticide_cost":pest,"labor_cost":labor,"irrigation_cost":irrig,"misc_cost":misc,
             "expected_yield_q":yld,"expected_price_per_q":price,"transport_cost":trans,
             "language":user_lang()})
        if err: st.error(err)
        else:
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Total Cost",  data.get("total_cost",""))
            r2.metric("Revenue",     data.get("revenue",""))
            r3.metric("Net Profit",  data.get("profit",""))
            r4.metric("ROI",         f"{data.get('roi_percent',0)}%")
            st.info(f"📊 Break-even price: {data.get('break_even_price_per_q','')}/q")
            profit_val = str(data.get("profit","")).replace("₹","").replace(",","")
            try:
                pv = float(profit_val)
                if pv > 0: st.success(f"✅ Profitable crop! Net profit: {data.get('profit','')} for {area} {unit}")
                else:       st.warning("⚠️ This crop may not be profitable at these prices. Consider reducing costs.")
            except: pass

# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
def page_analytics():
    import pandas as pd
    inject_anim()
    st.markdown("<div class='sec-head'>📊 Analytics</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Farm performance overview</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", "₹6.2L", "+18%")
    c2.metric("Total Cost",    "₹1.4L", "+5%")
    c3.metric("Net Profit",    "₹4.8L", "+24%")
    c4.metric("ROI",           "342%",  "+19%")
    yd = pd.DataFrame({"Month":["Aug","Sep","Oct","Nov","Dec","Jan","Feb"],
        "Wheat":[28,31,35,40,38,44,48],"Onion":[0,8,22,30,35,40,42],"Tomato":[12,18,24,20,16,22,28]}).set_index("Month")
    rd = pd.DataFrame({"Month":["Aug","Sep","Oct","Nov","Dec","Jan","Feb"],
        "Revenue":[42,55,68,75,70,82,90],"Cost":[18,20,25,22,24,26,28]}).set_index("Month")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**📈 Yield Trends (q/acre)**")
        st.line_chart(yd, height=220)
    with cb:
        st.markdown("**💸 Revenue vs Cost (₹K)**")
        st.area_chart(rd, height=220)

# ══════════════════════════════════════════════════════════════════════════════
# CALENDAR
# ══════════════════════════════════════════════════════════════════════════════
def page_calendar():
    inject_anim()
    st.markdown("<div class='sec-head'>📅 Farm Calendar</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Track your farming tasks and schedule</div>", unsafe_allow_html=True)
    tag_colors = {"Fertilizer":"chip-lime","Monitor":"chip-sky","Pest":"chip-rose","Irrigation":"chip-teal","Market":"chip-amber"}
    tasks = [
        {"date":"Feb 22","name":"Apply DAP fertilizer",  "field":"Field A – Wheat", "tag":"Fertilizer","done":False},
        {"date":"Feb 22","name":"Soil moisture check",   "field":"All fields",       "tag":"Monitor",   "done":True},
        {"date":"Feb 24","name":"Pesticide spray",        "field":"Field B – Onion",  "tag":"Pest",      "done":False},
        {"date":"Feb 25","name":"Irrigation schedule",   "field":"Field C",          "tag":"Irrigation","done":False},
        {"date":"Feb 28","name":"Market visit Nashik",   "field":"Tomato ready",     "tag":"Market",    "done":False},
    ]
    for task in tasks:
        col1, col2 = st.columns([1, 10])
        with col1:
            st.checkbox("Done", value=task["done"], label_visibility="collapsed", key=f"tk_{task['name']}")
        with col2:
            chip = tag_colors.get(task["tag"],"chip-sky")
            st.markdown(
                f"**{task['name']}** <span class='chip {chip}'>{task['tag']}</span>"
                f"\n\n📍 {task['field']} · 📅 {task['date']}",
                unsafe_allow_html=True
            )
        st.markdown("<hr style='border-color:rgba(255,255,255,.05);margin:4px 0'>", unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    new = st.text_input("Add new task", placeholder="e.g. Water tomatoes tomorrow", key="new_task")
    if st.button("➕ Add Task", type="primary") and new:
        st.success(f"✅ Added: {new}")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if st.session_state.screen == "login":
        screen_login()
    else:
        sidebar()
        {
            "dashboard":  page_dashboard,
            "chat":       page_chat,
            "disease":    page_disease,
            "voice":      page_voice,
            "market":     page_market,
            "schemes":    page_schemes,
            "soil":       page_soil,
            "irrigation": page_irrigation,
            "planner":    page_planner,
            "predict":    page_predict,
            "profit":     page_profit,
            "analytics":  page_analytics,
            "calendar":   page_calendar,
        }.get(st.session_state.page, page_dashboard)()

if __name__ == "__main__":
    main()
