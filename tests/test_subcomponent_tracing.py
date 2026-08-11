from __future__ import annotations

import inspect

from app.mock_llm import FakeLLM
from app.mock_rag import retrieve


def test_rag_retrieval_is_observed_without_changing_behavior() -> None:
    assert hasattr(retrieve, "__wrapped__")
    assert retrieve.__wrapped__("Explain monitoring") == [
        "Metrics detect incidents, traces localize them, logs explain root cause."
    ]


def test_llm_generation_is_observed_without_changing_behavior() -> None:
    assert hasattr(FakeLLM.generate, "__wrapped__")
    signature = inspect.signature(FakeLLM.generate)
    assert tuple(signature.parameters) == ("self", "prompt")

    response = FakeLLM.generate.__wrapped__(FakeLLM(), "sanitized prompt")

    assert response.model == "claude-sonnet-4-5"
    assert response.usage.input_tokens >= 20
    assert response.usage.output_tokens >= 80
