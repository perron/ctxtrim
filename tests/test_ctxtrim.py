import io
import json
from pathlib import Path
import pytest
import ctxtrim.cli as ct


def test_help_and_version():
    with pytest.raises(SystemExit) as exc:
        ct.main(["--help"])
    assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        ct.main(["--version"])
    assert exc.value.code == 0


def test_html_outline_budget(tmp_path, capsys):
    html = """
    <html><head><title>Docs</title></head><body>
    <h1>Install</h1><p>""" + ("word " * 4000) + """</p>
    <h2>Config</h2><a href="/api">API</a>
    <form><input name="q"></form>
    </body></html>
    """
    path = tmp_path / "page.html"
    path.write_text(html)
    assert ct.main([str(path), "--budget", "80", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["format"] == "html"
    assert data["output_tokens"] <= 80
    assert data["input_tokens"] > data["output_tokens"]
    assert "# Docs" in data["text"]
    assert "Install" in data["text"]
    assert "link:" in data["text"]


def test_json_string_cap(tmp_path, capsys):
    payload = {"rows": [{"body": "x" * 5000} for _ in range(5)], "ok": True}
    path = tmp_path / "blob.json"
    path.write_text(json.dumps(payload))
    assert ct.main([str(path), "--budget", "400", "--stats-only"]) == 0
    out = capsys.readouterr().out
    assert "format=json" in out
    assert "out=" in out


def test_log_keeps_errors(tmp_path, capsys):
    lines = [f"INFO ok {i}" for i in range(200)]
    lines[50] = "ERROR boom at line 50"
    path = tmp_path / "app.log"
    path.write_text("\n".join(lines))
    assert ct.main([str(path), "--budget", "500"]) == 0
    captured = capsys.readouterr()
    assert "ERROR boom at line 50" in captured.out


def test_detect_markdown():
    assert ct.detect_format("# Title\n\nHello", "auto") == "markdown"
    assert ct.detect_format('{"a": 1}', "auto") == "json"
    assert ct.detect_format("2024-01-01 00:00:00 INFO start\n", "auto") == "log"
    assert ct.detect_format("just some words", "auto") == "text"


def test_missing_file(tmp_path, capsys):
    assert ct.main([str(tmp_path / "nope.txt")]) == 1
    assert "file not found" in capsys.readouterr().err


def test_empty_input(tmp_path, capsys):
    path = tmp_path / "empty.txt"
    path.write_text("")
    assert ct.main([str(path), "--budget", "10", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["input_tokens"] == 0
    assert data["text"] == ""


def test_unicode_roundtrip(tmp_path, capsys):
    path = tmp_path / "note.md"
    path.write_text("# タイトル\n\n本文と絵文字 ✅\n", encoding="utf-8")
    assert ct.main([str(path), "--budget", "50"]) == 0
    out = capsys.readouterr().out
    assert "タイトル" in out
    assert "✅" in out or "タイトル" in out


def test_tiny_budget_never_exceeds(tmp_path, capsys):
    path = tmp_path / "big.txt"
    path.write_text("word " * 5000)
    assert ct.main([str(path), "--budget", "1", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["output_tokens"] <= 1
    assert data["input_tokens"] > 1


def test_negative_budget(tmp_path, capsys):
    path = tmp_path / "a.txt"
    path.write_text("hi")
    assert ct.main([str(path), "--budget", "0"]) == 1
    assert "budget must be positive" in capsys.readouterr().err


def test_markdown_outline(tmp_path, capsys):
    path = tmp_path / "doc.md"
    path.write_text("# Title\n\nA long paragraph.\n\n## Section\n\n- item one\n- item two\n")
    assert ct.main([str(path), "--budget", "200", "--strategy", "outline"]) == 0
    out = capsys.readouterr().out
    assert "# Title" in out
    assert "## Section" in out
    assert "item one" in out
    assert "A long paragraph" not in out


def test_tail_strategy(tmp_path, capsys):
    path = tmp_path / "lines.txt"
    path.write_text("\n".join(f"line {i}" for i in range(200)))
    assert ct.main([str(path), "--format", "text", "--strategy", "tail", "--budget", "500"]) == 0
    out = capsys.readouterr().out
    assert "line 199" in out
    assert "line 0" not in out


def test_json_ellipsis(tmp_path, capsys):
    path = tmp_path / "blob.json"
    path.write_text(json.dumps({"body": "x" * 5000, "ok": True}))
    assert ct.main([str(path), "--budget", "2000"]) == 0
    out = capsys.readouterr().out
    assert "more chars" in out


def test_stdin_large(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("word " * 20000))
    assert ct.main(["-", "--budget", "20", "--stats-only"]) == 0
    out = capsys.readouterr().out
    assert "out=" in out
    import re
    match = re.search(r"\bout=(\d+)\b", out)
    assert match and int(match.group(1)) <= 20
