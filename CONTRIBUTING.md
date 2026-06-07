# Contributing to MOSO AI

We welcome contributions! MOSO AI is a privacy-first, local-first AI assistant platform. By contributing, you help us keep AI personal and private for everyone.

## Getting Started

1. Read the [README](README.md) and [ROADMAP](ROADMAP.md).
2. Check open issues for "good first issue" labels.
3. Fork the repository and clone it.
4. Set up your development environment (see below).

## Development Setup

### Prerequisites

- Git
- Flutter SDK 3.16+
- Python 3.11+
- Rust 1.75+
- Docker (optional, for backend development)

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your configuration

# Install Python dependencies
pip install -r backend/requirements.txt

# Install Rust toolchain
rustup default stable
```

## Project Structure

```
moso-ai/
├── apps/             # Platform-specific apps
├── shared/           # Shared engines and utilities
├── moso-core/        # Core AI inference runtime
├── moso-memory-engine/ # Memory and retrieval system
├── backend/          # Cloud backend services
├── models/           # AI model configurations
├── docs/             # Documentation
├── scripts/          # Build and utility scripts
├── tests/            # All test suites
└── tools/            # Developer tools
```

## Pull Request Process

1. Create a feature branch from `main`.
2. Make your changes following the coding style.
3. Add or update tests as needed.
4. Run tests locally: see specific test runner in each module's README.
5. Submit a PR with a clear description of changes.

## Coding Standards

- **Dart/Flutter:** Follow [Effective Dart](https://dart.dev/effective-dart) guidelines.
- **Python:** Follow [PEP 8](https://peps.python.org/pep-0008/), use type hints.
- **Rust:** Follow [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/).
- **Documentation:** All public APIs must have doc comments.
- **Privacy:** Never log or expose user data. Use the encryption utilities for any data persistence.

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(memory): add episodic memory retrieval
fix(core): resolve crash on model load
docs: update architecture diagram
```

## Testing

- **Unit tests:** Required for all new code.
- **Integration tests:** Required for cross-component changes.
- **AI evaluation tests:** Required for model/pipeline changes.
- **Performance benchmarks:** Required for inference engine changes.

## Architecture Review

Significant changes affecting architecture require review from the core team. Please tag `@moso-core` on your PR.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
