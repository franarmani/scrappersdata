"""
Scraper temporal para completar thumbnails faltantes en xnxx.json.
Lee el json del root del workspace, visita cada url sin thumbnail_url y extrae og:image.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_DELAY_SEC = 1.0


def _workspace_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", ".."))


def _load_items(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return list(data.values())
    return []


def _write_items(path: str, items: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _default_repo_path() -> str:
    return os.path.join(
        _workspace_root(),
        "PELICULAS-SERIES-ANIME",
        "peliculas",
        "scrappersdata",
    )


def _sync_to_repo(json_path: str, repo_path: str) -> None:
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        return

    dest_path = os.path.join(repo_path, "xnxx.json")
    shutil.copyfile(json_path, dest_path)

    subprocess.run(["git", "-C", repo_path, "add", "xnxx.json"], check=False)
    diff_result = subprocess.run(["git", "-C", repo_path, "diff", "--cached", "--quiet"], check=False)
    if diff_result.returncode == 0:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    subprocess.run(
        ["git", "-C", repo_path, "commit", "-m", f"Update xnxx.json {timestamp}"],
        check=False,
    )
    subprocess.run(["git", "-C", repo_path, "push"], check=False)


def _get_html(session: requests.Session, url: str, referer: Optional[str] = None, timeout: int = 15) -> str:
    headers = {}
    if referer:
        headers["Referer"] = referer
        headers["Origin"] = f"{urlparse(referer).scheme}://{urlparse(referer).netloc}"
    response = session.get(url, timeout=timeout, headers=headers or None)
    response.encoding = "utf-8"
    return response.text


def _extract_og_image(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    og_image = soup.select_one("meta[property='og:image']")
    if og_image and og_image.get("content"):
        return og_image.get("content")
    match = re.search(r"<meta\s+property=\"og:image\"\s+content=\"([^\"]+)\"", html)
    if match:
        return match.group(1)
    return ""


def fill_missing_thumbnails(items: List[Dict], delay_sec: float) -> int:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    })

    updated = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        if not url or item.get("thumbnail_url"):
            continue

        html = _get_html(session, url, referer=url)
        thumb = _extract_og_image(html)
        if thumb:
            item["thumbnail_url"] = thumb
            updated += 1

        time.sleep(delay_sec)

    return updated


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Completa thumbnails faltantes en xnxx.json")
    parser.add_argument("--input", default=os.path.join(_workspace_root(), "xnxx.json"))
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SEC)
    parser.add_argument("--push", action="store_true", help="Sube xnxx.json al repo scrappersdata")
    parser.add_argument("--repo-path", default=_default_repo_path(), help="Ruta local del repo scrappersdata")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    items = _load_items(args.input)
    if not items:
        return 1

    fill_missing_thumbnails(items, args.delay)
    _write_items(args.input, items)
    if args.push:
        _sync_to_repo(args.input, args.repo_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
