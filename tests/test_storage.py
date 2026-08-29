import os
import unittest
from unittest.mock import patch

from storage import PgVectorStore, VectorRecord


class PgVectorStoreTests(unittest.TestCase):
    def test_requires_database_url(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "DATABASE_URL"):
                PgVectorStore()

    def test_rejects_invalid_dimensions(self):
        with self.assertRaisesRegex(ValueError, "dimensions"):
            PgVectorStore("postgresql://example", dimensions=0)

    def test_empty_upsert_does_not_connect(self):
        store = PgVectorStore("postgresql://example", dimensions=3)
        with patch.object(store, "_connect") as connect:
            self.assertEqual(store.upsert([]), 0)
            connect.assert_not_called()

    def test_upsert_validates_embedding_dimensions_before_connect(self):
        store = PgVectorStore("postgresql://example", dimensions=3)
        record = VectorRecord("doc.txt", 0, "hello", [0.1, 0.2])
        with patch.object(store, "_connect") as connect:
            with self.assertRaisesRegex(ValueError, "embedding length"):
                store.upsert([record])
            connect.assert_not_called()

    def test_search_validates_top_k_before_connect(self):
        store = PgVectorStore("postgresql://example", dimensions=3)
        with patch.object(store, "_connect") as connect:
            with self.assertRaisesRegex(ValueError, "top_k"):
                store.search([0.1, 0.2, 0.3], top_k=0)
            connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
