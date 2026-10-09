"""Find relevant ordinance sections with cosine similarity."""

import numpy as np

from services.embedding_service import create_gemini_client, embed_question
from services.markdown_service import get_section_content
from services.settings import EMBEDDING_DIMENSIONS


TOP_RESULTS = 3
MIN_SIMILARITY = 0.20


def search_knowledge(question, knowledge_sections, client=None):
    """Return the most relevant sections and the Gemini client."""
    if not question or not question.strip():
        raise ValueError("Please enter a question about the B.Tech ordinance.")
    if not knowledge_sections:
        raise RuntimeError(
            "No valid index embeddings are loaded. "
            "Run python scripts/build_index.py, then restart the app."
        )

    client = client or create_gemini_client()
    question_vector = np.asarray(embed_question(question.strip(), client), dtype=float)
    if question_vector.ndim != 1 or question_vector.size != EMBEDDING_DIMENSIONS:
        raise ValueError("Gemini returned an invalid question embedding.")

    scored_sections = []
    for section in knowledge_sections:
        section_vector = np.asarray(section["embedding"], dtype=float)
        if section_vector.ndim != 1 or section_vector.size != EMBEDDING_DIMENSIONS:
            continue

        score = cosine_similarity(question_vector, section_vector)
        scored_sections.append((score, section))

    scored_sections.sort(key=lambda item: item[0], reverse=True)
    if not scored_sections or scored_sections[0][0] < MIN_SIMILARITY:
        return [], client

    results = []
    for score, section in scored_sections[:TOP_RESULTS]:
        if score < MIN_SIMILARITY:
            continue
        section_text = get_section_content(section["document"], section["section"])
        results.append({
            "section_id": section["section_id"],
            "document": section["document"],
            "section": section["section"],
            "section_name": section["section"],
            "page": str(section.get("page", "Not specified")),
            "similarity_score": score,
            "text": section_text,
        })

    return results, client


def cosine_similarity(first, second):
    """Calculate cosine similarity with NumPy, including zero-vector handling."""
    first_size = np.linalg.norm(first)
    second_size = np.linalg.norm(second)
    if first_size == 0 or second_size == 0:
        return 0.0
    return float(np.dot(first, second) / (first_size * second_size))
