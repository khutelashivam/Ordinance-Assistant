# IIIT Bhagalpur B.Tech Ordinance Assistant

A Flask application that searches the official B.Tech Ordinance 2026, retrieves the matching Markdown section, and asks Gemini to answer with a source citation.

## Knowledge flow

```text
B.Tech-ordinance2026.pdf
    -> scripts/pdf_to_markdown.py
    -> knowledge/sections/*.md
    -> scripts/build_index.py
    -> knowledge/index.md
    -> Flask question search and Markdown retrieval
    -> Gemini answer with citations
```

The PDF is processed only by `scripts/pdf_to_markdown.py`. A normal question does not read or process the PDF. The generated Markdown files hold the extracted ordinance wording. The index holds section IDs, file references, section names, source pages, and Gemini embeddings; it does not contain ordinance text.

## Build the knowledge files

The project includes `B.Tech-ordinance2026.pdf` in its root folder. The converter reads that copy:

```bash
python scripts/pdf_to_markdown.py
```

It writes one file per numbered ordinance topic under `knowledge/sections/`. Each numbered clause is a Markdown section, and a hidden page marker records the printed PDF page for citations. Existing files made by the converter are refreshed on each run.

Generate or update the semantic index with the Gemini API key in `.env`:

```text
GEMINI_API_KEY=your-key
```

Then run:

```bash
python scripts/build_index.py
```

The builder uses `gemini-embedding-001` for section and question embeddings. Run it after converting the PDF or changing the Markdown. It waits one minute after the first 100 sections to stay within the free-tier embedding limit.

## Run the application

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5001`. The existing Flask route remains `POST /` and accepts a form field named `question`. For example:

```bash
curl -X POST http://127.0.0.1:5001/ \
  -F 'question=What happens if my attendance is below 50 percent?'
```

At startup, the app parses `knowledge/index.md` into memory. For each submitted question, it embeds the question, ranks the stored vectors using NumPy cosine similarity, reads the selected sections from their source Markdown files, and sends that actual Markdown text to Gemini. Answers cite the source filename, ordinance section, and printed page.

## Render

Use `pip install -r requirements.txt` as the build command and `gunicorn app:app` as the start command. Set `GEMINI_API_KEY` in Render. Commit the generated `knowledge/sections/` files and `knowledge/index.md`; Render does not need the original PDF to answer questions.

## PDF conversion assumptions

The converter skips the cover and contents pages, uses the numbered headings in the ordinance to group sections, and removes only the repeating document title and printed page header. It preserves extracted PDF wording and line order. Complex tables are retained as extracted text rather than reconstructed as Markdown tables, so their column layout may not be as readable as the original PDF. Page markers use the printed page number shown in the PDF.
