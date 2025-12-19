"""Test chat endpoint with lowered threshold."""
import requests
import json

def test_query(query: str, use_translation: bool = True):
    """Test a single query."""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print(f"Use Arabic translation: {use_translation}")
    print('='*70)

    response = requests.post(
        "http://localhost:8000/chat",
        json={"query": query, "use_arabic_translation": use_translation}
    )

    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Retrieved chunks: {result.get('retrieved_chunks', 0)}")
    print(f"\nAnswer:\n{result['answer']}")

    if result.get('citations'):
        print(f"\nCitations ({len(result['citations'])}):")
        for i, citation in enumerate(result['citations'], 1):
            print(f"  {i}. {citation['book']} - Page {citation['page']}")
            print(f"     {citation['excerpt'][:100]}...")

def main():
    test_queries = [
        "How do I perform tawaf?",
        "What are the types of Hajj?",
        "When should I enter ihram?"
    ]

    for query in test_queries:
        test_query(query, use_translation=True)

if __name__ == "__main__":
    main()
