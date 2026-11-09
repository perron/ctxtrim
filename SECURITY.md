# Security Policy

This project is a small local command-line tool. It does not phone home and does not require an API key.

## Reporting a vulnerability

Please open a [GitHub issue](https://github.com/perron/ctxtrim/issues) and mention that it is a security report. Do not include secrets, tokens, or private file contents in the issue.

If the report includes a working exploit against this tool, describe the impact and a minimal reproduction without pasting live credentials.

## Notes for this tool

ctxtrim reads a local file or stdin and writes a trimmed copy to stdout. It does not fetch URLs.

## Supported versions

The `master` branch and the latest tagged release, when one exists, are supported.
