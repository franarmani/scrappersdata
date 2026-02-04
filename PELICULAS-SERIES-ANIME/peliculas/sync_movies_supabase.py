"""
Módulo para sincronizar películas con Supabase
Realiza inserciones y actualizaciones automáticas en la base de datos
"""

import json
import logging
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MoviesSuabaseSync:
    def __init__(self):
        self.supabase = None
        self.table_name = 'movies'
        
    def initialize_supabase(self) -> bool:
        """Inicializa la conexión a Supabase"""
        try:
            from supabase import create_client, Client
            
            # Cargar variables de entorno
            load_dotenv()
            
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                logger.error("❌ Variables de entorno SUPABASE_URL o SUPABASE_KEY no configuradas")
                return False
            
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("✅ Conexión a Supabase inicializada")
            return True
            
        except ImportError:
            logger.error("❌ Módulo supabase no instalado")
            return False
        except Exception as e:
            logger.error(f"❌ Error inicializando Supabase: {e}")
            return False
    
    def sync_movies_to_supabase(self, movies: List[Dict]) -> bool:
        """Sincroniza películas con Supabase"""
        if not self.supabase:
            logger.error("❌ Conexión a Supabase no inicializada")
            return False
        
        try:
            total = len(movies)
            inserted = 0
            updated = 0
            errors = 0
            
            logger.info(f"📊 Sincronizando {total} películas...")
            
            for idx, movie in enumerate(movies):
                try:
                    # Preparar datos para inserción
                    movie_data = {
                        'tmdb_id': movie.get('tmdb_id'),
                        'title': movie.get('title'),
                        'year': movie.get('year'),
                        'servers': json.dumps(movie.get('servers', []), ensure_ascii=False),
                        'updated_at': 'now()'
                    }
                    
                    # Intentar upsert (insertar o actualizar)
                    try:
                        # Primero intentar actualizar
                        result = self.supabase.table(self.table_name).update(movie_data).eq('tmdb_id', movie['tmdb_id']).execute()
                        
                        if result.data:
                            updated += 1
                            logger.debug(f"✏️ Actualizada: {movie['title']}")
                        else:
                            # Si no existe, insertar
                            result = self.supabase.table(self.table_name).insert(movie_data).execute()
                            inserted += 1
                            logger.debug(f"➕ Insertada: {movie['title']}")
                    
                    except Exception as e:
                        # Si falla actualización, intentar inserción
                        try:
                            result = self.supabase.table(self.table_name).insert(movie_data).execute()
                            inserted += 1
                            logger.debug(f"➕ Insertada: {movie['title']}")
                        except:
                            errors += 1
                            logger.warning(f"⚠️ Error procesando: {movie.get('title', 'Unknown')} ({e})")
                    
                    # Mostrar progreso cada 10 películas
                    if (idx + 1) % 10 == 0:
                        logger.info(f"  Progreso: {idx + 1}/{total}")
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"❌ Error procesando película: {e}")
            
            # Mostrar resumen
            logger.info(f"\n📈 RESUMEN DE SINCRONIZACIÓN")
            logger.info(f"  ✅ Total procesadas: {total}")
            logger.info(f"  ➕ Insertadas: {inserted}")
            logger.info(f"  ✏️ Actualizadas: {updated}")
            logger.info(f"  ❌ Errores: {errors}")
            
            return errors == 0
            
        except Exception as e:
            logger.error(f"❌ Error sincronizando con Supabase: {e}")
            return False
