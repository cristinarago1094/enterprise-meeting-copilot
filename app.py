import os
from flask import Flask, request, render_template_string, Response
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = Flask(__name__)

elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
latest_audio = None

HTML = """
<!doctype html>
<html>
<head>
  <title>Enterprise Meeting Copilot</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 920px; margin: 50px auto; padding: 20px; background: #f7f7f4; color: #1f2933; }
    main { background: white; padding: 32px; border-radius: 18px; border: 1px solid #e5e7eb; }
    h1 { font-size: 34px; margin-bottom: 8px; }
    label { display: block; margin-top: 18px; font-weight: 600; }
    input, textarea, select { width: 100%; padding: 12px; margin-top: 6px; font-size: 16px; border-radius: 10px; border: 1px solid #d1d5db; }
    button { margin-top: 22px; padding: 13px 20px; font-size: 16px; border-radius: 10px; border: 0; background: #111827; color: white; font-weight: 600; cursor: pointer; }
    .briefing { margin-top: 30px; padding: 24px; background: #f3f4f6; border-radius: 14px; white-space: pre-line; }
    audio { margin-top: 18px; width: 100%; }
    .hint { color: #6b7280; font-size: 14px; }
  </style>
</head>
<body>
  <main>
    <h1>🎙 Enterprise Meeting Copilot</h1>
    <p>Voice-powered AI copilot for Enterprise Account Executives, built with Gemini Search Grounding and ElevenLabs.</p>

    <form method="post">
      <label>Company</label>
      <input name="company" placeholder="Ferrari" required>

      <label>Stakeholder</label>
      <select name="stakeholder">
        <option>CIO</option>
        <option>CTO</option>
        <option>CHRO</option>
        <option>CFO</option>
        <option>CMO</option>
        <option>CEO</option>
      </select>

      <label>Meeting objective</label>
      <textarea name="objective" placeholder="Discovery call about AI adoption, customer experience automation, internal productivity..." required></textarea>

      <button type="submit">Generate Briefing</button>
    </form>

    {% if briefing %}
    <div class="briefing">
      <h2>Executive briefing</h2>
      {{ briefing }}
      <audio controls>
        <source src="/audio" type="audio/mpeg">
      </audio>
      <p class="hint">Generated with Gemini + Google Search grounding. Voice by ElevenLabs.</p>
    </div>
    {% endif %}
  </main>
</body>
</html>
"""

def generate_briefing(company, stakeholder, objective):
    prompt = f"""
You are an Enterprise Account Executive meeting copilot.

Prepare a practical executive briefing for Cristina before a customer meeting.

Company: {company}
Stakeholder: {stakeholder}
Meeting objective: {objective}

Use Google Search grounding to find recent and relevant information.

Focus on:
- recent leadership changes: new CEO, CIO, CTO, CHRO, CFO, CMO
- AI, digital transformation, automation, cloud, HR, finance or customer experience initiatives
- budget, investment, efficiency or cost-reduction signals
- acquisitions, expansion, layoffs, hiring or strategic priorities
- anything that creates a good business reason to speak with a {stakeholder}

Return two sections:

SCREEN_BRIEF:
A complete executive briefing for the screen, structured as:
1. What changed recently
2. Why it matters for the stakeholder
3. Buying signals
4. Suggested opener
5. Discovery questions
6. Risks / objections
7. Recommended next step

VOICE_BRIEF:
A short 35-second spoken briefing for Cristina.
Maximum 120 words.
Make it sound natural, like a quick prep before walking into the meeting.
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
    )

    return response.text

@app.route("/", methods=["GET", "POST"])
def home():
    global latest_audio
    briefing = None

    if request.method == "POST":
        company = request.form.get("company", "")
        stakeholder = request.form.get("stakeholder", "")
        objective = request.form.get("objective", "")

        briefing = generate_briefing(company, stakeholder, objective)

      if "VOICE_BRIEF:" in briefing:
    voice_summary = briefing.split("VOICE_BRIEF:", 1)[1].strip()
else:
    voice_summary = briefing[:400]

audio = elevenlabs_client.text_to_speech.convert(
    voice_id=VOICE_ID,
    model_id="eleven_multilingual_v2",
    text=voice_summary,
)

latest_audio = b"".join(audio)

    return render_template_string(HTML, briefing=briefing)

@app.route("/audio")
def audio():
    if latest_audio is None:
        return "No audio generated yet", 404
    return Response(latest_audio, mimetype="audio/mpeg")
