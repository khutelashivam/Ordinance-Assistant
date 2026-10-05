# IIIT Bhagalpur Ordinance Assistant

A small Flask app that searches ordinance notes by meaning, asks Gemini to answer from the matching passages, and displays the source, section, and page.

## How the code works

1. `app.py` receives the student's question.
2. `services/knowledge_loader.py` reads the Markdown files in `knowledge/` and keeps their citation details.
3. `services/knowledge_search.py` uses Gemini embeddings to find passages similar in meaning. It saves the vectors in `knowledge_index.json` and reuses them until the knowledge text changes.
4. `services/ai_service.py` gives the question and matching passages to Gemini.
5. `templates/index.html` shows the answer and citations. `static/style.css` styles the page.

## Run the app

1. Activate the project's virtual environment.
2. Install packages with `pip install -r requirements.txt`.
3. Add your Gemini API key to `.env` as `GEMINI_API_KEY=your-key`.
4. Run `python app.py` and open `http://127.0.0.1:5000`.

If no saved embedding index exists, the first question creates one, so it can take longer. Later questions reuse it. When a knowledge file changes, the app creates a fresh index. The app also reuses the index from the earlier project version when the knowledge files are unchanged.

## Knowledge file citations

Markdown files in `knowledge/` start with YAML details such as `document`, `title`, `section`, `source_pages`, and `source_file`. Numbered headings such as `8.2 Minimum Attendance` are used as the citation section when available. Optional `related_sections` values add directly linked sections to the answer's sources.
