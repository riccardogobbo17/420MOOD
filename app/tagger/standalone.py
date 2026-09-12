"""HTML unico del tagger: stesso documento per Streamlit, download e serve.py."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def standalone_html() -> str:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "tagger.css").read_text(encoding="utf-8")
    js = (ROOT / "tagger.js").read_text(encoding="utf-8")
    html = re.sub(
        r'<link rel="stylesheet" href="tagger\.css[^"]*"\s*/>',
        lambda _m: f"<style>\n{css}\n</style>",
        html,
        count=1,
    )
    html = re.sub(
        r'<script src="tagger\.js[^"]*"></script>',
        lambda _m: f"<script>\n{js}\n</script>",
        html,
        count=1,
    )
    return html
