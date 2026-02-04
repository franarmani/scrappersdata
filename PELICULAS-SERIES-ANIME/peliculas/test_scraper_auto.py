#!/usr/bin/env python3
"""
Script de prueba para verificar el scraper con sincronización automática
Ejecuta el scraper con --max-pages 1 para probar la funcionalidad completa
"""

import sys
import os

# Agregar ruta del scraper
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from scraper_pelisplushd_movies import VerpeliculasUltraaScraper

if __name__ == '__main__':
    # Crear instancia del scraper
    scraper = VerpeliculasUltraaScraper()
    
    print("=" * 60)
    print("SCRAPER PELÍCULAS CON SINCRONIZACIÓN AUTOMÁTICA")
    print("=" * 60)
    print()
    print("Características:")
    print("✅ Extrae películas desde verpeliculasultra.com")
    print("✅ Obtiene metadatos de TMDB")
    print("✅ Extrae servidores con URLs y idiomas")
    print("✅ Sincroniza automáticamente a GitHub")
    print("✅ Sincroniza automáticamente a Supabase")
    print()
    print("Ejecutando scraper con 1 página de prueba...")
    print()
    
    # Ejecutar scraper
    scraper.run(max_pages=1)
    
    print()
    print("=" * 60)
    print("✅ Proceso completado")
    print("=" * 60)
