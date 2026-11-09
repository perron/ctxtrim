# ctxtrim

Trim logs, HTML, Markdown, and JSON down to a token budget before they
land in an agent context window. Full-page crawls and verbose tool dumps
are a common way to blow the window after two pages.

Token counts use `ceil(utf-8 bytes / 4)`. No API key is required.

## Install

Python 3.10 or later.

From a checkout:

```bash
python3 -m pip install .
python3 -m pip install -e ".[dev]"  # optional, for tests
ctxtrim page.html --budget 2000
```

## 30-second quick start

```bash
cat > page.html << 'EOF'
<html><head><title>Docs</title></head><body>
<h1>Install</h1><p>A very long paragraph would go here.</p>
<h2>API</h2><a href="/api">API reference</a>
</body></html>
EOF

ctxtrim page.html --budget 80 --stats-only
ctxtrim page.html --budget 80
```

Sample output from that exact example:

```
$ ctxtrim page.html --budget 80 --stats-only
format=html in=42 out=13 budget=80 estimator=ceil(utf8_bytes / 4)

$ ctxtrim page.html --budget 80
# ctxtrim format=html in=42 out=13 budget=80
# Docs
# Install
## API
link: API reference -> /api
```

`--format auto` detects HTML, JSON, Markdown, and logs. HTML and Markdown
default to an outline (title, headings, links, form fields). JSON caps long
strings and long arrays. Logs keep error lines plus a tail.

## Credit

Motivated by public complaints that "the whole site as markdown eats the
window" and by the idea of sandboxing tool output. Original trim strategies;
no source was copied from any context-window product.

## Limits

- Token counts use `ceil(utf-8 bytes / 4)`, not a vendor tokenizer.
- ctxtrim reads a local file or stdin. It does not fetch URLs.
- HTML/Markdown "outline" mode keeps titles, headings, links, and form fields, not the full prose.
- If the budget is smaller than a trim marker, the output may be a single ellipsis (or empty) so it never exceeds the budget.

From GitHub you can also install with:

```bash
python3 -m pip install git+https://github.com/perron/ctxtrim.git
```

This package is not published to PyPI.

## Use it with your agent

You can point a coding agent at this repository and ask it to use the tool, adapt it, or write a small tool in the same style. That works with Claude Code, Codex, Cursor, Grok Bot, and anything else that can clone a git repo and run a Python CLI.

A short prompt you can paste:

> Clone https://github.com/perron/ctxtrim, install it, and trim ./page.html down to a 2000-token budget. Show me the stats and the outline. Token counts are ceil(utf-8 bytes / 4), not a vendor tokenizer.

If you want a new tool in this style, say so explicitly: one job, standard-library Python, pytest first, no API key, and an honest Limits section.

## Contributing / how you can help

Bug reports, tight tests, and small honest features are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to run the suite and for pull request guidelines.

Good first issues:

- A `--keep-ids` option for JSON that always preserves named keys (for example `id`, `error`).
- Drop `<script>` and `<style>` bodies from the HTML outline more aggressively.
- Add `--budget-bytes` as an alternative to the token estimate.

If you are unsure whether an idea fits, open an issue before writing a large patch.

## License

MIT. See `LICENSE`. Please read `SECURITY.md` before filing a vulnerability report. Agents should also read `AGENTS.md`.
