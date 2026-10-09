"""Read ordinance sections and entries from Markdown files."""

import os

import yaml

from services.settings import (
    EMBEDDING_DIMENSIONS,
    KNOWLEDGE_FOLDER,
    KNOWLEDGE_INDEX_PATH,
    KNOWLEDGE_SOURCE_FOLDER,
)


def list_markdown_files():
    """List the PDF-derived source files."""
    return [
        os.path.join(KNOWLEDGE_SOURCE_FOLDER, name)
        for name in sorted(os.listdir(KNOWLEDGE_SOURCE_FOLDER))
        if name.endswith(".md")
    ]


def read_markdown_sections(file_path):
    """Return each ## heading, its text, and its source page."""
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.read().splitlines()

    sections = []
    current_section = None

    for line in lines:
        if line.startswith("## "):
            if current_section:
                current_section["text"] = "\n".join(current_section["lines"]).strip()
                sections.append(current_section)

            current_section = {
                "section": line[3:].strip(),
                "page": "Not specified",
                "lines": [],
            }
        elif current_section and line.startswith("<!-- source-pages:"):
            current_section["page"] = line.split(":", 1)[1].replace("-->", "").strip()
        elif current_section:
            current_section["lines"].append(line)

    if current_section:
        current_section["text"] = "\n".join(current_section["lines"]).strip()
        sections.append(current_section)

    return sections


def read_index_entries():
    """Read section metadata and embeddings from the YAML block in index.md."""
    with open(KNOWLEDGE_INDEX_PATH, "r", encoding="utf-8") as file:
        index_text = file.read()

    yaml_text = index_text.split("```yaml", 1)[1].split("```", 1)[0]
    index_data = yaml.safe_load(yaml_text)
    return index_data["sections"]


def load_knowledge_sections():
    """Load the index and make sure it covers every Markdown section."""
    entries = read_index_entries()
    section_count = sum(len(read_markdown_sections(path)) for path in list_markdown_files())

    if len(entries) != section_count:
        raise ValueError("Run python scripts/build_index.py to update the index.")

    for entry in entries:
        if len(entry["embedding"]) != EMBEDDING_DIMENSIONS:
            raise ValueError("An index entry has an invalid embedding.")
        if not os.path.isfile(os.path.join(KNOWLEDGE_FOLDER, entry["document"])):
            raise FileNotFoundError("A Markdown source file listed in index.md is missing.")

    return entries


def get_section_content(document, section_name):
    """Find and return the real text for one indexed section."""
    file_path = os.path.join(KNOWLEDGE_FOLDER, document)
    for section in read_markdown_sections(file_path):
        if section["section"] == section_name:
            return section["text"]

    raise ValueError("Section " + section_name + " was not found in " + document)
