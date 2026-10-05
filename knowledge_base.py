"""Simple entry point for retrieving knowledge passages."""

from services.knowledge_search import search_knowledge


def retrieve(question, k=3):
    """Return up to k passages that match a question."""
    passages, client = search_knowledge(question, k)
    return passages
