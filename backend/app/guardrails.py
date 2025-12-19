"""Guardrails for topic filtering and validation."""
from openai import OpenAI
from app.config import settings
from typing import Dict, Any
import json
import re

client = OpenAI(api_key=settings.openai_api_key)

# Hajj-related keywords for quick filtering
HAJJ_KEYWORDS = [
    "hajj", "haj", "pilgrimage", "ihram", "tawaf", "sa'i", "say", "kaaba", "kabah",
    "miqat", "arafat", "arafah", "muzdalifah", "mina", "jamarat", "stoning",
    "sacrifice", "qurbani", "halq", "taqsir", "umrah", "tamattu", "qiran", "ifrad",
    "black stone", "hajar", "zamzam", "safa", "marwa", "farewell tawaf",
    "tawaf al-ifadah", "tawaf al-ziyarah", "wuquf", "standing", "days of hajj",
    "eid al-adha", "yawm al-nahr", "tashriq", "ihram restrictions", "forbidden",
    "mahram", "hajj types", "hajj rituals", "hajj steps", "hajj requirements"
]


def is_hajj_related(query: str) -> bool:
    """
    Quick check if query is Hajj-related based on keywords.

    Args:
        query: User query in English

    Returns:
        True if likely Hajj-related, False otherwise
    """
    query_lower = query.lower()

    # Check for direct keyword matches
    for keyword in HAJJ_KEYWORDS:
        if keyword in query_lower:
            return True

    # Use LLM for more nuanced check
    return llm_topic_check(query)


def llm_topic_check(query: str) -> bool:
    """
    Use LLM to determine if query is Hajj-related.

    Args:
        query: User query

    Returns:
        True if Hajj-related, False otherwise
    """
    system_prompt = """You are a topic classifier. Determine if the user's question is related to Hajj (Islamic pilgrimage to Mecca).

Hajj-related topics include:
- Hajj rituals (ihram, tawaf, sa'i, standing at Arafat, stoning, sacrifice, etc.)
- Hajj requirements and conditions
- Hajj types (Tamattu, Qiran, Ifrad)
- Umrah (lesser pilgrimage)
- Places related to Hajj (Mecca, Mina, Muzdalifah, Arafat, Kaaba, etc.)
- Ihram restrictions and rules
- Hajj timeline and days

NOT Hajj-related:
- General Islamic topics (prayer, zakat, fasting, etc.)
- Other pillars of Islam
- Islamic history unrelated to Hajj
- General religious questions

Respond with ONLY a JSON object: {"is_hajj_related": true} or {"is_hajj_related": false}"""

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=50
        )

        result = response.choices[0].message.content.strip()
        parsed = json.loads(result)
        return parsed.get("is_hajj_related", False)
    except Exception:
        # If LLM fails, default to False (reject)
        return False


def validate_citations(response_text: str, retrieved_chunks: list) -> bool:
    """
    Validate that the response contains proper citations.

    Args:
        response_text: Generated response
        retrieved_chunks: Chunks that were retrieved

    Returns:
        True if citations are valid, False otherwise
    """
    # Check if response contains citation markers
    has_citations = bool(re.search(r'\[.*?\]|\(.*?Page \d+.*?\)', response_text, re.IGNORECASE))

    if not has_citations:
        return False

    # Check if page numbers in citations match retrieved chunks
    page_numbers_in_chunks = {chunk["page_number"] for chunk in retrieved_chunks}
    cited_pages = re.findall(r'Page (\d+)', response_text, re.IGNORECASE)

    if cited_pages:
        cited_page_numbers = {int(page) for page in cited_pages}
        # All cited pages should be in retrieved chunks
        return cited_page_numbers.issubset(page_numbers_in_chunks)

    return True  # Has citation format but no specific page numbers


def create_refusal_response(reason: str = "not_hajj") -> Dict[str, Any]:
    """
    Create a refusal response.

    Args:
        reason: Reason for refusal

    Returns:
        Structured refusal response
    """
    if reason == "not_hajj":
        return {
            "answer": "I apologize, but I can only answer questions specifically about Hajj (the Islamic pilgrimage to Mecca). Your question appears to be about a different topic. Please ask me about Hajj rituals, requirements, or related topics.",
            "citations": [],
            "status": "refused",
            "reason": "Question is not related to Hajj"
        }
    elif reason == "no_sources":
        return {
            "answer": "I don't know the answer to this question based on the provided books. The sources available to me do not contain sufficient information to answer your question about Hajj.",
            "citations": [],
            "status": "refused",
            "reason": "No relevant information found in sources"
        }
    elif reason == "low_confidence":
        return {
            "answer": "I cannot provide a confident answer to this question based on the available sources. The information retrieved does not meet the confidence threshold required.",
            "citations": [],
            "status": "refused",
            "reason": "Low confidence in retrieved information"
        }
    else:
        return {
            "answer": "I apologize, but I cannot answer this question.",
            "citations": [],
            "status": "refused",
            "reason": "Unknown reason"
        }
