from flask import Flask, request, jsonify
from flask_cors import CORS

from dotenv import load_dotenv
from perplexity import Perplexity
from groq import Groq

import re

# ============================
# Load Environment Variables
# ============================

load_dotenv()

# ============================
# AI Clients
# ============================

perplexity_client = Perplexity()
groq_client = Groq()

# ============================
# Flask App
# ============================

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "OPTIONS"]
)

app.config["CORS_HEADERS"] = "Content-Type"

# ============================
# Prompt Builder
# ============================

def build_prompt(question):

    return f"""
You are AI Pocket Scientist.

RULES:
- Maximum 25 words.
- Exactly 2 sentences.
- No lists.
- No headings.
- No markdown.
- No bullet points.
- No introduction.
- Stop immediately after the second sentence.
- Answer in simple language for school students.

Question:
{question}
"""

# ============================
# Perplexity
# ============================

def ask_perplexity(question):

    prompt = build_prompt(question)

    response = perplexity_client.chat.completions.create(
        model="sonar",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response.choices[0].message.content

    # Remove citation numbers like [1][2]
    answer = re.sub(r"\[\d+\]", "", answer)

    answer = answer.strip()

    return answer

# ============================
# Groq
# ============================

def ask_groq(question):

    prompt = build_prompt(question)

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()

# ============================
# Home
# ============================

@app.route("/")
def home():

    return "AI Pocket Scientist Server Running!"

# ============================
# Ask AI
# ============================

@app.route("/ask", methods=["POST"])
def ask():

    try:

        data = request.get_json()

        if not data:
            return jsonify({"answer": "No JSON received."}), 400

        question = data.get("question", "").strip()

        if question == "":
            return jsonify({"answer": "Please enter a question."}), 400

        # Try Perplexity first
        try:

            answer = ask_perplexity(question)

            return jsonify({
                "answer": answer,
                "model": "Perplexity"
            })

        except Exception as e:

            print("Perplexity Error:", e)

            # Fallback to Groq

            answer = ask_groq(question)

            return jsonify({
                "answer": answer,
                "model": "Groq"
            })

    except Exception as e:

        print(e)

        return jsonify({
            "answer": "Something went wrong."
        }), 500

# ============================
# Run Server
# ============================

if __name__ == "__main__":

    app.run(debug=True)

