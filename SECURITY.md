# Security Policy

## Reporting a vulnerability

Please do not open a public issue for sensitive vulnerabilities. Use GitHub's private vulnerability reporting feature when available.

## Security notes

This repository currently processes local Markdown and text files. Retrieved text is treated as **untrusted source data**, never as trusted system instructions. The answer-generation system prompt explicitly tells the model not to follow instructions embedded in retrieved passages, including requests to override system rules, reveal secrets, change roles, or execute tools/actions.

Deterministic tests verify that instruction-like retrieved content remains in the untrusted user/context portion of the prompt and that the trusted system message preserves the source-grounding and prompt-injection boundary.

This is a defense-in-depth control, not a claim that prompt injection is solved. A production deployment that accepts arbitrary external documents should also add content provenance, upload/type/size validation, least-privilege tool access, secret isolation, output monitoring, adversarial evaluation against the actual deployed model, request/rate limits, and incident logging appropriate to the data sensitivity.
