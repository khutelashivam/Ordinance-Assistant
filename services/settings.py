"""Shared paths and Gemini model settings."""

import os
from dotenv import load_dotenv


PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_FOLDER = "knowledge"
KNOWLEDGE_SOURCE_FOLDER = os.path.join(KNOWLEDGE_FOLDER, "sections")
KNOWLEDGE_INDEX_PATH = os.path.join(KNOWLEDGE_FOLDER, "index.md")

# Load the Gemini key and model choice from the project's .env file.
load_dotenv(os.path.join(PROJECT_FOLDER, ".env"))

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768
GEMINI_TIMEOUT_MILLISECONDS = 180_000
PDF_PATH = os.path.join(PROJECT_FOLDER, "B.Tech-ordinance2026.pdf")
ANSWER_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_ANSWER_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash")
