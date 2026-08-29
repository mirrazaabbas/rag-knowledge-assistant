# AI platform compatibility

This repository keeps retrieval independent from any model vendor. The deterministic TF-IDF retrieval path works with no API key. Optional answer generation can use the shared `AIClient` interface with:

- OpenAI and OpenAI-compatible chat APIs
- Anthropic Claude Messages API
- Google Gemini GenerateContent API
- Other OpenAI-compatible providers by setting `AI_BASE_URL`

## 1. Run the offline tests first

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

These tests use fake/mocked providers and do not spend API credits.

## 2. Select a live provider

Set these environment variables in your terminal. Never commit API keys.

### OpenAI or OpenAI-compatible

```bash
export AI_PROVIDER=openai
export AI_API_KEY="YOUR_KEY"
export AI_MODEL="YOUR_CHAT_MODEL"
# Optional for another OpenAI-compatible service:
# export AI_BASE_URL="https://provider.example/v1"
```

### Anthropic Claude

```bash
export AI_PROVIDER=anthropic
export AI_API_KEY="YOUR_KEY"
export AI_MODEL="YOUR_CLAUDE_MODEL"
```

### Google Gemini

```bash
export AI_PROVIDER=gemini
export AI_API_KEY="YOUR_KEY"
export AI_MODEL="YOUR_GEMINI_MODEL"
```

## 3. Run a grounded answer

```bash
python - <<'PY'
from ai_features import answer_with_ai
from ai_platform import create_ai_client

result = answer_with_ai(
    "How can AI agents reduce unsupported claims?",
    create_ai_client(),
    top_k=2,
)
print(result["answer"])
print(result["sources"])
PY
```

This path retrieves passages locally first and sends only the grounded context to the selected chat provider. The existing semantic-search path remains available separately for embedding-capable integrations.

## Provider-neutral design

Project logic depends on the `AIClient` protocol rather than a vendor SDK. Adding another provider only requires a new adapter that implements `generate(system, user) -> str`.
