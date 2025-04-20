from flask import Flask, jsonify, render_template, request, abort
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
auth_token = os.getenv("API_AUTH_TOKEN")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/dirtyline", methods=["GET"])
def get_dirty_line():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if auth_token and token != auth_token:
        abort(401)

    prompt = "Give me a short, playful, and mildly dirty pickup line to send to my wife. Keep it flirty, funny, and under 30 words."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=60
        )
        line = response.choices[0].message.content.strip()
        return jsonify({"line": line})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
