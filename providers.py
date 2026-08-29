"""Optional OpenAI-compatible embedding and chat provider for production RAG paths."""
from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class ProviderClient(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    def chat(self, system: str, user: str) -> str: ...


@dataclass(frozen=True)
class ProviderConfig:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4.1-mini"
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        timeout_raw = os.getenv("PROVIDER_TIMEOUT_SECONDS", "30")
        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise RuntimeError("PROVIDER_TIMEOUT_SECONDS must be numeric.") from exc
        if timeout <= 0:
            raise RuntimeError("PROVIDER_TIMEOUT_SECONDS must be greater than zero.")
        return cls(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            chat_model=os.getenv("CHAT_MODEL", "gpt-4.1-mini"),
            timeout_seconds=timeout,
        )


class OpenAICompatibleClient:
    def __init__(self, config: ProviderConfig):
        self.config = config

    def _post(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        request = urllib.request.Request(
            f"{self.config.base_url}/{path.lstrip('/')}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"Provider HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Provider connection failed: {exc.reason}") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Provider returned invalid JSON.") from exc
        if not isinstance(data, dict):
            raise RuntimeError("Provider returned an unexpected response shape.")
        return data

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Embedding input must contain non-empty strings.")
        data = self._post(
            "embeddings",
            {"model": self.config.embedding_model, "input": texts},
        )
        items = data.get("data")
        if not isinstance(items, list) or len(items) != len(texts):
            raise RuntimeError("Provider returned an invalid embedding response.")
        vectors: list[list[float]] = []
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise RuntimeError("Provider embedding item is malformed.")
            vectors.append([float(value) for value in item["embedding"]])
        return vectors

    def chat(self, system: str, user: str) -> str:
        if not system.strip() or not user.strip():
            raise ValueError("System and user messages must be non-empty.")
        data = self._post(
            "chat/completions",
            {
                "model": self.config.chat_model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Provider returned no chat choices.")
        first = choices[0]
        if not isinstance(first, dict):
            raise RuntimeError("Provider chat choice is malformed.")
        message = first.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise RuntimeError("Provider returned an invalid chat message.")
        content = message["content"].strip()
        if not content:
            raise RuntimeError("Provider returned an empty chat message.")
        return content


def create_provider_client() -> OpenAICompatibleClient:
    return OpenAICompatibleClient(ProviderConfig.from_env())


def dense_cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("Embedding vectors must be non-empty and have equal dimensions.")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def semantic_rank(
    texts: list[str], query: str, client: ProviderClient, k: int = 3
) -> list[tuple[float, int]]:
    if k <= 0:
        raise ValueError("top-k must be greater than zero.")
    if not query.strip():
        raise ValueError("Query cannot be empty.")
    if not texts:
        return []
    vectors = client.embed_texts([query, *texts])
    if len(vectors) != len(texts) + 1:
        raise RuntimeError("Embedding provider returned an unexpected vector count.")
    query_vector = vectors[0]
    ranked = [
        (dense_cosine(query_vector, vector), index)
        for index, vector in enumerate(vectors[1:])
    ]
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[: min(k, len(ranked))]


def grounded_answer(query: str, passages: list[str], client: ProviderClient) -> str:
    if not passages:
        raise ValueError("At least one passage is required for answer generation.")
    context = "\n\n".join(f"[{index}] {text}" for index, text in enumerate(passages, 1))
    system = (
        "You are a source-grounded assistant. Answer only from the provided passages. "
        "Cite supporting passages with bracketed numbers such as [1]. If the passages do not "
        "support an answer, say that the available sources are insufficient."
    )
    user = f"Question: {query}\n\nPassages:\n{context}"
    return client.chat(system, user)
