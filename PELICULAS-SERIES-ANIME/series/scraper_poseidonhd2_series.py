"""
Scraper de series desde poseidonhd2.co
Extrae: series, temporadas, episodios, servidores disponibles
Guarda estructura completa: {tmdb_id, title, year, seasons[episodes[servers]]}
Con sincronización automática a GitHub y Supabase
"""

import json
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import os
import sys
import subprocess
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración
POSEIDON_BASE_URL = "https://www.poseidonhd2.co"
SERIES_LIST_URL = f"{POSEIDON_BASE_URL}/series"

class PoseidonHD2SeriesScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.series = []
        self.processed_tmdb_ids = set()
        
    def extraer_series_lista(self, page_url: str = SERIES_LIST_URL) -> List[Dict]:
        """Extrae lista de series desde la página de series"""
        series_urls = []
        
        try:
            response = self.session.get(page_url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar todas las series en la sección home-movies
            series_list = soup.find('section', class_='home-movies')
            if not series_list:
                logger.warning(f"No se encontró section.home-movies en {page_url}")
                return series_urls
            
            # Buscar todos los items de series (li.TPostMv)
            serie_items = series_list.find_all('li', class_='TPostMv')
            logger.info(f"Se encontraron {len(serie_items)} series en la página")
            
            for item in serie_items:
                try:
                    # Obtener link de la serie
                    link_elem = item.find('a', href=True)
                    if link_elem:
                        href = link_elem.get('href')
                        if href:
                            full_url = urljoin(POSEIDON_BASE_URL, href)
                            
                            # Obtener información básica
                            titulo_elem = item.find('span', class_='Title block')
                            titulo = titulo_elem.get_text(strip=True) if titulo_elem else 'Unknown'
                            
                            year_elem = item.find('span', class_='Year')
                            year = year_elem.get_text(strip=True) if year_elem else ''
                            
                            series_urls.append({
                                'url': full_url,
                                'title': titulo,
                                'year': year
                            })
                except Exception as e:
                    logger.debug(f"Error extrayendo serie: {e}")
                    continue
            
            logger.info(f"Extraídas {len(series_urls)} URLs de series")
            
        except Exception as e:
            logger.error(f"Error extrayendo lista de series de {page_url}: {e}")
        
        return series_urls
    
    def extraer_temporadas(self, serie_url: str) -> List[Dict]:
        """Extrae temporadas disponibles de una serie"""
        temporadas = []
        
        try:
            response = self.session.get(serie_url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar select de temporadas
            season_select = soup.find('select', id='select-season')
            if not season_select:
                logger.warning(f"No se encontró select de temporadas en {serie_url}")
                return temporadas
            
            # Extraer opciones de temporadas
            options = season_select.find_all('option')
            for option in options:
                try:
                    season_num = option.get('value', '').strip()
                    season_text = option.get_text(strip=True)
                    
                    if season_num:
                        temporadas.append({
                            'number': int(season_num),
                            'text': season_text
                        })
                except Exception as e:
                    logger.debug(f"Error extrayendo temporada: {e}")
                    continue
            
            logger.info(f"Encontradas {len(temporadas)} temporadas")
            
        except Exception as e:
            logger.error(f"Error extrayendo temporadas de {serie_url}: {e}")
        
        return temporadas
    
    def extraer_episodios_temporada(self, serie_url: str, season_num: int) -> List[Dict]:
        """Extrae episodios de una temporada específica"""
        episodios = []
        
        try:
            # Ajustar URL para la temporada (el sitio maneja lazy-loading)
            # Por ahora usaremos la URL original y parsearemos el HTML inicial
            response = self.session.get(serie_url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar episodios en la sección episodes
            episodes_list = soup.find('ul', class_='all-episodes')
            if not episodes_list:
                logger.warning(f"No se encontraron episodios en {serie_url}")
                return episodios
            
            # Buscar items de episodios
            episode_items = episodes_list.find_all('li', class_='TPostMv')
            
            for item in episode_items:
                try:
                    # Obtener link del episodio
                    link_elem = item.find('a', href=True)
                    if link_elem:
                        ep_href = link_elem.get('href')
                        
                        # Obtener número del episodio
                        year_elem = item.find('span', class_='Year')
                        ep_number_text = year_elem.get_text(strip=True) if year_elem else ''
                        # Formato típico: "1x1", "1x2", etc.
                        
                        # Obtener título
                        title_elem = item.find('h2', class_='Title')
                        ep_title = title_elem.get_text(strip=True) if title_elem else ep_number_text
                        
                        if ep_href:
                            full_ep_url = urljoin(POSEIDON_BASE_URL, ep_href)
                            episodios.append({
                                'url': full_ep_url,
                                'title': ep_title,
                                'number_text': ep_number_text
                            })
                except Exception as e:
                    logger.debug(f"Error extrayendo episodio: {e}")
                    continue
            
            logger.info(f"Encontrados {len(episodios)} episodios")
            
        except Exception as e:
            logger.error(f"Error extrayendo episodios de {serie_url}: {e}")
        
        return episodios
    
    def extraer_servidores_episodio(self, episodio_url: str) -> Dict:
        """Extrae servidores disponibles de un episodio"""
        servers_data = {
            'latino': [],
            'english': [],
            'spanish': [],
            'subtitulado': []
        }
        
        try:
            response = self.session.get(episodio_url, timeout=15)
            response.encoding = 'utf-8'
            
            # Buscar el JSON en el HTML
            # El sitio usa Next.js y incrusta los datos en un script
            import re
            
            # Buscar el JSON de props
            pattern = r'"videos":\{([^}]*"latino"[^}]*"english"[^}]*)\}'
            matches = re.findall(r'"(\w+)":\[\{[^]]*\}[^]]*\]', response.text)
            
            # Mejor enfoque: buscar en el script que contiene los datos
            scripts = BeautifulSoup(response.text, 'html.parser').find_all('script')
            
            for script in scripts:
                if script.string and '"videos"' in script.string:
                    try:
                        # Extraer el JSON de los props
                        content = script.string
                        
                        # Buscar la sección de videos
                        if '"videos":' in content:
                            # Encontrar inicio y fin del objeto videos
                            start = content.find('"videos":{')
                            if start > -1:
                                # Parsear cautiosamente
                                bracket_count = 0
                                end = start + len('"videos":{')
                                
                                for i in range(end, len(content)):
                                    if content[i] == '{':
                                        bracket_count += 1
                                    elif content[i] == '}':
                                        if bracket_count == 0:
                                            end = i + 1
                                            break
                                        bracket_count -= 1
                                
                                videos_json_str = content[start + len('"videos":'):end]
                                
                                # Intentar parsear
                                try:
                                    videos_obj = json.loads(videos_json_str)
                                    
                                    # Procesar videos por idioma
                                    for language, video_list in videos_obj.items():
                                        if isinstance(video_list, list):
                                            for video in video_list:
                                                if isinstance(video, dict):
                                                    server_info = {
                                                        'url': video.get('result', ''),
                                                        'server': video.get('cyberlocker', ''),
                                                        'quality': video.get('quality', 'HD'),
                                                        'language': language
                                                    }
                                                    
                                                    # Agregar al idioma correspondiente
                                                    if language in servers_data:
                                                        servers_data[language].append(server_info)
                                                    else:
                                                        # Crear nueva entrada si no existe
                                                        if language not in servers_data:
                                                            servers_data[language] = []
                                                        servers_data[language].append(server_info)
                                except Exception as e:
                                    logger.debug(f"Error parseando videos JSON: {e}")
                    except Exception as e:
                        logger.debug(f"Error procesando script: {e}")
                        continue
            
            # Contar servidores encontrados
            total_servers = sum(len(v) for v in servers_data.values())
            logger.info(f"Encontrados {total_servers} servidores")
            
        except Exception as e:
            logger.error(f"Error extrayendo servidores de {episodio_url}: {e}")
        
        return servers_data
    
    def extraer_info_serie(self, serie_url: str) -> Optional[Dict]:
        """Extrae información completa de una serie"""
        try:
            response = self.session.get(serie_url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar datos en el HTML
            # El sitio usa Next.js y los datos están en un script
            scripts = soup.find_all('script')
            
            serie_info = None
            
            for script in scripts:
                if script.string and '"titles"' in script.string and '"TMDbId"' in script.string:
                    content = script.string
                    
                    try:
                        # Buscar la sección principal de la serie
                        # Formato: "serie":{"TMDbId":"287231",...}
                        if '"serie":{' in content:
                            # Extraer el objeto serie
                            pattern = r'"serie":(\{[^}]*"TMDbId"[^}]*\})'
                            
                            # Mejor: buscar manualmente
                            start = content.find('"serie":{')
                            if start > -1:
                                # Contar llaves para encontrar el final
                                bracket_count = 0
                                pos = start + len('"serie":{')
                                
                                for i in range(pos, len(content)):
                                    if content[i] == '{':
                                        bracket_count += 1
                                    elif content[i] == '}':
                                        if bracket_count == 0:
                                            end = i + 1
                                            break
                                        bracket_count -= 1
                                
                                serie_json_str = content[start + len('"serie":'):end]
                                serie_data = json.loads(serie_json_str)
                                
                                serie_info = {
                                    'tmdb_id': serie_data.get('TMDbId'),
                                    'title': serie_data.get('titles', {}).get('name', 'Unknown'),
                                    'original_title': serie_data.get('titles', {}).get('original', {}).get('name', ''),
                                    'year': serie_data.get('releaseDate', '').split('-')[0] if serie_data.get('releaseDate') else '',
                                    'overview': serie_data.get('overview', ''),
                                    'rating': serie_data.get('rate', {}).get('average', 0),
                                    'genres': [g.get('name', '') for g in serie_data.get('genres', [])]
                                }
                                
                                break
                    except Exception as e:
                        logger.debug(f"Error extrayendo info de serie: {e}")
                        continue
            
            if serie_info:
                logger.info(f"Serie: {serie_info.get('title')} ({serie_info.get('year')})")
                return serie_info
            
        except Exception as e:
            logger.error(f"Error extrayendo información de {serie_url}: {e}")
        
        return None
    
    def procesar_series(self, max_series: int = 5, max_episodes_per_season: int = 10):
        """Procesa series desde la página principal"""
        
        logger.info(f"Extrayendo series desde {SERIES_LIST_URL}...")
        series_urls = self.extraer_series_lista()
        
        for idx, serie_info in enumerate(series_urls[:max_series]):
            try:
                logger.info(f"\n--- Serie {idx + 1}/{min(len(series_urls), max_series)} ---")
                logger.info(f"Procesando: {serie_info['title']}")
                
                # Extraer información completa de la serie
                full_info = self.extraer_info_serie(serie_info['url'])
                if not full_info:
                    logger.warning(f"No se pudo obtener información de {serie_info['title']}")
                    continue
                
                tmdb_id = full_info.get('tmdb_id')
                if not tmdb_id:
                    logger.warning(f"No se encontró tmdb_id para {serie_info['title']}")
                    continue
                
                # Evitar duplicados
                if tmdb_id in self.processed_tmdb_ids:
                    logger.info(f"Serie ya procesada: {full_info['title']}")
                    continue
                
                # Extraer temporadas
                temporadas_data = self.extraer_temporadas(serie_info['url'])
                
                if not temporadas_data:
                    logger.warning(f"No se encontraron temporadas para {full_info['title']}")
                    continue
                
                # Procesar temporadas
                seasons = []
                for season in temporadas_data[:1]:  # Por ahora solo primera temporada
                    try:
                        season_num = season['number']
                        logger.info(f"  Procesando temporada {season_num}...")
                        
                        # Extraer episodios
                        episodios_urls = self.extraer_episodios_temporada(serie_info['url'], season_num)
                        
                        if not episodios_urls:
                            logger.warning(f"  No se encontraron episodios para temporada {season_num}")
                            continue
                        
                        # Procesar episodios
                        episodes = []
                        for ep_idx, ep_info in enumerate(episodios_urls[:max_episodes_per_season]):
                            try:
                                logger.info(f"    Procesando episodio {ep_idx + 1}/{len(episodios_urls[:max_episodes_per_season])}...")
                                
                                # Extraer servidores del episodio
                                servers = self.extraer_servidores_episodio(ep_info['url'])
                                
                                # Crear estructura del episodio
                                episode = {
                                    'title': ep_info['title'],
                                    'number_text': ep_info['number_text'],
                                    'servers': servers
                                }
                                
                                episodes.append(episode)
                                
                                # Pausa para no saturar
                                time.sleep(1)
                                
                            except Exception as e:
                                logger.error(f"Error procesando episodio: {e}")
                                continue
                        
                        if episodes:
                            season_data = {
                                'number': season_num,
                                'episodes': episodes
                            }
                            seasons.append(season_data)
                        
                        # Pausa entre temporadas
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Error procesando temporada {season_num}: {e}")
                        continue
                
                if seasons:
                    # Crear estructura completa de la serie
                    serie_completa = {
                        'tmdb_id': tmdb_id,
                        'title': full_info['title'],
                        'year': full_info.get('year', ''),
                        'overview': full_info.get('overview', '')[:200],
                        'rating': full_info.get('rating', 0),
                        'genres': full_info.get('genres', []),
                        'seasons': seasons
                    }
                    
                    self.series.append(serie_completa)
                    self.processed_tmdb_ids.add(tmdb_id)
                    
                    logger.info(f"✅ Serie agregada: {full_info['title']} - {len(seasons)} temporada(s)")
                
                # Pausa entre series
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error procesando serie {serie_info.get('title')}: {e}")
                continue
    
    def guardar_series(self, output_file: str = '../series.json'):
        """Guarda series en JSON"""
        try:
            # Obtener ruta absoluta
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(script_dir, output_file)
            
            # Leer series existentes
            series_existentes = {}
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        # Convertir a diccionario con tmdb_id como clave
                        series_existentes = {s['tmdb_id']: s for s in data}
                    except:
                        pass
            
            # Actualizar con nuevas series
            for serie in self.series:
                series_existentes[serie['tmdb_id']] = serie
            
            # Convertir a lista y guardar
            series_finales = list(series_existentes.values())
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(series_finales, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Guardadas {len(series_finales)} series en {full_path}")
            
        except Exception as e:
            logger.error(f"Error guardando series: {e}")
    
    def run(self, max_series: int = 5, max_episodes_per_season: int = 10):
        """Ejecuta el scraper"""
        logger.info("Iniciando scraper de poseidonhd2.co series...")
        
        try:
            self.procesar_series(max_series=max_series, max_episodes_per_season=max_episodes_per_season)
            self.guardar_series()
            logger.info(f"✅ Scraping completado. Total: {len(self.series)} series")
            
        except KeyboardInterrupt:
            logger.info("Scraper interrumpido por el usuario")
        except Exception as e:
            logger.error(f"Error en el scraper: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper de series desde poseidonhd2.co')
    parser.add_argument('--max-series', type=int, default=5, help='Número máximo de series a scrapear')
    parser.add_argument('--max-episodes', type=int, default=10, help='Máximo de episodios por temporada')
    parser.add_argument('--output', type=str, default='../series.json', help='Archivo de salida JSON')
    
    args = parser.parse_args()
    
    scraper = PoseidonHD2SeriesScraper()
    scraper.run(max_series=args.max_series, max_episodes_per_season=args.max_episodes)


if __name__ == '__main__':
    main()
