"""Use Gemini embeddings to find matching ordinance passages."""

import json
import math
import os

from google import genai
from google.genai import types

from services.knowledge_loader import load_knowledge
from services.settings import EMBEDDING_MODEL, INDEX_FILE


def search_knowledge(question):
    """Return the three closest ordinance passages and the Gemini client."""
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("Add GEMINI_API_KEY to the project's .env file.")

    client = genai.Client(
        http_options=types.HttpOptions(timeout=20_000)
    )
    passages = read_index()

    # Make the saved vectors once, then reuse them for later questions.
    if not passages:
        passages = add_embeddings(load_knowledge(), client)
        with open(INDEX_FILE, "w", encoding="utf-8") as file:
            json.dump({"items": passages}, file)

    question_response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY", output_dimensionality=768
        ),
    )
    question_vector = question_response.embeddings[0].values

    scored_passages = []
    for passage in passages:
        score = cosine_similarity(question_vector, passage["embedding"])
        scored_passages.append((score, passage))
    scored_passages.sort(key=lambda item: item[0], reverse=True)

    # Show up to three different section citations, without repeating one.
    matches = []
    seen_citations = []
    for score, passage in scored_passages:
        citation = (passage["document"], passage["section"], passage["page"])
        if citation in seen_citations:
            continue
        seen_citations.append(citation)
        matches.append({
            "text": passage["text"],
            "document": passage["document"],
            "section": passage["section"],
            "page": passage["page"],
            "source_file": passage.get("source_file", ""),
        })
        if len(matches) == 3:
            break

    return matches, client


def read_index():
    """Read saved passage vectors, or return an empty list if there are none."""
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as file:
            saved_index = json.load(file)
        return saved_index.get("items", [])
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def add_embeddings(passages, client):
    """Get and save one vector for each ordinance passage."""
    for start in range(0, len(passages), 50):
        batch = passages[start:start + 50]
        texts = [passage["text"] for passage in batch]
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768
            ),
        )

        for number, passage in enumerate(batch):
            passage["embedding"] = list(response.embeddings[number].values)
    return passages


def cosine_similarity(first, second):
    """Return a score that measures how close two vectors are."""
    dot_product = sum(first[index] * second[index] for index in range(len(first)))
    first_size = math.sqrt(sum(value * value for value in first))
    second_size = math.sqrt(sum(value * value for value in second))
    if first_size == 0 or second_size == 0:
        return 0
    return dot_product / (first_size * second_size)
