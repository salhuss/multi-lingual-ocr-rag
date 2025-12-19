"""Embedding generation using OpenAI."""
from openai import OpenAI
from app.config import settings
from typing import List

client = OpenAI(api_key=settings.openai_api_key)


def get_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI."""
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=text
    )
    return response.data[0].embedding


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts."""
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=texts
    )
    return [item.embedding for item in response.data]
