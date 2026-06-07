# MOSO AI — Team Permission Architecture

## Organization Structure

### Organization: `MOSO-AI`

```
MOSO-AI/
├── moso-app/           # Cross-platform application
├── moso-core/          # AI inference runtime
├── moso-memory-engine/ # Memory and retrieval system
├── moso-docs/          # Documentation hub
```

---

## Teams & Permissions

### 1. Core Maintainers (`@MOSO-AI/core-maintainers`)

| Permission | Value |
|------------|-------|
| Role | Admin (all repos) |
| Push access | Yes |
| Merge access | Yes |
| Settings access | Yes |

**Responsibilities:**
- Overall project direction and governance
- Final approval on all merges to `main`
- Security vulnerability handling
- Release management
- CODEOWNERS for all critical paths

---

### 2. AI Engineers (`@MOSO-AI/ai-engineers`)

| Permission | Value |
|------------|-------|
| Role | Write (`moso-core`, `moso-memory-engine`) |
| Push access | To `dev` and `feature/*` only |
| Merge access | No (require core maintainer approval) |

**Responsibilities:**
- AI model integration and optimization
- Inference engine development
- Memory engine and RAG pipeline development
- Model training and fine-tuning
- Prompt engineering

---

### 3. Backend Engineers (`@MOSO-AI/backend-engineers`)

| Permission | Value |
|------------|-------|
| Role | Write (`moso-app` backend dirs) |
| Push access | To `dev` and `feature/*` only |
| Merge access | No (require core maintainer approval) |

**Responsibilities:**
- API development (FastAPI)
- Sync and WebSocket services
- Database schema and migrations
- Cloud infrastructure

---

### 4. Platform Engineers

#### Android Engineers (`@MOSO-AI/android-engineers`)
- **Role:** Write (`moso-app/apps/android`)
- **Focus:** Android app, Kotlin, Flutter

#### iOS Engineers (`@MOSO-AI/ios-engineers`)
- **Role:** Write (`moso-app/apps/ios`)
- **Focus:** iOS app, SwiftUI, Flutter

#### macOS Engineers (`@MOSO-AI/macos-engineers`)
- **Role:** Write (`moso-app/apps/macos`)
- **Focus:** macOS desktop app

#### Desktop Engineers (`@MOSO-AI/desktop-engineers`)
- **Role:** Write (`moso-app/apps/windows`, `moso-app/apps/linux`)
- **Focus:** Windows & Linux desktop apps

---

### 5. Infrastructure Engineers (`@MOSO-AI/infrastructure-engineers`)

| Permission | Value |
|------------|-------|
| Role | Write (CI/CD, Cloud configs) |
| Push access | To `dev` and `feature/*` only |
| Merge access | No |

**Responsibilities:**
- CI/CD pipeline maintenance
- Docker and container orchestration
- Cloud infrastructure (AWS, GCP, Cloudflare)
- Monitoring and alerting

---

### 6. Community Contributors (External)

| Permission | Value |
|------------|-------|
| Role | Read (all repos) |
| Issues | Can open and comment |
| Discussions | Can participate |
| PRs | Can submit (no merge rights) |
| Push access | ❌ No |
| Fork | Restricted (requires approval) |

---

## Repository Access Matrix

| Team / Role | `moso-app` | `moso-core` | `moso-memory-engine` | `moso-docs` |
|-------------|------------|-------------|----------------------|-------------|
| Public | Read | Read | Read | Read |
| Community | Read + Issues | Read + Issues | Read + Issues | Read + Issues |
| Contributors | Read + PRs | Read + PRs | Read + PRs | Read + PRs |
| Core Maintainers | Admin | Admin | Admin | Admin |
| AI Engineers | Read | Write | Write | Read |
| Backend Engineers | Write (backend/) | Read | Read | Read |
| Platform Engineers | Write (apps/) | Read | Read | Read |
| Infrastructure | Write (.github/) | Read | Read | Read |

---

## Merge Approval Flow

```
feature/* ──PR──> dev ──PR──> staging ──PR──> main
  │                  │              │             │
  └── 1 approval     │              │             │
                     └── 1 approval │             │
                                    └── 1 approval│
                                                   └── 2 approvals
```

1. `feature/*` → `dev`: Requires 1 maintainer approval
2. `dev` → `staging`: Requires 1 maintainer approval (scheduled weekly)
3. `staging` → `main`: Requires 2 core maintainer approvals (release)

---

## Onboarding New Team Members

1. Existing maintainer nominates the candidate
2. Core team votes (majority approval required)
3. GitHub team membership is granted
4. Candidate reads and agrees to:
   - [MOSO Source Available License](LICENSE)
   - [Code of Conduct](CODE_OF_CONDUCT.md)
   - [Contributing Guidelines](CONTRIBUTING.md)
   - [Security Policy](SECURITY.md)

---

*Last updated: 2025*
