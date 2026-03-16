from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json, smtplib, re, time, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from fastapi import Form
from datetime import datetime

app = FastAPI()

# ═══════════════════════════════════════════════════════════════════════════════
# 🔴 CRITICAL: CORS MIDDLEWARE - MUST BE FIRST BEFORE ANY OTHER MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                    # Allow all origins
    allow_credentials=True,                 # CRITICAL: Allow credentials
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],                    # Allow all headers
    max_age=3600,                           # Cache preflight for 1 hour
)

# ═══════════════════════════════════════════════════════════════════════════════
# 🟢 EXPLICIT OPTIONS HANDLER - Catches all preflight requests
# ═══════════════════════════════════════════════════════════════════════════════
@app.options("/{full_path:path}", include_in_schema=False)
async def preflight(full_path: str):
    """Handle CORS preflight (OPTIONS) requests for ALL paths"""
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

# ── EMAIL CONFIG — env vars first, hardcoded fallback ─────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST",     "smtpout.secureserver.net")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER     = os.getenv("SMTP_USER",     "support@zoikogroup.com")
SMTP_PASS     = os.getenv("SMTP_PASS",     "NoxxMC26070%!LGM")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@zoikogroup.com")

print(f"\n📧 EMAIL CONFIGURATION:")
print(f"   SMTP Host: {SMTP_HOST}")
print(f"   SMTP Port: {SMTP_PORT}")
print(f"   From Email: {SMTP_USER}")
print(f"   Support Email: {SUPPORT_EMAIL}")

# ── STATIC FRONTEND - MULTIPLE PATH STRATEGIES ─────────────────────────────────
possible_paths = [
    Path(__file__).resolve().parent.parent / "frontend",
    Path(__file__).resolve().parent / "frontend",
    Path("frontend"),
    Path("../frontend"),
]

frontend_path = None
for path in possible_paths:
    if path.exists() and (path / "index.html").exists():
        frontend_path = path
        print(f"✅ Frontend found at: {frontend_path}")
        break

if not frontend_path:
    print(f"⚠️  Frontend not found. Checked:")
    for path in possible_paths:
        print(f"   - {path}")
    frontend_path = possible_paths[0]

# ── MODELS ────────────────────────────────────────────────────────────────────
class CallbackRequest(BaseModel):
    name:  str
    email: str
    phone: str
    issue: str

class Message(BaseModel):
    message: str

# ── HELPERS ───────────────────────────────────────────────────────────────────
def gen_ref_id():
    """Generate reference ID from timestamp"""
    return "ZKN-" + str(int(time.time() * 1000))[-6:]

def valid_email(e: str) -> bool:
    """Validate email format"""
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", e))

def valid_phone(p: str) -> bool:
    """Validate phone number (10-15 digits)"""
    digits = re.sub(r"\D", "", p)
    return 10 <= len(digits) <= 15

def escape_html(s: str) -> str:
    """Escape HTML special characters"""
    return (s.replace("&","&amp;").replace("<","&lt;")
             .replace(">","&gt;").replace('"',"&quot;").replace("'","&#039;"))

def send_email(to_addr: str, subject: str, html_body: str, reply_to: str = None):
    """
    Send email via company SMTP.
    reply_to: optional Reply-To address (set to customer email on support emails)
    """
    print(f"\n📧 Sending email to: {to_addr}")
    print(f"   Subject: {subject}")
    print(f"   Via: {SMTP_HOST}:{SMTP_PORT}")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_USER
        msg["To"]      = to_addr
        if reply_to:
            msg["Reply-To"] = reply_to   # ← support can hit Reply to reach customer directly
        msg.attach(MIMEText(html_body, "html"))

        print(f"   Connecting to SMTP server...")
        with smtplib.SMTP(SMTP_HOST, 587, timeout=10) as server:
            print("   Connected! Starting TLS...")
            server.starttls()
            print("   TLS started. Logging in...")
            server.login(SMTP_USER, SMTP_PASS)
            print("   Logged in! Sending email...")
            server.sendmail(SMTP_USER, to_addr, msg.as_string())
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            print(f"   Connected! Logging in...")
            server.login(SMTP_USER, SMTP_PASS)
            print(f"   Logged in! Sending email...")
            server.sendmail(SMTP_USER, to_addr, msg.as_string())
            print(f"   ✅ Email sent successfully to {to_addr}")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error: {str(e)}")
        raise
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
from fastapi.responses import HTMLResponse

@app.get("/send-request", response_class=HTMLResponse)
async def send_request_form():
    return """
    <html>
    <head><title>Send Callback Request</title></head>
    <body>
        <h2>Zoiko Mobile Callback Request</h2>
        <form method="post" action="/send-request">
            Name:<br>
            <input name="name"><br><br>

            Email:<br>
            <input name="email"><br><br>

            Phone:<br>
            <input name="phone"><br><br>

            Issue:<br>
            <textarea name="issue"></textarea><br><br>

            <button type="submit">Send Request</button>
        </form>
    </body>
    </html>
    """

# ── /send-request ─────────────────────────────────────────────────────────────
@app.post("/send-request")
async def send_request(data: CallbackRequest):

    # ── Validation ────────────────────────────────────────────────────────────
    if not data.name.strip():
        return JSONResponse(
            {"success": False, "message": "Name is required"},
            status_code=400,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    if not data.email.strip():
        return JSONResponse(
            {"success": False, "message": "Email is required"},
            status_code=400,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    if not valid_email(data.email):
        return JSONResponse(
            {"success": False, "message": "Invalid email address"},
            status_code=400,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    if not data.phone.strip():
        return JSONResponse(
            {"success": False, "message": "Phone number is required"},
            status_code=400,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    if not valid_phone(data.phone):
        return JSONResponse(
            {"success": False, "message": "Phone number must be 10-15 digits"},
            status_code=400,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    if not data.issue.strip():
        return JSONResponse(
            {"success": False, "message": "Please describe how we can help"},
            status_code=400,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

    # ── Prepare data ──────────────────────────────────────────────────────────
    ref_id       = gen_ref_id()
    timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_name   = escape_html(data.name.strip())
    clean_email  = escape_html(data.email.strip())
    clean_phone  = escape_html(data.phone.strip())
    clean_issue  = escape_html(data.issue.strip())

    # ── SEND EMAIL TO SUPPORT ──────────────────────────────────────────────────
    support_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #FC8019;">🔔 New Zoiko Mobile Callback Request</h2>
        
        <p><strong>Reference ID:</strong> {ref_id}</p>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        
        <hr style="border: none; border-top: 2px solid #FC8019;">
        
        <h3>Customer Details</h3>
        <ul>
            <li><strong>Name:</strong> {clean_name}</li>
            <li><strong>Email:</strong> {clean_email}</li>
            <li><strong>Phone:</strong> {clean_phone}</li>
        </ul>
        
        <h3>Issue / Request</h3>
        <p style="background-color: #f5f5f5; padding: 10px; border-left: 4px solid #FC8019;">
            {clean_issue.replace(chr(10), '<br>')}
        </p>
        
        <hr style="border: none; border-top: 2px solid #FC8019;">
        
        <p><strong>Action Required:</strong> Contact customer at {clean_phone} or {clean_email}</p>
        <p style="color: #999; font-size: 12px;">This is an automated message from Zoiko Mobile Chatbot</p>
    </body>
    </html>
    """

    try:
        send_email(SUPPORT_EMAIL, f"🔔 Callback Request #{ref_id}", support_html, clean_email)
    except Exception as e:
        print(f"❌ Failed to send support email: {str(e)}")
        return JSONResponse(
            {"success": False, "message": f"Error: {str(e)}"},
            status_code=500,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

    # ── SEND CONFIRMATION EMAIL TO CUSTOMER ────────────────────────────────────
    customer_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #FC8019;">✅ Callback Request Received</h2>
        
        <p>Hi {clean_name},</p>
        
        <p>Thank you for contacting Zoiko Mobile! We've received your callback request.</p>
        
        <p><strong>Reference ID:</strong> {ref_id}</p>
        <p><strong>We will contact you at:</strong> {clean_phone}</p>
        
        <hr style="border: none; border-top: 2px solid #FC8019;">
        
        <p>Our support team will reach out to you soon to assist with your request.</p>
        
        <p>
            <strong>In the meantime:</strong><br>
            • Visit <a href="https://zoikomobile.com">zoikomobile.com</a> for FAQs<br>
            • Call <strong>800-988-8116</strong> for immediate support<br>
            • Check your email for updates
        </p>
        
        <hr style="border: none; border-top: 2px solid #FC8019;">
        
        <p style="color: #999; font-size: 12px;">
            Zoiko Mobile Support Team<br>
            Reference: {ref_id}
        </p>
    </body>
    </html>
    """

    try:
        send_email(clean_email, f"✅ Callback Request Received - {ref_id}", customer_html)
    except Exception as e:
        print(f"⚠️  Warning: Failed to send confirmation email: {str(e)}")
        # Don't fail the request if confirmation email fails

    # ── SUCCESS RESPONSE ───────────────────────────────────────────────────────
    return JSONResponse(
        {
            "success": True,
            "message": "Thank you! We received your callback request. Check your email for confirmation.",
            "ref_id": ref_id
        },
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ── /chat ──────────────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(request: Request):
    """Placeholder for chat endpoint"""
    try:
        body = await request.json()
        message = body.get("message", "").lower()
        
        return JSONResponse(
            {
                "response": "Hello! I'm Zoikon, the Zoiko Mobile AI Assistant. How can I help you today?",
                "success": True
            },
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        return JSONResponse(
            {"success": False, "message": str(e)},
            status_code=500,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

# ── /health ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse(
        {"status": "ok", "message": "Zoiko Mobile Chatbot is running"},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ── MOUNT FRONTEND ─────────────────────────────────────────────────────────────
if frontend_path and frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    print(f"✅ Frontend mounted at /")

# ── STARTUP INFO ───────────────────────────────────────────────────────────────
print("\n")
print("║════════════════════════════════════════════════════════════════╗")
print("║         🚀 Zoiko Mobile Chatbot Server Ready!                  ║")
print("║════════════════════════════════════════════════════════════════║")
print("║  GET   /ui                  (Chatbot interface)                ║")
print("║  GET   /health              (Health check)                     ║")
print("║  POST  /chat                (Chat with AI)                     ║")
print("║  POST  /send-request        (Callback requests)                ║")
print("║  OPTIONS /*                 (CORS preflight)                   ║")
print("║════════════════════════════════════════════════════════════════║")
print("║  CORS: ✅ Enabled for all origins                              ║")
print("║  SMTP: ✅ Configured                                           ║")
print("║════════════════════════════════════════════════════════════════║\n")