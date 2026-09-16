"""Validate the versioned public wiki's structure, navigation and repository links.

Copyright (c) 2026 Gadash +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPOSITORY = Path(__file__).resolve().parents[1]
WIKI = REPOSITORY / "About-Info" / "Wiki"
PUBLIC_ROOT = "https://github.com/GGadash/GDTT"
LINK = re.compile(r"\]\((https://github\.com/GGadash/GDTT[^\s)]*)\)")
WIKI_TARGET = re.compile(r"\]\(https://github\.com/GGadash/GDTT/wiki/([^\s)#]+)")


def validate() -> tuple[int, int, list[str]]:
    files = sorted(WIKI.glob("*.md"))
    pages = {path.stem for path in files if not path.stem.startswith("_")}
    errors: list[str] = []
    links = 0
    if not {"Home", "Release-Status-and-Safety", "License-Credits-and-Support"} <= pages:
        errors.append("Missing required entry, safety or credits page.")
    sidebar = (WIKI / "_Sidebar.md").read_text(encoding="utf-8")
    sidebar_pages = {unquote(name) for name in WIKI_TARGET.findall(sidebar)}
    if sidebar_pages != pages:
        errors.append(f"Sidebar coverage differs: {sorted(sidebar_pages ^ pages)}")
    footer = (WIKI / "_Footer.md").read_text(encoding="utf-8")
    for phrase in ("Unsigned", "clean-Windows", "License-Credits-and-Support", "OpenAI Codex"):
        if phrase not in footer:
            errors.append(f"Footer missing {phrase}.")
    for path in files:
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            errors.append(f"{path.name}: missing final newline")
        if not path.stem.startswith("_"):
            if not text.startswith("# "):
                errors.append(f"{path.name}: missing title")
            expected = "## In brief" if path.stem == "Home" else "## Summary"
            if expected not in text:
                errors.append(f"{path.name}: missing summary")
        if len(re.findall(r"^\x60{3}", text, re.MULTILINE)) % 2:
            errors.append(f"{path.name}: unmatched code fence")
        if re.search(r"\]\((?:repo|tree|wiki):", text) or "§" in text:
            errors.append(f"{path.name}: unresolved authoring placeholder")
        for url in LINK.findall(text):
            links += 1
            route = unquote(urlsplit(url).path).removeprefix("/GGadash/GDTT/")
            if route.startswith("wiki/"):
                target = route.removeprefix("wiki/")
                if target not in pages:
                    errors.append(f"{path.name}: unknown wiki page {target}")
            elif route.startswith(("blob/main/", "tree/main/")):
                target = route.split("/", 2)[2]
                if not (REPOSITORY / target).exists():
                    errors.append(f"{path.name}: missing repository target {target}")
    license_text = (REPOSITORY / "LICENSE").read_text(encoding="utf-8").strip()
    credits = (WIKI / "License-Credits-and-Support.md").read_text(encoding="utf-8")
    quoted_license = "\n".join(
        line.removeprefix("> ").removeprefix(">")
        for line in credits.splitlines()
        if line.startswith(">")
    ).strip()
    if quoted_license != license_text:
        errors.append("Wiki license quotation differs from root LICENSE.")
    return len(pages), links, errors


if __name__ == "__main__":
    page_count, link_count, findings = validate()
    for finding in findings:
        print(f"ERROR: {finding}")
    if findings:
        raise SystemExit(1)
    print(f"Verified {page_count} wiki content pages, sidebar/footer and {link_count} local links.")
    print("Root license quotation matches. External sites and rendered diagrams need live review.")
