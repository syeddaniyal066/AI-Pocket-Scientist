import os
import re

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

try:
    from perplexity import Perplexity
except Exception:
    Perplexity = None

try:
    from groq import Groq
except Exception:
    Groq = None


# ======================================================
# ENVIRONMENT
# ======================================================

load_dotenv()

# Existing API keys are automatically used.
#
# PERPLEXITY_API_KEY
# GROQ_API_KEY
#
# NO .env CHANGES REQUIRED.

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

perplexity_client = (
    Perplexity(api_key=PERPLEXITY_API_KEY)
    if Perplexity and PERPLEXITY_API_KEY
    else None
)

groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if Groq and GROQ_API_KEY
    else None
)


# ======================================================
# FLASK
# ======================================================

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "OPTIONS"]
)


# ======================================================
# HOME
# ======================================================

@app.route("/")
def home():
    return "AI Pocket Scientist Server Running!"


# ======================================================
# AI PROMPT
# ======================================================

def build_ai_prompt(question, vision=""):
    image_context = ""

    if vision:
        image_context = f"""
A local image recognition model identified the uploaded image as:
{vision}

Use this identification as context.
Do not say that you personally viewed the image.
"""

    return f"""
You are AI Pocket Scientist.

{image_context}

RULES:
- Maximum 25 words.
- Exactly 2 sentences.
- No lists.
- No headings.
- No markdown.
- No bullet points.
- No introduction.
- Use simple language for school students.
- Answer the student's actual question.
- Stop after the second sentence.

Question:
{question}
"""


# ======================================================
# PERPLEXITY
# ======================================================

def ask_perplexity(question, vision=""):
    prompt = build_ai_prompt(question, vision)

    response = (
        perplexity_client
        .chat
        .completions
        .create(
            model="sonar",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
    )

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    # Remove citation numbers such as [1], [2], etc.
    answer = re.sub(
        r"\[\d+\]",
        "",
        answer
    )

    return answer.strip()


# ======================================================
# GROQ FALLBACK
# ======================================================

def ask_groq(question, vision=""):
    prompt = build_ai_prompt(question, vision)

    response = (
        groq_client
        .chat
        .completions
        .create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
    )

    return (
        response
        .choices[0]
        .message
        .content
        .strip()
    )


# ======================================================
# ASK ENDPOINT
# ======================================================

@app.route(
    "/ask",
    methods=["POST"]
)
def ask():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "answer": "No question received."
            }), 400

        question = str(
            data.get("question", "")
        ).strip()

        vision = str(
            data.get("vision", "")
        ).strip()

        if question == "":
            return jsonify({
                "answer": "Please enter a question."
            }), 400

        print("\n=================================")
        print("QUESTION:", question)
        print("VISION:", vision)
        print("=================================")

        if not perplexity_client and not groq_client:
            return jsonify({
                "answer": "AI service is not configured on this server.",
                "vision": vision
            }), 503

        # ==================================================
        # PRIMARY: PERPLEXITY
        # ==================================================

        if perplexity_client:
            try:
                answer = ask_perplexity(
                    question,
                    vision
                )

                return jsonify({
                    "answer": answer,
                    "model": "Perplexity",
                    "vision": vision
                })

            except Exception as error:
                print(
                    "Perplexity Error:",
                    error
                )

        # ==================================================
        # FALLBACK: GROQ
        # ==================================================

        if groq_client:
            try:
                answer = ask_groq(
                    question,
                    vision
                )

                return jsonify({
                    "answer": answer,
                    "model": "Groq",
                    "vision": vision
                })

            except Exception as error:
                print(
                    "Groq Error:",
                    error
                )

        return jsonify({
            "answer": "AI service is temporarily unavailable.",
            "vision": vision
        }), 503

    except Exception as error:
        print(
            "SERVER ERROR:",
            error
        )

        return jsonify({
            "answer": "Something went wrong while processing your question."
        }), 500


# ======================================================
# LOCAL TEST
# ======================================================

if __name__ == "__main__":
    app.run(
        debug=True
    )