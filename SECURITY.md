# Security policy

## Supported version

Security fixes are applied to the latest code on the `main` branch. This
pre-release project does not currently maintain older release branches.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use the repository's
private **Security > Report a vulnerability** flow:

<https://github.com/hoseinmrh/multAIverse/security/advisories/new>

Include a concise impact description, reproduction steps, affected commit or
version, and any suggested mitigation. Remove API keys, real profile data, and
other unrelated personal information. If private vulnerability reporting is
not available, contact the repository owner privately through their GitHub
profile before sharing details publicly.

Please allow a reasonable period for acknowledgement, validation, and a fix
before disclosure.

## Security model

Multiverse is currently a local-first application without authentication. It
binds its development services to loopback by default and is not designed for
direct exposure to an untrusted network. OpenAI configuration is backend-only;
the mock provider keeps the core experience usable without external data
transfer. See the README's privacy section for the fields sent when OpenAI mode
is explicitly enabled.
