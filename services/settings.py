"""Shared paths and Gemini model names."""

import os
from dotenv import load_dotenv


PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_FOLDER = os.path.join(PROJECT_FOLDER, "knowledge")
INDEX_FILE = os.path.join(PROJECT_FOLDER, "knowledge_index.json")

# Load the Gemini key and model choice from the project's .env file.
load_dotenv(os.path.join(PROJECT_FOLDER, ".env"))

EMBEDDING_MODEL = "gemini-embedding-001"
ANSWER_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_ANSWER_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash")
