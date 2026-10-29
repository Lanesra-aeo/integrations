# Security

## Reporting a vulnerability

If you find a security problem in Lanesra, its MCP endpoint or the code in this repository, please tell us privately rather than in a public issue. Email **hello@lanesra.ai** with "Security" in the subject, and include what you found and how to reproduce it. We will reply to confirm we received it.

Please don't access other customers' data, run tests that degrade the service, or share the problem publicly before it is fixed.

## If a key leaked

An API key that reached a public place, such as a commit, a log or a chat, should be treated as known to others. In the Lanesra app, open **Integrations → API keys**, create a new key, move your job to it, then revoke the old one. Removing the key from a commit afterwards does not make it secret again.

This repository never needs a real key. Every example reads it from the `LANESRA_API_KEY` environment variable, and `.env` is ignored by git.
