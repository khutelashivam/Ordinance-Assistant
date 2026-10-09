"""Web page for the IIIT Bhagalpur ordinance assistant."""

from flask import Flask, render_template, request

from services.ai_service import generate_answer
from services.markdown_service import load_knowledge_sections
from services.search_service import search_knowledge


app = Flask(__name__)

try:
    KNOWLEDGE_SECTIONS = load_knowledge_sections()
    app.logger.info("Loaded %s ordinance sections with embeddings", len(KNOWLEDGE_SECTIONS))
except Exception:
    app.logger.exception("Could not load Markdown ordinance knowledge")
    KNOWLEDGE_SECTIONS = []


@app.route("/", methods=["GET", "POST"])
def home():
    """Show the page and answer a submitted question."""
    question = ""
    result = None
    error = None

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if not question:
            error = "Please enter a question about the B.Tech ordinance."
        elif not KNOWLEDGE_SECTIONS:
            error = (
                "The ordinance search index is missing or invalid. "
                "Run python scripts/build_index.py, then restart the app."
            )
        else:
            try:
                passages, client = search_knowledge(question, KNOWLEDGE_SECTIONS)
                if not passages:
                    error = "I could not find a relevant ordinance section for that question."
                else:
                    result = generate_answer(question, passages, client)
            except Exception as problem:
                app.logger.exception("Could not answer the question")
                if "429" in str(problem) or "quota" in str(problem).lower():
                    error = "Gemini is temporarily out of requests. Please try again in a minute."
                elif "401" in str(problem) or "403" in str(problem) or "API_KEY" in str(problem):
                    error = "Gemini rejected the API key. Check that it is correct and enabled."
                elif "503" in str(problem) or "UNAVAILABLE" in str(problem):
                    error = "Gemini is temporarily unavailable. Please try again shortly."
                elif "500" in str(problem) or "INTERNAL" in str(problem):
                    error = "Gemini encountered a temporary internal error. Please try again shortly."
                elif "404" in str(problem) or "NOT_FOUND" in str(problem):
                    error = "The configured Gemini model was not found. Check GEMINI_MODEL in .env."
                else:
                    error = "The assistant could not answer. See the terminal for the error details."

    return render_template("index.html", question=question, result=result, error=error)


if __name__ == "__main__":
    # macOS Control Center can occupy port 5000, so use 5001 for Flask.
    app.run(debug=True, port=5001)
