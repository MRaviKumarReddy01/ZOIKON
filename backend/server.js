

/**
 * Zoiko Mobile — Complete Backend Server with Email Integration
 * 
 * This server handles:
 * ✅ Callback requests from chatbot
 * ✅ Email to support team  
 * ✅ Confirmation emails to users
 * ✅ Phone number validation
 * ✅ Email validation
 * 
 * SETUP INSTRUCTIONS:
 * 1. npm install express nodemailer cors body-parser
 * 2. Update GMAIL_USER and GMAIL_PASS below with your credentials
 * 3. node server.js
 * 
 * GET GMAIL APP PASSWORD:
 * - Go to: https://myaccount.google.com/security
 * - Enable 2-Step Verification
 * - Create App Password for Mail
 * - Copy and paste into GMAIL_PASS below
 */

const express = require("express");
const nodemailer = require("nodemailer");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();

// ═══════════════════════════════════════════════════════════════════
//  MIDDLEWARE
// ═══════════════════════════════════════════════════════════════════

app.use(cors());
app.use(bodyParser.json());

// ═══════════════════════════════════════════════════════════════════
//  📧 EMAIL CONFIGURATION — UPDATE THESE!
// ═══════════════════════════════════════════════════════════════════

const GMAIL_USER = "support@zoikogroup.com";        // 👈 UPDATE THIS
const GMAIL_PASS = "NoxxMC26070%!LGM";         // 👈 UPDATE THIS (Gmail App Password)
const SUPPORT_EMAIL = "support@zoikomobile.com";  // 👈 UPDATE THIS if needed

const transporter = nodemailer.createTransport({
  host: "smtpout.secureserver.net",
  port: 465,
  secure: true,
  auth: {
    user: GMAIL_USER,
    pass: GMAIL_PASS
  }
});

// Test email configuration on startup
transporter.verify((error, success) => {
  if (error) {
    console.error('❌ Email configuration error:', error.message);
  } else {
    console.log('✅ Email service ready');
  }
});

// ═══════════════════════════════════════════════════════════════════
//  HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════

function generateRefId() {
  return 'ZKN-' + Date.now().toString().slice(-6);
}

function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

function validatePhone(phone) {
  const phoneOnlyDigits = phone.replace(/\D/g, '');
  return phoneOnlyDigits.length >= 10 && phoneOnlyDigits.length <= 15;
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

// ═══════════════════════════════════════════════════════════════════
//  API ENDPOINT: POST /send-request
// ═══════════════════════════════════════════════════════════════════

app.post("/send-request", async (req, res) => {
  const { name, email, phone, issue } = req.body;

  // ─────────────────────────────────────────────────────────────────
  // VALIDATION
  // ─────────────────────────────────────────────────────────────────
  
  if (!name || !name.trim()) {
    return res.json({ 
      success: false, 
      message: "Name is required" 
    });
  }

  if (!email || !email.trim()) {
    return res.json({ 
      success: false, 
      message: "Email is required" 
    });
  }

  if (!validateEmail(email)) {
    return res.json({ 
      success: false, 
      message: "Invalid email address" 
    });
  }

  if (!phone || !phone.trim()) {
    return res.json({ 
      success: false, 
      message: "Phone number is required" 
    });
  }

  if (!validatePhone(phone)) {
    return res.json({ 
      success: false, 
      message: "Phone number must be 10-15 digits" 
    });
  }

  if (!issue || !issue.trim()) {
    return res.json({ 
      success: false, 
      message: "Please describe how we can help" 
    });
  }

  // ─────────────────────────────────────────────────────────────────
  // PREPARE DATA
  // ─────────────────────────────────────────────────────────────────

  const refId = generateRefId();
  const timestamp = new Date().toLocaleString();
  const cleanName = escapeHtml(name.trim());
  const cleanEmail = email.trim();
  const cleanPhone = phone.trim();
  const cleanIssue = escapeHtml(issue.trim());

  // ─────────────────────────────────────────────────────────────────
  // SEND EMAILS
  // ─────────────────────────────────────────────────────────────────

  try {
    
    // ─── EMAIL 1: TO SUPPORT TEAM ──────────────────────────────────

    const supportEmailHtml = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          * { margin: 0; padding: 0; }
          body { font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { 
            background: linear-gradient(135deg, #FC8019 0%, #FF9A40 100%); 
            color: white; 
            padding: 25px; 
            border-radius: 8px 8px 0 0; 
            text-align: center;
          }
          .header h2 { margin: 0; font-size: 24px; }
          .content { 
            background: #f9f9f9; 
            padding: 25px; 
            border: 1px solid #ddd;
            border-top: none;
          }
          .field { margin-bottom: 20px; }
          .label { 
            font-weight: 700; 
            color: #FC8019; 
            margin-bottom: 8px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .value { 
            color: #333; 
            padding: 12px; 
            background: white; 
            border-left: 4px solid #FC8019;
            border-radius: 2px;
          }
          .footer { 
            background: #f0f0f0; 
            padding: 20px; 
            text-align: center; 
            font-size: 12px; 
            color: #666;
            border-top: 1px solid #ddd;
          }
          .ref-id { color: #FC8019; font-weight: bold; font-size: 14px; }
          .urgent { color: #e74c3c; font-weight: bold; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h2>🎧 New Callback Request</h2>
          </div>
          
          <div class="content">
            <div class="field">
              <div class="label">👤 Customer Name</div>
              <div class="value">${cleanName}</div>
            </div>
            
            <div class="field">
              <div class="label">📧 Email Address</div>
              <div class="value"><a href="mailto:${cleanEmail}" style="color: #FC8019; text-decoration: none;">${cleanEmail}</a></div>
            </div>
            
            <div class="field">
              <div class="label">📱 Phone Number</div>
              <div class="value"><a href="tel:${cleanPhone.replace(/\D/g, '')}" style="color: #FC8019; text-decoration: none;">${cleanPhone}</a></div>
            </div>
            
            <div class="field">
              <div class="label">❓ Request Details</div>
              <div class="value" style="white-space: pre-wrap;">${cleanIssue.replace(/\n/g, '<br>')}</div>
            </div>
          </div>
          
          <div class="footer">
            <p style="margin: 10px 0;">
              <strong>Reference ID:</strong> <span class="ref-id">${refId}</span>
            </p>
            <p style="margin: 8px 0;">
              <strong>Received:</strong> ${timestamp}
            </p>
            <p style="margin: 8px 0; font-size: 11px;">
              <em>🎯 Please respond to this customer within 24 hours</em>
            </p>
          </div>
        </div>
      </body>
      </html>
    `;

    await transporter.sendMail({
      from: GMAIL_USER,
      to: SUPPORT_EMAIL,
      subject: `📲 New Callback Request from ${cleanName}`,
      html: supportEmailHtml
    });

    console.log(`✅ Support email sent: ${refId} → ${SUPPORT_EMAIL}`);

    // ─── EMAIL 2: CONFIRMATION TO USER ─────────────────────────────

    const userEmailHtml = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          * { margin: 0; padding: 0; }
          body { font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { 
            background: linear-gradient(135deg, #FC8019 0%, #FF9A40 100%); 
            color: white; 
            padding: 40px 25px;
            border-radius: 8px 8px 0 0; 
            text-align: center;
          }
          .checkmark { 
            font-size: 48px; 
            margin-bottom: 15px;
            display: block;
          }
          .header h2 { margin: 0; font-size: 26px; }
          .content { 
            background: white; 
            padding: 30px; 
            border: 1px solid #ddd;
            border-top: none;
          }
          .content p { margin: 15px 0; }
          .info-box { 
            background: #f0f8ff; 
            border-left: 4px solid #FC8019; 
            padding: 15px; 
            margin: 20px 0;
            border-radius: 2px;
          }
          .ref-box { 
            background: #fff8e1; 
            border: 2px solid #FC8019; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 20px 0; 
            text-align: center;
          }
          .ref-id { 
            font-size: 20px; 
            color: #FC8019; 
            font-weight: bold;
            display: block;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
          }
          .quick-contact { 
            background: #f5f5f5; 
            padding: 20px; 
            border-radius: 5px;
            margin: 20px 0;
          }
          .contact-item { 
            margin: 10px 0; 
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
          }
          .contact-item:last-child { border-bottom: none; }
          .contact-label { 
            color: #FC8019; 
            font-weight: bold;
          }
          a { color: #FC8019; text-decoration: none; }
          a:hover { text-decoration: underline; }
          .footer { 
            background: #f9f9f9; 
            padding: 25px; 
            text-align: center; 
            font-size: 12px; 
            color: #666;
            border-top: 1px solid #ddd;
          }
          .footer-text { margin: 5px 0; }
          .highlight { color: #FC8019; font-weight: bold; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <span class="checkmark">✅</span>
            <h2>Request Received!</h2>
          </div>
          
          <div class="content">
            <p style="font-size: 16px;">Hi <span class="highlight">${cleanName.split(' ')[0]}</span>,</p>
            
            <p>Thank you for reaching out to Zoiko Mobile! We've received your callback request and our support team will contact you within <strong>24 hours</strong>.</p>
            
            <div class="info-box">
              <strong style="display: block; margin-bottom: 8px;">📞 We'll call you at:</strong>
              <span style="font-size: 16px; color: #FC8019; font-weight: bold;">${cleanPhone}</span>
            </div>
            
            <div class="ref-box">
              <strong style="font-size: 12px; color: #999;">YOUR REFERENCE ID</strong>
              <div class="ref-id">${refId}</div>
              <span style="font-size: 11px; color: #666;">Keep this for your records</span>
            </div>
            
            <h3 style="color: #333; margin: 25px 0 15px 0; font-size: 16px;">Can't wait? Quick contact options:</h3>
            
            <div class="quick-contact">
              <div class="contact-item">
                <span class="contact-label">📞 Call 24/7:</span>
                <a href="tel:+18009888116">800-988-8116</a>
              </div>
              <div class="contact-item">
                <span class="contact-label">🌐 Visit us:</span>
                <a href="https://zoikomobile.com">zoikomobile.com</a>
              </div>
              <div class="contact-item">
                <span class="contact-label">💬 Live Chat:</span>
                Available on our website (business hours)
              </div>
              <div class="contact-item">
                <span class="contact-label">📧 Email:</span>
                <a href="mailto:support@zoikomobile.com">support@zoikomobile.com</a>
              </div>
            </div>
            
            <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
              Thanks for choosing Zoiko Mobile! 💚
            </p>
          </div>
          
          <div class="footer">
            <p class="footer-text">© 2026 Zoiko Mobile. All rights reserved.</p>
            <p class="footer-text" style="font-size: 10px; color: #999;">
              <em>Your information is secure and will never be shared with third parties.</em>
            </p>
          </div>
        </div>
      </body>
      </html>
    `;

    await transporter.sendMail({
      from: GMAIL_USER,
      to: cleanEmail,
      subject: `✅ We Received Your Request — Zoiko Mobile (${refId})`,
      html: userEmailHtml
    });

    console.log(`✅ Confirmation email sent: ${cleanEmail}`);

    // ─────────────────────────────────────────────────────────────────
    // SUCCESS RESPONSE
    // ─────────────────────────────────────────────────────────────────

    res.json({ 
      success: true, 
      message: "Request submitted successfully",
      refId: refId,
      email: cleanEmail,
      phone: cleanPhone
    });

  } catch (error) {
    console.error("❌ Error:", error.message);
    
    res.json({ 
      success: false, 
      message: "Error processing request. Please try again.",
      error: error.message 
    });
  }
});

// ═══════════════════════════════════════════════════════════════════
//  HEALTH CHECK ENDPOINT
// ═══════════════════════════════════════════════════════════════════

app.get("/health", (req, res) => {
  res.json({ 
    status: "✅ Server is healthy",
    time: new Date().toLocaleString(),
    service: "Zoiko Mobile Chatbot Backend",
    version: "1.0"
  });
});

// ═══════════════════════════════════════════════════════════════════
//  404 HANDLER
// ═══════════════════════════════════════════════════════════════════

app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: "Endpoint not found",
    available: [
      "POST /send-request",
      "GET /health"
    ]
  });
});

// ═══════════════════════════════════════════════════════════════════
//  START SERVER
// ═══════════════════════════════════════════════════════════════════

const PORT = process.env.PORT || 5000;

const server = app.listen(PORT, () => {
  console.log("\n");
  console.log("╔════════════════════════════════════════════╗");
  console.log("║  🎧 ZOIKO MOBILE BACKEND SERVER           ║");
  console.log("╠════════════════════════════════════════════╣");
  console.log("║  ✅ Status: Running                        ║");
  console.log(`║  📍 Port: ${PORT.toString().padEnd(38)} ║`);
  console.log("║  📧 Email: Configured                     ║");
  console.log("║  🎯 Ready: YES                            ║");
  console.log("╚════════════════════════════════════════════╝\n");
  
  console.log("📌 API ENDPOINTS:");
  console.log(`   POST http://localhost:${PORT}/send-request`);
  console.log(`   GET  http://localhost:${PORT}/health\n`);
  
  console.log("⏸️  To stop the server: Press Ctrl+C\n");
});

// ═══════════════════════════════════════════════════════════════════
//  ERROR HANDLERS
// ═══════════════════════════════════════════════════════════════════

process.on('uncaughtException', (err) => {
  console.error('❌ Uncaught Exception:', err.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection:', reason);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use!`);
    console.error(`   Try: node server.js (with different PORT)`);
  } else {
    console.error('❌ Server error:', err.message);
  }
  process.exit(1);
});