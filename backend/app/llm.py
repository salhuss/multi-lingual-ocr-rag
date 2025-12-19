"""LLM generation with strict grounding."""
from openai import OpenAI
from app.config import settings
from typing import List, Dict, Any
import json

client = OpenAI(api_key=settings.openai_api_key)


def generate_answer(query: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate answer based on retrieved chunks with strict grounding.

    Args:
        query: User question in English
        retrieved_chunks: List of relevant chunks

    Returns:
        Structured response with answer and citations
    """
    if not retrieved_chunks:
        return {
            "answer": "I don't know the answer to this question based on the provided books.",
            "citations": [],
            "status": "no_sources"
        }

    # Build context from chunks
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks):
        context_parts.append(
            f"[Source {i+1}]\n"
            f"Book: {chunk['book_title']}\n"
            f"Page: {chunk['page_number']}\n"
            f"Arabic Text: {chunk['arabic_text']}\n"
            f"Similarity: {chunk['similarity']:.2f}\n"
        )

    context = "\n---\n".join(context_parts)

    system_prompt = """You are a Hajj knowledge assistant. Answer questions ONLY based on the provided Arabic source texts about Hajj.

CRITICAL RULES:
1. Answer ONLY using information from the provided sources
2. If the sources don't contain the answer, say "I don't know based on the provided books"
3. ALWAYS include citations in your answer: [Book Name, Page X]
4. Provide answers in English, but include relevant Arabic excerpts
5. Do NOT add external knowledge, speculation, or fatwas
6. Do NOT answer questions outside of what the sources explicitly state
7. If sources conflict, present both views with citations
8. Keep answers concise (2-4 sentences) unless more detail is needed

Respond in JSON format with the following structure:
{
  "answer": "Your concise answer in English with citations [Book, Page X]",
  "citations": [
    {
      "book": "Book name",
      "page": page_number,
      "excerpt": "Relevant Arabic excerpt (1-2 sentences max)"
    }
  ]
}"""

    user_prompt = f"""Question: {query}

Sources:
{context}

Provide your answer following the output format."""

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Validate that citations exist
        if not result.get("citations") or len(result["citations"]) == 0:
            return {
                "answer": "I cannot provide an answer without proper citations from the sources.",
                "citations": [],
                "status": "no_citations"
            }

        result["status"] = "success"
        return result

    except Exception as e:
        return {
            "answer": f"Error generating response: {str(e)}",
            "citations": [],
            "status": "error"
        }


def translate_query_to_arabic(query: str) -> str:
    """
    Translate English query to Arabic for better retrieval.

    Args:
        query: English query

    Returns:
        Arabic translation
    """
    system_prompt = """You are a translator. Translate the English question about Hajj to Arabic.
Provide ONLY the Arabic translation, no explanations."""

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=100
        )

        return response.choices[0].message.content.strip()
    except Exception:
        return query  # Fallback to original query
