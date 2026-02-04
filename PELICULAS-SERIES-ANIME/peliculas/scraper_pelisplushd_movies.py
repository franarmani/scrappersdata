"""
Scraper de películas desde verpeliculasultra.com
Extrae: título, año, servidores disponibles
Busca tmdb_id en TMDB
Guarda estructura simplificada: {tmdb_id, title, year, servers}
Con sincronización automática a GitHub y Supabase
"""

import json
import time
import logging
from urllib.parse import urljoin
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import sys
import subprocess
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración TMDB
TMDB_API_KEY = "201d333198374a91c81dba3c443b1a8e"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

class VerpeliculasUltraaScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.movies = []
        self.processed_tmdb_ids = set()
        
    def buscar_tmdb(self, title: str, year: str) -> Optional[Dict]:
        """Busca película en TMDB y retorna su información"""
        try:
            # Limpiar título para búsqueda
            search_title = title.split('(')[0].strip() if '(' in title else title
            
            params = {
                'api_key': TMDB_API_KEY,
                'query': search_title,
                'language': 'es-ES',
                'page': 1
            }
            
            response = self.session.get(f"{TMDB_BASE_URL}/search/movie", params=params, timeout=10)
            response.raise_for_status()
            
            results = response.json().get('results', [])
            
            if not results:
                logger.warning(f"No se encontró en TMDB: {search_title}")
                return None
            
            # Buscar coincidencia por año si está disponible
            best_match = None
            for movie in results:
                release_date = movie.get('release_date', '')
                movie_year = release_date.split('-')[0] if release_date else ''
                
                # Coincidir por año si está disponible
                if year and movie_year == year:
                    best_match = movie
                    break
            
            # Si no hay coincidencia de año, usar el primer resultado
            best_match = best_match or results[0]
            
            return {
                'tmdb_id': best_match.get('id'),
                'title': best_match.get('title'),
                'year': best_match.get('release_date', '').split('-')[0] if best_match.get('release_date') else year
            }
            
        except Exception as e:
            logger.error(f"Error buscando en TMDB '{title}': {e}")
            return None
    
    def extraer_servidores(self, url: str) -> List[Dict]:
        """Extrae servidores y sus URLs de la página de película"""
        servidores = []
        servidores_vistos = set()
        
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar todos los tabs con sus idiomas
            tabs_sidebar = soup.find('div', class_='tabs-sidebar')
            if not tabs_sidebar:
                logger.warning(f"No se encontró tabs-sidebar en {url}")
                return servidores
            
            # Obtener los tabs ul li para extraer idiomas
            tabs_ul = tabs_sidebar.find('ul', class_='tabs-sidebar-ul')
            idiomas_info = {}
            
            if tabs_ul:
                for idx, li in enumerate(tabs_ul.find_all('li')):
                    link = li.find('a')
                    if link:
                        href = link.get('href')
                        span = link.find('span')
                        idioma = span.get_text(strip=True) if span else f"Tab {idx}"
                        if href and href.startswith('#'):
                            tab_id = href[1:]  # Quitar el #
                            idiomas_info[tab_id] = idioma
            
            # Buscar los bloques de tabs
            tabs_blocks = tabs_sidebar.find_all('div', class_='tabs-sidebar-block')
            
            for block in tabs_blocks:
                block_id = block.get('id', '')
                idioma = idiomas_info.get(block_id, 'Desconocido')
                
                # Buscar el mejs-container
                video_div = block.find('div', class_='mejs-container')
                if video_div:
                    data_src = video_div.get('data-src')
                    if data_src:
                        # Extraer información del servidor
                        from urllib.parse import urlparse
                        parsed = urlparse(data_src)
                        domain = parsed.netloc.replace('www.', '')
                        
                        # Crear clave única para evitar duplicados exactos
                        key = f"{domain}|{data_src}"
                        
                        if key not in servidores_vistos:
                            servidor_info = {
                                'url': data_src,
                                'server': domain,
                                'language': idioma
                            }
                            servidores.append(servidor_info)
                            servidores_vistos.add(key)
            
            logger.info(f"Servidores encontrados: {len(servidores)} ({', '.join([s['server'] for s in servidores])})")
            
        except Exception as e:
            logger.error(f"Error extrayendo servidores de {url}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return servidores
    
    def extraer_película_info(self, url: str) -> Optional[Dict]:
        """Extrae información de una película desde su página individual"""
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar título en #bar-film
            bar_film = soup.find('section', id='bar-film')
            if not bar_film:
                logger.warning(f"No se encontró #bar-film en {url}")
                return None
            
            # Extraer título
            titulo_elem = bar_film.find('span', class_='f-info-text')
            titulo = titulo_elem.get_text(strip=True) if titulo_elem else None
            
            if not titulo:
                logger.warning(f"No se encontró título en {url}")
                return None
            
            # Extraer año
            year_elem = None
            for li in bar_film.find_all('li'):
                span_title = li.find('span', class_='f-info-title')
                if span_title and 'Año' in span_title.get_text():
                    year_elem = li.find('span', class_='f-info-text')
                    break
            
            year = year_elem.get_text(strip=True) if year_elem else ''
            
            logger.info(f"Película encontrada: {titulo} ({year})")
            
            return {
                'title': titulo,
                'year': year,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo información de {url}: {e}")
            return None
    
    def extraer_grid_películas(self, page_url: str) -> List[Dict]:
        """Extrae URLs de películas desde la página de grid"""
        películas = []
        try:
            response = self.session.get(page_url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar todos los divs con clase shortf
            shortf_divs = soup.find_all('div', class_='shortf')
            
            logger.info(f"Se encontraron {len(shortf_divs)} películas en la página")
            
            for shortf in shortf_divs:
                # Buscar el link de la película
                link_elem = shortf.find('a', href=True)
                if link_elem and link_elem.get('href'):
                    url = link_elem['href']
                    películas.append({'url': url})
            
            logger.info(f"Extraídas {len(películas)} URLs de películas")
            
        except Exception as e:
            logger.error(f"Error extrayendo grid de {page_url}: {e}")
        
        return películas
    
    def procesar_películas(self, page_url: str = "https://verpeliculasultra.com/lastnews/", max_pages: int = 1):
        """Procesa películas desde las páginas de grid"""
        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                url = page_url
            else:
                url = f"{page_url}page/{page_num}/"
            
            logger.info(f"Procesando página {page_num}: {url}")
            
            # Extraer URLs del grid
            películas_urls = self.extraer_grid_películas(url)
            
            for idx, película_info in enumerate(películas_urls):
                try:
                    logger.info(f"Procesando película {idx + 1}/{len(películas_urls)}")
                    
                    # Extraer información de la película
                    info = self.extraer_película_info(película_info['url'])
                    if not info:
                        continue
                    
                    # Buscar en TMDB
                    tmdb_info = self.buscar_tmdb(info['title'], info['year'])
                    if not tmdb_info or not tmdb_info.get('tmdb_id'):
                        logger.warning(f"No se encontró tmdb_id para {info['title']}")
                        continue
                    
                    # Evitar duplicados
                    if tmdb_info['tmdb_id'] in self.processed_tmdb_ids:
                        logger.info(f"Película ya procesada: {tmdb_info['title']}")
                        continue
                    
                    # Extraer servidores
                    servidores = self.extraer_servidores(película_info['url'])
                    
                    # Crear estructura simplificada
                    película = {
                        'tmdb_id': tmdb_info['tmdb_id'],
                        'title': tmdb_info['title'],
                        'year': tmdb_info['year'],
                        'servers': servidores
                    }
                    
                    self.movies.append(película)
                    self.processed_tmdb_ids.add(tmdb_info['tmdb_id'])
                    
                    logger.info(f"Película añadida: {película['title']} ({película['year']}) - Servidores: {len(servidores)}")
                    
                    # Pequeña pausa para no saturar servidores
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error procesando película {película_info.get('url')}: {e}")
                    continue
            
            # Pausa entre páginas
            time.sleep(2)
    
    def guardar_películas(self, output_file: str = '../peliculas.json'):
        """Guarda películas en JSON con estructura simplificada"""
        try:
            # Obtener ruta absoluta
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(script_dir, output_file)
            
            # Leer películas existentes
            películas_existentes = {}
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        # Convertir a diccionario con tmdb_id como clave
                        películas_existentes = {p['tmdb_id']: p for p in data}
                    except:
                        pass
            
            # Actualizar con nuevas películas
            for película in self.movies:
                películas_existentes[película['tmdb_id']] = película
            
            # Convertir a lista y guardar
            películas_finales = list(películas_existentes.values())
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(películas_finales, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Guardadas {len(películas_finales)} películas en {full_path}")
            
        except Exception as e:
            logger.error(f"Error guardando películas: {e}")
    
    def run(self, max_pages: int = 1):
        """Ejecuta el scraper"""
        logger.info("Iniciando scraper de verpeliculasultra.com...")
        
        try:
            self.procesar_películas(max_pages=max_pages)
            self.guardar_películas()
            logger.info(f"✅ Scraping completado. Total: {len(self.movies)} películas")
            
            # Sincronizar automáticamente con GitHub y Supabase
            self.sync_to_github()
            self.sync_to_supabase()
            
        except KeyboardInterrupt:
            logger.info("Scraper interrumpido por el usuario")
        except Exception as e:
            logger.error(f"Error en el scraper: {e}")
    
    def sync_to_github(self):
        """Sincroniza automáticamente con GitHub"""
        try:
            logger.info("\n🚀 SINCRONIZANDO CON GITHUB")
            logger.info("=" * 40)
            
            # Obtener ruta del proyecto raíz
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
            
            # Cambiar a directorio del proyecto
            os.chdir(project_root)
            
            # Ejecutar comandos git
            logger.info("📝 Preparando cambios...")
            subprocess.run(['git', 'add', 'PELICULAS-SERIES-ANIME/peliculas.json'], 
                          check=True, capture_output=True)
            
            # Crear commit con timestamp
            commit_msg = f"Update: peliculas.json - {len(self.movies)} movies from verpeliculasultra.com [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
            result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Commit creado: {commit_msg[:50]}...")
            else:
                logger.warning("⚠️ No hay cambios para commit o ya existe")
                return
            
            # Pull remoto para traer cambios
            logger.info("📥 Trayendo cambios del remoto...")
            subprocess.run(['git', 'pull', 'origin', 'master', '--rebase'], 
                          check=False, capture_output=True)
            
            # Push a remoto
            logger.info("📤 Subiendo a GitHub...")
            result = subprocess.run(['git', 'push', 'origin', 'master'], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("🎉 ¡Push a GitHub exitoso!")
            else:
                logger.error(f"❌ Error en push: {result.stderr}")
        
        except subprocess.CalledProcessError as e:
            logger.error(f"⚠️ Error ejecutando git: {e}")
            logger.info("💡 Git command failed, but JSON saved successfully")
        except Exception as e:
            logger.error(f"⚠️ Error sincronizando con GitHub: {e}")
            logger.info("💡 JSON file saved successfully")
    
    def sync_to_supabase(self):
        """Sincroniza automáticamente con Supabase"""
        try:
            logger.info(f"\n🚀 SINCRONIZANDO CON SUPABASE")
            logger.info("=" * 40)
            
            # Importar módulo de sincronización
            from sync_movies_supabase import MoviesSuabaseSync
            
            # Crear instancia del sincronizador
            supabase_sync = MoviesSuabaseSync()
            
            # Inicializar conexión a Supabase
            if not supabase_sync.initialize_supabase():
                logger.error("❌ No se pudo inicializar la conexión a Supabase")
                return
            
            # Leer películas del archivo
            script_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(script_dir, '../peliculas.json')
            
            with open(json_path, 'r', encoding='utf-8') as f:
                movies = json.load(f)
            
            # Sincronizar películas
            success = supabase_sync.sync_movies_to_supabase(movies)
            
            if success:
                logger.info("🎉 ¡Películas sincronizadas con Supabase exitosamente!")
            else:
                logger.warning("⚠️ Error durante la sincronización con Supabase")
                
        except ImportError:
            logger.warning("⚠️ Módulo de sincronización Supabase no disponible")
            logger.info("💡 Instala las dependencias: pip install supabase python-dotenv")
        except FileNotFoundError:
            logger.error("⚠️ Archivo peliculas.json no encontrado")
        except Exception as e:
            error_msg = str(e)
            if "getaddrinfo failed" in error_msg:
                logger.warning("⚠️ Sin conexión a internet, sincronización omitida")
                logger.info("💡 El archivo JSON se guardó correctamente")
            else:
                logger.error(f"⚠️ Error sincronizando con Supabase: {e}")
                logger.info("💡 El archivo JSON se guardó correctamente")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper de películas desde verpeliculasultra.com')
    parser.add_argument('--max-pages', type=int, default=1, help='Número máximo de páginas a scrapear')
    parser.add_argument('--output', type=str, default='../peliculas.json', help='Archivo de salida JSON')
    
    args = parser.parse_args()
    
    scraper = VerpeliculasUltraaScraper()
    scraper.run(max_pages=args.max_pages)


if __name__ == '__main__':
    main()
