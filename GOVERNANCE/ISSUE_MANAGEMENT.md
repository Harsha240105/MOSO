# MOSO AI — Issue Management Workflow

## Lifecycle

```
Open → Triage → Assign → Develop → Review → Close
  │       │         │        │         │       │
  │       └── Labels│        │         │       │
  │                  │        │         │       │
  └─── Community ───┘        └─── PR ──┘       │
                   Feedback                      │
                   Loop                          │
                                                 │
                    ┌──── Resolved ──────────────┘
                    ├──── Duplicate ─────────────
                    └──── Wontfix ───────────────
```

## Workflow Steps

### 1. Open
Anyone can open an issue using the provided templates:
- [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
- [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
- [AI Feedback](.github/ISSUE_TEMPLATE/ai-feedback.md)

### 2. Triage (within 72 hours)
A maintainer:
- Applies relevant labels (bug, enhancement, component-*, priority-*)
- Validates the issue is complete and actionable
- Requests missing information if needed
- Closes duplicates with a reference link

### 3. Assign
- Core maintainers assign issues during weekly sprint planning
- Priority determines assignment urgency
- `priority-critical` gets immediate attention
- `good-first-issue` is reserved for new contributors

### 4. Develop
- Developer creates a branch from `dev`: `feature/issue-123-short-name`
- Developer links PR to the issue (e.g., "Fixes #123")
- All status checks must pass
- At least the required number of approvals must be obtained

### 5. Review & Close
- Maintainer verifies the fix/feature works as described
- Issue is closed with a reference to the merged PR
- If a follow-up is needed, a new issue is created

---

## Issue Triage Labels

| Label | Triage Action |
|-------|--------------|
| `bug` | Verify reproduction, assign priority |
| `enhancement` | Scope the feature, assess architecture impact |
| `ai-feedback` | Route to AI engineers, log for model improvement |
| `privacy-review` | Flag for privacy impact assessment |
| `good-first-issue` | Add context and pointers for newcomers |

## Response SLAs

| Issue Type | Initial Response | Resolution Target |
|------------|-----------------|-------------------|
| Bug (critical) | 24 hours | 3 days |
| Bug (normal) | 72 hours | 14 days |
| Feature request | 1 week | Per roadmap |
| AI Feedback | 1 week | Per training cycle |
| Question | 48 hours | N/A |

---

## Sprint Cycle

- **Planning:** Every Monday
- **Duration:** 1 week (Mon → Fri)
- **Review:** Every Friday
- **Tools:** GitHub Projects board

---

*Last updated: 2025*
