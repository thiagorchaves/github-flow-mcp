# Security Policy

## Reporting a vulnerability

Please use GitHub private vulnerability reporting instead of opening a public issue for suspected vulnerabilities or exposed credentials.

Never include active GitHub tokens, private repository data, internal URLs, or customer data in a report. Revoke any credential immediately if you believe it has been exposed.

## Credential guidance

Use a fine-grained GitHub token scoped to the minimum repositories and permissions required. Keep `.env` out of source control and leave `GITHUB_WRITE_ENABLED=false` when remote mutations are not needed.
