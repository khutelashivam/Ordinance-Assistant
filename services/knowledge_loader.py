"""Load the ordinance Markdown files and split long text into passages."""

import hashlib
import os
import re

from services.okf_reader import read_okf_file
from services.settings import KNOWLEDGE_FOLDER


def load_knowledge():
    """Return passages and a hash that changes when a knowledge file changes."""
    passages = []
    knowledge_hash = hashlib.sha256()

    for folder, subfolders, file_names in os.walk(KNOWLEDGE_FOLDER):
        subfolders.sort()
        file_names.sort()

        for file_name in file_names:
            if not file_name.endswith(".md"):
                continue

            file_path = os.path.join(folder, file_name)
            file_data = read_okf_file(file_path)
            relative_path = os.path.relpath(file_path, KNOWLEDGE_FOLDER).replace(os.sep, "/")
            knowledge_hash.update(relative_path.encode("utf-8"))
            knowledge_hash.update(file_data["raw_text"].encode("utf-8"))
            metadata = file_data["metadata"]
            title = metadata.get("title", file_name[:-3].replace("-", " ").title())
            section = str(metadata.get("section", "Not specified"))
            page = str(metadata.get("source_pages", metadata.get("page", "Not specified")))
            related_sections = metadata.get("related_sections", [])
            if isinstance(related_sections, str):
                related_sections = related_sections.replace(";", ",").split(",")
            if not isinstance(related_sections, list):
                related_sections = []

            # A numbered heading (for example 8.2) is a more exact citation.
            headings = re.split(r"(?m)^#{1,6}\s+", file_data["content"])
            heading_titles = re.findall(r"(?m)^#{1,6}\s+(.+)$", file_data["content"])

            for number, text in enumerate(headings):
                text = text.strip()
                if not text:
                    continue

                heading = heading_titles[number - 1] if number > 0 else str(title)
                section_match = re.search(r"\b\d+(?:\.\d+)+\b", heading)
                passage_section = section_match.group(0) if section_match else section

                words = text.split()
                start = 0
                while start < len(words):
                    passage_text = " ".join(words[start:start + 180])
                    if len(passage_text) >= 20:
                        passages.append({
                            "text": str(title) + "\n" + heading + "\n" + passage_text,
                            "title": str(title),
                            "document": str(metadata.get("document", "IIIT Bhagalpur B.Tech Ordinances")),
                            "section": passage_section,
                            "page": page.replace("–", "-").replace("—", "-"),
                            "source_file": str(metadata.get("source_file", "")),
                            "related_sections": [str(value).strip() for value in related_sections],
                        })
                    if start + 180 >= len(words):
                        break
                    start += 150

    if not passages:
        raise RuntimeError("No Markdown knowledge files were found.")
    return passages, knowledge_hash.hexdigest()
