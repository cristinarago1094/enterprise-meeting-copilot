import os
from flask import Flask, request, render_template_string
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

HTML = """
<!doctype html>
<html>
<head>
  <title>Pre-Meeting AI Briefing</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 760px; margin: 60px auto; padding: 20px; }
    textarea { width: 100%; height: 120px; padding: 12px; font-size: 16px; }
    button { padding: 12px 18px; font-size: 16px; margin-top: 12px; }
    .briefing { margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 12px; }
  </style>
</head>
<body>
  <h1>🎙 Pre-Meeting AI Briefing</h1>
  <p>Generate a short voice briefing before an enterprise customer meeting.</p>

  <form method="post">
    <textarea name="meeting" placeholder="Example: Tomorrow I have a meeting with Ferrari's CIO about AI adoption."></textarea>
    <br>
    <button type="submit">Generate briefing</button>
  </form>

  {% if briefing %}
  <div class="briefing">
    <h2>Briefing</h2>
    <p>{{ briefing }}</p>
    <audio controls>
      <source src="/audio" type="audio/mpeg">
    </audio>
  </div>
  {% endif %}
</body>
</html>
"""

latest_audio = None

def generate_briefing(meeting):
    return f"""
Here is your pre-meeting briefing.

Meeting context: {meeting}

Suggested opener:
Start by referencing the customer's current business priorities and position the conversation around impact, not features.

Three discovery questions:
1. What business process are you trying to improve with AI?
2. Where are your teams still losing time in manual workflows?
3. What would need to be true for this project to become a priority this quarter?

Potential risk:
The customer may be interested in AI but not yet have a clear owner or budget.

Recommended focus:
Anchor the discussion on measurable business outcomes and next steps.
"""

@app.route("/", methods=["GET", "POST"])
def home():
    global latest_audio
    briefing = None

    if request.method == "POST":
        meeting = request.form.get("meeting", "")
        briefing = generate_briefing(meeting)

        audio = client.text_to_speech.convert(
            voice_id="HKSyJ8Hw3U0MRVcY90xW",
            model_id="eleven_multilingual_v2",
            text=briefing,
        )

        latest_audio = b"".join(audio)

    return render_template_string(HTML, briefing=briefing)

@app.route("/audio")
def audio():
    from flask import Response
    if latest_audio is None:
        return "No audio generated yet", 404
    return Response(latest_audio, mimetype="audio/mpeg")
