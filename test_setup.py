#!/usr/bin/env python3
"""
KrishiAI Setup Tester
Run: python test_setup.py
Tells you exactly what's working and what's broken.
"""
import os, sys

print("\n" + "="*55)
print("  KrishiAI Diagnostic Test")
print("="*55)

errors = []
warnings = []

# ── 1. Check .env ─────────────────────────────────────────
print("\n[1] Checking .env file...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("    ✅ python-dotenv OK")
except ImportError:
    errors.append("python-dotenv not installed → pip install python-dotenv")

GROQ_KEY    = os.getenv("GROQ_API_KEY", "")
TAVILY_KEY  = os.getenv("TAVILY_API_KEY", "")
MYSQL_HOST  = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER  = os.getenv("MYSQL_USER", "root")
MYSQL_PASS  = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB    = os.getenv("MYSQL_DATABASE", "krishiai")

if not GROQ_KEY:
    errors.append("GROQ_API_KEY missing from .env")
elif not GROQ_KEY.startswith("gsk_"):
    warnings.append(f"GROQ_API_KEY looks wrong (should start with gsk_): {GROQ_KEY[:12]}...")
else:
    print(f"    ✅ GROQ_API_KEY found: {GROQ_KEY[:12]}...")

if not TAVILY_KEY:
    warnings.append("TAVILY_API_KEY missing (web search won't work, chat still works)")
else:
    print(f"    ✅ TAVILY_API_KEY found: {TAVILY_KEY[:12]}...")

# ── 2. Check Python packages ──────────────────────────────
print("\n[2] Checking Python packages...")
packages = {
    "fastapi":         "fastapi",
    "uvicorn":         "uvicorn",
    "pymysql":         "pymysql",
    "bcrypt":          "bcrypt",
    "jose":            "python-jose",
    "langchain_groq":  "langchain-groq",
    "groq":            "groq",
    "streamlit":       "streamlit",
    "requests":        "requests",
}
for mod, pkg in packages.items():
    try:
        __import__(mod)
        print(f"    ✅ {pkg}")
    except ImportError:
        errors.append(f"{pkg} not installed → pip install {pkg}")

# ── 3. Check Groq API + list available models ─────────────
print("\n[3] Testing Groq API connection...")
if GROQ_KEY:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        models = client.models.list()
        model_ids = [m.id for m in models.data]

        # Check chat models
        chat_models = [m for m in model_ids if "llama" in m.lower() or "mixtral" in m.lower()]
        print(f"    ✅ Groq API connected. {len(model_ids)} models available.")

        # Check vision models specifically
        vision_models = [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "llama-3.2-90b-vision-preview",
            "llama-3.2-11b-vision-preview",
        ]
        print("\n    Vision models on your account:")
        found_vision = []
        for vm in vision_models:
            if vm in model_ids:
                print(f"      ✅ {vm}")
                found_vision.append(vm)
            else:
                print(f"      ❌ {vm}  (not available)")

        if not found_vision:
            errors.append(
                "No vision models available on your Groq account!\n"
                "  → Go to console.groq.com and check your plan.\n"
                "  → Free tier may not include vision models.\n"
                "  → Try upgrading or use text-only disease detection."
            )
        else:
            print(f"\n    ✅ Best vision model to use: {found_vision[0]}")

        # Check main chat model
        main_model = "llama-3.3-70b-versatile"
        if main_model in model_ids:
            print(f"    ✅ Chat model available: {main_model}")
        else:
            alt = next((m for m in chat_models if "70b" in m or "llama-3" in m), None)
            warnings.append(f"{main_model} not found. Closest: {alt}")

    except Exception as e:
        errors.append(f"Groq API error: {e}")
else:
    print("    ⏭  Skipped (no API key)")

# ── 4. Check MySQL ────────────────────────────────────────
print("\n[4] Testing MySQL connection...")
try:
    import pymysql
    conn = pymysql.connect(
        host=MYSQL_HOST, user=MYSQL_USER,
        password=MYSQL_PASS, database=MYSQL_DB,
        charset="utf8mb4", connect_timeout=5,
    )
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = [r[0] for r in cur.fetchall()]
    print(f"    ✅ MySQL connected to '{MYSQL_DB}'")
    print(f"    ✅ Tables: {tables if tables else '(none yet — will be created on first run)'}")
    cur.close()
    conn.close()
except Exception as e:
    errors.append(f"MySQL error: {e}\n  → Check MYSQL_HOST/USER/PASSWORD/DATABASE in .env")

# ── 5. Check backend port ─────────────────────────────────
print("\n[5] Checking if backend is running on port 9999...")
try:
    import requests
    r = requests.get("http://127.0.0.1:9999/health", timeout=3)
    if r.ok:
        print(f"    ✅ Backend is running! Version: {r.json().get('version','?')}")
    else:
        warnings.append(f"Backend returned status {r.status_code}")
except Exception:
    warnings.append("Backend not running on port 9999 (start it with: python backend.py)")

# ── Summary ───────────────────────────────────────────────
print("\n" + "="*55)
if errors:
    print(f"  ❌ {len(errors)} ERROR(S) — fix these first:\n")
    for i, e in enumerate(errors, 1):
        print(f"  {i}. {e}\n")
else:
    print("  ✅ All checks passed!")

if warnings:
    print(f"\n  ⚠️  {len(warnings)} WARNING(S):\n")
    for i, w in enumerate(warnings, 1):
        print(f"  {i}. {w}\n")

print("="*55 + "\n")

if errors:
    sys.exit(1)
