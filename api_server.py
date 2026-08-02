"""
Hookly — Optional AI backend (upgrade path)

This is a minimal Flask server that proxies generation requests to OpenAI.
Use it to replace the template engine in index.html with GPT-4 quality output.

Setup:
  1. pip install flask flask-cors openai
  2. export OPENAI_API_KEY=sk-...
  3. python api_server.py
  4. Update index.html: change generateContent() to call /api/generate
"""

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

app = Flask(__name__)
CORS(app)

if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYSTEM_PROMPT = """You are an expert viral-content strategist who has helped creators generate billions of views on TikTok, Instagram Reels, and YouTube Shorts.

You deeply understand:
- The psychology of the first 3 seconds (the "hook")
- Pattern interrupts and curiosity loops
- Platform-specific algorithms (TikTok watch time, Reels shares, Shorts subscribers)
- Niche-specific viral formats (fitness, finance, cooking, tech, dating, etc.)
- The 6 viral hook styles: Controversial, Curious, Shocking, Relatable, Educational, Funny

Your output is ALWAYS in this exact JSON shape, no extra text, no markdown:

{
  "hooks": ["hook 1", "hook 2", "hook 3", "hook 4", "hook 5"],
  "script": "Full 30-60 second script with [HOOK] [PROBLEM] [REVEAL] [PAYOFF] [CTA] sections + visual notes",
  "caption": "Engaging 2-3 line caption with emoji and CTA",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5", "#hashtag6", "#hashtag7", "#hashtag8"]
}

Hooks must be MAX 15 words each, scroll-stopping, and immediately understandable.
Script must include [VISUAL DIRECTION] at the end with shot-by-shot notes.
Hashtags must mix 2 niche-specific + 4 broad reach + 2 trending."""


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json
    niche = data.get("niche", "")
    platform = data.get("platform", "TikTok")
    topic = data.get("topic", "")
    tone = data.get("tone", "Curious / Question")

    if not niche or not topic:
        return jsonify({"error": "niche and topic are required"}), 400

    if not HAS_OPENAI or not os.getenv("OPENAI_API_KEY"):
        return jsonify({
            "error": "OPENAI_API_KEY not set. Install openai and set the env var, or use the template engine in index.html."
        }), 503

    user_prompt = f"""Generate viral content for:
- Niche: {niche}
- Platform: {platform}
- Topic: {topic}
- Hook tone: {tone}

Return ONLY the JSON object, no markdown formatting."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "openai_configured": HAS_OPENAI and bool(os.getenv("OPENAI_API_KEY"))
    })


if __name__ == "__main__":
    print("\n🔥 Hookly API server running on http://localhost:5000")
    print("   OpenAI:", "✅ configured" if HAS_OPENAI and os.getenv("OPENAI_API_KEY") else "❌ not configured (set OPENAI_API_KEY)")
    print("   Health: http://localhost:5000/health\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
