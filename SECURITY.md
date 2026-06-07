# Security Policy

## Privacy-First Architecture

MOSO AI is built on a **privacy-first foundation**. All AI processing is designed to run locally on-device by default. Your data belongs to you.

### Core Security Principles

1. **Local-First** — All inference, memory, and personalization runs locally unless explicitly opted into sync.
2. **Zero-Knowledge Sync** — Any synchronized data is encrypted end-to-end with keys only accessible on your devices.
3. **Secure Enclave** — Cryptographic keys are stored in hardware-backed secure storage (Secure Enclave on Apple, TEE on Android, TPM on Windows).
4. **No Telemetry by Default** — No data leaves your device without explicit consent. Telemetry is opt-in and anonymized.

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in MOSO AI, please follow responsible disclosure:

1. **Do not** file a public GitHub issue.
2. Email security@moso.ai with details of the vulnerability.
3. Include steps to reproduce and potential impact assessment.

We will respond within 72 hours and work with you to address the issue promptly.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Encryption Standards

| Data Type             | At Rest              | In Transit          |
| --------------------- | -------------------- | ------------------- |
| Conversational Memory | AES-256-GCM          | TLS 1.3             |
| User Preferences      | AES-256-GCM          | TLS 1.3             |
| Embeddings            | AES-256-GCM          | TLS 1.3             |
| Sync Payloads         | XChaCha20-Poly1305   | TLS 1.3             |
| Model Files           | Optional AES-256     | HTTPS/TLS 1.3       |

## Data Retention

- **Local data:** Retained until user deletes it or uninstalls the application.
- **Synced data (if enabled):** Retained on servers until user initiates account deletion.
- **Anonymous telemetry (if enabled):** Retained for 90 days.
