from __future__ import annotations

from types import SimpleNamespace

from sqlharness.providers.openai import OpenAISQLGenerator


class FakeResponses:
    def __init__(self):
        self.request = None

    def create(self, **request):
        self.request = request
        return SimpleNamespace(
            status="completed",
            output_text='{"sql":"SELECT COUNT(*) FROM customers"}',
            usage=SimpleNamespace(
                input_tokens=100,
                output_tokens=30,
                input_tokens_details=SimpleNamespace(cached_tokens=40),
                output_tokens_details=SimpleNamespace(reasoning_tokens=20),
            ),
        )


def test_openai_adapter_requests_structured_output_and_captures_usage():
    responses = FakeResponses()
    client = SimpleNamespace(responses=responses)
    generator = OpenAISQLGenerator(
        model="pinned-test-model",
        reasoning_effort="low",
        client=client,
    )

    generation = generator.generate(
        question="How many customers are there?",
        evidence="",
        schema="customers(id, name)",
    )

    assert generation.sql == "SELECT COUNT(*) FROM customers"
    assert generation.usage.input_tokens == 100
    assert generation.usage.cached_input_tokens == 40
    assert generation.usage.reasoning_tokens == 20
    assert responses.request["store"] is False
    assert responses.request["text"]["format"]["type"] == "json_schema"
    assert responses.request["reasoning"] == {"effort": "low"}
