# Contributing to MOSO AI

## Important Legal Notice

**Viewing access does not grant usage rights.**

By contributing to MOSO AI, you agree to the terms of the
[MOSO Source Available License](LICENSE). MOSO AI is source-available, not open source.
All code is protected by this license.

## Who Can Contribute

| Role        | Can Submit PRs | Can Merge | Requires |
|-------------|----------------|-----------|----------|
| Public      | No             | No        | N/A      |
| Contributor | Yes            | No        | Approval |
| Maintainer  | Yes            | Yes       | Review   |

Community members can contribute by:
- Opening issues for bugs, feature requests, or feedback
- Participating in GitHub Discussions
- Providing research insights and use cases

**Only approved maintainers can push code or merge pull requests.**

## Contribution Workflow

```
Report Issue → Discuss → Assign → Create Branch → PR → Review → Merge
   ↑                                                              |
   └────────────────────── Community Loop ────────────────────────┘
```

1. **Start with a discussion** — Open an issue or discussion before writing code
2. **Get assigned** — A maintainer will review and assign if accepted
3. **Branch from dev** — Create a branch following the naming convention
4. **Write code** — Follow the coding standards below
5. **Submit a PR** — Target the `dev` branch with a clear description
6. **Pass all checks** — CI, lint, tests, and maintainer approval required
7. **Merge** — Only maintainers can merge after approvals

## Branch Naming Convention

```
feature/   — New features        (e.g., feature/voice-wake-word)
hotfix/    — Critical fixes      (e.g., hotfix/crash-on-startup)
bugfix/    — Bug fixes           (e.g., bugfix/memory-leak)
docs/      — Documentation       (e.g., docs/api-ref-update)
refactor/  — Code refactoring    (e.g., refactor/inference-engine)
```

## Pull Request Requirements

- PRs must target the `dev` branch (never `main` directly)
- At least **2 maintainer approvals** required for merge
- All **status checks must pass** before merge
- **Signed commits** (GPG or SSH) required
- PR description must include:
  - What the change does
  - Why it's needed
  - Testing performed
  - Privacy/security impact assessment

## Coding Standards

### General
- Follow the existing code style in the repository
- Write clear, self-documenting code (avoid unnecessary comments)
- Include type annotations where applicable
- Keep functions small and focused

### Python
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for all function signatures
- Use `black` for formatting, `isort` for import ordering

### Rust
- Follow [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Run `cargo clippy` and `cargo fmt` before submitting
- No `unsafe` code without explicit review

### Flutter / Dart
- Follow [Effective Dart](https://dart.dev/effective-dart)
- Use `dart format` before committing

## Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `security`

Examples:
```
feat(memory): add episodic memory consolidation
fix(core): resolve crash on GGUF model load
security(auth): patch prompt injection vector
```

## Review Process

1. Maintainer reviews the PR within 72 hours
2. Feedback is provided as inline comments
3. Author addresses feedback with additional commits
4. Second maintainer does final approval
5. Maintainer merges into `dev`
6. Staging merges occur on a weekly schedule
7. Maintainers approve production releases to `main`

## Code of Conduct

All contributors must adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

Open a GitHub Discussion with the "contributing" category tag.
