"""
Enriquecedor de metadata TMDB para el repositorio scrappersdata
Agrega poster_url, backdrop_url y genres_spanish a los archivos JSON principales
Versión optimizada para archivos grandes
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

class ScrappersdataEnricher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Archivos en la raíz del repositorio scrappersdata
        self.movies_file = "peliculas.json"
        self.series_file = "series.json" 
        self.anime_file = "anime.json"
        
        self.enriched_count = 0
        self.error_count = 0
        self.skipped_count = 0
    
    def get_tmdb_details(self, tmdb_id: Union[str, int], media_type: str = "movie") -> Optional[Dict]:
        """Obtiene detalles de TMDB incluyendo poster, backdrop y géneros en español"""
        try:
            tmdb_id = int(tmdb_id) if isinstance(tmdb_id, str) else tmdb_id
            
            url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}"
            params = {
                'api_key': TMDB_API_KEY,
                'language': 'es-ES'
            }
            
            response = self.session.get(url, params=params, timeout=10)
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
        """Enriquece un elemento individual con metadata de TMDB"""
        if not item.get('tmdb_id'):
            self.skipped_count += 1
            return item
        
        # Verificar si ya está enriquecido
        if not force_update and item.get('poster_url') and item.get('backdrop_url'):
            self.skipped_count += 1
            return item
        
        details = self.get_tmdb_details(item['tmdb_id'], media_type)
        
        if details:
            # Crear copia y agregar nuevos campos
            enriched_item = item.copy()
            enriched_item.update({
                'poster_url': details['poster_url'],
                'backdrop_url': details['backdrop_url'],
                'genres_spanish': details['genres_spanish']
            })
            
            # Agregar overview en español si no existe o está vacío
            if details.get('overview_spanish') and not item.get('overview'):
                enriched_item['overview'] = details['overview_spanish']
            
            # Agregar rating si no existe
            if not item.get('rating') and details.get('vote_average'):
                enriched_item['rating'] = details['vote_average']
            
            self.enriched_count += 1
            logger.info(f"✓ Enriquecido: {item.get('title', 'Sin título')} (ID: {item['tmdb_id']})")
            
            # Rate limiting
            time.sleep(0.3)
            
            return enriched_item
        else:
            return item

    def enrich_file(self, filename: str, media_type: str, batch_size: int = 50, start_index: int = 0, max_items: int = None) -> bool:
        """
        Enriquece un archivo JSON por lotes
        
        Args:
            filename: Nombre del archivo JSON
            media_type: 'movie' o 'tv' 
            batch_size: Cantidad de elementos a procesar por lote
            start_index: Índice donde empezar
            max_items: Máximo número de elementos a procesar (None = todos)
        """
        try:
            logger.info(f"=== ENRIQUECIENDO {filename.upper()} ===")
            
            # Leer archivo
            if not os.path.exists(filename):
                logger.error(f"Archivo no encontrado: {filename}")
                return False
            
            logger.info(f"Cargando {filename}...")
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_items = len(data)
            logger.info(f"Total de elementos: {total_items}")
            
            # Determinar rango a procesar
            end_index = total_items if max_items is None else min(start_index + max_items, total_items)
            items_to_process = data[start_index:end_index]
            
            logger.info(f"Procesando elementos {start_index}-{end_index-1} ({len(items_to_process)} elementos)")
            
            # Procesar por lotes
            processed = 0
            for i in range(0, len(items_to_process), batch_size):
                batch = items_to_process[i:i+batch_size]
                batch_start = start_index + i
                batch_end = batch_start + len(batch) - 1
                
                logger.info(f"Procesando lote {batch_start}-{batch_end} ({len(batch)} elementos)")
                
                # Enriquecer cada elemento del lote
                for j, item in enumerate(batch):
                    abs_index = batch_start + j
                    enriched_item = self.enrich_item(item, media_type)
                    data[abs_index] = enriched_item
                    processed += 1
                    
                    if processed % 10 == 0:
                        logger.info(f"Progreso: {processed}/{len(items_to_process)} elementos procesados")
                
                # Guardar progreso después de cada lote
                backup_file = f"{filename}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                logger.info(f"Guardando progreso en backup: {backup_file}")
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Guardar archivo final
            logger.info(f"Guardando archivo final: {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ {filename} enriquecido exitosamente!")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando {filename}: {e}")
            return False

    def run_enrichment(self, process_movies=True, process_series=True, process_anime=True, 
                      batch_size=50, max_items_per_type=None):
        """Ejecuta el enriquecimiento completo o selectivo"""
        start_time = datetime.now()
        logger.info("🚀 INICIANDO ENRIQUECIMIENTO SCRAPPERSDATA")
        
        # Resetear contadores
        self.enriched_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
        success = True
        
        try:
            if process_movies:
                success &= self.enrich_file(self.movies_file, 'movie', batch_size, 0, max_items_per_type)
            
            if process_series:
                success &= self.enrich_file(self.series_file, 'tv', batch_size, 0, max_items_per_type)
                
            if process_anime:
                success &= self.enrich_file(self.anime_file, 'tv', batch_size, 0, max_items_per_type)
            
            # Estadísticas finales
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=" * 50)
            logger.info("📊 ESTADÍSTICAS FINALES")
            logger.info(f"• Elementos enriquecidos: {self.enriched_count}")
            logger.info(f"• Elementos saltados: {self.skipped_count}")
            logger.info(f"• Errores: {self.error_count}")
            logger.info(f"• Duración: {duration}")
            logger.info("=" * 50)
            
            if success:
                logger.info("🎉 ¡ENRIQUECIMIENTO COMPLETADO!")
            else:
                logger.error("❌ El proceso tuvo errores")
            
            return success
            
        except Exception as e:
            logger.error(f"Error crítico: {e}")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enriquecimiento de metadata TMDB para scrappersdata')
    parser.add_argument('--movies', action='store_true', help='Procesar solo películas')
    parser.add_argument('--series', action='store_true', help='Procesar solo series')
    parser.add_argument('--anime', action='store_true', help='Procesar solo anime')
    parser.add_argument('--batch-size', type=int, default=50, help='Tamaño del lote (default: 50)')
    parser.add_argument('--max-items', type=int, default=None, help='Máximo elementos por tipo (para pruebas)')
    
    args = parser.parse_args()
    
    # Si no se especifica nada, procesar todo
    if not any([args.movies, args.series, args.anime]):
        process_movies = process_series = process_anime = True
    else:
        process_movies = args.movies
        process_series = args.series
        process_anime = args.anime
    
    enricher = ScrappersdataEnricher()
    success = enricher.run_enrichment(
        process_movies=process_movies,
        process_series=process_series, 
        process_anime=process_anime,
        batch_size=args.batch_size,
        max_items_per_type=args.max_items
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())