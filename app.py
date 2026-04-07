from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
from translate import translate_bp
import base64
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- MAIL CONFIG ---------------- #

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'   # 🔴 change this
app.config['MAIL_PASSWORD'] = 'your_app_password'      # 🔴 change this
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

mail = Mail(app)

# ---------------- REGISTER BLUEPRINT ---------------- #

app.register_blueprint(translate_bp)

# ---------------- LOGIN DETAILS ---------------- #

EMAIL = "ved@gmail.com"
PASSWORD = "0807"

# ---------------- LOGIN ---------------- #

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == EMAIL and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Invalid email or password")

    return render_template("login.html")

# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template("dashboard.html")

# ---------------- SEND TEXT EMAIL ---------------- #

@app.route("/send-text-email", methods=["POST"])
def send_text_email():
    if not session.get('logged_in'):
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    original_text = data.get("original_text")
    translated_text = data.get("translated_text")
    recipient_email = data.get("email")

    try:
        msg = Message(
            subject="🎤 Voice Translation Result",
            recipients=[recipient_email]
        )
        msg.body = f"""
Voice Translation Results

Original Text:
{original_text}

Translated Text:
{translated_text}
"""
        mail.send(msg)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ---------------- SEND PDF EMAIL ---------------- #

@app.route("/send-pdf-email", methods=["POST"])
def send_pdf_email():
    if not session.get('logged_in'):
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    pdf_content = data.get('pdf_content')
    filename = data.get('filename')
    recipient_email = data.get("email")

    try:
        msg = Message(
            subject="🎤 Voice Translation PDF",
            recipients=[recipient_email]
        )
        msg.body = "PDF attached"

        msg.attach(
            filename,
            "application/pdf",
            pdf_content.encode('latin-1') if isinstance(pdf_content, str) else pdf_content
        )

        mail.send(msg)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ---------------- SEND AUDIO EMAIL ---------------- #

@app.route("/send-audio-email", methods=["POST"])
def send_audio_email():
    if not session.get('logged_in'):
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    audio_base64 = data.get('audio_base64')
    audio_format = data.get('audio_format', 'webm')
    recipient_email = data.get("email")

    try:
        audio_bytes = base64.b64decode(audio_base64)

        msg = Message(
            subject="🎤 Voice Recording",
            recipients=[recipient_email]
        )
        msg.body = "Audio attached"

        msg.attach(f"recording.{audio_format}", "audio/mpeg", audio_bytes)

        mail.send(msg)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ---------------- TTS GENERATE ---------------- #

@app.route("/tts-generate", methods=["POST"])
def tts_generate():
    if not session.get('logged_in'):
        return jsonify({"error": "Not logged in"}), 401

    from gtts import gTTS
    import io

    data = request.get_json()
    text = data.get("text", "")

    try:
        tts = gTTS(text=text, lang="en")
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)

        audio_b64 = base64.b64encode(audio_buffer.getvalue()).decode('utf-8')
        return jsonify({"success": True, "audio_base64": audio_b64})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- RUN APP (FIXED FOR RENDER) ---------------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
