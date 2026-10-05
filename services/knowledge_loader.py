"""Read the ordinance notes and make short passages for searching."""

import os

from services.okf_reader import read_okf_file
from services.settings import KNOWLEDGE_FOLDER


def load_knowledge():
    """Read each Markdown file and return passages with their citation details."""
    passages = []

    for folder, subfolders, file_names in os.walk(KNOWLEDGE_FOLDER):
        subfolders.sort()
        file_names.sort()

        for file_name in file_names:
            if not file_name.endswith(".md"):
                continue

            file_path = os.path.join(folder, file_name)
            file_data = read_okf_file(file_path)
            metadata = file_data["metadata"]
            title = str(metadata.get("title", file_name[:-3].replace("-", " ").title()))
            document = str(metadata.get("document", "IIIT Bhagalpur B.Tech Ordinances"))
            section = str(metadata.get("section", "Not specified"))
            page = str(metadata.get("source_pages", metadata.get("page", "Not specified")))
            source_file = str(metadata.get("source_file", ""))

            # Read one line at a time. Text belongs to the heading above it.
            content = file_data["content"]
            sections = []
            current_heading = title
            current_text = []

            for line in content.splitlines():
                if line.startswith("#"):
                    if current_text:
                        sections.append((current_heading, "\n".join(current_text).strip()))
                    current_heading = line.lstrip("#").strip()
                    current_text = []
                else:
                    current_text.append(line)

            if current_text:
                sections.append((current_heading, "\n".join(current_text).strip()))

            for heading, text in sections:
                if not text:
                    continue

                first_word = heading.split(" ", 1)[0]
                parts = first_word.split(".")
                is_section_number = len(parts) > 1 and all(part.isdigit() for part in parts)
                passage_section = first_word if is_section_number else section
                words = text.split()
                start = 0

                while start < len(words):
                    passage_text = " ".join(words[start:start + 180])
                    if len(passage_text) >= 20:
                        passages.append({
                            "text": title + "\n" + heading + "\n" + passage_text,
                            "title": title,
                            "document": document,
                            "section": passage_section,
                            "page": page.replace("–", "-").replace("—", "-"),
                            "source_file": source_file,
                        })

                    if start + 180 >= len(words):
                        break
                    start += 150

    if not passages:
        raise RuntimeError("No Markdown knowledge files were found.")
    return passages
