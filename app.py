from flask import Flask, jsonify, render_template, request
import os
import openai
import requests
import json
import random
import logging

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SAVED_LINES_FILE = "data/saved_lines.json"

# OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def load_saved_lines():
    if not os.path.exists(SAVED_LINES_FILE):
        logging.info("No saved_lines.json file found. Returning empty list.")
        return []
    try:
        with open(SAVED_LINES_FILE, "r") as f:
            lines = json.load(f)
            logging.info(f"Loaded {len(lines)} saved lines.")
            return lines
    except Exception as e:
        logging.error(f"Error loading saved lines: {e}")
        return []

def save_saved_lines(lines):
    with open(SAVED_LINES_FILE, "w") as f:
        json.dump(lines, f, indent=2)
    logging.info(f"Saved {len(lines)} lines to saved_lines.json")

@app.route("/")
def index():
    logging.info("GET / - Serving index.html")
    return render_template("index.html")

@app.route("/api/dirtylines", methods=["GET"])
def get_dirty_lines():
    logging.info("GET /api/dirtylines - Generating new pickup lines")
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
                "max_tokens": 400,
                "stream": False   # <<< ADD THIS
            },
            timeout=15
        )
        data = response.json()
        logging.info(f"OpenRouter raw response JSON: {data}")

        if "choices" not in data or not data["choices"]:
            logging.error(f"Invalid OpenRouter response: {data}")
            return jsonify({"error": "Invalid OpenRouter API response"}), 502

        text = data["choices"][0]["message"]["content"].strip()

        # Remove Markdown-style triple backticks if present
        if text.startswith("```"):
            logging.info("Stripping Markdown formatting from response")
            parts = text.split("\n", 1)
            if len(parts) > 1:
                text = parts[1]  # skip first line (```json)
            text = text.strip()
            if text.endswith("```"):
                text = text[:-3].strip()

        # Now it should be a clean JSON array


        if not text:
            logging.error(f"Empty message content received from OpenRouter: {data}")
            return jsonify({"error": "Empty message from OpenRouter"}), 502

        try:
            lines = json.loads(text)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse pickup lines JSON: {e}")
            return jsonify({"error": "Failed to parse pickup lines."}), 502

        logging.info(f"Successfully generated {len(lines)} lines.")
        return jsonify({"lines": lines})

    except Exception as e:
        logging.error(f"Error generating lines: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/rate_line", methods=["POST"])
def rate_line():
    data = request.get_json()
    line = data.get("line")
    rating = data.get("rating")
    logging.info(f"POST /api/rate_line - Rating: {rating} stars for: {line}")

    if not line or rating is None:
        logging.warning("Rating request missing 'line' or 'rating'")
        return jsonify({"error": "Missing line or rating"}), 400

    if int(rating) >= 4:
        saved_lines = load_saved_lines()
        if not any(entry["line"] == line for entry in saved_lines):
            saved_lines.append({"line": line, "rating": rating})
            save_saved_lines(saved_lines)
            logging.info(f"Saved new line: {line}")

    return jsonify({"status": "ok"})

@app.route("/api/delete_line", methods=["POST"])
def delete_line():
    data = request.get_json()
    line = data.get("line")
    logging.info(f"POST /api/delete_line - Deleting line: {line}")

    if not line:
        logging.warning("Delete request missing 'line'")
        return jsonify({"error": "Missing line to delete"}), 400

    saved_lines = load_saved_lines()
    new_saved_lines = [entry for entry in saved_lines if entry["line"] != line]
    save_saved_lines(new_saved_lines)

    logging.info(f"Deleted line: {line}")
    return jsonify({"status": "deleted"})

@app.route("/api/saved_lines", methods=["GET"])
def get_saved_lines():
    logging.info("GET /api/saved_lines - Returning all saved lines")
    saved_lines = load_saved_lines()
    return jsonify({"saved_lines": saved_lines})

@app.route("/api/ha_pickup_line", methods=["GET"])
def ha_pickup_line():
    logging.info("GET /api/ha_pickup_line - Returning one random saved line")
    saved_lines = load_saved_lines()
    if not saved_lines:
        return jsonify({"line": "No saved pickup lines yet!"})
    selected = random.choice(saved_lines)
    logging.info(f"Selected line for HA: {selected['line']}")
    return jsonify({"line": selected["line"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
