#!/usr/bin/env python3
"""
Script de prueba rápida del scraper de series
Ejecuta con solo 2 series y 3 episodios para probar funcionamiento
"""

import sys
import os

# Agregar ruta del scraper
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from scraper_poseidonhd2_series import PoseidonHD2SeriesScraper

if __name__ == '__main__':
    scraper = PoseidonHD2SeriesScraper()
    
    print("=" * 60)
    print("PRUEBA RÁPIDA: SCRAPER DE SERIES POSEIDONHD2")
    print("=" * 60)
    print()
    print("Configuración de prueba:")
    print("  • Series: 2")
    print("  • Episodios por temporada: 3")
    print()
    print("Ejecutando scraper...")
    print()
    
    # Ejecutar con parámetros reducidos para prueba
    scraper.run(max_series=2, max_episodes_per_season=3)
    
    print()
    print("=" * 60)
    print("✅ Prueba completada")
    print("=" * 60)
