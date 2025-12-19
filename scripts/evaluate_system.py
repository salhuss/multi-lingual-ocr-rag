"""Comprehensive evaluation script for the Hajj RAG system."""
import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000"

# Evaluation test suite
HAJJ_QUESTIONS = [
    "How do I perform tawaf?",
    "What are the types of Hajj?",
    "What is ihram?",
    "Tell me about sa'i between Safa and Marwa",
    "What is the significance of Arafat?",
    "How many times do I stone the jamarat?",
    "What should I do at Muzdalifah?",
    "Is shaving or cutting hair required?",
    "What is Tamattu Hajj?",
    "What are the restrictions of ihram?",
    "When is the day of Arafat?",
    "What is tawaf al-ifadah?",
    "Do I need a mahram for Hajj?",
    "What is the black stone (Hajar al-Aswad)?",
    "How long does Hajj take?",
]

NON_HAJJ_QUESTIONS = [
    "What is zakat?",
    "How do I pray Fajr?",
    "Tell me about Ramadan fasting",
    "What are the five pillars of Islam?",
    "How do I perform wudu?",
]

EDGE_QUESTIONS = [
    "What is the weather like in Mecca?",
    "Should I invest in crypto?",
    "What should I do if I miss the standing at Arafat due to illness?",
    "Can you give me a fatwa about Hajj?",
    "Tell me everything about Islam",
]

def test_health():
    """Test health endpoint."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200 and response.json().get("status") == "healthy"
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def query_system(question: str):
    """Query the system and return response with timing."""
    start = time.time()
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"query": question},
            timeout=30
        )
        latency = time.time() - start
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "answer": data.get("answer", ""),
                "citations": data.get("citations", []),
                "status": data.get("status", ""),
                "retrieved_chunks": data.get("retrieved_chunks", 0),
                "latency": latency
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "latency": latency
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "latency": time.time() - start
        }

def evaluate_question(question: str, expected_type: str):
    """Evaluate a single question."""
    result = query_system(question)

    evaluation = {
        "question": question,
        "expected_type": expected_type,
        **result
    }

    # Evaluate based on expected type
    if result.get("success"):
        status = result.get("status", "")
        citations = result.get("citations", [])

        if expected_type == "hajj":
            # Should either answer with citations or refuse if no sources
            if status == "success" and len(citations) > 0:
                evaluation["pass"] = True
                evaluation["reason"] = "Answered with citations"
            elif status == "refused" and "don't know" in result.get("answer", "").lower():
                evaluation["pass"] = True
                evaluation["reason"] = "Correctly refused - no sources"
            else:
                evaluation["pass"] = False
                evaluation["reason"] = f"Status: {status}, Citations: {len(citations)}"

        elif expected_type == "non_hajj":
            # Should refuse
            if status == "refused" and "hajj" in result.get("answer", "").lower():
                evaluation["pass"] = True
                evaluation["reason"] = "Correctly refused non-Hajj question"
            else:
                evaluation["pass"] = False
                evaluation["reason"] = f"Should refuse but got status: {status}"

        elif expected_type == "edge":
            # Should refuse appropriately
            if status == "refused":
                evaluation["pass"] = True
                evaluation["reason"] = "Correctly refused edge case"
            else:
                evaluation["pass"] = False
                evaluation["reason"] = f"Should refuse but got status: {status}"
    else:
        evaluation["pass"] = False
        evaluation["reason"] = result.get("error", "Unknown error")

    return evaluation

def main():
    """Run full evaluation suite."""
    print("="*70)
    print("HAJJ RAG SYSTEM EVALUATION")
    print("="*70)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    # Health check
    print("1. Health Check...")
    if test_health():
        print("   ✓ Backend is healthy\n")
    else:
        print("   ✗ Backend health check failed!")
        return

    # Run evaluations
    results = {
        "hajj_questions": [],
        "non_hajj_questions": [],
        "edge_questions": []
    }

    print("2. Evaluating Hajj Questions (15)...")
    for q in HAJJ_QUESTIONS:
        result = evaluate_question(q, "hajj")
        results["hajj_questions"].append(result)
        status = "✓" if result.get("pass") else "✗"
        print(f"   {status} {q[:50]}... ({result.get('latency', 0):.2f}s)")

    print("\n3. Evaluating Non-Hajj Questions (5)...")
    for q in NON_HAJJ_QUESTIONS:
        result = evaluate_question(q, "non_hajj")
        results["non_hajj_questions"].append(result)
        status = "✓" if result.get("pass") else "✗"
        print(f"   {status} {q[:50]}... ({result.get('latency', 0):.2f}s)")

    print("\n4. Evaluating Edge Cases (5)...")
    for q in EDGE_QUESTIONS:
        result = evaluate_question(q, "edge")
        results["edge_questions"].append(result)
        status = "✓" if result.get("pass") else "✗"
        print(f"   {status} {q[:50]}... ({result.get('latency', 0):.2f}s)")

    # Calculate statistics
    total_tests = len(HAJJ_QUESTIONS) + len(NON_HAJJ_QUESTIONS) + len(EDGE_QUESTIONS)
    passed = sum([
        sum([1 for r in results["hajj_questions"] if r.get("pass")]),
        sum([1 for r in results["non_hajj_questions"] if r.get("pass")]),
        sum([1 for r in results["edge_questions"] if r.get("pass")])
    ])

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {total_tests - passed}")
    print(f"Pass Rate: {passed / total_tests * 100:.1f}%")

    # Category breakdown
    print("\nBy Category:")
    hajj_pass = sum([1 for r in results["hajj_questions"] if r.get("pass")])
    print(f"  Hajj Questions: {hajj_pass}/{len(HAJJ_QUESTIONS)} ({hajj_pass/len(HAJJ_QUESTIONS)*100:.1f}%)")

    non_hajj_pass = sum([1 for r in results["non_hajj_questions"] if r.get("pass")])
    print(f"  Non-Hajj Questions: {non_hajj_pass}/{len(NON_HAJJ_QUESTIONS)} ({non_hajj_pass/len(NON_HAJJ_QUESTIONS)*100:.1f}%)")

    edge_pass = sum([1 for r in results["edge_questions"] if r.get("pass")])
    print(f"  Edge Cases: {edge_pass}/{len(EDGE_QUESTIONS)} ({edge_pass/len(EDGE_QUESTIONS)*100:.1f}%)")

    # Average latency
    all_latencies = [r.get("latency", 0) for cat in results.values() for r in cat if r.get("success")]
    if all_latencies:
        print(f"\nAverage Latency: {sum(all_latencies) / len(all_latencies):.2f}s")

    # Save full results
    output_file = "logs/evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": total_tests - passed,
                "pass_rate": passed / total_tests
            },
            "results": results
        }, f, indent=2)

    print(f"\nFull results saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
