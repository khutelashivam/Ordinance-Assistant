"""Find the ordinance passages closest in meaning to a student's question."""

import json
import math
import os

from google import genai
from google.genai import types

from services.knowledge_loader import load_knowledge
from services.settings import EMBEDDING_MODEL, INDEX_FILE


def search_knowledge(question, number_of_results=3):
    """Return the three best matches and the Gemini client."""
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to the project .env file.")

    client = genai.Client()
    passages, knowledge_hash = load_knowledge()

    # Reuse saved vectors until a knowledge file changes. The first condition
    # reads the simplified index; the second also accepts the earlier format.
    saved_index = read_index()
    if saved_index and saved_index.get("knowledge_hash") == knowledge_hash:
        passages = saved_index["passages"]
    elif (
        saved_index
        and saved_index.get("corpus_hash") == knowledge_hash
        and saved_index.get("embedding_model") == EMBEDDING_MODEL
    ):
        passages = saved_index["items"]
    else:
        passages = add_embeddings(passages, client)
        with open(INDEX_FILE, "w", encoding="utf-8") as file:
            json.dump({
                "knowledge_hash": knowledge_hash,
                "embedding_model": EMBEDDING_MODEL,
                "passages": passages,
            }, file)

    question_response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY", output_dimensionality=768
        ),
    )
    question_vector = question_response.embeddings[0].values

    for passage in passages:
        passage["score"] = cosine_similarity(question_vector, passage["embedding"])
    passages.sort(key=lambda item: item["score"], reverse=True)

    # Avoid showing the same citation more than once.
    matches = []
    seen_citations = []
    for passage in passages:
        citation = (passage["document"], passage["section"], passage["page"])
        if citation in seen_citations:
            continue
        seen_citations.append(citation)
        matches.append({key: value for key, value in passage.items() if key != "embedding"})
        if len(matches) == number_of_results:
            break

    # Add up to two sections explicitly linked in the knowledge metadata.
    related_count = 0
    for match in list(matches):
        for related_section in match.get("related_sections", []):
            for passage in passages:
                if passage["section"] != related_section:
                    continue
                citation = (passage["document"], passage["section"], passage["page"])
                if citation not in seen_citations:
                    related_passage = {
                        key: value for key, value in passage.items() if key != "embedding"
                    }
                    related_passage["related"] = True
                    matches.append(related_passage)
                    seen_citations.append(citation)
                    related_count += 1
                break
            if related_count == 2:
                break
        if related_count == 2:
            break

    return matches, client


def read_index():
    """Read the saved embedding vectors, if an index already exists."""
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def add_embeddings(passages, client):
    """Ask Gemini for one vector for each ordinance passage."""
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
    """Compare two vectors; a higher result means a closer match."""
    dot = sum(first[index] * second[index] for index in range(len(first)))
    first_size = math.sqrt(sum(value * value for value in first))
    second_size = math.sqrt(sum(value * value for value in second))
    if first_size == 0 or second_size == 0:
        return 0
    return dot / (first_size * second_size)
