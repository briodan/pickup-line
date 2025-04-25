from flask import Flask, jsonify, render_template, request
import openai
import os
import json
import random

app = Flask(__name__)

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenAI client setup
import openai
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Storage for saved lines
SAVED_LINES_FILE = "saved_lines.json"

def load_saved_lines():
    if os.path.exists(SAVED_LINES_FILE):
        with open(SAVED_LINES_FILE, "r") as f:
            return json.load(f)
    else:
        return []

def save_saved_lines(lines):
    with open(SAVED_LINES_FILE, "w") as f:
        json.dump(lines, f, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/dirtyline", methods=["GET"])
def get_dirty_line():
    saved_lines = load_saved_lines()

    # If we have saved lines, include a few examples
    examples_text = ""
    if saved_lines:
        examples = random.sample(saved_lines, min(3, len(saved_lines)))
        examples_text = "\nExamples:\n" + "\n".join(f"- {line}" for line in examples)

    prompt = f"""
Give me a short, bold, dirty pickup line to send to my wife. 
It should be raunchy, NSFW, sexually suggestive, and flirty — something to whisper when we're alone.
Keep it under 30 words.
{examples_text}

Now give me a new one:
    """

    try:
        # First attempt OpenRouter
        try:
            import requests
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "Pickup Line App"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.95,
                    "max_tokens": 60
                },
                timeout=10
            )
            data = response.json()
            line = data["choices"][0]["message"]["content"].strip()
            return jsonify({"line": line, "source": "openrouter"})
        except Exception as e:
            print(f"OpenRouter failed: {e}")

        # Fallback to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=60
        )
        line = response.choices[0].message.content.strip()
        return jsonify({"line": line, "source": "openai"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/rate_line", methods=["POST"])
def rate_line():
    data = request.get_json()
    line = data.get("line")
    rating = data.get("rating")

    if not line or not rating:
        return jsonify({"error": "Missing line or rating"}), 400

    if rating >= 4:
        saved_lines = load_saved_lines()
        if line not in saved_lines:
            saved_lines.append(line)
            save_saved_lines(saved_lines)

    return jsonify({"status": "ok"})

@app.route("/api/saved_lines", methods=["GET"])
def get_saved_lines():
    saved_lines = load_saved_lines()
    return jsonify({"saved_lines": saved_lines})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
