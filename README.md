# ctxtrim

Trim logs, HTML, Markdown, and JSON down to a token budget before they
land in an agent context window. Full-page crawls and verbose tool dumps
are a common way to blow the window after two pages.

Token counts use `ceil(utf-8 bytes / 4)`. No API key is required.

## Install

```bash
python3 -m pip install -e .
ctxtrim page.html --budget 2000
```

## 30-second example

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

`--format auto` detects HTML, JSON, Markdown, and logs. HTML and Markdown
default to an outline (title, headings, links, form fields). JSON caps long
strings and long arrays. Logs keep error lines plus a tail.

## Credit

Motivated by public complaints that "the whole site as markdown eats the
window" and by the idea of sandboxing tool output. Original trim strategies;
no source was copied from any context-window product.
