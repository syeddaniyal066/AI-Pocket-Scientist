from flask import Flask, request, jsonify
from flask_cors import CORS

from research import research_question
from summarizer import summarize_research


# ======================================================
# CREATE FLASK APP
# ======================================================

app = Flask(__name__)


# Allow Netlify/frontend to talk to Render/backend
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
        # GET JSON FROM JAVASCRIPT
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
        # "golden retriever, Labrador retriever, dog"

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
        # BUILD RESEARCH QUERY
        # ==================================================

        research_query = question


        # If an image was analyzed,
        # add the visual information to the search.
        if vision:

            research_query = (
                question
                + " "
                + vision
            )


        print("\nRESEARCH QUERY:")
        print(research_query)


        # ==================================================
        # STEP 1
        # SEARCH REAL WEBSITES
        # ==================================================

        research_results = research_question(
            research_query
        )


        if not research_results:

            return jsonify({
                "answer":
                "I could not find enough reliable information for that question."
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
            question,
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
        # SEND RESULT TO WEBSITE
        # ==================================================

        return jsonify({

            "answer": summary,

            "vision": vision,

            "sources": sources,

            "system":
                "AI Pocket Scientist Research Engine"

        })


    except Exception as error:

        print(
            "\nSERVER ERROR:",
            error
        )


        return jsonify({

            "answer":
                "Something went wrong while researching your question."

        }), 500


# ======================================================
# LOCAL RUN
# ======================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )