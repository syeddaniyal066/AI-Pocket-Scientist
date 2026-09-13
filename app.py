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
# TEXT PROMPT
# ======================================================

def build_ai_prompt(question, vision=""):
    image_context = ""

    if vision:
        image_context = f"""
A local image recognition model identified the uploaded image as:
{vision}

Use this identification only as supporting context.
Do not claim that you personally viewed the image.
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
# VISION PROMPT
# ======================================================

def build_vision_prompt(question):
    return f"""
You are AI Pocket Scientist.

Look at the uploaded image directly and answer the student's question about it.
Identify visible objects, animals, plants, diagrams, text, or scientific details as accurately as possible.
If the exact identity is uncertain, say "appears to be" instead of pretending to be certain.
Do not mention MobileNet or any image label.

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
# PERPLEXITY - TEXT
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
# GROQ - TEXT FALLBACK
# ======================================================

def ask_groq_text(question, vision=""):
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
# GROQ - REAL IMAGE VISION
# ======================================================

def ask_groq_vision(question, image_data_url):
    prompt = build_vision_prompt(question)

    response = (
        groq_client
        .chat
        .completions
        .create(
            model="qwen/qwen3.6-27b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=150
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

        # Optional MobileNet label. Used only as a fallback.
        vision = str(
            data.get("vision", "")
        ).strip()

        # Actual image as a browser-generated data URL.
        image = str(
            data.get("image", "")
        ).strip()

        if question == "":
            return jsonify({
                "answer": "Please enter a question."
            }), 400

        if image and not image.startswith("data:image/"):
            return jsonify({
                "answer": "The uploaded image format is not supported."
            }), 400

        print("\n=================================")
        print("QUESTION:", question)
        print("IMAGE RECEIVED:", bool(image))
        print("MOBILENET FALLBACK LABEL:", vision)
        print("=================================")

        if not perplexity_client and not groq_client:
            return jsonify({
                "answer": "AI service is not configured on this server."
            }), 503

        # ==================================================
        # IMAGE QUESTION: GROQ VISION FIRST
        # ==================================================

        if image:
            if groq_client:
                try:
                    answer = ask_groq_vision(
                        question,
                        image
                    )

                    return jsonify({
                        "answer": answer,
                        "model": "Groq Vision",
                        "vision_model": "qwen/qwen3.6-27b"
                    })

                except Exception as error:
                    print(
                        "Groq Vision Error:",
                        error
                    )

            # If vision fails, use the old MobileNet label as backup.
            if vision and perplexity_client:
                try:
                    answer = ask_perplexity(
                        question,
                        vision
                    )

                    return jsonify({
                        "answer": answer,
                        "model": "Perplexity",
                        "fallback": "MobileNet label"
                    })

                except Exception as error:
                    print(
                        "Perplexity Image Fallback Error:",
                        error
                    )

            if vision and groq_client:
                try:
                    answer = ask_groq_text(
                        question,
                        vision
                    )

                    return jsonify({
                        "answer": answer,
                        "model": "Groq Text",
                        "fallback": "MobileNet label"
                    })

                except Exception as error:
                    print(
                        "Groq Image Fallback Error:",
                        error
                    )

            return jsonify({
                "answer": "I could not analyze this image right now. Please try another image."
            }), 503

        # ==================================================
        # TEXT QUESTION: PERPLEXITY FIRST
        # ==================================================

        if perplexity_client:
            try:
                answer = ask_perplexity(
                    question
                )

                return jsonify({
                    "answer": answer,
                    "model": "Perplexity"
                })

            except Exception as error:
                print(
                    "Perplexity Error:",
                    error
                )

        # ==================================================
        # TEXT FALLBACK: GROQ
        # ==================================================

        if groq_client:
            try:
                answer = ask_groq_text(
                    question
                )

                return jsonify({
                    "answer": answer,
                    "model": "Groq"
                })

            except Exception as error:
                print(
                    "Groq Error:",
                    error
                )

        return jsonify({
            "answer": "AI service is temporarily unavailable."
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
