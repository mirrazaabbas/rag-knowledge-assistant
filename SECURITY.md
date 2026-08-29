# Security Policy

## Reporting a vulnerability

Please do not open a public issue for sensitive vulnerabilities. Use GitHub's private vulnerability reporting feature when available.

## Security notes

This repository currently processes local Markdown and text files. Future upload and LLM integrations should validate file type and size, isolate retrieved text from trusted system instructions, avoid logging secrets or sensitive document content, and test prompt-injection scenarios before deployment.
