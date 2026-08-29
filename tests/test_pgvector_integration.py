from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

import api
from storage import PgVectorStore, VectorRecord


class FakeProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            vectors.append([1.0, 0.0] if "agent" in lowered or "ground" in lowered else [0.0, 1.0])
        return vectors

    def chat(self, system: str, user: str) -> str:
        return "Grounded answer [1]."


@unittest.skipUnless(
    os.getenv("RUN_PGVECTOR_INTEGRATION", "").strip().lower() in {"1", "true", "yes", "on"},
    "pgvector integration test is opt-in",
)
class PgVectorIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.store = PgVectorStore()
        cls.store.ensure_schema()

    def test_store_upsert_and_cosine_search(self) -> None:
        records = [
            VectorRecord("integration-agent.md", 0, "Agents stay grounded with evidence.", [1.0, 0.0]),
            VectorRecord("integration-python.md", 0, "Python syntax and tooling.", [0.0, 1.0]),
        ]
        self.assertEqual(self.store.upsert(records), 2)
        results = self.store.search([1.0, 0.0], top_k=1)
        self.assertEqual(results[0]["source"], "integration-agent.md")
        self.assertGreater(results[0]["score"], 0.99)

    def test_semantic_search_endpoint_uses_pgvector(self) -> None:
        original_factory = api.provider_client_factory
        api.provider_client_factory = FakeProvider
        try:
            response = TestClient(api.app).post(
                "/semantic-search",
                json={"query": "How do agents stay grounded?", "top_k": 1},
            )
        finally:
            api.provider_client_factory = original_factory

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertGreaterEqual(payload["indexed_chunks"], 1)
        self.assertEqual(len(payload["passages"]), 1)
        self.assertIn("agent", payload["passages"][0]["text"].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
