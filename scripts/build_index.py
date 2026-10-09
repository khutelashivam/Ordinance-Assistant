"""Create knowledge/index.md from the ordinance Markdown sections."""

import json
import os
import sys
import time

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_FOLDER not in sys.path:
    sys.path.insert(0, PROJECT_FOLDER)

from services.embedding_service import create_gemini_client, embed_sections
from services.markdown_service import list_markdown_files, read_markdown_sections
from services.settings import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, KNOWLEDGE_FOLDER


BATCH_SIZE = 20


def make_section_id(file_name, section_name):
    """Build an ID such as attendance_8_2 from a file and heading."""
    topic = os.path.splitext(file_name)[0].replace("section_", "", 1)
    topic = topic.split("_", 1)[1]
    section = section_name.replace(".", "_").replace("-", "_").replace(" ", "_")
    return topic + "_" + section.lower()


def write_index(sections):
    """Save metadata and vectors in one YAML block inside index.md."""
    lines = [
        "# Knowledge Index", "", "```yaml",
        "embedding_model: " + EMBEDDING_MODEL,
        "embedding_dimensions: " + str(EMBEDDING_DIMENSIONS),
        "sections:",
    ]

    for section in sections:
        lines.append("  - section_id: " + json.dumps(section["section_id"]))
        for name in ("document", "section", "topic", "page"):
            lines.append("    " + name + ": " + json.dumps(str(section[name]), ensure_ascii=False))
        numbers = ", ".join(format(value, ".9g") for value in section["embedding"])
        lines.append("    embedding: [" + numbers + "]")

    lines.extend(["```", ""])
    index_path = os.path.join(KNOWLEDGE_FOLDER, "index.md")
    with open(index_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def main():
    """Read sections, create their embeddings, and write the index."""
    sections = []
    texts = []

    for file_path in list_markdown_files():
        file_name = os.path.basename(file_path)
        document = os.path.relpath(file_path, KNOWLEDGE_FOLDER)
        with open(file_path, "r", encoding="utf-8") as file:
            title = file.readline().replace("#", "").strip()

        for part in read_markdown_sections(file_path):
            section_text = part["section"] + "\n" + part["text"]
            sections.append({
                "section_id": make_section_id(file_name, part["section"]),
                "document": document,
                "section": part["section"],
                "topic": title,
                "page": part["page"],
                "embedding": [],
            })
            texts.append(section_text)

    if not texts:
        raise ValueError("No Markdown sections found. Run scripts/pdf_to_markdown.py first.")

    client = create_gemini_client()
    for start in range(0, len(texts), BATCH_SIZE):
        # Gemini's free tier allows 100 embedding inputs per minute.
        if start == 100:
            print("Waiting one minute for the Gemini embedding limit to reset...")
            time.sleep(61)

        vectors = embed_sections(texts[start:start + BATCH_SIZE], client)
        for index, vector in enumerate(vectors):
            sections[start + index]["embedding"] = vector

    write_index(sections)
    print("Indexed " + str(len(sections)) + " ordinance sections.")


if __name__ == "__main__":
    main()
