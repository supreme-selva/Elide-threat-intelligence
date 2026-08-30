# Security Policy

## Scope

This project produces a DNS blocklist from public upstream sources. The most
relevant "security" concerns are:

- A source URL that has been hijacked, redirected, or is serving tampered content.
- A domain wrongly included (false positive) that breaks a legitimate service.
- A supply-chain concern with one of the upstream lists.

## Reporting

Please **do not** open a public issue for a suspected source-integrity or
supply-chain problem. Instead, report it privately:

- Use GitHub's [private vulnerability reporting](https://github.com/supreme-selva/Elide-threat-intelligence/security/advisories/new) for this repository, or
- Contact the maintainer directly via the email on their GitHub profile.

For ordinary false positives or list-content requests, a regular
[issue](https://github.com/supreme-selva/Elide-threat-intelligence/issues) is fine.

## What to include

- The domain(s) or source involved.
- What you observed and what you expected.
- Any evidence (logs, diffs, upstream references).

## Response

Reports are reviewed on a best-effort basis. Confirmed issues will be addressed
by updating the sources or the build logic in `process_lists.py`; the next
scheduled run then republishes a corrected `final_blocklist.txt`.

## Supported versions

Only the current `main` branch is maintained. The published artifact always
reflects the latest successful build.
