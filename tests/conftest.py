"""Shared fixtures and mocks for the test suite."""

import pytest
from typing import Dict, Any, List
from benchmark_arabic_llms.services.llm_client import LLMClient


class MockLLMClient(LLMClient):
    """Mock LLM client for deterministic testing without external API calls."""

    def __init__(self, model: str = "mock-arabic-model"):
        self.model = model

    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        prompt_lower = prompt.lower()
        # QA response
        if "أين ولد" in prompt:
            return "واشنطن العاصمة"
        # Sarcasm response
        if "ساخر" in prompt or "سخرية" in prompt or "sarcasm" in prompt_lower:
            return "ساخر"
        # Summarization response
        return "ملخص موجز للنص المعروض."

    def test_connection(self) -> bool:
        return True


@pytest.fixture
def mock_llm_client():
    return MockLLMClient()


@pytest.fixture
def sample_qa_data() -> List[Dict[str, Any]]:
    return [
        {
            "text": "ولد جوني ويلش في واشنطن العاصمة في الثاني من ديسمبر عام 1906.",
            "question": "أين ولد جوني ويلش؟",
            "answer": "واشنطن العاصمة",
        },
        {
            "text": "تعتبر القاهرة عاصمة جمهورية مصر العربية وأكبر مدنها.",
            "question": "ما هي عاصمة مصر؟",
            "answer": "القاهرة",
        },
    ]


@pytest.fixture
def sample_summarization_data() -> List[Dict[str, Any]]:
    return [
        {
            "text": "شهدت تكنولوجيا الذكاء الاصطناعي تطورا ملحوظا خلال السنوات الأخيرة، حيث ساهمت في تحسين جودة الخدمات الرقمية وتسهيل الأعمال في مختلف القطاعات حول العالم.",
            "summary": "تطور الذكاء الاصطناعي وساهم في تحسين الخدمات الرقمية والأعمال عالميا.",
        }
    ]


@pytest.fixture
def sample_sarcasm_data() -> List[Dict[str, Any]]:
    return [
        {
            "text": "يا سلام على الالتزام بالمواعيد الرائع!",
            "sarcasm": "ساخر",
        },
        {
            "text": "الطقس معتدل اليوم وجميل في الإسكندرية.",
            "sarcasm": "غير ساخر",
        },
    ]
