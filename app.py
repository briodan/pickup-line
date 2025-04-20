from flask import Flask, jsonify, render_template, request
import openai
import os

app = Flask(__name__)

# Set up the OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/dirtyline", methods=["GET"])
def get_dirty_line():
    prompt = "Give me a short, playful, and mildly dirty pickup line to send to my wife. Keep it flirty, funny, and under 30 words."

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=60
        )
        line = response.choices[0].message.content.strip()
        return jsonify({"line": line})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
