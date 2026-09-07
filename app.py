from flask import Flask, request, jsonify
from flask_cors import CORS

from research import research_question
from summarizer import summarize_research


# ======================================================
# CREATE FLASK APP
# ======================================================

app = Flask(__name__)


# Allow frontend / Netlify to talk to backend / Render
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "OPTIONS"]
)


# ======================================================
# HOME ROUTE
# ======================================================

@app.route("/")
def home():

    return "AI Pocket Scientist Server Running!"


# ======================================================
# ASK ROUTE
# ======================================================

@app.route("/ask", methods=["POST"])
def ask():

    try:

        # --------------------------------------------------
        # GET DATA FROM JAVASCRIPT
        # --------------------------------------------------

        data = request.get_json()


        if not data:

            return jsonify({
                "answer": "No question received."
            }), 400


        # --------------------------------------------------
        # GET QUESTION
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
        # GET VISION RESULT
        # --------------------------------------------------

        # Example:
        # "butterfly, monarch butterfly, insect"

        vision = data.get(
            "vision",
            ""
        ).strip()


        # --------------------------------------------------
        # DEBUG PRINT
        # --------------------------------------------------

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
        # BUILD RESEARCH QUERY
        # ==================================================

        research_query = question

        summary_question = question


        # --------------------------------------------------
        # IF IMAGE EXISTS
        # --------------------------------------------------

        if vision:

            question_lower = question.lower()


            # Questions like:
            #
            # what is this?
            # what is this image?
            # identify this
            #
            # are too generic for normal web search.
            #
            # So we search mainly using what
            # MobileNet detected.

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
                "what object is this"

            ]


            is_generic_image_question = any(

                phrase in question_lower

                for phrase in generic_image_questions

            )


            # ------------------------------------------------
            # GENERIC IMAGE QUESTION
            # ------------------------------------------------

            if is_generic_image_question:

                research_query = (
                    vision
                    + " science identification"
                )


                # For summarizer,
                # focus on the detected object.

                summary_question = vision


            # ------------------------------------------------
            # IMAGE + SPECIFIC QUESTION
            # ------------------------------------------------

            else:

                # Example:
                #
                # Question:
                # Why does this butterfly have blue wings?
                #
                # Vision:
                # butterfly, insect
                #
                # Search:
                # Why does this butterfly have blue wings?
                # butterfly insect

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
        # PRINT FINAL SEARCH QUERY
        # ==================================================

        print("\nRESEARCH QUERY:")
        print(research_query)


        print("\nSUMMARY QUESTION:")
        print(summary_question)


        # ==================================================
        # STEP 1
        # SEARCH REAL WEBSITES
        # ==================================================

        research_results = research_question(
            research_query
        )


        # --------------------------------------------------
        # NOTHING FOUND
        # --------------------------------------------------

        if not research_results:

            return jsonify({

                "answer":
                    "I could not find enough reliable information for that question.",

                "vision": vision,

                "sources": [],

                "system":
                    "AI Pocket Scientist Research Engine"

            })


        print(
            "\nWebsites found:",
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


        print("\n3-LINE SUMMARY:")

        print(summary)


        # ==================================================
        # COLLECT SOURCE URLS
        # ==================================================

        sources = [

            result["url"]

            for result in research_results

        ]


        # ==================================================
        # STEP 3
        # SEND ANSWER TO FRONTEND
        # ==================================================

        return jsonify({

            "answer": summary,

            "vision": vision,

            "sources": sources,

            "system":
                "AI Pocket Scientist Research Engine"

        })


    # ======================================================
    # ERROR HANDLING
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