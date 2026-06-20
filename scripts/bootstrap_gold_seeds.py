#!/usr/bin/env python3
"""Export gold seed catalog to data/seeds/ and .local/seeds/draft/ (Stage 2)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from seed_catalog.freemarker import FREEMARKER_SEEDS  # noqa: E402
from seed_catalog.html import HTML_SEEDS  # noqa: E402
from seed_catalog.javascript import JAVASCRIPT_SEEDS  # noqa: E402

CATALOG = {
    "javascript": (JAVASCRIPT_SEEDS, ROOT / "data" / "seeds" / "javascript"),
    "html": (HTML_SEEDS, ROOT / "data" / "seeds" / "html"),
    "freemarker": (FREEMARKER_SEEDS, ROOT / "data" / "seeds" / "freemarker"),
}

LOCAL_DRAFT = ROOT / ".local" / "seeds" / "draft"


def write_seed(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    total = 0
    for language, (seeds, promoted_dir) in CATALOG.items():
        for record in seeds:
            filename = f"{record['id']}.json"
            write_seed(promoted_dir / filename, record)
            write_seed(LOCAL_DRAFT / language / filename, record)
            total += 1

    print(f"Wrote {total} gold seeds ({total // 3} per language)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
