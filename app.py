"""
POWERGEEKZ ENGINEERING LTD — Flask Backend
Auto-sends email notification to team + confirmation to client on every form submission.

Requirements:
    pip install flask flask-mail python-dotenv

.env file:
    MAIL_SERVER    = smtp.gmail.com
    MAIL_PORT      = 587
    app.config["MAIL_USE_TLS"] = True
    MAIL_USERNAME  = powergeekzengineeringltd@gmail.com
    MAIL_PASSWORD  = zfdrphwhfdrhcbqv
    MAIL_RECIPIENT = powergeekzengineeringltd@gmail.com
    SECRET_KEY     = powergeekz-secret-2025
"""

import os
import re
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

# ── App ────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "powergeekz-dev-secret-2025")

# ── Mail ───────────────────────────────────────────────────────
app.config["MAIL_SERVER"]         = os.environ.get("MAIL_SERVER",   "smtp.gmail.com")
app.config["MAIL_PORT"]           = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"]        = True
app.config["MAIL_USE_SSL"]        = False
app.config["MAIL_USERNAME"]       = os.environ.get("MAIL_USERNAME", "powergeekzengineeringltd@gmail.com")
app.config["MAIL_PASSWORD"]       = os.environ.get("MAIL_PASSWORD", "zfdrphwhfdrhcbqv")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME", "powergeekzengineeringltd@gmail.com")

mail = Mail(app)

MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "powergeekzengineeringltd@gmail.com")

# ── Label maps ─────────────────────────────────────────────────
SERVICE_LABELS = {
    "solar_pv":      "Solar PV System",
    "solar_heating": "Solar Water Heating",
    "ups":           "UPS Systems",
    "inverter":      "Inverter & Charger Systems",
    "generator":     "Generator & AVR",
    "batteries":     "Battery Supply & Replacement",
    "cctv":          "CCTV Installation",
    "data_cables":   "Data & Electrical Cabling",
    "ict":           "ICT & Computer Supplies",
    "maintenance":   "Maintenance Contract",
    "other":         "Other / Not Sure",
}
HOW_HEARD_LABELS = {
    "google":   "Google Search",
    "facebook": "Facebook",
    "tiktok":   "TikTok",
    "referral": "Referral / Word of Mouth",
    "repeat":   "Returning Client",
    "other":    "Other",
}

# ══════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════

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

@app.route("/documentaries")
def documentaries():
    return render_template("documentaries.html")

@app.route("/contact", methods=["GET", "POST"])
@app.route("/contact.html", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return render_template("contact.html")
    return _handle_contact_form()

# Alias for {{ url_for('contact_page') }} used in some templates
@app.route("/contact-page", methods=["GET"])
def contact_page():
    return render_template("contact.html")


# ══════════════════════════════════════════════════════════════
#  CONTACT FORM HANDLER
# ══════════════════════════════════════════════════════════════

def _handle_contact_form():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "Invalid request format."}), 400

    # Validate required fields
    required = ["first_name", "last_name", "email", "phone", "service", "location", "message"]
    for field in required:
        if not data.get(field, "").strip():
            label = field.replace("_", " ").title()
            return jsonify({"success": False, "message": label + " is required."}), 422

    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", data["email"].strip()):
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 422

    # Sanitise
    fn          = data["first_name"].strip()[:100]
    ln          = data["last_name"].strip()[:100]
    email       = data["email"].strip()[:200]
    phone       = data["phone"].strip()[:50]
    company     = data.get("company", "").strip()[:200]
    service_key = data.get("service", "other").strip()
    location    = data["location"].strip()[:200]
    message     = data["message"].strip()[:2000]
    how_heard   = data.get("how_heard", "").strip()
    timestamp   = datetime.now().strftime("%d %B %Y at %H:%M")

    service_label   = SERVICE_LABELS.get(service_key, service_key)
    how_heard_label = HOW_HEARD_LABELS.get(how_heard, how_heard or "Not specified")
    full_name       = fn + " " + ln

    # Auto-send both emails
    try:
        _send_team_notification(
            full_name, fn, email, phone, company,
            service_label, location, message,
            how_heard_label, timestamp,
        )
        _send_client_confirmation(fn, email, service_label)
    except Exception as exc:
        app.logger.error("[MAIL ERROR] " + str(exc))

    return jsonify({
        "success": True,
        "message": "Thank you! We received your enquiry and will be in touch within 24 hours.",
    })


# ══════════════════════════════════════════════════════════════
#  EMAIL 1 — Team Notification
#  NOTE: HTML is a plain string with .format() — NOT an f-string
#  This avoids Python misreading CSS curly braces as variables.
# ══════════════════════════════════════════════════════════════

def _send_team_notification(
    full_name, first_name, email, phone, company,
    service_label, location, message,
    how_heard_label, timestamp,
):
    subject = "New Quote Request — " + service_label + " — " + full_name

    plain = (
        "New enquiry received via the Powergeekz website.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "CONTACT DETAILS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Name       : " + full_name + "\n"
        "Email      : " + email + "\n"
        "Phone      : " + phone + "\n"
        "Company    : " + (company or "Not provided") + "\n\n"
        "PROJECT DETAILS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Service    : " + service_label + "\n"
        "Location   : " + location + "\n"
        "How heard  : " + how_heard_label + "\n\n"
        "MESSAGE\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        + message + "\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Received on " + timestamp + "\n"
        "Reply to: " + email
    )

    # HTML uses .format() so CSS {} braces don't confuse Python
    html_template = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:Arial,sans-serif; background:#0a0f1e; padding:24px; }
  .wrap { max-width:620px; margin:0 auto; }
  .card { background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 8px 40px rgba(0,0,0,0.25); }
  .hdr { background:linear-gradient(135deg,#0d47c5,#1a6bff,#00aaff); padding:32px; text-align:center; }
  .hdr h1 { color:#fff; font-size:1.3rem; font-weight:900; margin-bottom:4px; }
  .hdr p { color:rgba(255,255,255,0.75); font-size:0.82rem; }
  .badge { display:inline-block; background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.3);
           border-radius:50px; padding:4px 14px; font-size:0.72rem; font-weight:700; color:#fff;
           text-transform:uppercase; letter-spacing:0.1em; margin-top:12px; }
  .body { padding:32px; }
  .sec { font-size:0.65rem; font-weight:800; letter-spacing:0.16em; text-transform:uppercase;
         color:#7c8db5; margin:24px 0 12px; border-bottom:1px solid #eef0f7; padding-bottom:6px; }
  .sec:first-child { margin-top:0; }
  .row { display:flex; align-items:baseline; gap:10px; margin-bottom:9px; }
  .lbl { font-size:0.78rem; font-weight:700; color:#8891a8; min-width:88px; flex-shrink:0; }
  .val { font-size:0.9rem; color:#1a1f36; }
  .val a { color:#1a6bff; text-decoration:none; font-weight:600; }
  .chip { display:inline-block; background:#eef3ff; border:1px solid #c7d8ff;
          border-radius:6px; padding:3px 12px; font-size:0.88rem; font-weight:700; color:#1a6bff; }
  .msgbox { background:#f7f8fc; border-left:4px solid #1a6bff; border-radius:0 10px 10px 0;
            padding:16px 18px; font-size:0.9rem; line-height:1.75; color:#2d3350;
            white-space:pre-wrap; margin-top:4px; }
  .reply-btn { display:inline-block; background:linear-gradient(135deg,#1a6bff,#00aaff); color:#fff;
               padding:13px 28px; border-radius:8px; font-weight:700; text-decoration:none;
               font-size:0.9rem; margin-top:8px; }
  .ftr { background:#f7f8fc; border-top:1px solid #eef0f7; padding:18px 32px;
         font-size:0.75rem; color:#9aa0b8; text-align:center; line-height:1.6; }
  .ftr a { color:#1a6bff; }
</style>
</head>
<body>
<div class="wrap"><div class="card">
  <div class="hdr">
    <h1>New Quote Request</h1>
    <p>Received via Powergeekz website</p>
    <div class="badge">{SERVICE}</div>
  </div>
  <div class="body">
    <div class="sec">Contact Details</div>
    <div class="row"><span class="lbl">Name</span><span class="val">{FULLNAME}</span></div>
    <div class="row"><span class="lbl">Email</span><span class="val"><a href="mailto:{EMAIL}">{EMAIL}</a></span></div>
    <div class="row"><span class="lbl">Phone</span><span class="val"><a href="tel:{PHONE}">{PHONE}</a></span></div>
    <div class="row"><span class="lbl">Company</span><span class="val">{COMPANY}</span></div>

    <div class="sec">Project Details</div>
    <div class="row"><span class="lbl">Service</span><span class="val"><span class="chip">{SERVICE}</span></span></div>
    <div class="row"><span class="lbl">Location</span><span class="val">{LOCATION}</span></div>
    <div class="row"><span class="lbl">How Heard</span><span class="val">{HOWHEARD}</span></div>

    <div class="sec">Message</div>
    <div class="msgbox">{MESSAGE}</div>

    <div style="margin-top:24px;text-align:center">
      <a href="mailto:{EMAIL}" class="reply-btn">Reply to {FIRSTNAME}</a>
    </div>
  </div>
  <div class="ftr">
    Powergeekz Engineering Ltd &middot; Limuru Road, Ruaka, Nairobi<br>
    Received on {TIMESTAMP} &middot; <a href="tel:{PHONE}">{PHONE}</a>
  </div>
</div></div>
</body>
</html>"""

    html = (html_template
        .replace("{SERVICE}",    service_label)
        .replace("{FULLNAME}",   full_name)
        .replace("{EMAIL}",      email)
        .replace("{PHONE}",      phone)
        .replace("{COMPANY}",    company or "—")
        .replace("{LOCATION}",   location)
        .replace("{HOWHEARD}",   how_heard_label)
        .replace("{MESSAGE}",    message)
        .replace("{FIRSTNAME}",  first_name)
        .replace("{TIMESTAMP}",  timestamp)
    )

    msg = Message(
        subject=subject,
        recipients=[MAIL_RECIPIENT],
        body=plain,
        html=html,
        reply_to=email,
    )
    mail.send(msg)


# ══════════════════════════════════════════════════════════════
#  EMAIL 2 — Client Auto-Confirmation
#  NOTE: HTML is a plain string with .replace() — NOT an f-string
# ══════════════════════════════════════════════════════════════

def _send_client_confirmation(first_name, client_email, service_label):
    subject = "We received your enquiry — Powergeekz Engineering Ltd"

    plain = (
        "Hi " + first_name + ",\n\n"
        "Thank you for contacting Powergeekz Engineering Ltd!\n\n"
        "We have received your enquiry for: " + service_label + "\n\n"
        "A member of our engineering team will get back to you within 24 hours\n"
        "with a tailored proposal and, if needed, arrange a free site visit.\n\n"
        "For urgent matters, please call or WhatsApp us:\n"
        "  +254 723 233 209\n"
        "  +254 101 233 209\n"
        "  powergeekzengineeringltd@gmail.com\n\n"
        "Best regards,\n"
        "The Powergeekz Engineering Team\n"
        "Limuru Road, Ruaka, Nairobi, Kenya\n"
    )

    html_template = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:Arial,sans-serif; background:#0a0f1e; padding:24px; }
  .wrap { max-width:560px; margin:0 auto; }
  .card { background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 8px 40px rgba(0,0,0,0.25); }
  .hdr { background:linear-gradient(135deg,#0d47c5,#1a6bff,#00aaff); padding:36px 32px; text-align:center; }
  .hdr-logo { font-size:1.5rem; font-weight:900; color:#fff; letter-spacing:0.06em; margin-bottom:4px; }
  .hdr-tag { font-size:0.8rem; color:rgba(255,255,255,0.72); }
  .body { padding:36px 32px; text-align:center; }
  .emoji { font-size:3rem; display:block; margin-bottom:16px; }
  h2 { font-size:1.3rem; font-weight:900; color:#1a1f36; margin-bottom:10px; }
  .lead { font-size:0.93rem; color:#555e7a; line-height:1.75; margin-bottom:20px; }
  .chip { display:inline-block; background:#eef3ff; border:1px solid #c7d8ff; border-radius:8px;
          padding:8px 20px; font-size:0.9rem; font-weight:700; color:#1a6bff; margin-bottom:24px; }
  .steps { background:#f7f8fc; border-radius:12px; padding:20px 24px; text-align:left; margin-bottom:24px; }
  .steps h4 { font-size:0.68rem; font-weight:800; letter-spacing:0.14em; text-transform:uppercase;
              color:#7c8db5; margin-bottom:14px; }
  .step { display:flex; align-items:center; gap:12px; margin-bottom:10px; font-size:0.88rem; color:#2d3350; }
  .num { width:26px; height:26px; background:linear-gradient(135deg,#1a6bff,#00aaff); border-radius:50%;
         display:flex; align-items:center; justify-content:center; font-size:0.72rem;
         font-weight:800; color:#fff; flex-shrink:0; }
  .contacts { background:#f7f8fc; border-radius:12px; padding:18px 22px; text-align:left; margin-bottom:24px; }
  .contacts h4 { font-size:0.68rem; font-weight:800; letter-spacing:0.14em; text-transform:uppercase;
                 color:#7c8db5; margin-bottom:12px; }
  .crow { display:flex; align-items:center; gap:10px; margin-bottom:8px; font-size:0.88rem; color:#2d3350; }
  .crow a { color:#1a6bff; text-decoration:none; font-weight:600; }
  .cta { display:inline-block; background:linear-gradient(135deg,#1a6bff,#00aaff); color:#fff;
         padding:14px 32px; border-radius:10px; font-weight:700; text-decoration:none;
         font-size:0.92rem; box-shadow:0 6px 20px rgba(26,107,255,0.35); }
  .ftr { background:#f7f8fc; border-top:1px solid #eef0f7; padding:18px 32px;
         font-size:0.73rem; color:#9aa0b8; text-align:center; line-height:1.7; }
  .ftr a { color:#1a6bff; text-decoration:none; }
</style>
</head>
<body>
<div class="wrap"><div class="card">
  <div class="hdr">
    <div class="hdr-logo">POWERGEEKZ</div>
    <div class="hdr-tag">Engineering Ltd &middot; Nairobi, Kenya</div>
  </div>
  <div class="body">
    <span class="emoji">&#9728;&#65039;</span>
    <h2>Hi {FIRSTNAME}, message received!</h2>
    <p class="lead">
      Thank you for reaching out to <strong>Powergeekz Engineering Ltd</strong>.
      Your enquiry about <strong>{SERVICE}</strong> has been received.
      Our engineering team will respond within <strong>24 hours</strong>.
    </p>
    <div class="chip">&#128203; {SERVICE}</div>

    <div class="steps">
      <h4>What happens next?</h4>
      <div class="step"><div class="num">1</div><span>Our team reviews your enquiry</span></div>
      <div class="step"><div class="num">2</div><span>We contact you within 24 hours</span></div>
      <div class="step"><div class="num">3</div><span>Free site assessment scheduled</span></div>
      <div class="step"><div class="num">4</div><span>Tailored proposal delivered</span></div>
    </div>

    <div class="contacts">
      <h4>Need us sooner?</h4>
      <div class="crow">&#128222; <a href="tel:+254723233209">+254 723 233 209</a></div>
      <div class="crow">&#128222; <a href="tel:+254101233209">+254 101 233 209</a></div>
      <div class="crow">&#128172; <a href="https://wa.me/254723233209">WhatsApp us now</a></div>
      <div class="crow">&#9993; <a href="mailto:powergeekzengineeringltd@gmail.com">powergeekzengineeringltd@gmail.com</a></div>
      <div class="crow">&#128205; Limuru Road, Ruaka, Nairobi</div>
    </div>

    <a href="http://www.powergeekzengineeringltd.co.ke/portfolio" class="cta">View Our Projects &rarr;</a>
  </div>
  <div class="ftr">
    &copy; 2025 Powergeekz Engineering Ltd &middot; Reg: CPR/2013/103782<br>
    You received this because you submitted an enquiry on our website.<br>
    <a href="http://www.powergeekzengineeringltd.co.ke">www.powergeekzengineeringltd.co.ke</a>
  </div>
</div></div>
</body>
</html>"""

    html = (html_template
        .replace("{FIRSTNAME}", first_name)
        .replace("{SERVICE}",   service_label)
    )

    msg = Message(
        subject=subject,
        recipients=[client_email],
        body=plain,
        html=html,
    )
    mail.send(msg)


# ══════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return render_template("index.html"), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Server error. Please try again later."}), 500


# ══════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    print("""
  Powergeekz Engineering Ltd — Server Starting
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  http://localhost:{port}
  Notifications  -> {recipient}
  Auto-confirm   -> client email on every submission
  Debug mode     -> {debug}
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """.format(port=port, recipient=MAIL_RECIPIENT, debug=debug))
    app.run(host="0.0.0.0", port=port, debug=debug)