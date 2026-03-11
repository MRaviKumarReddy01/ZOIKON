from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json, smtplib, re, time, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

app = FastAPI()

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── EMAIL CONFIG - FROM ENVIRONMENT VARIABLES ─────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "smtpout.secureserver.net")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER     = os.getenv("SMTP_USER", "support@zoikogroup.com")
SMTP_PASS     = os.getenv("SMTP_PASS", "")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@zoikomobile.com")

# ✅ NEW: Gmail as fallback (more reliable on GCP)
USE_GMAIL = os.getenv("USE_GMAIL", "false").lower() == "true"
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")

# ── STATIC FRONTEND ───────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent
frontend_path = BASE_DIR / "frontend"
print("✅ Frontend path:", frontend_path)

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
    return "ZKN-" + str(int(time.time() * 1000))[-6:]

def valid_email(e: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", e))

def valid_phone(p: str) -> bool:
    digits = re.sub(r"\D", "", p)
    return 10 <= len(digits) <= 15

def escape_html(s: str) -> str:
    return (s.replace("&","&amp;").replace("<","&lt;")
             .replace(">","&gt;").replace('"',"&quot;").replace("'","&#039;"))

def send_email(to_addr: str, subject: str, html_body: str):
    """
    ✅ Enhanced email sending with fallback
    - Primary: Use configured SMTP (GoDaddy/custom)
    - Fallback: Use Gmail (more reliable on GCP)
    """
    try:
        if USE_GMAIL and GMAIL_USER and GMAIL_PASS:
            print(f"📧 Sending via Gmail to {to_addr}")
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = GMAIL_USER
            msg["To"]      = to_addr
            msg.attach(MIMEText(html_body, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(GMAIL_USER, GMAIL_PASS)
                server.sendmail(GMAIL_USER, to_addr, msg.as_string())
            print(f"✅ Email sent via Gmail")
        else:
            print(f"📧 Sending via {SMTP_HOST} to {to_addr}")
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = SMTP_USER
            msg["To"]      = to_addr
            msg.attach(MIMEText(html_body, "html"))
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, to_addr, msg.as_string())
            print(f"✅ Email sent via {SMTP_HOST}")
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        raise

# ── /send-request ─────────────────────────────────────────────────────────────
@app.post("/send-request")
async def send_request(data: CallbackRequest):

    # ── Validation ────────────────────────────────────────────────────────────
    if not data.name.strip():
        return JSONResponse({"success": False, "message": "Name is required"})
    if not data.email.strip():
        return JSONResponse({"success": False, "message": "Email is required"})
    if not valid_email(data.email):
        return JSONResponse({"success": False, "message": "Invalid email address"})
    if not data.phone.strip():
        return JSONResponse({"success": False, "message": "Phone number is required"})
    if not valid_phone(data.phone):
        return JSONResponse({"success": False, "message": "Phone number must be 10-15 digits"})
    if not data.issue.strip():
        return JSONResponse({"success": False, "message": "Please describe how we can help"})

    ref_id      = gen_ref_id()
    clean_name  = escape_html(data.name.strip())
    clean_email = data.email.strip()
    clean_phone = data.phone.strip()
    clean_issue = escape_html(data.issue.strip()).replace("\n", "<br>")
    first_name  = clean_name.split()[0]

    # ── Email to support team ─────────────────────────────────────────────────
    support_html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
      body{{font-family:'Segoe UI',Arial,sans-serif;color:#333;line-height:1.6}}
      .container{{max-width:600px;margin:0 auto;padding:20px}}
      .header{{background:linear-gradient(135deg,#CC0000,#880000);color:white;padding:25px;border-radius:8px 8px 0 0;text-align:center}}
      .content{{background:#f9f9f9;padding:25px;border:1px solid #ddd;border-top:none}}
      .label{{font-weight:700;color:#CC0000;margin-bottom:8px;font-size:12px;text-transform:uppercase;letter-spacing:.5px}}
      .value{{color:#333;padding:12px;background:white;border-left:4px solid #CC0000;border-radius:2px;margin-bottom:20px}}
      .footer{{background:#f0f0f0;padding:20px;text-align:center;font-size:12px;color:#666;border-top:1px solid #ddd}}
      .ref{{color:#CC0000;font-weight:bold}}
    </style></head><body>
    <div class="container">
      <div class="header"><h2>🎧 New Callback Request — {ref_id}</h2></div>
      <div class="content">
        <div class="label">👤 Customer Name</div>
        <div class="value">{clean_name}</div>
        <div class="label">📧 Email</div>
        <div class="value"><a href="mailto:{clean_email}" style="color:#CC0000">{clean_email}</a></div>
        <div class="label">📱 Phone</div>
        <div class="value"><a href="tel:{re.sub(r'\\D','',clean_phone)}" style="color:#CC0000">{clean_phone}</a></div>
        <div class="label">❓ Request Details</div>
        <div class="value" style="white-space:pre-wrap">{clean_issue}</div>
      </div>
      <div class="footer">Reference: <span class="ref">{ref_id}</span> · Zoiko Mobile Support</div>
    </div></body></html>"""

    # ── Confirmation email to customer ────────────────────────────────────────
    user_html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
      body{{font-family:'Segoe UI',Arial,sans-serif;color:#333;line-height:1.6}}
      .container{{max-width:600px;margin:0 auto;padding:20px}}
      .header{{background:linear-gradient(135deg,#CC0000,#880000);color:white;padding:40px 25px;border-radius:8px 8px 0 0;text-align:center}}
      .content{{background:white;padding:30px;border:1px solid #ddd;border-top:none}}
      .ref-box{{background:#fff8e1;border:2px solid #CC0000;padding:15px;border-radius:5px;margin:20px 0;text-align:center}}
      .ref-id{{font-size:20px;color:#CC0000;font-weight:bold;font-family:'Courier New',monospace;display:block;margin:10px 0}}
      .info-box{{background:#fff0f0;border-left:4px solid #CC0000;padding:15px;margin:20px 0}}
      .contact-item{{margin:10px 0;padding:8px 0;border-bottom:1px solid #eee}}
      .contact-item:last-child{{border-bottom:none}}
      a{{color:#CC0000;text-decoration:none}}
      .footer{{background:#f9f9f9;padding:25px;text-align:center;font-size:12px;color:#666;border-top:1px solid #ddd}}
    </style></head><body>
    <div class="container">
      <div class="header">
        <div style="font-size:48px;margin-bottom:15px">✅</div>
        <h2>Request Received!</h2>
      </div>
      <div class="content">
        <p style="font-size:16px">Hi <strong style="color:#CC0000">{first_name}</strong>,</p>
        <p style="margin:15px 0">Thank you for reaching out to Zoiko Mobile! Our support team will contact you within <strong>24 hours</strong>.</p>
        <div class="info-box">
          <strong>📞 We'll call you at:</strong><br>
          <span style="font-size:16px;color:#CC0000;font-weight:bold">{clean_phone}</span>
        </div>
        <div class="ref-box">
          <strong style="font-size:12px;color:#999">YOUR REFERENCE ID</strong>
          <div class="ref-id">{ref_id}</div>
          <span style="font-size:11px;color:#666">Keep this for your records</span>
        </div>
        <h3 style="color:#333;margin:25px 0 15px">Can't wait? Contact us directly:</h3>
        <div style="background:#f5f5f5;padding:20px;border-radius:5px">
          <div class="contact-item"><strong style="color:#CC0000">📞 Call 24/7:</strong> <a href="tel:+18009888116">800-988-8116</a></div>
          <div class="contact-item"><strong style="color:#CC0000">🌐 Website:</strong> <a href="https://zoikomobile.com">zoikomobile.com</a></div>
          <div class="contact-item"><strong style="color:#CC0000">📧 Email:</strong> <a href="mailto:support@zoikomobile.com">support@zoikomobile.com</a></div>
        </div>
        <p style="margin-top:30px;padding-top:20px;border-top:1px solid #eee">Thanks for choosing Zoiko Mobile! 🎉</p>
      </div>
      <div class="footer">© 2026 Zoiko Mobile. All rights reserved.</div>
    </div></body></html>"""

    try:
        send_email(SUPPORT_EMAIL, f"🎧 New Callback Request — {clean_name} ({ref_id})", support_html)
        send_email(clean_email,  f"✅ We Received Your Request — Zoiko Mobile ({ref_id})", user_html)
        return JSONResponse({
            "success": True,
            "message": "Request submitted successfully",
            "refId":   ref_id,
            "email":   clean_email,
            "phone":   clean_phone
        })
    except Exception as e:
        print(f"❌ Email error: {e}")
        return JSONResponse({
            "success": False,
            "message": "Error sending email. Please try again or call 800-988-8116.",
            "error":   str(e)
        }, status_code=500)

# ── /health ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":  "✅ Server is healthy",
        "service": "Zoiko Mobile Chatbot Backend",
        "version": "2.0",
        "email_configured": bool(SMTP_PASS or (USE_GMAIL and GMAIL_PASS))
    }

# ── Knowledge base chat ───────────────────────────────────────────────────────
def load_knowledge():
    p = Path("data/knowledge.json")
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}

knowledge = load_knowledge()

@app.post("/chat")
def chat(msg: Message):
    user_msg = msg.message.lower()
    for k, v in knowledge.items():
        if k in user_msg:
            return {"response": v}
    return {"response": "I don't know yet."}

# ── Serve frontend LAST (catch-all) ──────────────────────────────────────────
if frontend_path.exists():
    app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

# ── Startup message ───────────────────────────────────────────────────────────
print("=" * 80)
print("✅ Zoikon Chatbot Backend Started")
print("=" * 80)
print(f"Email Service: {'Gmail' if USE_GMAIL else 'Custom SMTP'}")
print(f"SMTP Host: {SMTP_HOST if not USE_GMAIL else 'smtp.gmail.com'}")
print(f"Support Email: {SUPPORT_EMAIL}")
print("=" * 80)