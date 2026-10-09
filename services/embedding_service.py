"""Generate Gemini embeddings for ordinance sections and user questions."""

import os

from google import genai
from google.genai import types

from services.settings import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    GEMINI_TIMEOUT_MILLISECONDS,
)


def create_gemini_client():
    """Create a Gemini client using the API key from the environment."""
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("Add GEMINI_API_KEY to the environment before using Gemini.")
    return genai.Client(
        http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MILLISECONDS)
    )


def embed_sections(section_texts, client):
    """Generate document embeddings for a batch of Markdown sections."""
    if not section_texts:
        return []

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=section_texts,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )

    vectors = []
    for item in response.embeddings or []:
        vector = [float(value) for value in item.values]
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                "Gemini returned an embedding with an unexpected number of values."
            )
        vectors.append(vector)

    if len(vectors) != len(section_texts):
        raise RuntimeError("Gemini did not return an embedding for every section.")
    return vectors


def embed_question(question, client):
    """Generate a query embedding using the same Gemini embedding model."""
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )

    if not response.embeddings:
        raise RuntimeError("Gemini did not return an embedding for the question.")
    vector = [float(value) for value in response.embeddings[0].values]
    if len(vector) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "Gemini returned a question embedding with an unexpected number of values."
        )
    return vector
