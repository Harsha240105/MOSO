# MOSO AI — Security Policy

## Repository Access Security

MOSO AI repositories enforce strict access controls to protect the integrity of the AI Core systems.

### Access Levels

| Role           | Access                        | Push  | Merge | Fork  |
|----------------|-------------------------------|-------|-------|-------|
| Public         | View / Read only              | No    | No    | Restricted |
| Community User | View + Issues + Discussions   | No    | No    | Restricted |
| Contributor    | View + PRs                    | No    | No    | Restricted |
| Maintainer     | Full access                   | Yes   | Yes   | N/A    |
| Admin          | Full + Settings               | Yes   | Yes   | N/A    |

### Strict Rules

- **No public write access** — Only approved maintainers can push code
- **No direct push to main** — All changes require pull requests
- **No force pushes** — Rewriting history is prohibited on all protected branches
- **No unauthorized merges** — Only maintainers can merge pull requests
- **Forking is restricted** — Repository forks require explicit approval
- **Branch protection is mandatory** — All rules are enforced at the GitHub level

## Vulnerability Reporting

If you discover a security vulnerability in MOSO AI:

1. **Do NOT** file a public GitHub issue
2. **Do NOT** discuss it in public forums
3. Email `security@moso.ai` with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested mitigations

You can expect:
- Acknowledgment within 48 hours
- A detailed response within 5 business days
- Credit in security advisories (if desired)

## Supported Versions

| Version | Supported | Status |
|---------|-----------|--------|
| 1.x     | Yes       | Active development |
| 0.x     | No        | Pre-release archive |

## Data Security

| Data Type             | At Rest           | In Transit        | Storage           |
|-----------------------|-------------------|-------------------|-------------------|
| Source code           | N/A               | TLS 1.3           | GitHub            |
| AI Models             | AES-256-GCM       | HTTPS/TLS 1.3     | CDN / Local       |
| Issue discussions     | N/A               | TLS 1.3           | GitHub Issues     |
| Community feedback    | N/A               | TLS 1.3           | GitHub Discussions |

## Encryption Requirements

All code contributions and communications must use:
- Git over SSH or HTTPS with TLS 1.3
- Signed commits (GPG or SSH) — **required for all merges**
- Encrypted secrets in CI/CD pipelines

## Compliance

MOSO AI adheres to:
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [OpenSSF Scorecard](https://securityscorecards.dev/) best practices

---

*Last updated: 2025*
