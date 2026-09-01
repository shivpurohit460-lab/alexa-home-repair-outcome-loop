from __future__ import annotations

import json
from pathlib import Path

from alexa_outcome_loop.pages_export import API_FETCH, PAGES_FETCH, build_pages_site


def test_pages_export_uses_real_demo_engine(tmp_path: Path) -> None:
    data = build_pages_site(tmp_path)

    assert data["verified"] is True
    assert [event["step"] for event in data["events"]] == list(range(1, 8))
    assert data["events"][3]["state"] == "verification_failed"
    assert data["events"][-1]["state"] == "verified_resolved"

    exported = json.loads((tmp_path / "demo.json").read_text(encoding="utf-8"))
    assert exported == data

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert PAGES_FETCH in html
    assert API_FETCH not in html
    assert (tmp_path / ".nojekyll").exists()
