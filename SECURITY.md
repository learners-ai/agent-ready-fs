# Security policy

Please report security issues privately through GitHub's private vulnerability reporting: open the **Security** tab of this repository and choose **Report a vulnerability**. Don't open a public issue for a security problem.

We aim to acknowledge reports within 3 business days.

## Scope

- `skills/agent-ready-check/scripts/check.py` — the scanner. It makes GET requests only, to the one domain the user names, and stores nothing.
- The skill instructions and reference files.

The scanner is meant to be run only against sites the user owns or is authorized to test.
