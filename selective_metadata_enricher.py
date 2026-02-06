"""
Enriquecedor selectivo de metadata
Permite procesar solo ciertos tipos de contenido o rangos específicos
"""

import json
import time
import logging
from typing import List, Dict, Optional, Union
import requests
import argparse
from datetime import datetime
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración TMDB
TMDB_API_KEY = "201d333198374a91c81dba3c443b1a8e"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

class SelectiveMetadataEnricher:
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
        
        self.enriched_count = 0
        self.error_count = 0
    
    def get_tmdb_details(self, tmdb_id: Union[str, int], media_type: str = "movie") -> Optional[Dict]:
        """Obtiene detalles de TMDB"""
        try:
            tmdb_id = int(tmdb_id) if isinstance(tmdb_id, str) else tmdb_id
            
            url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}"
            params = {
                'api_key': TMDB_API_KEY,
                'language': 'es-ES'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
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
            self.error_count += 1
            return None

    def enrich_item(self, item: Dict, media_type: str, force_update: bool = False) -> Dict:
        """Enriquece un elemento individual"""
        if not item.get('tmdb_id'):
            return item
        
        # Verificar si ya está enriquecido (a menos que force_update sea True)
        if not force_update and item.get('poster_url') and item.get('backdrop_url'):
            logger.debug(f"Ya enriquecido (saltando): {item.get('title')}")
            return item
        
        logger.info(f"Enriqueciendo: {item.get('title')} (ID: {item['tmdb_id']})")
        
        details = self.get_tmdb_details(item['tmdb_id'], media_type)
        
        if details:
            enriched_item = item.copy()
            enriched_item.update({
                'poster_url': details['poster_url'],
                'backdrop_url': details['backdrop_url'],
                'genres_spanish': details['genres_spanish']
            })
            
            if details.get('overview_spanish') and not item.get('overview'):
                enriched_item['overview'] = details['overview_spanish']
            
            if not item.get('rating') and details.get('vote_average'):
                enriched_item['rating'] = details['vote_average']
            
            self.enriched_count += 1
            logger.info(f"✓ Enriquecido: {item.get('title')}")
            time.sleep(0.25)  # Rate limiting
            
            return enriched_item
        else:
            return item

    def enrich_movies(self, start_index: int = 0, end_index: int = None, force_update: bool = False) -> bool:
        """Enriquece películas en un rango específico"""
        try:
            logger.info(f"=== ENRIQUECIENDO PELÍCULAS (índices {start_index}-{end_index or 'fin'}) ===")
            
            with open(self.movies_file, 'r', encoding='utf-8') as f:
                movies = json.load(f)
            
            # Determinar el rango
            end_index = end_index or len(movies)
            movies_to_process = movies[start_index:end_index]
            
            logger.info(f"Procesando {len(movies_to_process)} películas...")
            
            # Enriquecer películas en el rango
            for i, movie in enumerate(movies_to_process):
                abs_index = start_index + i
                logger.info(f"Progreso: {abs_index + 1}/{len(movies)}")
                movies[abs_index] = self.enrich_item(movie, 'movie', force_update)
            
            # Guardar cambios
            backup_file = self.movies_file.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            
            # Crear backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(json.load(open(self.movies_file, 'r', encoding='utf-8')), f, ensure_ascii=False, indent=2)
            
            # Guardar archivo actualizado
            with open(self.movies_file, 'w', encoding='utf-8') as f:
                json.dump(movies, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Películas actualizadas. Backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando películas: {e}")
            return False

    def enrich_series(self, start_index: int = 0, end_index: int = None, force_update: bool = False) -> bool:
        """Enriquece series en un rango específico"""
        try:
            logger.info(f"=== ENRIQUECIENDO SERIES (índices {start_index}-{end_index or 'fin'}) ===")
            
            with open(self.series_file, 'r', encoding='utf-8') as f:
                series = json.load(f)
            
            end_index = end_index or len(series)
            series_to_process = series[start_index:end_index]
            
            logger.info(f"Procesando {len(series_to_process)} series...")
            
            for i, serie in enumerate(series_to_process):
                abs_index = start_index + i
                logger.info(f"Progreso: {abs_index + 1}/{len(series)}")
                series[abs_index] = self.enrich_item(serie, 'tv', force_update)
            
            backup_file = self.series_file.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(json.load(open(self.series_file, 'r', encoding='utf-8')), f, ensure_ascii=False, indent=2)
            
            with open(self.series_file, 'w', encoding='utf-8') as f:
                json.dump(series, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Series actualizadas. Backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando series: {e}")
            return False

    def enrich_anime(self, start_index: int = 0, end_index: int = None, force_update: bool = False) -> bool:
        """Enriquece anime en un rango específico"""
        try:
            logger.info(f"=== ENRIQUECIENDO ANIME (índices {start_index}-{end_index or 'fin'}) ===")
            
            with open(self.anime_file, 'r', encoding='utf-8') as f:
                animes = json.load(f)
            
            end_index = end_index or len(animes)
            animes_to_process = animes[start_index:end_index]
            
            logger.info(f"Procesando {len(animes_to_process)} animes...")
            
            for i, anime in enumerate(animes_to_process):
                abs_index = start_index + i
                logger.info(f"Progreso: {abs_index + 1}/{len(animes)}")
                animes[abs_index] = self.enrich_item(anime, 'tv', force_update)
            
            backup_file = self.anime_file.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(json.load(open(self.anime_file, 'r', encoding='utf-8')), f, ensure_ascii=False, indent=2)
            
            with open(self.anime_file, 'w', encoding='utf-8') as f:
                json.dump(animes, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Anime actualizado. Backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando anime: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Enriquecimiento selectivo de metadata')
    parser.add_argument('--type', choices=['movies', 'series', 'anime', 'all'], 
                       default='all', help='Tipo de contenido a procesar')
    parser.add_argument('--start', type=int, default=0, 
                       help='Índice de inicio (0-based)')
    parser.add_argument('--end', type=int, default=None, 
                       help='Índice de fin (0-based, exclusivo)')
    parser.add_argument('--force', action='store_true', 
                       help='Forzar actualización incluso si ya está enriquecido')
    
    args = parser.parse_args()
    
    enricher = SelectiveMetadataEnricher()
    
    start_time = datetime.now()
    success = True
    
    try:
        logger.info("🚀 INICIANDO ENRIQUECIMIENTO SELECTIVO")
        logger.info(f"Configuración: tipo={args.type}, start={args.start}, end={args.end}, force={args.force}")
        
        if args.type in ['movies', 'all']:
            success &= enricher.enrich_movies(args.start, args.end, args.force)
        
        if args.type in ['series', 'all']:
            success &= enricher.enrich_series(args.start, args.end, args.force)
            
        if args.type in ['anime', 'all']:
            success &= enricher.enrich_anime(args.start, args.end, args.force)
        
        # Estadísticas
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 50)
        logger.info("📊 ESTADÍSTICAS FINALES")
        logger.info(f"• Elementos enriquecidos: {enricher.enriched_count}")
        logger.info(f"• Errores: {enricher.error_count}")
        logger.info(f"• Duración: {duration}")
        logger.info("=" * 50)
        
        if success:
            logger.info("🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        else:
            logger.error("❌ El proceso tuvo errores")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        return 1

if __name__ == "__main__":
    exit(main())