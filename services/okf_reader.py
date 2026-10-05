"""Read a Markdown file and its YAML details."""

import re
import yaml


def read_okf_file(file_path):
    """Return a file's metadata and the Markdown text below it."""
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    # Knowledge files start with YAML between two --- lines.
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.S)
    if not match:
        return {"metadata": {}, "content": text}

    metadata = yaml.safe_load(match.group(1)) or {}
    if not isinstance(metadata, dict):
        metadata = {}

    return {"metadata": metadata, "content": match.group(2)}
