"""Check local documentation links and CSV structure without third-party packages."""
from __future__ import annotations

import csv
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPO_PREFIX = "/Ehtisham514/apex-reconciliation-toolkit/"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"href", "src"} and value:
                self.links.append(value)


def local_target(source: Path, link: str):
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc:
        if parsed.netloc != "github.com" or not parsed.path.startswith(REPO_PREFIX):
            return None
        tail = parsed.path[len(REPO_PREFIX):]
        if tail.startswith("blob/main/"):
            return ROOT / unquote(tail[len("blob/main/"):])
        if tail.startswith("tree/main/"):
            return ROOT / unquote(tail[len("tree/main/"):])
        return None
    if not parsed.path or parsed.path.startswith("/"):
        return None
    return (source.parent / unquote(parsed.path)).resolve()


def main():
    errors = []
    checked_links = 0
    checked_csv = 0
    for source in sorted(ROOT.rglob("*")):
        rel = source.relative_to(ROOT)
        if not source.is_file() or any(p.startswith(".") or p in {"node_modules", "__pycache__", "private-data", "exports"} for p in rel.parts):
            continue
        if source.suffix in {".md", ".html"}:
            text = source.read_text(encoding="utf-8")
            if source.suffix == ".html":
                parser = Links()
                parser.feed(text)
                links = parser.links
            else:
                # Omit code blocks so examples of Markdown syntax are not links.
                prose = re.sub(r"```.*?```", "", text, flags=re.S)
                links = re.findall(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", prose)
            for link in links:
                target = local_target(source, link.strip("<>"))
                if target is not None:
                    checked_links += 1
                    if not target.exists():
                        errors.append(f"{rel}: missing target {link}")
        elif source.suffix == ".csv":
            checked_csv += 1
            with source.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle, strict=True)
                header = next(reader, None)
                if not header or any(not cell.strip() for cell in header) or len(set(header)) != len(header):
                    errors.append(f"{rel}: missing, blank or duplicate CSV header")
                    continue
                for line, row in enumerate(reader, 2):
                    if row and len(row) != len(header):
                        errors.append(f"{rel}:{line}: {len(row)} cells, expected {len(header)}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {checked_links} local documentation links and {checked_csv} CSV files checked")


if __name__ == "__main__":
    main()
