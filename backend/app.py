from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import json, smtplib, re, time, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from fastapi import Form
from datetime import datetime

app = FastAPI()

# ═══════════════════════════════════════════════════════════════════════════════
# 🔴 CRITICAL: CORS MIDDLEWARE - MUST BE FIRST!
# ═══════════════════════════════════════════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    max_age=3600,
)

# ═══════════════════════════════════════════════════════════════════════════════
# 🟢 EXPLICIT OPTIONS HANDLER
# ═══════════════════════════════════════════════════════════════════════════════
@app.options("/{full_path:path}", include_in_schema=False)
async def preflight(full_path: str):
    """Handle CORS preflight requests"""
    return JSONResponse(
        content={},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        },
    )

# ── EMAIL CONFIG ───────────────────────────────────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST",     "smtpout.secureserver.net")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER     = os.getenv("SMTP_USER",     "support@zoikogroup.com")
SMTP_PASS     = os.getenv("SMTP_PASS",     "NoxxMC26070%!LGM")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@zoikogroup.com")

print(f"\n📧 EMAIL CONFIGURATION:")
print(f"   SMTP Host: {SMTP_HOST}")
print(f"   SMTP Port: {SMTP_PORT}")
print(f"   From Email: {SMTP_USER}")

# ── FIND FRONTEND (Multiple paths) ─────────────────────────────────────────────
def find_frontend_path():
    """Find frontend folder - try multiple paths"""
    paths_to_try = [
        Path("/app/frontend"),                              # Docker container root
        Path(__file__).resolve().parent.parent / "frontend", # ../frontend from backend/
        Path(__file__).resolve().parent / "frontend",       # ./frontend from backend/
        Path("frontend"),
        Path("../frontend"),
    ]
    
    for path in paths_to_try:
        index_file = path / "index.html"
        if path.exists() and index_file.exists():
            print(f"✅ Frontend found at: {path}")
            print(f"   index.html size: {index_file.stat().st_size} bytes")
            return path
    
    print(f"❌ Frontend not found! Tried:")
    for path in paths_to_try:
        print(f"   - {path}")
    return None

frontend_path = find_frontend_path()

# ── MODELS ─────────────────────────────────────────────────────────────────────
class CallbackRequest(BaseModel):
    name:  str
    email: str
    phone: str
    issue: str

class Message(BaseModel):
    message: str

# ── HELPERS ────────────────────────────────────────────────────────────────────
def gen_ref_id():
    """Generate reference ID"""
    return "ZKN-" + str(int(time.time() * 1000))[-6:]

def valid_email(e: str) -> bool:
    """Validate email format"""
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", e))

def valid_phone(p: str) -> bool:
    """Validate phone number"""
    digits = re.sub(r"\D", "", p)
    return 10 <= len(digits) <= 15

def escape_html(s: str) -> str:
    """Escape HTML special characters"""
    return (s.replace("&","&amp;").replace("<","&lt;")
             .replace(">","&gt;").replace('"',"&quot;").replace("'","&#039;"))

def send_email(to_addr: str, subject: str, html_body: str, reply_to: str = None):
    """Send email via SMTP"""
    print(f"\n📧 Sending email to: {to_addr}")
    print(f"   Subject: {subject}")
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_USER
        msg["To"]      = to_addr
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(html_body, "html"))

        # Try SMTP_SSL first
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                print(f"   Logging in (SSL)...")
                server.login(SMTP_USER, SMTP_PASS)
                print(f"   Sending...")
                server.sendmail(SMTP_USER, to_addr, msg.as_string())
                print(f"   ✅ Email sent!")
                return
        except:
            pass
        
        # Fallback to SMTP + STARTTLS
        with smtplib.SMTP(SMTP_HOST, 587, timeout=10) as server:
            print(f"   Starting TLS...")
            server.starttls()
            print(f"   Logging in (TLS)...")
            server.login(SMTP_USER, SMTP_PASS)
            print(f"   Sending...")
            server.sendmail(SMTP_USER, to_addr, msg.as_string())
            print(f"   ✅ Email sent!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

# ── /send-request (CORS headers included) ──────────────────────────────────────
@app.post("/send-request")
async def send_request(data: CallbackRequest):
    """Handle callback requests"""
    
    # Validation
    if not data.name.strip():
        return JSONResponse(
            {"success": False, "message": "Name is required"},
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )
    if not valid_email(data.email):
        return JSONResponse(
            {"success": False, "message": "Invalid email address"},
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )
    if not valid_phone(data.phone):
        return JSONResponse(
            {"success": False, "message": "Phone must be 10-15 digits"},
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    # Prepare data
    ref_id = gen_ref_id()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_name = escape_html(data.name.strip())
    clean_email = escape_html(data.email.strip())
    clean_phone = escape_html(data.phone.strip())
    clean_issue = escape_html(data.issue.strip())

    # Email to support
    support_html = f"""
    <html><body style="font-family: Arial; color: #333;">
    <h2 style="color: #FC8019;">🔔 New Callback Request</h2>
    <p><strong>Ref ID:</strong> {ref_id}</p>
    <p><strong>Time:</strong> {timestamp}</p>
    <hr>
    <p><strong>Name:</strong> {clean_name}</p>
    <p><strong>Email:</strong> {clean_email}</p>
    <p><strong>Phone:</strong> {clean_phone}</p>
    <hr>
    <p><strong>Issue:</strong></p>
    <p>{clean_issue.replace(chr(10), '<br>')}</p>
    </body></html>
    """

    try:
        send_email(SUPPORT_EMAIL, f"Callback #{ref_id}", support_html, clean_email)
    except Exception as e:
        return JSONResponse(
            {"success": False, "message": f"Error: {str(e)}"},
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    # Email to customer
    customer_html = f"""
    <html><body style="font-family: Arial; color: #333;">
    <h2 style="color: #FC8019;">✅ Request Received</h2>
    <p>Hi {clean_name},</p>
    <p>Thank you! We received your request.</p>
    <p><strong>Ref ID:</strong> {ref_id}</p>
    <p>We'll call you soon at {clean_phone}</p>
    <p>Or call us: <strong>800-988-8116</strong></p>
    </body></html>
    """

    try:
        send_email(clean_email, f"Request Received - {ref_id}", customer_html)
    except:
        pass  # Don't fail if confirmation email fails

    return JSONResponse(
        {
            "success": True,
            "message": "Thank you! Check your email for confirmation.",
            "ref_id": ref_id
        },
        status_code=200,
        headers={"Access-Control-Allow-Origin": "*"}
    )

# ── /chat (CORS headers included) ──────────────────────────────────────────────
@app.post("/chat")
async def chat(request: Request):
    """Chat endpoint"""
    try:
        body = await request.json()
        message = body.get("message", "").lower()
        
        return JSONResponse(
            {"response": "Hello! How can I help?", "success": True},
            status_code=200,
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        return JSONResponse(
            {"success": False, "message": str(e)},
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )

# ── /health ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Health check"""
    return JSONResponse(
        {"status": "ok", "message": "Zoiko Chatbot Running"},
        status_code=200,
        headers={"Access-Control-Allow-Origin": "*"}
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 🔴 CRITICAL: SERVE FRONTEND AT /ui
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/ui")
async def serve_ui():
    """Serve index.html at /ui"""
    if frontend_path and (frontend_path / "index.html").exists():
        return FileResponse(frontend_path / "index.html", media_type="text/html")
    return JSONResponse(
        {"error": "Frontend not found"},
        status_code=404,
        headers={"Access-Control-Allow-Origin": "*"}
    )

# ── Mount frontend as static files ─────────────────────────────────────────────
if frontend_path and frontend_path.exists():
    try:
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")
        print(f"✅ Frontend mounted at / from {frontend_path}\n")
    except Exception as e:
        print(f"⚠️  Could not mount frontend: {e}\n")

# ── STARTUP MESSAGE ────────────────────────────────────────────────────────────
print("\n╔════════════════════════════════════════════════════════════╗")
print("║  🚀 ZOIKO MOBILE CHATBOT BACKEND                           ║")
print("║  CORS: ✅ Enabled  SMTP: ✅ Configured                     ║")
print("╠════════════════════════════════════════════════════════════╣")
print("║  API ENDPOINTS:                                            ║")
print("║  GET    /ui                 (Frontend @ /ui)               ║")
print("║  GET    /                   (Static files)                 ║")
print("║  GET    /health             (Health check)                 ║")
print("║  POST   /send-request       (Callback requests)            ║")
print("║  POST   /chat               (Chat API)                     ║")
print("║  OPTIONS /*                 (CORS preflight)               ║")
print("╠════════════════════════════════════════════════════════════╣")
print("║  Status: ✅ Ready                                          ║")
print("╚════════════════════════════════════════════════════════════╝\n")