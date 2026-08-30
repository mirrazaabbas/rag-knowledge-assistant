import unittest

import integration_contract


class IntegrationContractTests(unittest.TestCase):
    def test_build_and_validate_record(self):
        record = integration_contract.build_evaluation_record(
            "What is RAG?",
            "RAG grounds generation in retrieved context.",
            [
                {"rank": 1, "score": 0.91, "source": "sample_docs/ai_agents.md", "text": "RAG retrieves relevant context."},
                {"rank": 2, "score": 0.74, "source": "docs/BENCHMARKING.md", "text": "Evaluation measures retrieval quality."},
            ],
            latency_ms=12.5,
            tool_calls=[{"name": "rag.answer", "arguments": {"top_k": 2}}],
        )
        self.assertEqual(record["schema_version"], "portfolio-evidence/v1")
        self.assertEqual(record["producer"], "rag-knowledge-assistant")
        self.assertEqual(record["retrieved_ids"][0], "sample_docs/ai_agents.md")
        self.assertEqual(record["citations"], record["retrieved_ids"])
        self.assertEqual(integration_contract.validate_evaluation_record(record), [])

    def test_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            integration_contract.build_evaluation_record("", "answer", [])
        with self.assertRaises(ValueError):
            integration_contract.build_evaluation_record("query", "answer", [{"source": "x"}])
        with self.assertRaises(ValueError):
            integration_contract.build_evaluation_record("query", "answer", [], latency_ms=-1)

    def test_validator_reports_contract_errors(self):
        errors = integration_contract.validate_evaluation_record({"schema_version": "wrong"})
        self.assertTrue(errors)
        self.assertTrue(any("schema_version" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
