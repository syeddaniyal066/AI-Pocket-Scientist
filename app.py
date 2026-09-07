from flask import Flask, request, jsonify
from flask_cors import CORS

from research import research_question
from summarizer import summarize_research


# ======================================================
# CREATE FLASK APP
# ======================================================

app = Flask(__name__)


# Allow Netlify frontend to talk to Render backend
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
# ASK
# ======================================================

@app.route("/ask", methods=["POST"])
def ask():

    try:

        # --------------------------------------------------
        # RECEIVE DATA FROM JAVASCRIPT
        # --------------------------------------------------

        data = request.get_json()


        if not data:

            return jsonify({
                "answer": "No question received."
            }), 400


        # --------------------------------------------------
        # QUESTION
        # --------------------------------------------------

        question = data.get(
            "question",
            ""
        ).strip()


        if question == "":

            return jsonify({
                "answer": "Please enter a question."
            }), 400


        # --------------------------------------------------
        # VISION RESULT
        # --------------------------------------------------

        # Example:
        # lycaenid butterfly

        vision = data.get(
            "vision",
            ""
        ).strip()


        print("\n===================================")
        print("QUESTION:")
        print(question)

        print("\nVISION:")
        print(
            vision
            if vision
            else "No image"
        )

        print("===================================")


        # ==================================================
        # DEFAULT
        # ==================================================

        research_query = question

        summary_question = question


        # ==================================================
        # IMAGE EXISTS
        # ==================================================

        if vision:

            question_lower = question.lower()


            # ------------------------------------------------
            # GENERIC IMAGE QUESTIONS
            # ------------------------------------------------
            #
            # Example:
            #
            # "what is this image"
            # "what is this"
            # "identify this"
            #
            # In these cases we IGNORE the question
            # for web search.
            #
            # We search ONLY:
            #
            # lycaenid butterfly
            #
            # ------------------------------------------------

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

                phrase in question_lower

                for phrase in generic_image_questions

            )


            # ==================================================
            # GENERIC IMAGE QUESTION
            # ==================================================

            if is_generic_image_question:

                # Search ONLY vision result
                research_query = vision

                # Summarizer also focuses
                # on vision result
                summary_question = vision


            # ==================================================
            # SPECIFIC IMAGE QUESTION
            # ==================================================
            #
            # Example:
            #
            # "Why are this butterfly's wings blue?"
            #
            # We need BOTH:
            #
            # question + vision
            #
            # ==================================================

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


        # ==================================================
        # SHOW FINAL QUERY IN RENDER LOGS
        # ==================================================

        print("\nRESEARCH QUERY:")
        print(research_query)


        print("\nSUMMARY QUESTION:")
        print(summary_question)


        # ==================================================
        # STEP 1
        # SEARCH WEBSITES
        # ==================================================

        research_results = research_question(
            research_query
        )


        # ==================================================
        # NO RESULTS
        # ==================================================

        if not research_results:

            print(
                "\nNO RESEARCH RESULTS FOUND"
            )


            return jsonify({

                "answer":
                    "I could not find enough reliable information for that question.",

                "vision":
                    vision,

                "research_query":
                    research_query,

                "sources":
                    [],

                "system":
                    "AI Pocket Scientist Research Engine"

            })


        print(
            "\nWEBSITES FOUND:",
            len(research_results)
        )


        # ==================================================
        # STEP 2
        # OUR OWN SUMMARIZER
        # ==================================================

        summary = summarize_research(

            research_results,

            summary_question,

            3

        )


        print("\nSUMMARY:")
        print(summary)


        # ==================================================
        # SOURCES
        # ==================================================

        sources = [

            result["url"]

            for result in research_results

        ]


        # ==================================================
        # STEP 3
        # SEND RESULT TO NETLIFY PAGE
        # ==================================================

        return jsonify({

            "answer":
                summary,

            "vision":
                vision,

            "research_query":
                research_query,

            "sources":
                sources,

            "system":
                "AI Pocket Scientist Research Engine"

        })


    # ======================================================
    # ERROR
    # ======================================================

    except Exception as error:

        print("\nSERVER ERROR:")
        print(error)


        return jsonify({

            "answer":
                "Something went wrong while researching your question.",

            "system":
                "AI Pocket Scientist Research Engine"

        }), 500


# ======================================================
# LOCAL TESTING
# ======================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )