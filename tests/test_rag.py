from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import api
import app


class RetrievalCoreTests(unittest.TestCase):
    def test_tokenization_and_chunking(self) -> None:
        self.assertEqual(app.tokens("AI agents, RAG!"), ["agents", "rag"])
        self.assertEqual(app.chunk_text("one two three four five", size=3, overlap=1), ["one two three", "three four five", "five"])

    def test_invalid_chunk_settings(self) -> None:
        with self.assertRaises(ValueError):
            app.chunk_text("text", size=0)
        with self.assertRaises(ValueError):
            app.chunk_text("text", size=3, overlap=3)

    def test_corpus_loading_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "rag.md").write_text("RAG retrieves trusted context for grounded answers.", encoding="utf-8")
            (folder / "python.txt").write_text("Python is a programming language.", encoding="utf-8")
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
        chunk = app.Chunk("a.md", "trusted context", app.Counter(app.tokens("trusted context")))
        self.assertEqual(app.search([], "query"), [])
        with self.assertRaises(ValueError):
            app.search([chunk], "query", 0)
        with self.assertRaises(ValueError):
            app.search([chunk], "!!", 1)

    def test_vector_and_cosine_edge_cases(self) -> None:
        self.assertEqual(app.idf([]), {})
        self.assertEqual(app.vector(app.Counter(), {}), {})
        self.assertEqual(app.cosine({}, {}), 0.0)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(api.app)

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_search_endpoint(self) -> None:
        response = self.client.post(
            "/search",
            json={"query": "How can AI agents reduce unsupported claims?", "top_k": 1},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["query"], "How can AI agents reduce unsupported claims?")
        self.assertGreaterEqual(payload["indexed_chunks"], 1)
        self.assertEqual(len(payload["passages"]), 1)
        self.assertTrue(payload["passages"][0]["source"].startswith("sample_docs/"))

    def test_request_validation(self) -> None:
        response = self.client.post("/search", json={"query": "x", "top_k": 0})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
