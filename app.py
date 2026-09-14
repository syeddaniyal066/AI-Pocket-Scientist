import os
import re

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from openai import OpenAI

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
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")


# ======================================================
# CLIENTS
# ======================================================

perplexity_client = (
    Perplexity(
        api_key=PERPLEXITY_API_KEY
    )
    if Perplexity and PERPLEXITY_API_KEY
    else None
)


groq_client = (
    Groq(
        api_key=GROQ_API_KEY
    )
    if Groq and GROQ_API_KEY
    else None
)


qwen_client = (
    OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url=(
            "https://dashscope-intl.aliyuncs.com/"
            "compatible-mode/v1"
        )
    )
    if DASHSCOPE_API_KEY
    else None
)


# ======================================================
# FLASK
# ======================================================

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": "*"
        }
    },
    allow_headers=[
        "Content-Type"
    ],
    methods=[
        "GET",
        "POST",
        "OPTIONS"
    ]
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

def build_ai_prompt(question):

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
- Use simple language for school students.
- Answer the student's actual question.
- Stop after the second sentence.

Question:
{question}
"""


# ======================================================
# PERPLEXITY
# ======================================================

def ask_perplexity(question):

    if not perplexity_client:
        raise Exception(
            "Perplexity is not configured."
        )

    prompt = build_ai_prompt(
        question
    )

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

    # Remove Perplexity citation numbers
    answer = re.sub(
        r"\[\d+\]",
        "",
        answer
    )

    return answer.strip()


# ======================================================
# GROQ TEXT FALLBACK
# ======================================================

def ask_groq(question):

    if not groq_client:
        raise Exception(
            "Groq is not configured."
        )

    prompt = build_ai_prompt(
        question
    )

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
# QWEN VISION
# ======================================================

def ask_qwen_vision(
    question,
    image_base64
):

    if not qwen_client:
        raise Exception(
            "Qwen is not configured."
        )

    prompt = f"""
You are AI Pocket Scientist.

Carefully examine the uploaded image.

Answer the student's question using what you can actually
see in the image.

RULES:
- Maximum 25 words.
- Exactly 2 sentences.
- No lists.
- No headings.
- No markdown.
- Use simple language for school students.
- Be specific about the image.
- Do not invent details you cannot see.
- Stop after the second sentence.

Student question:
{question}
"""

    response = (
        qwen_client
        .chat
        .completions
        .create(
            model="qwen3-vl-plus",

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
                                "url":
                                    image_base64
                            }
                        }
                    ]
                }
            ],

            temperature=0.2,
            max_tokens=120
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

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "answer":
                    "No question received."
            }), 400


        question = (
            data.get(
                "question",
                ""
            )
            .strip()
        )


        image = (
            data.get(
                "image",
                ""
            )
            .strip()
        )


        if question == "":

            return jsonify({
                "answer":
                    "Please enter a question."
            }), 400


        print(
            "================================="
        )

        print(
            "QUESTION:",
            question
        )

        print(
            "IMAGE:",
            "YES"
            if image
            else "NO"
        )

        print(
            "================================="
        )


        # ==================================================
        # IMAGE → QWEN
        # ==================================================

        if image:

            try:

                print(
                    "Using Qwen Vision..."
                )

                answer = ask_qwen_vision(
                    question,
                    image
                )

                return jsonify({

                    "answer":
                        answer,

                    "model":
                        "Qwen3-VL-Plus"

                })

            except Exception as error:

                print(
                    "Qwen Vision Error:",
                    error
                )

                return jsonify({

                    "answer":
                        "I could not read this image. Please try again.",

                    "model":
                        "Qwen Vision Error"

                }), 500


        # ==================================================
        # TEXT → PERPLEXITY
        # ==================================================

        try:

            print(
                "Using Perplexity..."
            )

            answer = ask_perplexity(
                question
            )

            return jsonify({

                "answer":
                    answer,

                "model":
                    "Perplexity"

            })


        # ==================================================
        # FALLBACK → GROQ
        # ==================================================

        except Exception as error:

            print(
                "Perplexity Error:",
                error
            )


            try:

                print(
                    "Using Groq fallback..."
                )

                answer = ask_groq(
                    question
                )

                return jsonify({

                    "answer":
                        answer,

                    "model":
                        "Groq"

                })


            except Exception as groq_error:

                print(
                    "Groq Error:",
                    groq_error
                )

                return jsonify({

                    "answer":
                        "AI service is temporarily unavailable."

                }), 503


    except Exception as error:

        print(
            "SERVER ERROR:",
            error
        )

        return jsonify({

            "answer":
                "Something went wrong while processing your question."

        }), 500


# ======================================================
# LOCAL TEST
# ======================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )