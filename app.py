from flask import Flask, jsonify, render_template
import os
import requests
import openai

app = Flask(__name__)

# Load keys from .env
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/dirtyline", methods=["GET"])
def get_dirty_line():
    prompt = """
    Give me a short, bold, dirty pickup line to send to my wife. 
    It should be raunchy, NSFW, sexually suggestive, and flirty — the kind of thing I’d whisper in bed. 
    Keep it under 30 words.
    """

    # --- Try OpenRouter ---
    try:
        print("Trying OpenRouter...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Pickup Line App"
            },
            json={
                "model": "gpt-4o",  # or "nous-hermes-2-mixtral", etc.
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

    # --- Fallback: OpenAI ---
    try:
        print("Falling back to OpenAI...")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # You can change this to "gpt-4o" if you have access
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=60
        )
        line = response.choices[0].message.content.strip()
        return jsonify({"line": line, "source": "openai"})
    except Exception as e:
        print(f"OpenAI fallback failed: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
