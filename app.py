import os
import requests
from flask import Flask, request, render_template_string, Response
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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
    p { line-height: 1.5; }
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
    <p>An AI voice copilot that helps Enterprise Account Executives prepare for executive meetings using real-time research and ElevenLabs voice generation.</p>

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
      <p class="hint">Briefing generated from live web research and converted to voice with ElevenLabs.</p>
    </div>
    {% endif %}
  </main>
</body>
</html>
"""

def get_search_queries(company, stakeholder):
    role_focus = {
        "CIO": "AI digital transformation cloud cybersecurity data platform automation IT strategy",
        "CTO": "AI product engineering technology platform innovation developer infrastructure",
        "CHRO": "HR transformation hiring talent workforce learning employee experience AI HR",
        "CFO": "budget cost reduction margin efficiency investment financial results AI ROI",
        "CMO": "customer experience marketing personalization digital media loyalty brand AI",
        "CEO": "strategy leadership new CEO transformation growth investment AI market expansion",
    }

    focus = role_focus.get(stakeholder, "AI transformation digital innovation leadership")

    return [
        f"{company} latest news new CEO CIO CTO CHRO CFO CMO leadership change",
        f"{company} {focus} recent investment budget initiative",
        f"{company} AI digital transformation automation customer experience latest news",
    ]

def tavily_search(company, stakeholder):
    if not TAVILY_API_KEY:
        return "No Tavily API key configured."

    results = []

    for query in get_search_queries(company, stakeholder):
        response = requests.post(
            "https://api.tavily.com/search",
            headers={
                "Authorization": f"Bearer {TAVILY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "search_depth": "basic",
                "max_results": 4,
                "include_answer": True,
                "include_raw_content": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("answer"):
            results.append(f"Search answer for '{query}': {data['answer']}")

        for item in data.get("results", []):
            title = item.get("title", "")
            url = item.get("url", "")
            content = item.get("content", "")
            results.append(f"- {title}\n  {content}\n  Source: {url}")

    return "\n\n".join(results[:12])

def generate_dynamic_briefing(company, stakeholder, objective, research):
    if not OPENROUTER_API_KEY:
        return "No OpenRouter API key configured."

    prompt = f"""
You are an Enterprise Account Executive meeting copilot.

Prepare a concise executive briefing for Cristina before a customer meeting.

Company: {company}
Stakeholder: {stakeholder}
Meeting objective: {objective}

Use the web research below. Be practical and sales-oriented.
If the research mentions leadership changes, new CEO, new CIO, new CHRO, new CFO, new CMO, digital transformation, AI investment, HR budget, IT budget, cost reduction, hiring, layoffs, acquisitions, or strategic initiatives, highlight them clearly.

Web research:
{research}

Return the briefing in this structure:

1. What changed recently
- Bullet points with the most useful recent signals.
- Mention if there is a new CEO, CIO, CHRO, CFO or other relevant executive.
- Mention any AI, HR, IT, digital transformation or efficiency initiative.

2. Why it matters for a {stakeholder}
- Explain what this stakeholder is likely to care about.

3. Suggested opener
- Give Cristina a natural opening line for the meeting.

4. Discovery questions
- Give 4 strong questions tailored to the stakeholder.

5. Risks / objections
- Mention likely blockers.

6. Recommended next step
- Give one practical next step to secure after the meeting.

Keep it sharp, useful and under 450 words.
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/cristinarago1094/enterprise-meeting-copilot",
            "X-Title": "Enterprise Meeting Copilot",
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a practical enterprise sales coach."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

@app.route("/", methods=["GET", "POST"])
def home():
    global latest_audio
    briefing = None

    if request.method == "POST":
        company = request.form.get("company", "")
        stakeholder = request.form.get("stakeholder", "")
        objective = request.form.get("objective", "")

        research = tavily_search(company, stakeholder)
        briefing = generate_dynamic_briefing(company, stakeholder, objective, research)

        audio = elevenlabs_client.text_to_speech.convert(
            voice_id=VOICE_ID,
            model_id="eleven_multilingual_v2",
            text=briefing,
        )

        latest_audio = b"".join(audio)

    return render_template_string(HTML, briefing=briefing)

@app.route("/audio")
def audio():
    if latest_audio is None:
        return "No audio generated yet", 404
    return Response(latest_audio, mimetype="audio/mpeg")
