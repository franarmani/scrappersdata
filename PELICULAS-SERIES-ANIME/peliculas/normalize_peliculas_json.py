"""
Normaliza peliculas.json para que todas las peliculas tengan la misma estructura.
Convierte servers a lista de dicts cuando este como string JSON.
"""

import json
import os
from typing import Dict, List


def _workspace_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", ".."))


def _normalize_servers(servers) -> List[Dict]:
    if servers is None:
        return []
    if isinstance(servers, str):
        try:
            servers = json.loads(servers)
        except Exception:
            return []
    if not isinstance(servers, list):
        return []

    normalized: List[Dict] = []
    for item in servers:
        if isinstance(item, dict):
            normalized.append(item)
            continue
        if isinstance(item, str):
            try:
                parsed = json.loads(item)
            except Exception:
                continue
            if isinstance(parsed, dict):
                normalized.append(parsed)
            elif isinstance(parsed, list):
                normalized.extend([p for p in parsed if isinstance(p, dict)])
    return normalized


def _normalize_movie_record(record: Dict) -> Dict:
    normalized = dict(record) if record else {}

    normalized["tmdb_id"] = normalized.get("tmdb_id")
    normalized["title"] = normalized.get("title", "")
    normalized["year"] = normalized.get("year", "")
    normalized["servers"] = _normalize_servers(normalized.get("servers"))
    normalized["poster_url"] = normalized.get("poster_url", "")
    normalized["backdrop_url"] = normalized.get("backdrop_url", "")
    normalized["genres_spanish"] = normalized.get("genres_spanish", []) or []
    normalized["overview"] = normalized.get("overview", "")
    normalized["rating"] = normalized.get("rating", 0) or 0

    return normalized


def main() -> None:
    root = _workspace_root()
    file_path = os.path.join(root, "peliculas.json")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    normalized = [_normalize_movie_record(item) for item in data if isinstance(item, dict)]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)

    print(f"Normalizadas {len(normalized)} peliculas en {file_path}")


if __name__ == "__main__":
    main()
