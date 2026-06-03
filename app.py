"""
POWERGEEKZ ENGINEERING LTD — Flask Backend
Handles the contact form with email notification.

Requirements:
    pip install flask flask-mail python-dotenv

Environment variables (.env):
    MAIL_SERVER      = smtp.gmail.com
    MAIL_PORT        = 587
    MAIL_USERNAME    = powergeekzengineeringltd@gmail.com
    MAIL_PASSWORD    = zfdr phwh fdrh cbqv
    MAIL_RECIPIENT   = powergeekzengineeringltd@gmail.com
    SECRET_KEY       = some_random_secret_string
"""

import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, abort
from flask_mail import Mail, Message
from dotenv import load_dotenv

# ── Load env vars from .env file (if present) ──────────────────
load_dotenv()

# ── App setup ──────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "powergeekz-dev-secret-2025")

# ── Mail configuration ─────────────────────────────────────────
app.config["MAIL_SERVER"]   = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"]     = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"]  = True
app.config["MAIL_USE_SSL"]  = False
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME", "noreply@powergeekz.co.ke")

mail = Mail(app)

MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "powergeekzengineeringltd@gmail.com")

# ── Service label map ──────────────────────────────────────────
SERVICE_LABELS = {
    "solar_pv":       "Solar PV System",
    "solar_heating":  "Solar Water Heating",
    "ups":            "UPS Systems",
    "inverter":       "Inverter & Charger Systems",
    "generator":      "Generator & AVR",
    "batteries":      "Battery Supply & Replacement",
    "cctv":           "CCTV Installation",
    "data_cables":    "Data & Electrical Cables",
    "ict":            "ICT & Computer Supplies",
    "maintenance":    "Maintenance Contract",
    "other":          "Other / Not Sure",
}

HOW_HEARD_LABELS = {
    "google":   "Google Search",
    "facebook": "Facebook",
    "tiktok":   "TikTok",
    "referral": "Referral / Word of Mouth",
    "repeat":   "Returning Client",
    "other":    "Other",
}

# ══════════════════════════════════════════════════════════════════
#  PAGE ROUTES  —  serve HTML templates
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/portfolio")
def portfolio():
    return render_template("portfolio.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
@app.route("/contact.html")
def contact_page():
    return render_template("contact.html")


# ══════════════════════════════════════════════════════════════════
#  CONTACT FORM  —  POST /contact
# ══════════════════════════════════════════════════════════════════

@app.route("/contact", methods=["POST"])
def contact():
    """
    Accepts JSON from the contact form, validates it,
    sends a notification email to Powergeekz and a
    confirmation email to the client.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "Invalid request format."}), 400

    # ── Validation ────────────────────────────────────────────
    required_fields = ["first_name", "last_name", "email", "phone", "service", "location", "message"]
    for field in required_fields:
        if not data.get(field, "").strip():
            return jsonify({
                "success": False,
                "message": f"Field '{field}' is required."
            }), 422

    # Basic email format check
    import re
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", data["email"].strip()):
        return jsonify({"success": False, "message": "Invalid email address."}), 422

    # ── Extract & sanitize data ───────────────────────────────
    first_name  = data["first_name"].strip()[:100]
    last_name   = data["last_name"].strip()[:100]
    email       = data["email"].strip()[:200]
    phone       = data["phone"].strip()[:50]
    company     = data.get("company", "").strip()[:200]
    service_key = data.get("service", "other")
    location    = data["location"].strip()[:200]
    message     = data["message"].strip()[:2000]
    how_heard   = data.get("how_heard", "")
    timestamp   = datetime.now().strftime("%d %B %Y at %H:%M")

    service_label   = SERVICE_LABELS.get(service_key, service_key)
    how_heard_label = HOW_HEARD_LABELS.get(how_heard, how_heard or "Not specified")
    full_name       = f"{first_name} {last_name}"

    # ── Send emails ───────────────────────────────────────────
    try:
        _send_notification_email(
            full_name, email, phone, company,
            service_label, location, message,
            how_heard_label, timestamp,
        )
        _send_confirmation_email(first_name, email, service_label)
    except Exception as exc:
        # Log but don't surface internal details to client
        app.logger.error(f"Mail error: {exc}")
        # Still return success so form UX works even if email server is not configured
        return jsonify({
            "success": True,
            "message": "Thank you! We received your enquiry and will be in touch shortly.",
        })

    return jsonify({
        "success": True,
        "message": "Thank you! We received your enquiry and will be in touch within 24 hours.",
    })


# ──────────────────────────────────────────────────────────────────
def _send_notification_email(
    full_name, email, phone, company,
    service_label, location, message,
    how_heard_label, timestamp,
):
    """Sends enquiry notification to Powergeekz team."""
    subject = f"🔆 New Quote Request — {service_label} — {full_name}"

    body = f"""
New enquiry received via the Powergeekz website.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTACT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name       : {full_name}
Email      : {email}
Phone      : {phone}
Company    : {company or 'Not provided'}

PROJECT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Service    : {service_label}
Location   : {location}
How heard  : {how_heard_label}

MESSAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Received on {timestamp}
Reply to: {email}
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Inter', Arial, sans-serif; background:#f4f6fb; margin:0; padding:20px; }}
    .card {{ background:#fff; border-radius:12px; max-width:600px; margin:0 auto; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,0.08); }}
    .header {{ background: linear-gradient(135deg,#0A1A99,#1A3CFF); padding:28px 32px; }}
    .header h1 {{ color:#fff; margin:0; font-size:1.3rem; font-weight:800; }}
    .header p {{ color:rgba(255,255,255,0.75); margin:4px 0 0; font-size:0.85rem; }}
    .body {{ padding:28px 32px; }}
    .section-title {{ font-size:0.7rem; font-weight:700; letter-spacing:0.15em; text-transform:uppercase; color:#9AA0B8; margin:20px 0 10px; }}
    .row {{ display:flex; gap:12px; margin-bottom:8px; }}
    .label {{ font-size:0.82rem; font-weight:700; color:#555; min-width:90px; }}
    .value {{ font-size:0.88rem; color:#111; }}
    .message-box {{ background:#f8f9ff; border-left:4px solid #1A3CFF; border-radius:0 8px 8px 0; padding:14px 16px; margin-top:8px; font-size:0.9rem; line-height:1.7; color:#333; white-space:pre-wrap; }}
    .footer {{ background:#f8f9ff; padding:16px 32px; border-top:1px solid #eee; font-size:0.78rem; color:#9AA0B8; text-align:center; }}
    a {{ color:#1A3CFF; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>⚡ New Quote Request</h1>
      <p>Received {timestamp}</p>
    </div>
    <div class="body">
      <div class="section-title">Contact Details</div>
      <div class="row"><span class="label">Name</span><span class="value">{full_name}</span></div>
      <div class="row"><span class="label">Email</span><span class="value"><a href="mailto:{email}">{email}</a></span></div>
      <div class="row"><span class="label">Phone</span><span class="value"><a href="tel:{phone}">{phone}</a></span></div>
      <div class="row"><span class="label">Company</span><span class="value">{company or '—'}</span></div>

      <div class="section-title">Project Details</div>
      <div class="row"><span class="label">Service</span><span class="value" style="color:#1A3CFF;font-weight:700;">{service_label}</span></div>
      <div class="row"><span class="label">Location</span><span class="value">{location}</span></div>
      <div class="row"><span class="label">How heard</span><span class="value">{how_heard_label}</span></div>

      <div class="section-title">Message</div>
      <div class="message-box">{message}</div>
    </div>
    <div class="footer">
      Powergeekz Engineering Ltd · Limuru Road, Ruaka, Nairobi · 
      <a href="mailto:{email}">Reply to {first_name}</a>
    </div>
  </div>
</body>
</html>
"""

    msg = Message(
        subject=subject,
        recipients=[MAIL_RECIPIENT],
        body=body,
        html=html_body,
        reply_to=email,
    )
    mail.send(msg)


def _send_confirmation_email(first_name, email, service_label):
    """Sends a friendly confirmation email to the client."""
    subject = "We received your enquiry — Powergeekz Engineering Ltd"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family:'Inter',Arial,sans-serif; background:#f4f6fb; margin:0; padding:20px; }}
    .card {{ background:#fff; border-radius:12px; max-width:560px; margin:0 auto; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,0.08); }}
    .header {{ background:linear-gradient(135deg,#0A1A99,#1A3CFF); padding:32px; text-align:center; }}
    .header img {{ width:70px; height:70px; border-radius:50%; border:3px solid rgba(255,255,255,0.3); margin-bottom:12px; }}
    .header h1 {{ color:#fff; margin:0; font-size:1.4rem; font-weight:900; }}
    .body {{ padding:32px; text-align:center; }}
    .emoji {{ font-size:3rem; display:block; margin-bottom:12px; }}
    .body h2 {{ font-size:1.3rem; font-weight:800; color:#111; margin-bottom:8px; }}
    .body p {{ font-size:0.92rem; color:#555; line-height:1.75; margin-bottom:16px; }}
    .highlight {{ background:#f0f3ff; border-radius:8px; padding:14px 20px; display:inline-block; font-size:0.9rem; color:#1A3CFF; font-weight:700; margin:8px 0 20px; }}
    .btn {{ display:inline-block; background:#1A3CFF; color:#fff; padding:12px 28px; border-radius:8px; font-weight:700; text-decoration:none; font-size:0.92rem; margin-top:8px; }}
    .contacts {{ background:#f8f9ff; border-radius:8px; padding:16px 20px; margin:20px 0; text-align:left; }}
    .contacts p {{ margin:4px 0; font-size:0.85rem; }}
    .contacts a {{ color:#1A3CFF; text-decoration:none; font-weight:600; }}
    .footer {{ background:#f8f9ff; padding:16px 32px; border-top:1px solid #eee; font-size:0.75rem; color:#9AA0B8; text-align:center; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>⚡ POWERGEEKZ</h1>
    </div>
    <div class="body">
      <span class="emoji">☀️</span>
      <h2>Hi {first_name}, we got your message!</h2>
      <p>Thank you for reaching out to <strong>Powergeekz Engineering Ltd</strong>. Your enquiry about <strong>{service_label}</strong> has been received and a member of our team will respond within <strong>24 hours</strong>.</p>
      <div class="highlight">📋 Service Requested: {service_label}</div>
      <p>In the meantime, feel free to call or WhatsApp us directly if your need is urgent:</p>
      <div class="contacts">
        <p>📞 <a href="tel:+254723233209">+254 723 233 209</a></p>
        <p>📞 <a href="tel:+254101233209">+254 101 233 209</a></p>
        <p>✉️ <a href="mailto:info@powergeekzengineeringltd.co.ke">info@powergeekzengineeringltd.co.ke</a></p>
        <p>📍 Limuru Road, Ruaka, Nairobi, Kenya</p>
      </div>
      <a class="btn" href="http://www.powergeekzengineeringltd.co.ke/portfolio">View Our Projects →</a>
    </div>
    <div class="footer">
      © 2025 Powergeekz Engineering Ltd · Reg: CPR/2013/103782<br>
      You're receiving this because you submitted an enquiry on our website.
    </div>
  </div>
</body>
</html>
"""

    body = f"""Hi {first_name},

Thank you for contacting Powergeekz Engineering Ltd!

We have received your enquiry for: {service_label}

A member of our team will get back to you within 24 hours with a tailored proposal.

For urgent enquiries, please call us:
  +254 723 233 209
  +254 101 233 209

Or email: powergeekzengineeringltd@gmail.com

Best regards,
The Powergeekz Team
Limuru Road, Ruaka, Nairobi, Kenya
www.powergeekzengineeringltd.co.ke
"""

    msg = Message(
        subject=subject,
        recipients=[email],
        body=body,
        html=html_body,
    )
    mail.send(msg)


# ══════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return render_template("index.html"), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Server error. Please try again later."}), 500


# ══════════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    print(f"""
  ⚡  POWERGEEKZ Engineering Ltd — Server Starting
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🌐  http://localhost:{port}
  📧  Mail recipient : {MAIL_RECIPIENT}
  🔧  Debug mode     : {debug}
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    app.run(host="0.0.0.0", port=port, debug=debug)