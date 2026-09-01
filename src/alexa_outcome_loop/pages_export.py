from __future__ import annotations

import argparse
import json
from pathlib import Path

from .demo_engine import build_demo_timeline

API_FETCH = "const response = await fetch('/api/demo/run', {method:'POST'});"
PAGES_FETCH = "const response = await fetch('./demo.json', {cache:'no-store'});"


def build_pages_site(output_dir: Path) -> dict:
    """Build the public Pages simulator from the real deterministic demo engine."""
    output_dir.mkdir(parents=True, exist_ok=True)

    package_dir = Path(__file__).resolve().parent
    source_index = (package_dir / "static" / "index.html").read_text(encoding="utf-8")
    if API_FETCH not in source_index:
        raise RuntimeError("Judge demo HTML no longer contains the expected API fetch hook")

    pages_index = source_index.replace(API_FETCH, PAGES_FETCH, 1)
    (output_dir / "index.html").write_text(pages_index, encoding="utf-8")

    data = build_demo_timeline()
    (output_dir / "demo.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the public judge demo site")
    parser.add_argument("--output", default="site", help="Output directory")
    args = parser.parse_args()
    build_pages_site(Path(args.output))


if __name__ == "__main__":
    main()
