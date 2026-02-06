"""
Scraper de enriquecimiento de metadata para series, películas y anime
Agrega: poster_url, backdrop_url, géneros en español
Usa TMDB API para obtener la información adicional
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

class MetadataEnricher:
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
        
        # Contadores para estadísticas
        self.enriched_count = 0
        self.error_count = 0
    
    def get_tmdb_details(self, tmdb_id: Union[str, int], media_type: str = "movie") -> Optional[Dict]:
        """
        Obtiene detalles de TMDB incluyendo poster, backdrop y géneros en español
        
        Args:
            tmdb_id: ID de TMDB
            media_type: 'movie' o 'tv'
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
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red al obtener TMDB ID {tmdb_id}: {e}")
            self.error_count += 1
            return None
        except ValueError as e:
            logger.error(f"Error de formato TMDB ID {tmdb_id}: {e}")
            self.error_count += 1
            return None
        except Exception as e:
            logger.error(f"Error inesperado al obtener TMDB ID {tmdb_id}: {e}")
            self.error_count += 1
            return None

    def enrich_item(self, item: Dict, media_type: str) -> Dict:
        """
        Enriquece un elemento individual con metadata de TMDB
        """
        if not item.get('tmdb_id'):
            logger.warning(f"Elemento sin tmdb_id: {item.get('title', 'Desconocido')}")
            return item
        
        # Verificar si ya tiene metadata enriquecida
        if item.get('poster_url') and item.get('backdrop_url') and item.get('genres_spanish'):
            logger.debug(f"Elemento ya enriquecido: {item.get('title')}")
            return item
        
        logger.info(f"Enriqueciendo: {item.get('title')} (ID: {item['tmdb_id']})")
        
        # Obtener detalles de TMDB
        details = self.get_tmdb_details(item['tmdb_id'], media_type)
        
        if details:
            # Agregar nueva información manteniendo la existente
            enriched_item = item.copy()
            enriched_item.update({
                'poster_url': details['poster_url'],
                'backdrop_url': details['backdrop_url'],
                'genres_spanish': details['genres_spanish']
            })
            
            # Actualizar overview si está disponible en español y no existe o está vacío
            if details.get('overview_spanish') and not item.get('overview'):
                enriched_item['overview'] = details['overview_spanish']
            
            # Actualizar rating si no existe
            if not item.get('rating') and details.get('vote_average'):
                enriched_item['rating'] = details['vote_average']
            
            self.enriched_count += 1
            logger.info(f"✓ Enriquecido: {item.get('title')}")
            
            # Pequeña pausa para no saturar la API
            time.sleep(0.25)
            
            return enriched_item
        else:
            logger.warning(f"No se pudo enriquecer: {item.get('title')}")
            return item

    def enrich_movies(self) -> bool:
        """Enriquece el archivo de películas"""
        try:
            logger.info("=== ENRIQUECIENDO PELÍCULAS ===")
            
            # Leer archivo de películas
            with open(self.movies_file, 'r', encoding='utf-8') as f:
                movies = json.load(f)
            
            logger.info(f"Procesando {len(movies)} películas...")
            
            # Enriquecer cada película
            enriched_movies = []
            for i, movie in enumerate(movies):
                logger.info(f"Progreso películas: {i+1}/{len(movies)}")
                enriched_movie = self.enrich_item(movie, 'movie')
                enriched_movies.append(enriched_movie)
            
            # Guardar archivo actualizado
            backup_file = self.movies_file.replace('.json', '_backup.json')
            os.rename(self.movies_file, backup_file)
            logger.info(f"Backup guardado: {backup_file}")
            
            with open(self.movies_file, 'w', encoding='utf-8') as f:
                json.dump(enriched_movies, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Películas enriquecidas y guardadas: {self.movies_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando películas: {e}")
            return False

    def enrich_series(self) -> bool:
        """Enriquece el archivo de series"""
        try:
            logger.info("=== ENRIQUECIENDO SERIES ===")
            
            # Leer archivo de series
            with open(self.series_file, 'r', encoding='utf-8') as f:
                series = json.load(f)
            
            logger.info(f"Procesando {len(series)} series...")
            
            # Enriquecer cada serie
            enriched_series = []
            for i, serie in enumerate(series):
                logger.info(f"Progreso series: {i+1}/{len(series)}")
                enriched_serie = self.enrich_item(serie, 'tv')
                enriched_series.append(enriched_serie)
            
            # Guardar archivo actualizado
            backup_file = self.series_file.replace('.json', '_backup.json')
            os.rename(self.series_file, backup_file)
            logger.info(f"Backup guardado: {backup_file}")
            
            with open(self.series_file, 'w', encoding='utf-8') as f:
                json.dump(enriched_series, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Series enriquecidas y guardadas: {self.series_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando series: {e}")
            return False

    def enrich_anime(self) -> bool:
        """Enriquece el archivo de anime"""
        try:
            logger.info("=== ENRIQUECIENDO ANIME ===")
            
            # Leer archivo de anime
            with open(self.anime_file, 'r', encoding='utf-8') as f:
                animes = json.load(f)
            
            logger.info(f"Procesando {len(animes)} animes...")
            
            # Enriquecer cada anime
            enriched_animes = []
            for i, anime in enumerate(animes):
                logger.info(f"Progreso anime: {i+1}/{len(animes)}")
                enriched_anime = self.enrich_item(anime, 'tv')
                enriched_animes.append(enriched_anime)
            
            # Guardar archivo actualizado
            backup_file = self.anime_file.replace('.json', '_backup.json')
            os.rename(self.anime_file, backup_file)
            logger.info(f"Backup guardado: {backup_file}")
            
            with open(self.anime_file, 'w', encoding='utf-8') as f:
                json.dump(enriched_animes, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Anime enriquecido y guardado: {self.anime_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando anime: {e}")
            return False

    def run_enrichment(self):
        """Ejecuta el proceso completo de enriquecimiento"""
        start_time = datetime.now()
        logger.info("🚀 INICIANDO ENRIQUECIMIENTO DE METADATA")
        
        # Resetear contadores
        self.enriched_count = 0
        self.error_count = 0
        
        try:
            # Verificar archivos existentes
            files_to_check = [self.movies_file, self.series_file, self.anime_file]
            for file_path in files_to_check:
                if not os.path.exists(file_path):
                    logger.error(f"Archivo no encontrado: {file_path}")
                    return False
            
            # Procesar cada tipo de contenido
            success_movies = self.enrich_movies()
            success_series = self.enrich_series()
            success_anime = self.enrich_anime()
            
            # Mostrar estadísticas finales
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=" * 50)
            logger.info("📊 ESTADÍSTICAS FINALES")
            logger.info(f"• Elementos enriquecidos: {self.enriched_count}")
            logger.info(f"• Errores encontrados: {self.error_count}")
            logger.info(f"• Duración total: {duration}")
            logger.info(f"• Películas: {'✓' if success_movies else '✗'}")
            logger.info(f"• Series: {'✓' if success_series else '✗'}")
            logger.info(f"• Anime: {'✓' if success_anime else '✗'}")
            logger.info("=" * 50)
            
            if success_movies and success_series and success_anime:
                logger.info("🎉 ¡ENRIQUECIMIENTO COMPLETADO EXITOSAMENTE!")
                return True
            else:
                logger.error("❌ Algunos procesos fallaron")
                return False
                
        except Exception as e:
            logger.error(f"Error crítico en enriquecimiento: {e}")
            return False

def main():
    """Función principal"""
    try:
        enricher = MetadataEnricher()
        success = enricher.run_enrichment()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario")
        return 1
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        return 1

if __name__ == "__main__":
    exit(main())