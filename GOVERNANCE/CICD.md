# MOSO AI — CI/CD Pipeline Architecture

## Pipeline Overview

```
                    ┌─────────────────┐
                    │   Developer      │
                    │   Push Code      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Branch Match   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │  feature/*   │ │    dev       │ │  hotfix/*    │
     └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
            │                │                │
            ▼                ▼                ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ PR Gate      │ │  CI Pipeline │ │  Hotfix CI   │
     │ • Lint       │ │ • Lint      │ │ • Lint       │
     │ • Test       │ │ • Test      │ │ • Test       │
     │ • Security   │ │ • Security  │ │ • Security   │
     │ • License    │ │ • Build     │ │ • Build      │
     └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
            │                │                │
            ▼                ▼                │
     ┌──────────────┐ ┌──────────────┐        │
     │ Merge to dev │ │  staging     │        │
     └──────────────┘ │  Deploy      │        │
                      └──────┬───────┘        │
                             │                │
                             ▼                ▼
                      ┌──────────────┐ ┌──────────────┐
                      │  Release     │ │  Merge to    │
                      │  Pipeline    │ │  main        │
                      └──────┬───────┘ └──────┬───────┘
                             │                │
                             ▼                ▼
                      ┌──────────────┐ ┌──────────────┐
                      │  Production  │ │  Patch       │
                      │  Release     │ │  Release     │
                      └──────────────┘ └──────────────┘
```

---

## Pipeline Matrix

| Pipeline | Trigger | Branches | Checks | Duration |
|----------|---------|----------|--------|----------|
| **PR Gate** | PR opened/synced | `dev`, `staging`, `main` | Lint, Test, Security, License, Title | ~5 min |
| **CI Build** | Push | `dev`, `staging` | Lint, Test, Security, Build | ~10 min |
| **Security Scan** | Push + scheduled | All branches | CodeQL, Trivy, Secrets scan | ~8 min |
| **Branch Protection** | PR | All protected | Signed commits, Commit format | ~2 min |
| **Release** | Tag push | `main` | Full suite, artifact build, publish | ~15 min |
| **Scheduled** | Nightly | `main` | Full integration, performance benchmarks | ~30 min |

---

## Workflow Summary

| File | Purpose |
|------|---------|
| `pr-gate.yml` | Required checks for all pull requests |
| `branch-protection.yml` | Signed commit and conventional commit validation |
| `security-scan.yml` | CodeQL, Trivy, and secrets scanning |
| `release.yml` | Semantic versioning and GitHub Release creation |

---

## Common CI/CD Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `MOSO_ENV` | Environment (`test`, `staging`, `production`) | GitHub Secrets |
| `DOCKER_REGISTRY` | Container registry URL | GitHub Secrets |
| `CODECOV_TOKEN` | Code coverage upload token | GitHub Secrets |

---

## Best Practices

1. **Fail fast** — Lint runs before tests to give quick feedback
2. **Cache dependencies** — Python packages, Rust cache, Flutter pub cache
3. **Parallel execution** — Independent checks run in parallel
4. **Security first** — Every PR is scanned for vulnerabilities
5. **Signed commits** — All merges require verified signatures
6. **Artifact retention** — Build artifacts kept for 7 days
7. **Scheduled scanning** — Nightly full security scans

---

*Last updated: 2025*
