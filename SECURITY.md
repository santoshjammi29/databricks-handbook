# Security Policy & Vulnerability Disclosure

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x (Latest) | :white_check_mark: |
| 1.0.x | :white_check_mark: |
| < 1.0.0 | :x: |

## Reporting a Vulnerability

We prioritize the security and confidentiality of our data engineering curriculum, source code, and configurations. If you discover a security vulnerability or potential credential exposure:

- **Security Contact**: [santu.jammi@gmail.com](mailto:santu.jammi@gmail.com)
- **Security Advisor**: Modern Data Engineering Ecosystem (`https://moderndataengineer.uk/.well-known/security.txt`)

Please do **NOT** open public GitHub issues or public pull requests for security vulnerabilities or credential discoveries.

### Submission Guidelines

When reporting an issue, please include:
1. A clear description of the vulnerability, affected recipe, workflow, or configuration file.
2. Step-by-step reproduction instructions or proof of concept.
3. Potential operational impact (e.g. credential exposure, command injection, supply chain risk).

### Response Timeline

- **Initial Acknowledgment**: Within 48 hours
- **Triage & Remediation Plan**: Within 7 business days
- **Coordinated Disclosure**: 90-day coordinated disclosure period before public release

### Hardening Invariants

This repository enforces automated secret scanning via `.gitleaks.toml`, GitHub Actions dependency auditing via `pip-audit`, and zero-credential commit policies. All sample secrets in notebooks and tests must be RFC-compliant mock identifiers (e.g., UUIDv4 or example placeholders).
