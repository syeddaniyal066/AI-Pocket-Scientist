from flask import Flask, request, jsonify
from flask_cors import CORS

from dotenv import load_dotenv

from perplexity import Perplexity
from groq import Groq

from research import research_question
from summarizer import summarize_research

import re


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


perplexity_client = Perplexity()

groq_client = Groq()


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

def build_ai_prompt(
    question,
    vision=""
):

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

def ask_perplexity(
    question,
    vision=""
):

    prompt = build_ai_prompt(
        question,
        vision
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


    # Remove citation numbers
    answer = re.sub(
        r"\[\d+\]",
        "",
        answer
    )


    return answer.strip()


# ======================================================
# GROQ
# ======================================================

def ask_groq(
    question,
    vision=""
):

    prompt = build_ai_prompt(
        question,
        vision
    )


    response = (
        groq_client
        .chat
        .completions
        .create(

            model=
                "llama-3.3-70b-versatile",

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

        # --------------------------------------------------
        # RECEIVE REQUEST
        # --------------------------------------------------

        data = request.get_json()


        if not data:

            return jsonify({
                "answer":
                    "No question received."
            }), 400


        question = data.get(
            "question",
            ""
        ).strip()


        vision = data.get(
            "vision",
            ""
        ).strip()


        mode = data.get(
            "mode",
            "web"
        ).strip().lower()


        if question == "":

            return jsonify({
                "answer":
                    "Please enter a question."
            }), 400


        print(
            "\n================================="
        )

        print(
            "MODE:",
            mode
        )

        print(
            "QUESTION:",
            question
        )

        print(
            "VISION:",
            vision
        )

        print(
            "================================="
        )


        # ==================================================
        # AI MODE
        # ==================================================

        if mode == "ai":

            try:

                answer = ask_perplexity(
                    question,
                    vision
                )


                return jsonify({

                    "answer":
                        answer,

                    "model":
                        "Perplexity",

                    "vision":
                        vision,

                    "mode":
                        "ai"

                })


            except Exception as error:

                print(
                    "Perplexity Error:",
                    error
                )


                # ------------------------------------------
                # GROQ FALLBACK
                # ------------------------------------------

                answer = ask_groq(
                    question,
                    vision
                )


                return jsonify({

                    "answer":
                        answer,

                    "model":
                        "Groq",

                    "vision":
                        vision,

                    "mode":
                        "ai"

                })


        # ==================================================
        # WEB SEARCH MODE
        # ==================================================

        research_query = question

        summary_question = question


        if vision:

            question_lower = question.lower().strip()

            generic_image_questions = [

                "what is this",
                "what is this image",
                "what is that",
                "what is that image",
                "what's this",
                "what's that",

                "identify this",
                "identify that",

                "identify image",
                "identify the image",

                "what animal is this",
                "what object is this",
                "what plant is this",
                "what insect is this"

            ]


            is_generic_image_question = any(

                phrase
                in question_lower

                for phrase
                in generic_image_questions

            )


            # ----------------------------------------------
            # GENERIC IMAGE QUESTION
            # ----------------------------------------------

            if is_generic_image_question:

                # Search ONLY the image label
                #
                # Example:
                #
                # lycaenid butterfly

                research_query = vision

                summary_question = vision


            # ----------------------------------------------
            # SPECIFIC IMAGE QUESTION
            # ----------------------------------------------

            else:

                research_query = (
                    question
                    + " "
                    + vision
                )


                summary_question = (
                    question
                    + " "
                    + vision
                )


        print(
            "RESEARCH QUERY:",
            research_query
        )


        # ==================================================
        # STEP 1
        # ==================================================

        research_results =research_question(
                research_query
            )


        if not research_results:

            return jsonify({

                "answer":
                    "I could not find enough reliable information for that question.",

                "vision":
                    vision,

                "mode":
                    "web",

                "sources":
                    []

            })


        # ==================================================
        # STEP 2
        # ==================================================

        summary = summarize_research(

                research_results,

                summary_question,

                3

            )


        # ==================================================
        # SOURCES
        # ==================================================

        sources = [

            item["url"]

            for item
            in research_results

        ]


        # ==================================================
        # RETURN WEB RESULT
        # ==================================================

        return jsonify({

            "answer":
                summary,

            "vision":
                vision,

            "mode":
                "web",

            "sources":
                sources,

            "system":
                "AI Pocket Scientist Research Engine"

        })


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