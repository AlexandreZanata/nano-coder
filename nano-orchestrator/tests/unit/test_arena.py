"""Arena API helpers (CPU)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena.server import SAFE_NAME, api_file, api_overview, site_file_path  # noqa: E402


def test_safe_name() -> None:
    assert SAFE_NAME.match("site-home.html")
    assert not SAFE_NAME.match("../secret")


def test_overview_shape(tmp_path: Path, monkeypatch) -> None:
    import arena.server as srv

    proposal = tmp_path / "proposal"
    proposal.mkdir()
    (proposal / "package.json").write_text(
        json.dumps(
            {
                "human_gate": True,
                "auto_persist": False,
                "peak_vram_mb": 100,
                "files": [],
            }
        ),
        encoding="utf-8",
    )
    (proposal / "site-home.html").write_text("<html></html>\n", encoding="utf-8")
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "demo.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(srv, "PROPOSAL", proposal)
    monkeypatch.setattr(srv, "RUNS", runs)
    overview = api_overview()
    assert overview["ok"] is True
    assert overview["files"][0]["name"] == "site-home.html"
    payload, status = api_file("site-home.html")
    assert status == 200
    assert "<html>" in payload["content"]


def test_site_file_path_serves_css(tmp_path: Path, monkeypatch) -> None:
    import arena.server as srv

    proposal = tmp_path / "proposal"
    proposal.mkdir()
    (proposal / "styles.css").write_text("body{color:red}\n", encoding="utf-8")
    (proposal / "index.html").write_text(
        '<link rel="stylesheet" href="styles.css" />\n', encoding="utf-8"
    )
    monkeypatch.setattr(srv, "PROPOSAL", proposal)
    css = site_file_path("styles.css")
    html = site_file_path("index.html")
    assert css is not None and css.read_text().startswith("body")
    assert html is not None
    assert site_file_path("../styles.css") is None
