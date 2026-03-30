# ═══════════════════════════════════════════════════════════════════
#  mysql_setup.py — KrishiAI MySQL Connection Guide & Test Script
#  Run this to: test connection, create DB, create tables, insert demo data
#  Usage: python mysql_setup.py
# ═══════════════════════════════════════════════════════════════════

"""
╔══════════════════════════════════════════════════════════════════╗
║          MYSQL CONNECTION — STEP BY STEP GUIDE                 ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  STEP 1 — Install MySQL                                          ║
║  ─────────────────────────────────────────────────────────────  ║
║  Windows: Download XAMPP from https://apachefriends.org          ║
║           Open XAMPP → Click START next to MySQL                 ║
║                                                                  ║
║  OR: Download MySQL Installer from https://dev.mysql.com         ║
║      Set root password during install — remember it!             ║
║                                                                  ║
║  Linux:  sudo apt install mysql-server -y                        ║
║          sudo systemctl start mysql                              ║
║                                                                  ║
║  macOS:  brew install mysql && brew services start mysql         ║
║                                                                  ║
║  STEP 2 — Add MySQL password to .env                             ║
║  ─────────────────────────────────────────────────────────────  ║
║  Open your .env file and set:                                    ║
║    MYSQL_HOST=localhost                                          ║
║    MYSQL_PORT=3306                                               ║
║    MYSQL_USER=root                                               ║
║    MYSQL_PASSWORD=your_password_here  (XAMPP = leave empty)      ║
║    MYSQL_DATABASE=krishiai                                       ║
║                                                                  ║
║  STEP 3 — Run this script                                        ║
║  ─────────────────────────────────────────────────────────────  ║
║    python mysql_setup.py                                         ║
║                                                                  ║
║  STEP 4 — Start the app                                          ║
║  ─────────────────────────────────────────────────────────────  ║
║    Terminal 1:  python backend.py                                ║
║    Terminal 2:  streamlit run app.py                             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, sys
from dotenv import load_dotenv
load_dotenv()

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; C = "\033[96m"
B = "\033[1m";  X = "\033[0m"

def ok(m):   print(f"  {G}✅  {m}{X}")
def warn(m): print(f"  {Y}⚠️   {m}{X}")
def err(m):  print(f"  {R}❌  {m}{X}")
def hdr(m):  print(f"\n{B}{C}{'═'*56}\n  {m}\n{'═'*56}{X}")
def info(m): print(f"  {C}→   {m}{X}")

# ── Read config ────────────────────────────────────────────────────────────────
HOST = os.environ.get("MYSQL_HOST",     "localhost")
PORT = int(os.environ.get("MYSQL_PORT", "3306"))
USER = os.environ.get("MYSQL_USER",     "root")
PASS = os.environ.get("MYSQL_PASSWORD", "")
DB   = os.environ.get("MYSQL_DATABASE", "krishiai")

# ─────────────────────────────────────────────────────────────────────────────
hdr("STEP 1 — Check PyMySQL Installation")
try:
    import pymysql
    import pymysql.cursors
    ok(f"PyMySQL {pymysql.__version__} is installed")
except ImportError:
    err("PyMySQL not installed!")
    info("Run: pip install PyMySQL cryptography")
    info("Or:  pipenv install")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
hdr("STEP 2 — Test MySQL Connection")
info(f"Connecting to MySQL at {HOST}:{PORT} as '{USER}'...")
info(f"Password: {'(empty)' if not PASS else '***set***'}")

try:
    # Connect WITHOUT selecting a database first
    conn = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASS,
        charset="utf8mb4",
        connect_timeout=8,
    )
    ok(f"Connected to MySQL server at {HOST}:{PORT}")
    conn.close()

except pymysql.err.OperationalError as e:
    err(f"Connection failed: {e}")
    print(f"""
{R}  COMMON FIXES:{X}
  {Y}1. MySQL not running?{X}
     Windows/XAMPP : Open XAMPP → Click START next to MySQL
     Linux         : sudo systemctl start mysql
     macOS         : brew services start mysql

  {Y}2. Wrong password?{X}
     Edit MYSQL_PASSWORD in your .env file
     XAMPP default : MYSQL_PASSWORD=   (empty, no password)

  {Y}3. Port blocked?{X}
     Check MYSQL_PORT=3306 in .env
     Or try: mysql -u root -p   in terminal

  {Y}4. MySQL not installed?{X}
     Windows : https://www.apachefriends.org  (XAMPP)
     Linux   : sudo apt install mysql-server -y
     macOS   : brew install mysql
""")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
hdr("STEP 3 — Create Database")
try:
    conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASS,
                           charset="utf8mb4", connect_timeout=8)
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cur.execute("SHOW DATABASES LIKE %s", (DB,))
        exists = cur.fetchone()
    conn.commit()
    conn.close()
    ok(f"Database '{DB}' is ready (created if not existed)")
except Exception as e:
    err(f"Database creation failed: {e}"); sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
hdr("STEP 4 — Create All Tables")

def get_conn():
    return pymysql.connect(
        host=HOST, port=PORT, user=USER, password=PASS,
        database=DB, charset="utf8mb4", connect_timeout=8,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

try:
    conn = get_conn()
    with conn.cursor() as cur:

        # ── Table 1: users (NEW - for JWT auth) ───────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                name         VARCHAR(128) NOT NULL,
                email        VARCHAR(255) UNIQUE,
                phone        VARCHAR(20) UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                location     VARCHAR(255),
                languages    JSON,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        ok("Table 'users' created / already exists")

        # ── Table 2: disease_history (UPDATED - uses user_id INT) ─────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS disease_history (
                id            INT          AUTO_INCREMENT PRIMARY KEY,
                farmer_id     INT          NOT NULL,
                district      VARCHAR(128) NOT NULL DEFAULT 'Pune',
                crop_name     VARCHAR(128),
                symptoms      TEXT,
                disease_name  VARCHAR(255),
                confidence    VARCHAR(32),
                severity      VARCHAR(64),
                treatment     JSON,
                organic_opt   TEXT,
                yield_impact  VARCHAR(255),
                prevention    TEXT,
                detected_at   DATETIME     NOT NULL,
                image_name    VARCHAR(255) DEFAULT '',
                source        ENUM('text','photo') DEFAULT 'text',
                whatsapp_sent TINYINT(1)   DEFAULT 0,
                created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_farmer   (farmer_id),
                INDEX idx_district (district),
                INDEX idx_detected (detected_at),
                FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        ok("Table 'disease_history' created / already exists")

        # ── Table 3: disease_alerts ───────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS disease_alerts (
                id           INT          AUTO_INCREMENT PRIMARY KEY,
                district     VARCHAR(128) NOT NULL,
                disease_name VARCHAR(255) NOT NULL,
                crop_name    VARCHAR(128) NOT NULL,
                severity     VARCHAR(64),
                alert_count  INT          NOT NULL DEFAULT 1,
                last_seen    DATETIME     NOT NULL,
                updated_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_alert (district, disease_name, crop_name),
                INDEX idx_district (district),
                INDEX idx_count    (alert_count DESC)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        ok("Table 'disease_alerts' created / already exists")

        # ── Table 4: chat_history (UPDATED - uses user_id INT) ────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id         INT          AUTO_INCREMENT PRIMARY KEY,
                farmer_id  INT          NOT NULL,
                role       ENUM('user','bot') NOT NULL,
                message    TEXT         NOT NULL,
                language   VARCHAR(8)   NOT NULL DEFAULT 'en',
                sent_at    DATETIME     NOT NULL,
                INDEX idx_farmer_chat (farmer_id),
                INDEX idx_sent        (sent_at),
                FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        ok("Table 'chat_history' created / already exists")

    conn.commit()
    conn.close()

except Exception as e:
    err(f"Table creation failed: {e}"); sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
hdr("STEP 5 — Insert Demo Data")
try:
    import json, datetime, hashlib
    conn = get_conn()
    with conn.cursor() as cur:

        # Check if demo data already exists
        cur.execute("SELECT COUNT(*) as c FROM users WHERE email='demo@krishiai.com'")
        if cur.fetchone()["c"] > 0:
            warn("Demo data already exists — skipping insert.")
        else:
            now = datetime.datetime.now()
            
            # Insert demo user
            password_hash = hashlib.md5("demo123".encode()).hexdigest()  # simple hash for demo
            cur.execute("""
                INSERT INTO users (name, email, phone, password_hash, location, languages)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ("Demo Farmer", "demo@krishiai.com", "9876543210", password_hash, 
                  "Pune, Maharashtra", json.dumps(["hi", "mr", "en"])))
            user_id = cur.lastrowid

            # Insert disease history
            treatment_sample = json.dumps([
                "Apply Mancozeb 75% WP @ 2.5 g/litre water",
                "Spray in morning or evening, avoid afternoon sun",
                "Repeat spray after 7-10 days",
                "Remove and destroy severely infected leaves",
            ])

            cur.execute("""
                INSERT INTO disease_history
                  (farmer_id, district, crop_name, symptoms, disease_name,
                   confidence, severity, treatment, organic_opt, yield_impact,
                   prevention, detected_at, source)
                VALUES
                  (%s,'Pune','Tomato',
                   'Yellow leaves with brown spots and white powdery coating',
                   'Early Blight (Alternaria solani)',
                   '91%','Moderate',
                   %s,
                   'Spray neem oil 5ml/litre + garlic extract weekly',
                   '20-30% yield loss if untreated',
                   'Maintain proper plant spacing for air circulation',
                   %s, 'text')
            """, (user_id, treatment_sample, now))

            # Insert disease alerts
            cur.execute("""
                INSERT INTO disease_alerts
                  (district, disease_name, crop_name, severity, alert_count, last_seen)
                VALUES
                  ('Pune','Early Blight','Tomato','Moderate',3,%s),
                  ('Pune','Powdery Mildew','Wheat','Early',1,%s),
                  ('Nashik','Downy Mildew','Onion','Severe',5,%s)
                ON DUPLICATE KEY UPDATE
                  alert_count = alert_count + 1,
                  last_seen   = VALUES(last_seen)
            """, (now, now, now))

            ok("Demo data inserted: 1 user, 1 disease scan, 3 alerts")

    conn.commit()
    conn.close()
except Exception as e:
    warn(f"Demo data insert skipped: {e}")

# ─────────────────────────────────────────────────────────────────────────────
hdr("STEP 6 — Verify Everything")
try:
    conn = get_conn()
    with conn.cursor() as cur:
        tables = ["users","disease_history","disease_alerts","chat_history"]
        for tbl in tables:
            cur.execute(f"SELECT COUNT(*) as c FROM `{tbl}`")
            count = cur.fetchone()["c"]
            ok(f"{tbl:25s} → {count} rows")
    conn.close()
except Exception as e:
    err(f"Verification failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
hdr("STEP 7 — Connection String for backend.py")
print(f"""
  {B}Your MySQL settings (from .env):{X}

  {C}  Host:     {HOST}
    Port:     {PORT}
    User:     {USER}
    Password: {'(empty)' if not PASS else '(set)'}
    Database: {DB}{X}

  {B}PyMySQL code to copy-paste anywhere:{X}

  {C}  import pymysql
    conn = pymysql.connect(
        host="{HOST}",
        port={PORT},
        user="{USER}",
        password="{PASS or ''}",
        database="{DB}",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    ){X}

  {B}Test query example:{X}

  {C}  with conn.cursor() as cur:
        cur.execute("SELECT * FROM users LIMIT 5")
        rows = cur.fetchall()
        print(rows)
    conn.close(){X}
""")

# ─────────────────────────────────────────────────────────────────────────────
hdr("ALL DONE!")
print(f"""
  {G}MySQL is fully set up for KrishiAI!{X}

  {B}Next steps:{X}

  {C}  1. Start backend:    python backend.py{X}
  {C}  2. Start frontend:   streamlit run frontend.py{X}
  {C}  3. Open browser:     http://localhost:8501{X}
  {C}  4. Health check:     http://127.0.0.1:9999/health{X}
  {C}  5. Swagger API:      http://127.0.0.1:9999/docs{X}

  {B}MySQL GUI tools (optional):{X}
  {C}  • XAMPP phpMyAdmin  → http://localhost/phpmyadmin{X}
  {C}  • MySQL Workbench   → https://dev.mysql.com/downloads/workbench/{X}
  {C}  • DBeaver (free)    → https://dbeaver.io{X}

  {G}Jai Kisan! 🌾{X}
""")
