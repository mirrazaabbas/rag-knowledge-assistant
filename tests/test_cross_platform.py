from __future__ import annotations

import unittest
from unittest.mock import patch

import ai_features
import ai_platform


class FakeClient:
    def generate(self, system: str, user: str) -> str:
        self.system = system
        self.user = user
        return "Grounded answer [1]."


class CrossPlatformTests(unittest.TestCase):
    def test_rag_answer_feature(self) -> None:
        client = FakeClient()
        result = ai_features.answer_with_ai("How do agents stay grounded?", client, top_k=1)
        self.assertIn("[1]", result["answer"])
        self.assertEqual(len(result["sources"]), 1)
        self.assertIn("Retrieved passages", client.user)

    def test_provider_response_shapes(self) -> None:
        cases = [
            ("openai", {"choices": [{"message": {"content": "openai ok"}}]}, "openai ok"),
            ("anthropic", {"content": [{"text": "claude ok"}]}, "claude ok"),
            (
                "gemini",
                {"candidates": [{"content": {"parts": [{"text": "gemini ok"}]}}]},
                "gemini ok",
            ),
        ]
        for provider, payload, expected in cases:
            config = ai_platform.AIConfig(provider, "key", "model", "https://example.test")
            client = ai_platform.HTTPAIClient(config)
            with patch.object(client, "_post", return_value=payload):
                self.assertEqual(client.generate("system", "user"), expected)

    def test_invalid_provider_config(self) -> None:
        with patch.dict("os.environ", {"AI_PROVIDER": "unknown", "AI_API_KEY": "key"}, clear=True):
            with self.assertRaises(RuntimeError):
                ai_platform.AIConfig.from_env()


if __name__ == "__main__":
    unittest.main()
