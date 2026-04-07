from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
from translate import translate_bp
import base64
import os

app = Flask(__name__)
app.secret_key = "secret123"

# Gmail SMTP configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'   # Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

mail = Mail(app)

# Register translation blueprint
app.register_blueprint(translate_bp)

# Login credentials
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
==========================

📝 Original Text:
{original_text}

🌐 Translated Text:
{translated_text}

—
Sent from Voice Translation Web App
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
        msg.body = "Please find your voice translation PDF attached."
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
    audio_base64 = data.get('audio_base64')   # base64 encoded audio
    audio_format = data.get('audio_format', 'webm')  # webm/wav/ogg
    recipient_email = data.get("email")
    original_text = data.get("original_text", "")
    translated_text = data.get("translated_text", "")

    try:
        audio_bytes = base64.b64decode(audio_base64)

        msg = Message(
            subject="🎤 Voice Recording & Translation",
            recipients=[recipient_email]
        )
        msg.body = f"""
Hello!

Attached is your voice recording along with the translation.

📝 Original Text:
{original_text}

🌐 Translated Text:
{translated_text}

—
Sent from Voice Translation Web App
"""
        mime_map = {
            'webm': 'audio/webm',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'mp3': 'audio/mpeg'
        }
        mime_type = mime_map.get(audio_format, 'audio/webm')
        msg.attach(f"recording.{audio_format}", mime_type, audio_bytes)
        mail.send(msg)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ---------------- TTS GENERATE (audio only, no email) ---------------- #

@app.route("/tts-generate", methods=["POST"])
def tts_generate():
    if not session.get('logged_in'):
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    text = data.get("text", "")
    lang = data.get("lang", "en")

    try:
        from gtts import gTTS
        import io

        lang_map = {"en":"en","kn":"kn","hi":"hi","ta":"ta","te":"te","ml":"ml"}
        gtts_lang = lang_map.get(lang[:2], "en")
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_bytes = audio_buffer.getvalue()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        return jsonify({"success": True, "audio_base64": audio_b64})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ---------------- TTS + EMAIL (gTTS backend) ---------------- #

@app.route("/tts-email", methods=["POST"])
def tts_email():
    if not session.get('logged_in'):
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    text = data.get("text", "")
    lang = data.get("lang", "en")
    recipient_email = data.get("email")
    original_text = data.get("original_text", "")
    translated_text = data.get("translated_text", "")

    try:
        from gtts import gTTS
        import io

        # Map to valid gTTS lang codes
        lang_map = {"en":"en","kn":"kn","hi":"hi","ta":"ta","te":"te","ml":"ml"}
        gtts_lang = lang_map.get(lang[:2], "en")

        # Generate TTS audio — translated text spoken in target language voice
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_bytes = audio_buffer.getvalue()

        # Send email with text + audio attachment
        msg = Message(
            subject="🎤 Voice Translation — Text + Audio",
            recipients=[recipient_email]
        )
        msg.body = f"""
============================================
🎤 VOICE TRANSLATION RESULT
============================================

📝 ORIGINAL TEXT:
{original_text}

--------------------------------------------

🌐 TRANSLATED TEXT:
{translated_text}

--------------------------------------------

🔊 AUDIO:
The translated text as an MP3 audio file is attached.
Open the attachment to listen to the translated voice.

============================================
Sent from VoiceTranslate Pro
"""
        msg.attach("translated_audio.mp3", "audio/mpeg", audio_bytes)
        mail.send(msg)

        # Return base64 audio so frontend can play it
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        return jsonify({"success": True, "audio_base64": audio_b64})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(debug=True)
