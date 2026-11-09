"""Trim text, logs, HTML, Markdown, and JSON down to a token budget."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

__version__ = "0.1.0"


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text.encode("utf-8")) + 3) // 4)


def detect_format(text: str, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            json.loads(text)
            return "json"
        except json.JSONDecodeError:
            pass
    if re.search(r"</?(html|body|div|p|h1|article)\b", text, re.I):
        return "html"
    if re.search(r"^\s*(ERROR|WARN|INFO|DEBUG|TRACE|FATAL)\b", text, re.M) or re.search(
        r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}", text, re.M
    ):
        return "log"
    if re.search(r"^#{1,6}\s", text, re.M):
        return "markdown"
    return "text"


class _Outline(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._capture: str | None = None
        self._buf: list[str] = []
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_d = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._capture = "title"
            self._buf = []
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._capture = tag
            self._buf = []
        elif tag == "a" and attrs_d.get("href"):
            self._capture = "a"
            self._buf = [attrs_d["href"]]
        elif tag in {"input", "textarea", "select", "button"}:
            name = attrs_d.get("name") or attrs_d.get("id") or attrs_d.get("type") or tag
            self.parts.append(f"form:{tag} {name}")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._capture == "title" and tag == "title":
            self.title = "".join(self._buf).strip()
            self._capture = None
        elif self._capture in {"h1", "h2", "h3", "h4", "h5", "h6"} and tag == self._capture:
            text = "".join(self._buf).strip()
            if text:
                hashes = "#" * int(tag[1])
                self.parts.append(f"{hashes} {text}")
            self._capture = None
        elif self._capture == "a" and tag == "a":
            href = self._buf[0]
            label = "".join(self._buf[1:]).strip() or href
            self.parts.append(f"link: {label} -> {href}")
            self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture == "a":
            self._buf.append(data)
        elif self._capture:
            self._buf.append(data)


def html_outline(text: str) -> str:
    parser = _Outline()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return markdown_outline(re.sub(r"<[^>]+>", " ", text))
    lines = []
    if parser.title:
        lines.append(f"# {parser.title}")
    lines.extend(parser.parts)
    return "\n".join(lines).strip() or re.sub(r"<[^>]+>", " ", text)


def markdown_outline(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s+\S", line) or re.match(r"^\s*[-*+]\s+\S", line) or re.match(r"^\s*\d+\.\s+\S", line):
            lines.append(line.rstrip())
    return "\n".join(lines) if lines else text


def cap_json(value, max_string: int, max_items: int, depth: int = 0):
    if isinstance(value, str):
        if len(value) > max_string:
            return value[:max_string] + f"…[{len(value) - max_string} more chars]"
        return value
    if isinstance(value, list):
        kept = [cap_json(v, max_string, max_items, depth + 1) for v in value[:max_items]]
        if len(value) > max_items:
            kept.append(f"…[{len(value) - max_items} more items]")
        return kept
    if isinstance(value, dict):
        out = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= max_items:
                out["…"] = f"{len(value) - max_items} more keys"
                break
            out[k] = cap_json(v, max_string, max_items, depth + 1)
        return out
    return value


def json_trim(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text
    return json.dumps(cap_json(data, max_string=200, max_items=20), indent=2, ensure_ascii=False)


def log_trim(text: str) -> str:
    lines = text.splitlines()
    important = [ln for ln in lines if re.search(r"\b(ERROR|FATAL|CRITICAL|EXCEPTION|WARN|WARNING|Traceback)\b", ln, re.I)]
    tail = lines[-40:]
    seen = set()
    out = []
    for ln in important + ["--- tail ---"] + tail:
        if ln in seen and ln != "--- tail ---":
            continue
        seen.add(ln)
        out.append(ln)
    return "\n".join(out)


def apply_strategy(text: str, fmt: str, strategy: str) -> str:
    if strategy == "outline" or (strategy == "auto" and fmt in {"html", "markdown"}):
        return html_outline(text) if fmt == "html" else markdown_outline(text)
    if strategy == "json" or (strategy == "auto" and fmt == "json"):
        return json_trim(text)
    if strategy == "log" or (strategy == "auto" and fmt == "log"):
        return log_trim(text)
    if strategy == "tail":
        return "\n".join(text.splitlines()[-80:])
    if strategy == "head" or strategy == "auto":
        return text
    return text


def fit_budget(text: str, budget: int) -> str:
    if estimate_tokens(text) <= budget:
        return text
    # binary search a prefix that fits, keep a marker
    raw = text
    lo, hi = 0, len(raw)
    best = ""
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = raw[:mid].rstrip()
        marker = f"\n…[trimmed {estimate_tokens(raw) - estimate_tokens(candidate)} est. tokens]"
        if estimate_tokens(candidate + marker) <= budget:
            best = candidate + marker
            lo = mid + 1
        else:
            hi = mid - 1
    return best or raw[: max(0, budget * 2)]


def process(text: str, fmt: str, strategy: str, budget: int) -> dict:
    detected = detect_format(text, fmt)
    reduced = apply_strategy(text, detected, strategy)
    fitted = fit_budget(reduced, budget)
    return {
        "format": detected,
        "strategy": strategy,
        "budget": budget,
        "input_tokens": estimate_tokens(text),
        "output_tokens": estimate_tokens(fitted),
        "estimator": "ceil(utf8_bytes / 4)",
        "text": fitted,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ctxtrim",
        description="Budgeted trimmer for logs, HTML, Markdown, and JSON before they hit an agent context window.",
    )
    parser.add_argument("input", nargs="?", default="-", help="file, or '-' for stdin (default)")
    parser.add_argument("--budget", type=int, default=2000, help="max estimated tokens in the output (default 2000)")
    parser.add_argument("--format", choices=["auto", "text", "markdown", "html", "json", "log"], default="auto")
    parser.add_argument("--strategy", choices=["auto", "outline", "head", "tail", "json", "log"], default="auto")
    parser.add_argument("--stats-only", action="store_true")
    parser.add_argument("--json", action="store_true", help="wrap the result in a JSON object")
    parser.add_argument("--version", action="version", version=f"ctxtrim {__version__}")
    args = parser.parse_args(argv)
    if args.budget <= 0:
        print("error: --budget must be positive", file=sys.stderr)
        return 1
    if args.input == "-":
        text = sys.stdin.read()
    else:
        path = Path(args.input)
        if not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        text = path.read_text(encoding="utf-8", errors="replace")
    result = process(text, args.format, args.strategy, args.budget)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.stats_only:
        print(
            f"format={result['format']} in={result['input_tokens']} out={result['output_tokens']} "
            f"budget={result['budget']} estimator={result['estimator']}"
        )
    else:
        print(
            f"# ctxtrim format={result['format']} in={result['input_tokens']} "
            f"out={result['output_tokens']} budget={result['budget']}",
            file=sys.stderr,
        )
        sys.stdout.write(result["text"])
        if result["text"] and not result["text"].endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
