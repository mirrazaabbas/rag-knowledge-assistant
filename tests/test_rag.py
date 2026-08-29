from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import api
import app
import providers


class FakeProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append([1.0, 0.0] if "agent" in lowered or "ground" in lowered else [0.0, 1.0])
        return vectors

    def chat(self, system: str, user: str) -> str:
        if not system or not user:
            raise AssertionError("Expected non-empty grounded prompt")
        return "Grounded answer based on the retrieved passage [1]."


class RetrievalCoreTests(unittest.TestCase):
    def test_tokenization_and_chunking(self) -> None:
        self.assertEqual(app.tokens("AI agents, RAG!"), ["agents", "rag"])
        chunks = app.chunk_text(
            "one two three four five",
            size=3,
            overlap=1,
        )
        self.assertEqual(chunks, ["one two three", "three four five", "five"])

    def test_invalid_chunk_settings(self) -> None:
        with self.assertRaises(ValueError):
            app.chunk_text("text", size=0)
        with self.assertRaises(ValueError):
            app.chunk_text("text", size=3, overlap=3)

    def test_corpus_loading_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "rag.md").write_text(
                "RAG retrieves trusted context for grounded answers.",
                encoding="utf-8",
            )
            (folder / "python.txt").write_text(
                "Python is a programming language.",
                encoding="utf-8",
            )
            corpus = app.load_corpus(folder)
            self.assertEqual(len(corpus), 2)
            results = app.search(corpus, "trusted grounded context", 1)
            self.assertEqual(Path(results[0][1].source).name, "rag.md")
            self.assertGreater(results[0][0], 0)

    def test_missing_or_invalid_document_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            with self.assertRaises(FileNotFoundError):
                app.load_corpus(missing)
            file_path = Path(tmp) / "file.txt"
            file_path.write_text("hello", encoding="utf-8")
            with self.assertRaises(NotADirectoryError):
                app.load_corpus(file_path)

    def test_search_validation(self) -> None:
        chunk = app.Chunk(
            "a.md",
            "trusted context",
            app.Counter(app.tokens("trusted context")),
        )
        self.assertEqual(app.search([], "query"), [])
        with self.assertRaises(ValueError):
            app.search([chunk], "query", 0)
        with self.assertRaises(ValueError):
            app.search([chunk], "!!", 1)

    def test_vector_and_cosine_edge_cases(self) -> None:
        self.assertEqual(app.idf([]), {})
        self.assertEqual(app.vector(app.Counter(), {}), {})
        self.assertEqual(app.cosine({}, {}), 0.0)


class ProviderTests(unittest.TestCase):
    def test_dense_cosine_and_semantic_rank(self) -> None:
        self.assertEqual(providers.dense_cosine([1.0, 0.0], [1.0, 0.0]), 1.0)
        ranked = providers.semantic_rank(
            ["grounded agent answer", "unrelated python syntax"],
            "agent question",
            FakeProvider(),
            1,
        )
        self.assertEqual(ranked[0][1], 0)
        with self.assertRaises(ValueError):
            providers.dense_cosine([1.0], [1.0, 0.0])

    def test_grounded_answer(self) -> None:
        answer = providers.grounded_answer(
            "How do agents stay grounded?",
            ["Agents use retrieved sources."],
            FakeProvider(),
        )
        self.assertIn("[1]", answer)
        with self.assertRaises(ValueError):
            providers.grounded_answer("question", [], FakeProvider())

    def test_provider_config_requires_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                providers.ProviderConfig.from_env()


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(api.app)

    def setUp(self) -> None:
        self.original_factory = api.provider_client_factory
        api.provider_client_factory = FakeProvider

    def tearDown(self) -> None:
        api.provider_client_factory = self.original_factory

    def test_home(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("RAG Knowledge Assistant", response.text)

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_search_endpoint(self) -> None:
        response = self.client.post(
            "/search",
            json={
                "query": "How can AI agents reduce unsupported claims?",
                "top_k": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(payload["indexed_chunks"], 1)
        self.assertEqual(len(payload["passages"]), 1)

    def test_semantic_search_endpoint(self) -> None:
        response = self.client.post(
            "/semantic-search",
            json={"query": "How do agents stay grounded?", "top_k": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["passages"]), 1)

    def test_answer_endpoint(self) -> None:
        response = self.client.post(
            "/answer",
            json={"query": "How do agents stay grounded?", "top_k": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("[1]", response.json()["answer"])

    def test_provider_unavailable_returns_503(self) -> None:
        api.provider_client_factory = lambda: (_ for _ in ()).throw(RuntimeError("no provider"))
        response = self.client.post(
            "/semantic-search",
            json={"query": "How do agents stay grounded?", "top_k": 1},
        )
        self.assertEqual(response.status_code, 503)

    def test_request_validation(self) -> None:
        response = self.client.post("/search", json={"query": "x", "top_k": 0})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
