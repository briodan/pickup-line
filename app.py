from flask import Flask, jsonify, render_template, request
import os
import openai
import requests
import json
import random

app = Flask(__name__)

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SAVED_LINES_FILE = "saved_lines.json"

# OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def load_saved_lines():
    if not os.path.exists(SAVED_LINES_FILE):
        return []
    try:
        with open(SAVED_LINES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_saved_lines(lines):
    with open(SAVED_LINES_FILE, "w") as f:
        json.dump(lines, f, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/dirtylines", methods=["GET"])
def get_dirty_lines():
    saved_lines = load_saved_lines()

    examples_text = ""
    if saved_lines:
        examples = random.sample(saved_lines, min(3, len(saved_lines)))
        examples_text = "\nHere are some examples:\n" + "\n".join(f"- {entry['line']}" for entry in examples)

    prompt = f"""
Generate 10 short, funny, dirty pickup lines for my wife.
Make them playful, suggestive, slightly NSFW, flirty, and under 30 words each.
Use clever double meanings, humor, and innuendo.
{examples_text}

Respond only with a pure JSON array of pickup lines like:
["line 1", "line 2", "line 3", ..., "line 10"]
"""

    try:
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
                "max_tokens": 400
            },
            timeout=15
        )
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()

        lines = json.loads(text)  # Expect clean JSON array
        return jsonify({"lines": lines})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/rate_line", methods=["POST"])
def rate_line():
    data = request.get_json()
    line = data.get("line")
    rating = data.get("rating")

    if not line or rating is None:
        return jsonify({"error": "Missing line or rating"}), 400

    if int(rating) >= 4:
        saved_lines = load_saved_lines()
        if not any(entry["line"] == line for entry in saved_lines):
            saved_lines.append({"line": line, "rating": rating})
            save_saved_lines(saved_lines)

    return jsonify({"status": "ok"})

@app.route("/api/delete_line", methods=["POST"])
def delete_line():
    data = request.get_json()
    line = data.get("line")

    if not line:
        return jsonify({"error": "Missing line to delete"}), 400

    saved_lines = load_saved_lines()
    saved_lines = [entry for entry in saved_lines if entry["line"] != line]
    save_saved_lines(saved_lines)

    return jsonify({"status": "deleted"})

@app.route("/api/saved_lines", methods=["GET"])
def get_saved_lines():
    saved_lines = load_saved_lines()
    return jsonify({"saved_lines": saved_lines})

@app.route("/api/ha_pickup_line", methods=["GET"])
def ha_pickup_line():
    saved_lines = load_saved_lines()
    if not saved_lines:
        return jsonify({"line": "No saved pickup lines yet!"})
    return jsonify({"line": random.choice(saved_lines)["line"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
