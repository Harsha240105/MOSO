# MOSO AI — Release Strategy

## Semantic Versioning

MOSO AI follows **Semantic Versioning 2.0.0**: `MAJOR.MINOR.PATCH`

| Component | When to Increment | Example |
|-----------|-------------------|---------|
| **MAJOR** | Breaking API changes, incompatible model formats, significant architecture changes | `1.0.0` → `2.0.0` |
| **MINOR** | New features, new models, backward-compatible additions | `1.0.0` → `1.1.0` |
| **PATCH** | Bug fixes, performance improvements, security patches | `1.0.0` → `1.0.1` |

### Pre-release Tags

| Tag | Meaning | Example |
|-----|---------|---------|
| `-alpha.N` | Internal testing, unstable | `1.0.0-alpha.1` |
| `-beta.N` | Feature-complete, community testing | `1.0.0-beta.2` |
| `-rc.N` | Release candidate, final validation | `1.0.0-rc.3` |

---

## Release Cadence

| Release Type | Frequency | Branch From | Merged To |
|-------------|-----------|-------------|-----------|
| **Daily** (dev) | Daily | `feature/*` | `dev` |
| **Weekly** (staging) | Weekly | `dev` | `staging` |
| **Monthly** (release) | Monthly | `staging` | `main` |
| **Hotfix** | As needed | `main` | `main` (via `hotfix/*`) |

---

## Release Process

### 1. Development Phase (Weekly)
```
feature/* ──────> dev (daily merges)
                    │
                    │ PR with 1 approval
                    ▼
                  dev branch
```

### 2. Staging Phase (Weekend)
```
dev ──────────> staging (Friday merge)
  │                 │
  │                  │
  │                  ▼
  │               staging branch
  │                  │
  │                  │ Full test suite run
  │                  │ QA validation
  │                  │ Performance benchmarks
```

### 3. Release Phase (Monthly)
```
staging ──────> main (last Friday of month)
   │                 │
   │                  │
   │                  ▼
   │               main branch
   │                  │
   │                  │ Tag: vX.Y.Z
   │                  │ Release notes generated
   │                  │ GitHub Release created
```

### 4. Hotfix Process (As Needed)
```
main ──────────> hotfix/issue-desc
   │                 │
   │                  │
   │                  ▼
   │               hotfix branch
   │                  │
   │                  │ Fix + test
   │                  ▼
   │               PR back to main
   │                  │
   │                  │ 1 expedited approval
   │                  ▼
   │               Patch release: vX.Y.Z+1
```

---

## Changelog

Each release includes a `CHANGELOG.md` entry following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [1.2.0] - 2025-06-01

### Added
- Episodic memory consolidation (PR #142)
- Whisper streaming support (PR #138)

### Fixed
- Memory leak in vector DB connection pool (PR #145)
- Crash on model load with invalid GGUF (PR #140)

### Security
- Fixed prompt injection vector in chat pipeline (PR #143)

### Changed
- Updated llama.cpp to v3024 (PR #141)
```

---

## Release Artifacts

Each GitHub Release includes:

- **Source code** (zip + tar.gz)
- **Release notes** with changelog
- **Pre-built binaries** (when available):
  - `MOSO-Android-v1.2.0.apk`
  - `MOSO-iOS-v1.2.0.xcarchive`
  - `MOSO-macOS-v1.2.0.dmg`
  - `MOSO-Windows-v1.2.0.exe`
- **Checksums** (SHA-256)
- **GPG signature**

---

## Long-Term Support (LTS)

| Version | LTS Period | Status |
|---------|-----------|--------|
| 1.x     | 12 months | Active |
| 0.x     | Ended     | Archive |

LTS releases receive security patches for 12 months after the next major release.

---

*Last updated: 2025*
