"""
Versión de prueba del enriquecedor de metadata
Procesa solo los primeros N elementos de cada categoría para testing
"""

import json
import time
import logging
from typing import List, Dict, Optional, Union
import requests
from datetime import datetime
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración TMDB
TMDB_API_KEY = "201d333198374a91c81dba3c443b1a8e"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Configuración de prueba
TEST_LIMIT = 3  # Procesar solo los primeros 3 elementos de cada tipo

class MetadataEnricherTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Rutas de archivos
        self.base_path = r"c:\Users\franc\Desktop\SCRAPPERS\PELICULAS-SERIES-ANIME"
        self.series_file = os.path.join(self.base_path, "series.json")
        self.movies_file = os.path.join(self.base_path, "peliculas.json")
        self.anime_file = os.path.join(self.base_path, "anime.json")
    
    def get_tmdb_details(self, tmdb_id: Union[str, int], media_type: str = "movie") -> Optional[Dict]:
        """
        Obtiene detalles de TMDB incluyendo poster, backdrop y géneros en español
        """
        try:
            # Convertir a int si es string
            tmdb_id = int(tmdb_id) if isinstance(tmdb_id, str) else tmdb_id
            
            # URL para obtener detalles con idioma español
            url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}"
            params = {
                'api_key': TMDB_API_KEY,
                'language': 'es-ES'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extraer información relevante
            details = {
                'poster_url': f"{TMDB_IMAGE_BASE_URL}{data['poster_path']}" if data.get('poster_path') else None,
                'backdrop_url': f"{TMDB_IMAGE_BASE_URL}{data['backdrop_path']}" if data.get('backdrop_path') else None,
                'genres_spanish': [genre['name'] for genre in data.get('genres', [])],
                'overview_spanish': data.get('overview', ''),
                'vote_average': data.get('vote_average', 0)
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error al obtener TMDB ID {tmdb_id}: {e}")
            return None

    def test_single_item(self, item: Dict, media_type: str) -> None:
        """
        Prueba el enriquecimiento de un solo elemento y muestra los resultados
        """
        if not item.get('tmdb_id'):
            print(f"❌ Sin TMDB ID: {item.get('title', 'Desconocido')}")
            return
        
        print(f"\n📝 Probando: {item.get('title')} (ID: {item['tmdb_id']})")
        print(f"   Tipo: {media_type}")
        print("   Datos originales:")
        print(f"     - Título: {item.get('title')}")
        print(f"     - Año: {item.get('year')}")
        print(f"     - Géneros actuales: {item.get('genres', [])}")
        print(f"     - Rating actual: {item.get('rating', 'N/A')}")
        
        # Obtener detalles de TMDB
        details = self.get_tmdb_details(item['tmdb_id'], media_type)
        
        if details:
            print("   ✅ Datos obtenidos de TMDB:")
            print(f"     - Poster: {details['poster_url']}")
            print(f"     - Backdrop: {details['backdrop_url']}")
            print(f"     - Géneros en español: {details['genres_spanish']}")
            print(f"     - Rating TMDB: {details['vote_average']}")
            if details['overview_spanish']:
                print(f"     - Sinopsis (primeras 100 chars): {details['overview_spanish'][:100]}...")
        else:
            print("   ❌ No se pudieron obtener datos de TMDB")
        
        time.sleep(1)  # Pausa entre requests

    def test_movies(self) -> None:
        """Prueba el enriquecimiento de películas"""
        try:
            print("\n" + "="*50)
            print("🎬 PROBANDO PELÍCULAS")
            print("="*50)
            
            with open(self.movies_file, 'r', encoding='utf-8') as f:
                movies = json.load(f)
            
            print(f"Total de películas disponibles: {len(movies)}")
            print(f"Probando con las primeras {TEST_LIMIT} películas...")
            
            for i, movie in enumerate(movies[:TEST_LIMIT]):
                print(f"\n--- Película {i+1}/{TEST_LIMIT} ---")
                self.test_single_item(movie, 'movie')
                
        except Exception as e:
            print(f"❌ Error probando películas: {e}")

    def test_series(self) -> None:
        """Prueba el enriquecimiento de series"""
        try:
            print("\n" + "="*50)
            print("📺 PROBANDO SERIES")
            print("="*50)
            
            with open(self.series_file, 'r', encoding='utf-8') as f:
                series = json.load(f)
            
            print(f"Total de series disponibles: {len(series)}")
            print(f"Probando con las primeras {TEST_LIMIT} series...")
            
            for i, serie in enumerate(series[:TEST_LIMIT]):
                print(f"\n--- Serie {i+1}/{TEST_LIMIT} ---")
                self.test_single_item(serie, 'tv')
                
        except Exception as e:
            print(f"❌ Error probando series: {e}")

    def test_anime(self) -> None:
        """Prueba el enriquecimiento de anime"""
        try:
            print("\n" + "="*50)
            print("🎌 PROBANDO ANIME")
            print("="*50)
            
            with open(self.anime_file, 'r', encoding='utf-8') as f:
                animes = json.load(f)
            
            print(f"Total de animes disponibles: {len(animes)}")
            print(f"Probando con los primeros {TEST_LIMIT} animes...")
            
            for i, anime in enumerate(animes[:TEST_LIMIT]):
                print(f"\n--- Anime {i+1}/{TEST_LIMIT} ---")
                self.test_single_item(anime, 'tv')
                
        except Exception as e:
            print(f"❌ Error probando anime: {e}")

    def run_test(self):
        """Ejecuta todas las pruebas"""
        print("🧪 INICIANDO PRUEBAS DE ENRIQUECIMIENTO DE METADATA")
        print(f"Configuración: Procesando {TEST_LIMIT} elementos de cada tipo")
        
        start_time = datetime.now()
        
        try:
            # Verificar archivos
            files_to_check = [
                (self.movies_file, "películas"),
                (self.series_file, "series"),
                (self.anime_file, "anime")
            ]
            
            for file_path, name in files_to_check:
                if not os.path.exists(file_path):
                    print(f"❌ Archivo de {name} no encontrado: {file_path}")
                    return False
                else:
                    print(f"✅ Archivo de {name} encontrado")
            
            # Ejecutar pruebas
            self.test_movies()
            self.test_series()
            self.test_anime()
            
            # Estadísticas finales
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "="*50)
            print("📊 RESUMEN DE PRUEBAS")
            print("="*50)
            print(f"✅ Pruebas completadas en: {duration}")
            print(f"📝 Se probaron {TEST_LIMIT} elementos de cada tipo")
            print("🚀 Si las pruebas se ven bien, ejecuta el script completo")
            print("   usando: python enrich_metadata_scraper.py")
            
            return True
            
        except Exception as e:
            print(f"❌ Error crítico en las pruebas: {e}")
            return False

def main():
    """Función principal"""
    try:
        tester = MetadataEnricherTest()
        success = tester.run_test()
        
        if success:
            print("\n🎉 Pruebas completadas exitosamente!")
            print("\nPara ejecutar el enriquecimiento completo:")
            print("    python enrich_metadata_scraper.py")
            print("    o ejecuta: run_metadata_enricher.bat")
        else:
            print("\n❌ Las pruebas fallaron")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nPruebas interrumpidas por el usuario")
        return 1
    except Exception as e:
        print(f"Error fatal: {e}")
        return 1

if __name__ == "__main__":
    exit(main())