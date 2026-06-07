# MOSO AI — Branch Protection Rules

## Overview

This document defines the branch protection configuration for all MOSO AI repositories.
These rules are enforced at the GitHub organization and repository level.

---

## Protected Branches

### `main` — Production

| Setting | Value |
|---------|-------|
| Require pull request before merging | ✅ Yes |
| Required approvals | **2** |
| Dismiss stale approvals | ✅ Yes |
| Require review from Code Owners | ✅ Yes |
| Require status checks | ✅ All required |
| Require branches to be up-to-date | ✅ Yes |
| Require signed commits | ✅ Yes |
| Include administrators | ✅ Yes |
| Allow force pushes | ❌ No |
| Allow deletions | ❌ No |
| Lock branch | ❌ No |

### `staging` — Release Candidates

| Setting | Value |
|---------|-------|
| Require pull request before merging | ✅ Yes |
| Required approvals | **1** |
| Dismiss stale approvals | ✅ Yes |
| Require review from Code Owners | ✅ Yes |
| Require status checks | ✅ All required |
| Require branches to be up-to-date | ✅ Yes |
| Include administrators | ✅ Yes |
| Allow force pushes | ❌ No |
| Allow deletions | ❌ No |

### `dev` — Development

| Setting | Value |
|---------|-------|
| Require pull request before merging | ✅ Yes |
| Required approvals | **1** |
| Require review from Code Owners | ✅ Yes |
| Require status checks | ✅ All required |
| Include administrators | ✅ Yes |
| Allow force pushes | ❌ No |
| Allow deletions | ❌ No |

### `feature/*` — Feature Branches

| Setting | Value |
|---------|-------|
| Require pull request before merging | ❌ No |
| Allow force pushes | ❌ No |
| Allow deletions | ✅ Yes |
| Automatic deletion after merge | ✅ Yes |

### `hotfix/*` — Emergency Fixes

| Setting | Value |
|---------|-------|
| Require pull request before merging | ✅ Yes |
| Required approvals | **1** (expedited) |
| Require status checks | ✅ Critical only |
| Include administrators | ✅ Yes |

---

## Required Status Checks

Before merging to `main`, these checks must pass:

- [x] `lint` — Python linting with flake8 and black
- [x] `test` — All unit and integration tests pass
- [x] `security-scan` — CodeQL + Trivy + secrets scan pass
- [x] `license-check` — MOSO Source Available License compliance
- [x] `pr-title` — PR title follows conventional commits format
- [x] `branch-protection` — Signed commits and commit format validation
- [x] `codeowners` — Required reviews from CODEOWNERS

---

## Repository Configuration

### Settings to Apply

```yaml
# In GitHub repo Settings > General
default_branch: main
merge_commit_allowed: true
squash_merge_allowed: false
rebase_merge_allowed: true
allow_auto_merge: true
delete_head_branch: true

# In GitHub repo Settings > Branches
branch_protection_rules:
  - branch: main
    required_approving_review_count: 2
    dismiss_stale_reviews: true
    require_code_owner_review: true
    required_status_checks: [lint, test, security-scan, license-check]
    requires_committer_signature: true
    enforce_admins: true
    allows_force_pushes: false
    allows_deletions: false
```

---

## Enforcement

Branch protection rules are enforced by:
1. GitHub branch protection settings in each repository
2. CI/CD workflows that validate compliance
3. CODEOWNERS reviews blocking unauthorized changes
4. Organization-level rules applying to all MOSO-AI repositories

---

*Last updated: 2025*
