"""
Scraper de series desde poseidonhd2.co/series
Navega por grids, entra a cada serie, y extrae temporadas, episodios y servidores.
Guarda y actualiza series.json en el root del workspace.
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Configuracion
POSEIDON_BASE_URL = "https://www.poseidonhd2.co"
SERIES_URL = f"{POSEIDON_BASE_URL}/series"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PoseidonSeriesScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.series: List[Dict] = []
        self.processed_series_ids = set()

    def _workspace_root(self) -> str:
        """Devuelve la ruta base del workspace (dos niveles arriba)."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(script_dir, "..", ".."))

    def _get_next_data(self, html_text: str) -> Optional[Dict]:
        """Extrae el JSON de __NEXT_DATA__."""
        try:
            soup = BeautifulSoup(html_text, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if script:
                content = script.string if script.string else script.get_text(strip=False)
                if content:
                    return json.loads(content)
        except Exception as exc:
            logger.debug(f"Error parseando __NEXT_DATA__: {exc}")
        return None

    def _find_dict_with_keys(self, data, required_keys: List[str]) -> Optional[Dict]:
        """Busca recursivamente un dict que contenga todas las keys requeridas."""
        if isinstance(data, dict):
            if all(k in data for k in required_keys):
                return data
            for value in data.values():
                found = self._find_dict_with_keys(value, required_keys)
                if found:
                    return found
        elif isinstance(data, list):
            for item in data:
                found = self._find_dict_with_keys(item, required_keys)
                if found:
                    return found
        return None

    def _extract_tmdb_id_from_url(self, series_url: str) -> Optional[int]:
        match = re.search(r"/serie/(\d+)/", series_url)
        if match:
            try:
                return int(match.group(1))
            except Exception:
                return None
        return None

    def _extract_grid_series(self, page_url: str) -> Tuple[List[Dict], Optional[str]]:
        """Extrae URLs de series desde un grid y devuelve next page si existe."""
        results = []
        next_url = None
        try:
            response = self.session.get(page_url, timeout=15)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")

            section = soup.find("section", class_="home-movies")
            if not section:
                logger.warning("No se encontro section.home-movies")
                return results, None

            grid = section.find("ul", class_=re.compile(r"MovieList"))
            if not grid:
                logger.warning("No se encontro ul.MovieList en grid")
                return results, None

            items = grid.find_all("li", class_="TPostMv")
            for item in items:
                a = item.find("a", href=True)
                title_elem = item.find("span", class_="Title")
                year_elem = item.find("span", class_="Year")
                vote_elem = item.find("span", class_="Vote")

                if not a:
                    continue

                href = a.get("href", "")
                series_url = urljoin(POSEIDON_BASE_URL, href)
                results.append({
                    "url": series_url,
                    "title": title_elem.get_text(strip=True) if title_elem else "",
                    "year": year_elem.get_text(strip=True) if year_elem else "",
                    "vote": vote_elem.get_text(strip=True) if vote_elem else "",
                })

            nav = section.find("nav", class_=re.compile(r"pagination"))
            if nav:
                next_link = nav.find("a", class_=re.compile(r"next"), href=True)
                if next_link:
                    next_url = urljoin(POSEIDON_BASE_URL, next_link["href"])
        except Exception as exc:
            logger.error(f"Error extrayendo grid de {page_url}: {exc}")

        return results, next_url

    def _parse_series_info(self, series_url: str) -> Tuple[Optional[Dict], List[int]]:
        """Extrae informacion de la serie y temporadas disponibles."""
        try:
            response = self.session.get(series_url, timeout=15)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")

            title = ""
            original_title = ""
            overview = ""
            genres: List[str] = []
            poster_url = ""
            backdrop_url = ""
            vote_average = 0.0
            vote_count = 0
            popularity = 0.0
            status = ""
            first_air_date = ""

            # Intentar con __NEXT_DATA__ primero
            next_data = self._get_next_data(response.text)
            if next_data:
                serie_data = self._find_dict_with_keys(next_data, ["TMDbId", "titles", "overview"])
                if serie_data:
                    title = serie_data.get("titles", {}).get("name", "")
                    original_title = serie_data.get("titles", {}).get("originalName", "")
                    overview = serie_data.get("overview", "")
                    first_air_date = serie_data.get("releaseDate", "")
                    vote_average = serie_data.get("rate", {}).get("average", 0) or 0
                    vote_count = serie_data.get("rate", {}).get("count", 0) or 0
                    popularity = serie_data.get("popularity", 0) or 0
                    status = serie_data.get("status", "")
                    genres = [g.get("name", "") for g in serie_data.get("genres", []) if g.get("name")]
                    poster_url = serie_data.get("images", {}).get("poster", "")
                    backdrop_url = serie_data.get("images", {}).get("backdrop", "")

            # Fallback HTML
            if not title:
                title_elem = soup.find("h1", class_="Title")
                title = title_elem.get_text(strip=True) if title_elem else ""
            if not original_title:
                subtitle_elem = soup.find("span", class_="SubTitle")
                original_title = subtitle_elem.get_text(strip=True) if subtitle_elem else ""
            if not overview:
                desc = soup.find("div", class_="Description")
                overview = desc.get_text(" ", strip=True) if desc else ""

            if not genres:
                info_list = soup.find("ul", class_="InfoList")
                if info_list:
                    for li in info_list.find_all("li"):
                        if "Genero" in li.get_text():
                            for a in li.find_all("a"):
                                g = a.get_text(strip=True)
                                if g:
                                    genres.append(g)

            if not poster_url:
                poster_img = soup.select_one("article.TPost .Image img")
                poster_url = poster_img.get("src", "") if poster_img else ""
            if not backdrop_url:
                backdrop_img = soup.select_one("div.backdrop > div.Image img")
                backdrop_url = backdrop_img.get("src", "") if backdrop_img else ""

            if not vote_average:
                vote_elem = soup.find("div", id="TPVotes")
                if vote_elem and vote_elem.get("data-percent"):
                    try:
                        vote_average = float(vote_elem.get("data-percent")) / 10.0
                    except Exception:
                        vote_average = 0.0

            year = ""
            meta = soup.find("p", class_="meta")
            if meta:
                spans = meta.find_all("span")
                if spans:
                    year = spans[-1].get_text(strip=True)
                    if year and not first_air_date:
                        first_air_date = f"{year}-01-01"

            season_numbers = []
            select = soup.find("select", id="select-season")
            if select:
                for option in select.find_all("option"):
                    value = option.get("value")
                    try:
                        number = int(value)
                    except Exception:
                        number = None
                    if number and number > 0:
                        season_numbers.append(number)

            if not season_numbers:
                season_numbers = [1]

            tmdb_id = self._extract_tmdb_id_from_url(series_url)

            info = {
                "tmdb_id": tmdb_id,
                "name": title,
                "original_name": original_title or title,
                "overview": overview,
                "poster_path": poster_url,
                "backdrop_path": backdrop_url,
                "first_air_date": first_air_date,
                "genres": genres,
                "vote_average": vote_average,
                "vote_count": vote_count,
                "popularity": popularity,
                "status": status,
                "number_of_seasons": len(season_numbers),
                "number_of_episodes": 0,
                "pelicinehd_url": series_url,
            }

            return info, season_numbers
        except Exception as exc:
            logger.error(f"Error extrayendo info de serie {series_url}: {exc}")
            return None, []

    def _season_url(self, series_url: str, season_number: int) -> str:
        return f"{series_url}/temporada/{season_number}"

    def _extract_episode_cards(self, season_url: str) -> List[Dict]:
        """Extrae episodios desde una pagina de temporada."""
        episodes = []
        try:
            response = self.session.get(season_url, timeout=15)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")

            ul = soup.find("ul", class_=re.compile(r"all-episodes"))
            if not ul:
                return episodes

            items = ul.find_all("li", class_="TPostMv")
            for item in items:
                a = item.find("a", href=True)
                if not a:
                    continue
                href = a.get("href", "")
                ep_url = urljoin(POSEIDON_BASE_URL, href)

                title_elem = item.find("h2", class_="Title")
                title = title_elem.get_text(strip=True) if title_elem else ""

                ep_num = None
                year_span = item.find("span", class_="Year")
                if year_span:
                    match = re.search(r"\dx(\d+)", year_span.get_text(strip=True))
                    if match:
                        ep_num = int(match.group(1))

                if ep_num is None:
                    match = re.search(r"/episodio/(\d+)", ep_url)
                    if match:
                        ep_num = int(match.group(1))

                episodes.append({
                    "url": ep_url,
                    "title": title,
                    "episode": ep_num,
                })

        except Exception as exc:
            logger.error(f"Error extrayendo episodios de {season_url}: {exc}")

        return episodes

    def _extract_player_iframe(self, player_url: str) -> Optional[str]:
        """Extrae el iframe final desde un player poseidon."""
        try:
            response = self.session.get(player_url, timeout=10)
            response.encoding = "utf-8"
            match = re.search(r"var\s+url\s*=\s*['\"]([^'\"]+)['\"]", response.text)
            if match:
                return match.group(1)
        except Exception as exc:
            logger.debug(f"Error extrayendo iframe de {player_url}: {exc}")
        return None

    def _infer_language(self, text: str) -> str:
        text_low = text.lower()
        if "latino" in text_low:
            return "LAT"
        if "subtitulado" in text_low:
            return "SUB"
        if "ingles" in text_low or "english" in text_low:
            return "EN"
        if "espanol" in text_low or "español" in text_low:
            return "ES"
        return "LAT"

    def _extract_episode_servers(self, episode_url: str) -> List[Dict]:
        """Extrae servidores y links finales de un episodio."""
        servers: List[Dict] = []
        try:
            response = self.session.get(episode_url, timeout=15)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")

            # Buscar listas de servidores por idioma
            uls = soup.find_all("ul", class_=re.compile(r"sub-tab-lang"))
            for ul in uls:
                lang_text = ""
                # buscar texto de idioma cercano
                for prev in ul.find_all_previous("span"):
                    txt = prev.get_text(" ", strip=True)
                    if any(k in txt.lower() for k in ["latino", "subtitulado", "ingles", "english", "espanol", "español"]):
                        lang_text = txt
                        break
                language = self._infer_language(lang_text)

                for li in ul.find_all("li", attrs={"data-tr": True}):
                    player_url = li.get("data-tr")
                    if not player_url:
                        continue
                    final_url = self._extract_player_iframe(player_url) or player_url
                    server_text = li.get_text(" ", strip=True)
                    server_name = ""
                    quality = ""
                    match = re.search(r"\.\s*([^-]+?)\s*-\s*(\w+)", server_text)
                    if match:
                        server_name = match.group(1).strip()
                        quality = match.group(2).strip()

                    if not server_name:
                        parsed = urlparse(final_url)
                        server_name = parsed.netloc.replace("www.", "") if parsed.netloc else ""

                    servers.append({
                        "url": final_url,
                        "name": server_name,
                        "server": server_name,
                        "language": language,
                        "quality": quality,
                    })

            # Fallback si no se encontraron listas por idioma
            if not servers:
                for li in soup.find_all("li", attrs={"data-tr": True}):
                    player_url = li.get("data-tr")
                    if not player_url:
                        continue
                    final_url = self._extract_player_iframe(player_url) or player_url
                    parsed = urlparse(final_url)
                    server_name = parsed.netloc.replace("www.", "") if parsed.netloc else ""
                    servers.append({
                        "url": final_url,
                        "name": server_name,
                        "server": server_name,
                        "language": "LAT",
                        "quality": "",
                    })

        except Exception as exc:
            logger.error(f"Error extrayendo servidores de {episode_url}: {exc}")

        return servers

    def _load_existing_series(self, output_file: str = "series.json") -> Dict[int, Dict]:
        """Carga series existentes desde el root del workspace."""
        full_path = os.path.join(self._workspace_root(), output_file)
        if not os.path.exists(full_path):
            return {}
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {int(s["tmdb_id"]): s for s in data if s.get("tmdb_id")}
        except Exception as exc:
            logger.warning(f"No se pudo cargar series existentes: {exc}")
            return {}

    def _save_series(self, series_map: Dict[int, Dict], output_file: str = "series.json") -> None:
        full_path = os.path.join(self._workspace_root(), output_file)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(list(series_map.values()), f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Guardadas {len(series_map)} series en {full_path}")
        except Exception as exc:
            logger.error(f"Error guardando series: {exc}")

    def _merge_series(self, existing: Dict, new_info: Dict, new_episodes: List[Dict]) -> Dict:
        """Merge de metadata y episodios sin duplicar."""
        merged = dict(existing) if existing else {}
        for key, value in new_info.items():
            if key not in merged or merged.get(key) in (None, "", 0, []):
                merged[key] = value

        if "created_at" not in merged or not merged.get("created_at"):
            merged["created_at"] = datetime.now(timezone.utc).isoformat()

        existing_eps = {(e.get("season"), e.get("episode")) for e in merged.get("episodios", [])}
        merged.setdefault("episodios", [])
        for ep in new_episodes:
            key = (ep.get("season"), ep.get("episode"))
            if key not in existing_eps:
                merged["episodios"].append(ep)

        merged["number_of_episodes"] = len(merged.get("episodios", []))
        return merged

    def run(self, max_pages: Optional[int] = None, max_series: Optional[int] = None, max_episodes: Optional[int] = None):
        logger.info("Iniciando scraper de series Poseidon...")
        series_map = self._load_existing_series()

        current_url = SERIES_URL
        page = 1
        processed = 0

        while current_url:
            if max_pages and page > max_pages:
                break

            logger.info(f"Procesando grid {page}: {current_url}")
            items, next_url = self._extract_grid_series(current_url)
            if not items:
                break

            for item in items:
                if max_series and processed >= max_series:
                    break

                series_url = item.get("url")
                tmdb_id = self._extract_tmdb_id_from_url(series_url)
                if not series_url or not tmdb_id:
                    continue

                if tmdb_id in self.processed_series_ids:
                    continue

                logger.info(f"Serie: {item.get('title') or series_url}")
                info, seasons = self._parse_series_info(series_url)
                if not info:
                    continue

                existing = series_map.get(tmdb_id)
                existing_eps = {(e.get("season"), e.get("episode")) for e in existing.get("episodios", [])} if existing else set()

                new_episodes: List[Dict] = []
                for season_number in seasons:
                    if season_number == 0:
                        continue
                    season_url = self._season_url(series_url, season_number)
                    episode_cards = self._extract_episode_cards(season_url)

                    for ep in episode_cards:
                        ep_num = ep.get("episode")
                        if max_episodes and len(new_episodes) >= max_episodes:
                            break
                        if (season_number, ep_num) in existing_eps:
                            continue

                        servers = self._extract_episode_servers(ep.get("url"))
                        new_episodes.append({
                            "season": season_number,
                            "episode": ep_num,
                            "title": ep.get("title") or f"Episodio {ep_num}",
                            "servidores": servers,
                        })
                        time.sleep(0.5)

                    if max_episodes and len(new_episodes) >= max_episodes:
                        break

                series_map[tmdb_id] = self._merge_series(existing, info, new_episodes)
                self.processed_series_ids.add(tmdb_id)
                processed += 1

                logger.info(f"✅ Serie actualizada: {info.get('name')} (nuevos episodios: {len(new_episodes)})")
                time.sleep(1)

            if max_series and processed >= max_series:
                break

            current_url = next_url
            page += 1

        self._save_series(series_map)
        logger.info("Scraping completado.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scraper de series desde poseidonhd2.co")
    parser.add_argument("--max-pages", type=int, default=None, help="Numero maximo de paginas")
    parser.add_argument("--max-series", type=int, default=None, help="Numero maximo de series")
    parser.add_argument("--max-episodes", type=int, default=None, help="Numero maximo de episodios por corrida")

    args = parser.parse_args()

    scraper = PoseidonSeriesScraper()
    scraper.run(max_pages=args.max_pages, max_series=args.max_series, max_episodes=args.max_episodes)


if __name__ == "__main__":
    main()
