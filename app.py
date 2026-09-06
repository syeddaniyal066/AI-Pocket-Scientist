from flask import Flask, request, jsonify
from flask_cors import CORS

from research import research_question
from summarizer import summarize_research


# ======================================================
# CREATE FLASK APP
# ======================================================

app = Flask(__name__)


# Allow Netlify / browser to communicate
# with the Render backend.
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "OPTIONS"]
)


# ======================================================
# HOME PAGE
# ======================================================

@app.route("/")
def home():

    return "AI Pocket Scientist Server Running!"


# ======================================================
# ASK ENDPOINT
# ======================================================

@app.route("/ask", methods=["POST"])
def ask():

    try:

        # ----------------------------------------------
        # GET QUESTION FROM JAVASCRIPT
        # ----------------------------------------------

        data = request.get_json()


        if not data:

            return jsonify(
                {
                    "answer": "No question received."
                }
            ), 400


        question = data.get(
            "question",
            ""
        ).strip()


        if question == "":

            return jsonify(
                {
                    "answer":
                    "Please enter a question."
                }
            ), 400


        print("\n=================================")
        print("QUESTION:")
        print(question)
        print("=================================")


        # ==============================================
        # STEP 1
        # SEARCH REAL WEBSITES
        # ==============================================

        research_results = research_question(
            question
        )


        # Nothing useful found
        if not research_results:

            return jsonify(
                {
                    "answer":
                    "I could not find enough reliable information for that question."
                }
            )


        print(
            "\nResearch websites found:",
            len(research_results)
        )


        # ==============================================
        # STEP 2
        # OUR OWN SUMMARIZER
        # ==============================================

        summary = summarize_research(
            research_results,
            question,
            3
        )


        print("\n3-LINE SUMMARY:")
        print(summary)


        # ==============================================
        # STEP 3
        # SEND RESULT TO WEBSITE
        # ==============================================

        sources = [
            item["url"]
            for item in research_results
        ]


        return jsonify(
            {
                "answer": summary,
                "sources": sources,
                "system": "AI Pocket Scientist Research Engine"
            }
        )


    except Exception as error:

        print(
            "SERVER ERROR:",
            error
        )


        return jsonify(
            {
                "answer":
                "Something went wrong while researching your question."
            }
        ), 500


# ======================================================
# RUN LOCALLY
# ======================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )