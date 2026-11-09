import json
from pathlib import Path
import ctxtrim.cli as ct


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
