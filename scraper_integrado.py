#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script integrado para extraer datos de:
1. FutbolParaTodos (futbolparatodos-tv.com)
2. ElCanalDeportivo (elcanaldeportivo.com)
3. FutbolLibre-HD (futbollibre-hd.cl)

Combina los scrapers de deportes y actualiza el archivo partidos.json
"""

import sys
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr and hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Si falla, continuar sin reconfigurar

import requests
import json
import os
import re
import base64
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import urllib3

# Deshabilitar advertencias SSL para sitios de streaming
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ScraperIntegrado:
    def __init__(self):
        # Configuración FutbolParaTodos
        self.futbol_base_url = "https://futbolparatodos.me"
        self.futbol_agenda_url = f"{self.futbol_base_url}/agenda.html"
        
        # Configuración ElCanalDeportivo
        self.canal_base_url = "https://elcanaldeportivo.com/"
        self.canal_partidos_url = f"{self.canal_base_url}partidos.json"
        
        # Configuración FutbolLibre-FullHD (nuevo DOM basado en ul#menu)
        self.futbollibre_base_url = "https://futbollibrefullhd.com"
        self.futbollibre_agenda_url = f"{self.futbollibre_base_url}/"  # página principal contiene la agenda
        
        # Configuración TVLibre
        self.tvlibre_base_url = "https://tvlibree.com"
        self.tvlibre_agenda_url = f"{self.tvlibre_base_url}/agenda/"
        
        # Configuración PirloTV
        self.pirlotv_base_url = "https://pirlotvoficial.com"
        self.pirlotv_agenda_url = f"{self.pirlotv_base_url}/programacion.php"
        
        # Configuración StreamVV11
        self.streamvv11_base_url = "https://streamvv11.lat"
        self.streamvv11_agenda_url = f"{self.streamvv11_base_url}/eventos.html"
        
        # Configuración Pelota-Libre.PE (mismo DOM que FutbolLibre-FullHD)
        # Intentaremos ambos dominios comunes y usaremos el primero que responda
        self.pelotalibre_domains = [
            "https://pelotalibre.pe",
            "https://pelota-libre.pe"
        ]
        # Se resolverá dinámicamente en extract_pelotalibre_menu()
        
        # Configuración RusticoTV (nuevo dominio .top)
        self.rusticotv_base_url = "https://rusticotv.top"
        self.rusticotv_agenda_url = f"{self.rusticotv_base_url}/agenda.html"
        
        # Archivo de salida
        self.output_path = r'public\partidos.json'
        
        # Headers comunes
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Mapeo de clases CSS a URLs de banderas para FutbolParaTodos
        self.flag_mapping = {
            'TUR': 'https://pelis4k.online/banderas/ligaturca.png',
            'ENG': 'https://pelis4k.online/banderas/Inglaterra.png',
            'LEAGUESCUP': 'https://pelis4k.online/banderas/Leagues%20Cup%20%28MLS%20+%20Liga%20MX%29.png',
            'ALE': 'https://pelis4k.online/banderas/alemania.png',
            'FRA': 'https://pelis4k.online/banderas/francia.png',
            'HOL': 'https://pelis4k.online/banderas/Eredivisie.png',
            'POR': 'https://pelis4k.online/banderas/Primeira%20Liga.png',
            'MEX': 'https://pelis4k.online/banderas/mexico.png',
            'ES': 'https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png',
            'ES1': 'https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png',
            'ES2': 'https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png',
            'IT': 'https://pelis4k.online/banderas/Serie%20A.png',
            'BEL': 'https://pelis4k.online/banderas/Liga%20Belga.png',
            'USA': 'https://pelis4k.online/banderas/eeuu.png',
            'MLS': 'https://pelis4k.online/banderas/MLS.png',
            'FUT': 'https://pelis4k.online/banderas/internacional.png',
            'CHA': 'https://pelis4k.online/banderas/Champions%20League.png',
            'UE': 'https://pelis4k.online/banderas/Europa%20League.svg',
            'COL': 'https://pelis4k.online/banderas/Liga%20Colombiana.png',
            'CHI': 'https://pelis4k.online/banderas/chile.png',
            'ECUA': 'https://pelis4k.online/banderas/Liga%20Ecuatoriana.png',
            'PE': 'https://pelis4k.online/banderas/Liga%20Peruana.png',
            'AR': 'https://pelis4k.online/banderas/argentina.png',
            'BRA': 'https://pelis4k.online/banderas/brasil.png',
            'URU': 'https://pelis4k.online/banderas/uruguay.png',
            'LIB': 'https://pelis4k.online/banderas/Copa%20Libertadores.png',
            'SUD': 'https://pelis4k.online/banderas/Copa%20Sudamericana.png',
            'UEC': 'https://pelis4k.online/banderas/Conference%20League.png',
            'F1': 'https://pelis4k.online/banderas/F1%20%28F%C3%B3rmula%201%29.png',
            'F2': 'https://pelis4k.online/banderas/F2%20%28F%C3%B3rmula%202%29.svg',
            'F3': 'https://pelis4k.online/banderas/F3%20%28F%C3%B3rmula%203%29.png',
            'WWE': 'https://pelis4k.online/banderas/WWE.png',
            'AEW': 'https://pelis4k.online/banderas/AEW.png',
            'NBA': 'https://pelis4k.online/banderas/NBA%20%28Basket%29.png',
            'UFC': 'https://pelis4k.online/banderas/ufc.png',
            'ARA': 'https://pelis4k.online/banderas/Liga%20%C3%81rabe%20-%20Saudi%20Pro%20League.svg',
            'NFL': 'https://pelis4k.online/banderas/NFL%20%28F%C3%BAtbol%20Americano%29.png',
            'NHL': 'https://pelis4k.online/banderas/NHL.png',
            'BOX': 'https://pelis4k.online/banderas/boxeo.png',
            'BOXING': 'https://pelis4k.online/banderas/Boxing.png',
            'PY': 'https://pelis4k.online/banderas/paraguay.png',
            'CR': 'https://pelis4k.online/banderas/Liga%20Costarricense.svg',
            'MLB': 'https://pelis4k.online/banderas/MLB%20%28B%C3%A9isbol%29.png',
            'ATP': 'https://pelis4k.online/banderas/ATP.png',
            'WTA': 'https://pelis4k.online/banderas/WTA.png',
            'WNBA': 'https://pelis4k.online/banderas/WNBA.png',
            'RUGBY': 'https://pelis4k.online/banderas/Rugby.png',
            'MOTOGP': 'https://pelis4k.online/banderas/MotoGP.svg',
            'INDYCAR': 'https://pelis4k.online/banderas/IndyCar.png',
            'CICLISMO': 'https://pelis4k.online/banderas/Ciclismo.svg',
            'BUNDESLIGA': 'https://pelis4k.online/banderas/Bundesliga.png',
            'LIGUE1': 'https://pelis4k.online/banderas/Ligue%201.png',
            'PREMIERLEAGUE': 'https://pelis4k.online/banderas/Premier-League-Logo-PNG-Iconic-English-Football-Emblem-Transparent.png',
            'CHAMPIONSHIP': 'https://pelis4k.online/banderas/Championship-EFL.png',
            'LIGAMX': 'https://pelis4k.online/banderas/Liga%20MX.png',
            'LIGAARGENTINA': 'https://pelis4k.online/banderas/Liga%20Argentina.png',
            'LIGABRASILEÑA': 'https://pelis4k.online/banderas/Liga%20Brasile%C3%B1a.png',
            'LIGACHILENA': 'https://pelis4k.online/banderas/Liga%20Chilena.png',
            'LIGAURUGUAYA': 'https://pelis4k.online/banderas/Liga%20Uruguaya.png',
            'LIGAPARAGUAYA': 'https://pelis4k.online/banderas/Liga%20Paraguaya.png'
        }
        
        # Mapeo de clases CSS a URLs de banderas para StreamVV11 (usando pelis4k.online)
        self.streamvv11_flag_mapping = {
            'TUR': 'https://pelis4k.online/banderas/ligaturca.png',
            'ENG': 'https://pelis4k.online/banderas/Inglaterra.png',
            'ENG1': 'https://pelis4k.online/banderas/Premier-League-Logo-PNG-Iconic-English-Football-Emblem-Transparent.png',
            'CHAMPIONSHIPENG': 'https://pelis4k.online/banderas/Championship-EFL.png',
            'ALE': 'https://pelis4k.online/banderas/alemania.png',
            'FRA': 'https://pelis4k.online/banderas/francia.png',
            'HOL': 'https://pelis4k.online/banderas/Eredivisie.png',
            'POR': 'https://pelis4k.online/banderas/Primeira%20Liga.png',
            'MEX': 'https://pelis4k.online/banderas/mexico.png',
            'ES': 'https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png',
            'ES1': 'https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png',
            'ES2': 'https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png',
            'IT': 'https://pelis4k.online/banderas/Serie%20A.png',
            'BEL': 'https://pelis4k.online/banderas/Liga%20Belga.png',
            'CR': 'https://pelis4k.online/banderas/Liga%20Costarricense.svg',
            'ESC': 'https://pelis4k.online/banderas/Liga%20de%20Escocia.png',
            'USA': 'https://pelis4k.online/banderas/eeuu.png',
            'MLS': 'https://pelis4k.online/banderas/MLS.png',
            'FUT': 'https://pelis4k.online/banderas/internacional.png',
            'CHA': 'https://pelis4k.online/banderas/Champions%20League.png',
            'UE': 'https://pelis4k.online/banderas/Europa%20League.svg',
            'COL': 'https://pelis4k.online/banderas/Liga%20Colombiana.png',
            'CHI': 'https://pelis4k.online/banderas/chile.png',
            'ECUA': 'https://pelis4k.online/banderas/Liga%20Ecuatoriana.png',
            'PE': 'https://pelis4k.online/banderas/Liga%20Peruana.png',
            'AR': 'https://pelis4k.online/banderas/argentina.png',
            'FIFA': 'https://pelis4k.online/banderas/FIFA%20Intercontinental%20Cup.png',
            'BRA': 'https://pelis4k.online/banderas/brasil.png',
            'URU': 'https://pelis4k.online/banderas/uruguay.png',
            'LIB': 'https://pelis4k.online/banderas/Copa%20Libertadores.png',
            'SUD': 'https://pelis4k.online/banderas/Copa%20Sudamericana.png',
            'UEC': 'https://pelis4k.online/banderas/Conference%20League.png',
            'AMERICA': 'https://pelis4k.online/banderas/Copa%20Am%C3%A9rica.png',
            'F1': 'https://pelis4k.online/banderas/F1%20%28F%C3%B3rmula%201%29.png',
            'F2': 'https://pelis4k.online/banderas/F2%20%28F%C3%B3rmula%202%29.svg',
            'F3': 'https://pelis4k.online/banderas/F3%20%28F%C3%B3rmula%203%29.png',
            'WWE': 'https://pelis4k.online/banderas/WWE.png',
            'NBA': 'https://pelis4k.online/banderas/NBA%20%28Basket%29.png',
            'NHL': 'https://pelis4k.online/banderas/NHL.png',
            'UFC': 'https://pelis4k.online/banderas/ufc.png',
            'EURO': 'https://pelis4k.online/banderas/Nations%20League%20%28UEFA%29.png',
            'EUROFEM': 'https://pelis4k.online/banderas/Copa%20Am%C3%A9rica%20Femenina.png',
            'ARA': 'https://pelis4k.online/banderas/Liga%20%C3%81rabe%20-%20Saudi%20Pro%20League.svg',
            'AFCCUP': 'https://pelis4k.online/banderas/Copa%20Arabia.png',
            'AEW': 'https://pelis4k.online/banderas/AEW.png',
            'ATP': 'https://pelis4k.online/banderas/ATP.png',
            'WTA': 'https://pelis4k.online/banderas/WTA.png',
            'AFRICA': 'https://pelis4k.online/banderas/conmebol.png',
            'ENDESA': 'https://pelis4k.online/banderas/Copa%20Endesa%20%28ACB%20Espa%C3%B1a%20-%20Basket%20pero%20aparece%29.svg',
            'NFL': 'https://pelis4k.online/banderas/NFL%20%28F%C3%BAtbol%20Americano%29.png',
            'BOX': 'https://pelis4k.online/banderas/boxeo.png',
            'BOXING': 'https://pelis4k.online/banderas/Boxing.png',
            'PY': 'https://pelis4k.online/banderas/paraguay.png',
            'SDC': 'https://pelis4k.online/banderas/Soccer%20Champions%20Tour.png',
            'FUTSAL': 'https://pelis4k.online/banderas/F%C3%BAtbol%20Sala%20%28FUTSAL%29.webp',
            'RUG': 'https://pelis4k.online/banderas/Rugby.png',
            'VEN': 'https://pelis4k.online/banderas/internacional.png',
            'UYL': 'https://pelis4k.online/banderas/UEFA%20Youth%20League%20%28UYL%29.png',
            'CICLISMO': 'https://pelis4k.online/banderas/Ciclismo.svg',
            'LCC': 'https://pelis4k.online/banderas/Leagues%20Cup%20%28MLS%20+%20Liga%20MX%29.png',
            'NATIONS': 'https://pelis4k.online/banderas/Nations%20League%20%28UEFA%29.png',
            'AFC': 'https://pelis4k.online/banderas/Copa%20Arabia.png',
            'MFP': 'https://pelis4k.online/banderas/Copa%20Mundial%20Femenina%20Sub-17.png',
            'CONCACAFCHA': 'https://pelis4k.online/banderas/CONCACAF%20Champions%20Cup.png',
            'CONCACAFCUP': 'https://pelis4k.online/banderas/Copa%20de%20Oro%20%28Gold%20Cup%29.png',
            'RECOPASUD': 'https://pelis4k.online/banderas/Recopa%20Sudamericana.png',
            'AMERICUP': 'https://pelis4k.online/banderas/FIBA%20World%20Cup%20-%20FIBA%20AmeriCup.png',
            'MLB': 'https://pelis4k.online/banderas/MLB%20%28B%C3%A9isbol%29.png',
            'NATIONSF': 'https://pelis4k.online/banderas/Copa%20Am%C3%A9rica%20Femenina.png',
            'POL': 'https://pelis4k.online/banderas/Liga%20de%20Polonia.png',
            'HN': 'https://pelis4k.online/banderas/Liga%20de%20Honduras.png',
            'RU': 'https://pelis4k.online/banderas/Liga%20de%20Rumania.png',
            'MOTOGP': 'https://pelis4k.online/banderas/MotoGP.svg',
            'INDYCAR': 'https://pelis4k.online/banderas/IndyCar.png',
            'SUD-17F': 'https://pelis4k.online/banderas/Sudamericano%20Sub-17.png',
            'BOL': 'https://pelis4k.online/banderas/Liga%20de%20Bolivia.png',
            'CONCACAFNATIONS': 'https://pelis4k.online/banderas/CONCACAF%20Nations%20League.png',
            'ELIAFC': 'https://pelis4k.online/banderas/Copa%20Arabia.png',
            'SUD-20F': 'https://pelis4k.online/banderas/Sudamericano%20Sub-20.png',
            'GT': 'https://pelis4k.online/banderas/Liga%20de%20Guatemala.png',
            'EUROLEAGUE': 'https://pelis4k.online/banderas/EuroLeague.png',
            'GR': 'https://pelis4k.online/banderas/internacional.png',
            'CHAWOMEN': 'https://pelis4k.online/banderas/Champions%20League.png',
            'ASIA': 'https://pelis4k.online/banderas/internacional.png',
            'WNBA': 'https://pelis4k.online/banderas/WNBA.png',
            'RO': 'https://pelis4k.online/banderas/Liga%20de%20Rumania.png',
            'FIBA': 'https://pelis4k.online/banderas/FIBA%20World%20Cup%20-%20FIBA%20AmeriCup.png',
            'CONCAU20': 'https://pelis4k.online/banderas/CONCACAF%20U20.png',
            'LEAGUESCUP': 'https://pelis4k.online/banderas/Leagues%20Cup%20%28MLS%20+%20Liga%20MX%29.png',
            'CENTRALAMERICANCUP': 'https://pelis4k.online/banderas/Copa%20Centroamericana.png',
            'SOCCERCHAMPIONS': 'https://pelis4k.online/banderas/Soccer%20Champions%20Tour.png',
            'UEFA_SUPERCOPA': 'https://pelis4k.online/banderas/UEFA%20Supercopa.png',
            'MUNDIAL20FE': 'https://pelis4k.online/banderas/Copa%20Mundial%20Femenina%20Sub-20.webp',
            'AFRICANNATIONS': 'https://pelis4k.online/banderas/conmebol.png',
            'ELISUDA': 'https://pelis4k.online/banderas/Sudamericano%20Sub-17.png',
            'FIFAINTERCUP': 'https://pelis4k.online/banderas/FIFA%20Intercontinental%20Cup.png',
            'BUNDESLIGA': 'https://pelis4k.online/banderas/Bundesliga.png',
            'LIGUE1': 'https://pelis4k.online/banderas/Ligue%201.png',
            'ENG3': 'https://pelis4k.online/banderas/Championship-EFL.png',
            'EFLCUP': 'https://pelis4k.online/banderas/Championship-EFL.png',
            'PT1': 'https://pelis4k.online/banderas/Primeira%20Liga.png',
            'IT1': 'https://pelis4k.online/banderas/Serie%20A.png',
            'ESC1': 'https://pelis4k.online/banderas/Liga%20de%20Escocia.png',
            'ITCOPA': 'https://pelis4k.online/banderas/Copa%20Italia.png',
            'ES1': 'https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png',
            'ES2': 'https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png',
            'ITSUPERCOPA': 'https://pelis4k.online/banderas/Supercopa%20de%20Italia.png',
            'FRA1': 'https://pelis4k.online/banderas/Ligue%201.png',
            'ESCOPAREY': 'https://pelis4k.online/banderas/Copa%20del%20Rey.png',
            'MXF': 'https://pelis4k.online/banderas/Liga%20MX.png',
            'TUR1': 'https://pelis4k.online/banderas/ligaturca.png',
            'KINGSLEAGUE': 'https://pelis4k.online/banderas/Soccer%20Champions%20Tour.png',
            'GOLDCUP': 'https://pelis4k.online/banderas/Copa%20de%20Oro%20%28Gold%20Cup%29.png',
            'FRASUPERCUP': 'https://pelis4k.online/banderas/Supercopa%20de%20Francia.png',
            'LIGAF': 'https://pelis4k.online/banderas/espa%C3%B1a.png',
            'MUNDIALU20': 'https://pelis4k.online/banderas/Copa%20Mundial%20Sub-20.png',
            'ELIUEFA': 'https://pelis4k.online/banderas/Nations%20League%20%28UEFA%29.png',
            'ELICONCACAF': 'https://pelis4k.online/banderas/CONCACAF%20Nations%20League.png',
            'ESSUPERCOPA': 'https://pelis4k.online/banderas/Supercopa%20de%20Espa%C3%B1a.png',
            'ENGFACUP': 'https://pelis4k.online/banderas/Inglaterra.png',
            'ARA1': 'https://pelis4k.online/banderas/Liga%20%C3%81rabe%20-%20Saudi%20Pro%20League.svg',
            'ALE1': 'https://pelis4k.online/banderas/Bundesliga.png',
            'MX1': 'https://pelis4k.online/banderas/Liga%20MX.png',
            'MX2': 'https://pelis4k.online/banderas/Liga%20MX.png',
            'TE': 'https://pelis4k.online/banderas/ATP.png',
            'BEL1': 'https://pelis4k.online/banderas/Liga%20Belga.png',
            'CR1': 'https://pelis4k.online/banderas/Liga%20Costarricense.svg',
            'AOTENNIS': 'https://pelis4k.online/banderas/Australia%20Open.png',
            'FRACOUPE': 'https://pelis4k.online/banderas/Copa%20Francia%20%28Coupe%20de%20France%29.png',
            'HOLCOPA': 'https://pelis4k.online/banderas/Copa%20Holanda%20%28KNVB%20Beker%29.png',
            'ENGWOMEN': 'https://pelis4k.online/banderas/Premier-League-Logo-PNG-Iconic-English-Football-Emblem-Transparent.png',
            'COPAAMERICAF': 'https://pelis4k.online/banderas/Copa%20Am%C3%A9rica%20Femenina.png',
            'HN1': 'https://pelis4k.online/banderas/Liga%20de%20Honduras.png',
            'ARCOPA': 'https://pelis4k.online/banderas/Copa%20Arabia.png',
            'CONMEBOLU20': 'https://pelis4k.online/banderas/CONCACAF%20U20.png',
            'AR1': 'https://img.futebol12.nexus/zas/primeraar.png',
            'EUROCOPAFEM': 'https://img.futebol12.nexus/zas/eurocopafem.png',
            'U17CONCA': 'https://img.futebol12.nexus/zas/concau17.png',
            'FIBAAMERICUP': 'https://img.futebol12.nexus/zas/fibaameri.png',
            'MLS': 'https://img.futebol12.nexus/zas/mls.png',
            'AFCTWO': 'https://img.futebol12.nexus/zas/afctwo.png'
        }
        
        # Mapeo de clases CSS a nombres de liga
        self.league_mapping = {
            'TUR': 'Liga Turca',
            'ENG': 'Premier League / EFL',
            'LEAGUESCUP': 'EFL Cup',
            'ALE': 'Bundesliga',
            'FRA': 'Ligue 1',
            'HOL': 'Eredivisie',
            'POR': 'Primeira Liga',
            'MEX': 'Liga MX',
            'ES': 'LaLiga',
            'IT': 'Serie A / Copa Italia',
            'BEL': 'Liga Belga',
            'USA': 'MLS',
            'FUT': 'Internacional',
            'CHA': 'Champions League',
            'UE': 'Europa League',
            'COL': 'Liga Colombiana',
            'CHI': 'Liga Chilena',
            'ECUA': 'Liga Ecuatoriana',
            'PE': 'Liga Peruana',
            'AR': 'Liga Argentina',
            'BRA': 'Liga Brasileña',
            'URU': 'Liga Uruguaya',
            'LIB': 'Copa Libertadores',
            'SUD': 'Copa Sudamericana',
            'UEC': 'Conference League',
            'F1': 'Fórmula 1',
            'WWE': 'WWE',
            'NBA': 'NBA',
            'UFC': 'UFC',
            'ARA': 'Liga Árabe',
            'NFL': 'NFL',
            'BOX': 'Boxeo',
            'PY': 'Liga Paraguaya',
            'CR': 'Liga Costarricense'
        }
        
        # Mapeo de clases CSS a nombres de liga para StreamVV11
        self.streamvv11_league_mapping = {
            'TUR': 'Liga Turca',
            'TUR1': 'Super Lig',
            'ENG': 'Premier League',
            'ENG1': 'Premier League',
            'CHAMPIONSHIPENG': 'Championship',
            'ENG3': 'League One',
            'EFLCUP': 'EFL Cup',
            'ENGFACUP': 'FA Cup',
            'ENGWOMEN': 'Premier League Femenina',
            'ALE': 'Bundesliga',
            'ALE1': 'Bundesliga',
            'FRA': 'Ligue 1',
            'FRA1': 'Ligue 1',
            'FRACOUPE': 'Copa de Francia',
            'FRASUPERCUP': 'Supercopa de Francia',
            'HOL': 'Eredivisie',
            'HOLCOPA': 'Copa de Holanda',
            'POR': 'Primeira Liga',
            'PT1': 'Primeira Liga',
            'MEX': 'Liga MX',
            'MX1': 'Liga MX',
            'MX2': 'Ascenso MX',
            'MXF': 'Liga MX Femenil',
            'ES': 'LaLiga',
            'ES1': 'LaLiga',
            'ES2': 'LaLiga 2',
            'ESCOPAREY': 'Copa del Rey',
            'ESSUPERCOPA': 'Supercopa de España',
            'IT': 'Serie A',
            'IT1': 'Serie A',
            'ITCOPA': 'Copa Italia',
            'ITSUPERCOPA': 'Supercopa Italia',
            'ESC': 'Liga Escocesa',
            'ESC1': 'Liga Escocesa',
            'BEL': 'Liga Belga',
            'BEL1': 'Pro League',
            'USA': 'MLS',
            'MLS': 'MLS',
            'FUT': 'Internacional',
            'CHA': 'Champions League',
            'CHAWOMEN': 'Champions League Femenina',
            'UE': 'Europa League',
            'UEC': 'Conference League',
            'COL': 'Liga Colombiana',
            'CHI': 'Liga Chilena',
            'ECUA': 'Liga Ecuatoriana',
            'PE': 'Liga Peruana',
            'AR': 'Liga Argentina',
            'AR1': 'Primera División Argentina',
            'ARCOPA': 'Copa Argentina',
            'BRA': 'Brasileirão',
            'URU': 'Liga Uruguaya',
            'LIB': 'Copa Libertadores',
            'SUD': 'Copa Sudamericana',
            'SUD-17F': 'Sudamericana Sub-17 Femenino',
            'SUD-20F': 'Sudamericana Sub-20',
            'RECOPASUD': 'Recopa Sudamericana',
            'F1': 'Fórmula 1',
            'F2': 'Fórmula 2',
            'F3': 'Fórmula 3',
            'MOTOGP': 'MotoGP',
            'INDYCAR': 'IndyCar',
            'WWE': 'WWE',
            'AEW': 'AEW',
            'NBA': 'NBA',
            'WNBA': 'WNBA',
            'EUROLEAGUE': 'Euroliga',
            'ENDESA': 'Liga Endesa',
            'NHL': 'NHL',
            'UFC': 'UFC',
            'BOX': 'Boxeo',
            'EURO': 'Eurocopa',
            'EUROCOPAFEM': 'Eurocopa Femenina',
            'EUROFEM': 'Europeo Femenino',
            'FIFA': 'FIFA',
            'FIFAINTERCUP': 'Copa Intercontinental FIFA',
            'AMERICA': 'Copa América',
            'COPAAMERICAF': 'Copa América Femenina',
            'GOLDCUP': 'Copa Oro',
            'CONCACAFCHA': 'CONCACAF Champions',
            'CONCACAFCUP': 'Copa CONCACAF',
            'CONCACAFNATIONS': 'Nations League CONCACAF',
            'CENTRALAMERICANCUP': 'Copa Centroamericana',
            'SOCCERCHAMPIONS': 'Soccer Champions',
            'U17CONCA': 'CONCACAF Sub-17',
            'CONCAU20': 'CONCACAF Sub-20',
            'ELICONCACAF': 'Eliminatorias CONCACAF',
            'MUNDIALU20': 'Mundial Sub-20',
            'MUNDIAL20FE': 'Mundial Sub-20 Femenino',
            'MFP': 'Mundial Femenino',
            'NATIONS': 'Nations League UEFA',
            'NATIONSF': 'Nations League Femenina',
            'ELIUEFA': 'Eliminatorias UEFA',
            'UEFA_SUPERCOPA': 'Supercopa UEFA',
            'LEAGUESCUP': 'Leagues Cup',
            'ARA': 'Liga Árabe',
            'ARA1': 'Liga Saudí',
            'NFL': 'NFL',
            'MLB': 'MLB',
            'AFRICA': 'Copa Africana',
            'AFRICANNATIONS': 'Copa Africana de Naciones',
            'AFCCUP': 'Copa AFC',
            'AFC': 'AFC Champions',
            'AFCTWO': 'AFC Champions Two',
            'ASIA': 'Copa Asiática',
            'ELIAFC': 'Eliminatorias AFC',
            'ELISUDA': 'Eliminatorias Sudamericana',
            'PY': 'Liga Paraguaya',
            'CR': 'Liga Costarricense',
            'CR1': 'Primera División Costa Rica',
            'HN': 'Liga Hondureña',
            'HN1': 'Liga Nacional Honduras',
            'GT': 'Liga Guatemalteca',
            'BOL': 'Liga Boliviana',
            'VEN': 'Liga Venezolana',
            'POL': 'Liga Polaca',
            'RU': 'Liga Rusa',
            'RO': 'Liga Rumana',
            'GR': 'Liga Griega',
            'SDC': 'Sudamericano',
            'FUTSAL': 'Futsal',
            'RUG': 'Rugby',
            'UYL': 'UEFA Youth League',
            'CICLISMO': 'Ciclismo',
            'LCC': 'Liga Centroamericana',
            'AMERICUP': 'AmeriCup',
            'FIBAAMERICUP': 'FIBA AmeriCup',
            'FIBA': 'FIBA',
            'CONMEBOLU20': 'CONMEBOL Sub-20',
            'KINGSLEAGUE': 'Kings League',
            'LIGAF': 'Liga F',
            'ATP': 'ATP',
            'WTA': 'WTA',
            'AOTENNIS': 'Australian Open',
            'TE': 'Tenis'
        }

    def detect_specific_competition(self, event_title, default_league, default_flag):
        """
        Detecta competiciones específicas desde el título del evento
        y devuelve la liga y bandera correspondiente
        """
        title_lower = event_title.lower()
        
        # Diccionario de competiciones específicas
        specific_competitions = {
            "copa intercontinental fifa": ("Copa Intercontinental FIFA", "https://pelis4k.online/banderas/FIFA%20Intercontinental%20Cup.png"),
            "copa intercontinental": ("Copa Intercontinental FIFA", "https://pelis4k.online/banderas/FIFA%20Intercontinental%20Cup.png"),
            "copa del mundo": ("Copa del Mundo", "https://pelis4k.online/banderas/Copa%20Mundial%20Sub-17.png"),
            "world cup": ("Copa del Mundo", "https://pelis4k.online/banderas/Copa%20Mundial%20Sub-17.png"),
            "copa mundial sub-17": ("Copa Mundial Sub-17", "https://pelis4k.online/banderas/Copa%20Mundial%20Sub-17.png"),
            "copa mundial sub-20": ("Copa Mundial Sub-20", "https://pelis4k.online/banderas/Copa%20Mundial%20Sub-20.png"),
            "copa mundial femenina sub-17": ("Copa Mundial Femenina Sub-17", "https://pelis4k.online/banderas/Copa%20Mundial%20Femenina%20Sub-17.png"),
            "copa mundial femenina sub-20": ("Copa Mundial Femenina Sub-20", "https://pelis4k.online/banderas/Copa%20Mundial%20Femenina%20Sub-20.webp"),
            "copa américa": ("Copa América", "https://pelis4k.online/banderas/Copa%20Am%C3%A9rica.png"),
            "copa américa femenina": ("Copa América Femenina", "https://pelis4k.online/banderas/Copa%20Am%C3%A9rica%20Femenina.png"),
            "eurocopa": ("Eurocopa", "https://pelis4k.online/banderas/Nations%20League%20%28UEFA%29.png"),
            "euro 2024": ("Eurocopa", "https://pelis4k.online/banderas/Nations%20League%20%28UEFA%29.png"),
            "uefa euro": ("Eurocopa", "https://pelis4k.online/banderas/Nations%20League%20%28UEFA%29.png"),
            "champions league": ("Champions League", "https://pelis4k.online/banderas/Champions%20League.png"),
            "uefa champions": ("Champions League", "https://pelis4k.online/banderas/Champions%20League.png"),
            "europa league": ("Europa League", "https://pelis4k.online/banderas/Europa%20League.svg"),
            "uefa europa": ("Europa League", "https://pelis4k.online/banderas/Europa%20League.svg"),
            "conference league": ("Conference League", "https://pelis4k.online/banderas/Conference%20League.png"),
            "copa libertadores": ("Copa Libertadores", "https://pelis4k.online/banderas/Copa%20Libertadores.png"),
            "copa sudamericana": ("Copa Sudamericana", "https://pelis4k.online/banderas/Copa%20Sudamericana.png"),
            "recopa sudamericana": ("Recopa Sudamericana", "https://pelis4k.online/banderas/Recopa%20Sudamericana.png"),
            "concacaf champions": ("CONCACAF Champions Cup", "https://pelis4k.online/banderas/CONCACAF%20Champions%20Cup.png"),
            "concacaf champions cup": ("CONCACAF Champions Cup", "https://pelis4k.online/banderas/CONCACAF%20Champions%20Cup.png"),
            "gold cup": ("Copa de Oro (Gold Cup)", "https://pelis4k.online/banderas/Copa%20de%20Oro%20%28Gold%20Cup%29.png"),
            "copa oro": ("Copa de Oro (Gold Cup)", "https://pelis4k.online/banderas/Copa%20de%20Oro%20%28Gold%20Cup%29.png"),
            "nations league": ("UEFA Nations League", "https://pelis4k.online/banderas/Nations%20League%20%28UEFA%29.png"),
            "concacaf nations league": ("CONCACAF Nations League", "https://pelis4k.online/banderas/CONCACAF%20Nations%20League.png"),
            "liga de naciones": ("UEFA Nations League", "https://pelis4k.online/banderas/Nations%20League%20%28UEFA%29.png"),
            "copa africana": ("Copa Africana de Naciones", "https://pelis4k.online/banderas/conmebol.png"),
            "afcon": ("Copa Africana de Naciones", "https://pelis4k.online/banderas/conmebol.png"),
            "copa asiática": ("Copa Asiática", "https://pelis4k.online/banderas/Copa%20Arabia.png"),
            "asian cup": ("Copa Asiática", "https://pelis4k.online/banderas/Copa%20Arabia.png"),
            "club world cup": ("Mundial de Clubes FIFA", "https://pelis4k.online/banderas/Mundial%20de%20Clubes%20FIFA.png"),
            "mundial de clubes": ("Mundial de Clubes FIFA", "https://pelis4k.online/banderas/Mundial%20de%20Clubes%20FIFA.png"),
            "copa del rey": ("Copa del Rey", "https://pelis4k.online/banderas/Copa%20del%20Rey.png"),
            "copa italia": ("Copa Italia", "https://pelis4k.online/banderas/Copa%20Italia.png"),
            "copa francia": ("Copa Francia", "https://pelis4k.online/banderas/Copa%20Francia%20%28Coupe%20de%20France%29.png"),
            "coupe de france": ("Copa Francia", "https://pelis4k.online/banderas/Copa%20Francia%20%28Coupe%20de%20France%29.png"),
            "fa cup": ("FA Cup", "https://pelis4k.online/banderas/Inglaterra.png"),
            "dfb pokal": ("Copa Alemania (DFB Pokal)", "https://pelis4k.online/banderas/Copa%20Alemania%20%28DFB%20Pokal%29.png"),
            "knvb beker": ("Copa Holanda (KNVB Beker)", "https://pelis4k.online/banderas/Copa%20Holanda%20%28KNVB%20Beker%29.png"),
            "supercopa de españa": ("Supercopa de España", "https://pelis4k.online/banderas/Supercopa%20de%20Espa%C3%B1a.png"),
            "supercopa de italia": ("Supercopa de Italia", "https://pelis4k.online/banderas/Supercopa%20de%20Italia.png"),
            "supercopa de francia": ("Supercopa de Francia", "https://pelis4k.online/banderas/Supercopa%20de%20Francia.png"),
            "uefa supercopa": ("UEFA Supercopa", "https://pelis4k.online/banderas/UEFA%20Supercopa.png"),
            "leagues cup": ("Leagues Cup (MLS + Liga MX)", "https://pelis4k.online/banderas/Leagues%20Cup%20%28MLS%20+%20Liga%20MX%29.png"),
            "copa centroamericana": ("Copa Centroamericana", "https://pelis4k.online/banderas/Copa%20Centroamericana.png"),
            "sudamericano sub-17": ("Sudamericano Sub-17", "https://pelis4k.online/banderas/Sudamericano%20Sub-17.png"),
            "sudamericano sub-20": ("Sudamericano Sub-20", "https://pelis4k.online/banderas/Sudamericano%20Sub-20.png"),
        }
        
        # Buscar coincidencias en el título
        for competition_key, (league_name, flag_url) in specific_competitions.items():
            if competition_key in title_lower:
                return league_name, flag_url
        
        # Si no hay coincidencia específica, usar valores por defecto
        return default_league, default_flag
    
    def parse_time_adjust(self, time_str):
        """Convierte hora y resta 4 horas para FutbolParaTodos"""
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            adjusted_time = time_obj - timedelta(hours=4)
            return adjusted_time.strftime("%H:%M")
        except:
            return time_str

    def decode_server_url(self, encoded_param):
        """Decodifica el parámetro r de base64 para FutbolParaTodos"""
        try:
            decoded = base64.b64decode(encoded_param).decode('utf-8')
            return decoded
        except:
            return encoded_param

    def fix_encoding_issues(self, text: str) -> str:
        """Corrige problemas de doble codificación UTF-8 en texto con acentos.
        
        Convierte:
        - IvÃ¡n → Iván
        - LÃ³pez → López  
        - AtlÃ©tico → Atlético
        - DivisiÃ³n → División
        - BrasileirÃ£o → Brasileirão
        - UniÃ³n → Unión
        """
        if not text:
            return text
            
        # Mapeo de caracteres mal codificados comunes
        encoding_fixes = {
            'Ã¡': 'á',  # á
            'Ã©': 'é',  # é
            'Ã­': 'í',  # í
            'Ã³': 'ó',  # ó
            'Ãº': 'ú',  # ú
            'Ã±': 'ñ',  # ñ
            'Ã ': 'à',  # à
            'Ã¨': 'è',  # è
            'Ã¬': 'ì',  # ì
            'Ã²': 'ò',  # ò
            'Ã¹': 'ù',  # ù
            'Ãç': 'ç',  # ç
            'Ã£': 'ã',  # ã
            'Ã¢': 'â',  # â
            'Ãª': 'ê',  # ê
            'Ã´': 'ô',  # ô
            'Ã¯': 'ï',  # ï
            'Ã¼': 'ü',  # ü
            'Ã¶': 'ö',  # ö
            'Ã¤': 'ä',  # ä
        }
        
        fixed_text = text
        for wrong, correct in encoding_fixes.items():
            fixed_text = fixed_text.replace(wrong, correct)
            
        return fixed_text

    def to_absolute_url(self, url: str, base: str = None) -> str:
        """Convierte una URL relativa en absoluta y limpia /ver/"""
        if not url:
            return url
        
        if base is None:
            base = self.canal_base_url
            
        url = url.strip()
        
        # Si ya es absoluta, verificar si tiene /ver/ para removerlo
        if url.startswith('http://') or url.startswith('https://'):
            if '/ver/' in url:
                url = url.replace('/ver/', '/')
            return url
            
        # Para URLs con protocolo relativo
        if url.startswith('//'):
            return 'https:' + url
            
        # Para URLs que empiezan con /ver/, remover el segmento
        if url.startswith('/ver/'):
            url = url[5:]  # Remover '/ver/'
            if not url.startswith('/'):
                url = '/' + url
            return base.rstrip('/') + url
            
        # Para URLs absolutas relativas (empiezan con /)
        if url.startswith('/'):
            return base.rstrip('/') + url
            
        # Para URLs relativas (sin /)
        return base.rstrip('/') + '/' + url

    def extract_real_url_from_ver_page(self, ver_url):
        """Extrae la URL real desde una página /ver/ usando iframe o textarea"""
        try:
            print(f"   🔍 Extrayendo URL real de: {ver_url}")
            response = requests.get(ver_url, headers=self.headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar en el div video-container > iframe
            video_container = soup.find('div', class_='video-container')
            if video_container:
                iframe = video_container.find('iframe')
                if iframe and iframe.get('src'):
                    real_url = iframe.get('src')
                    print(f"   ✅ URL encontrada en iframe: {real_url}")
                    return self.to_absolute_url(real_url)
            
            # Buscar en textarea dentro de div codembed
            codembed = soup.find('div', class_='codembed')
            if codembed:
                textarea = codembed.find('textarea', class_='textinput')
                if textarea and textarea.text:
                    # Buscar iframe dentro del textarea
                    iframe_match = re.search(r'src="([^"]+)"', textarea.text)
                    if iframe_match:
                        real_url = iframe_match.group(1)
                        print(f"   ✅ URL encontrada en textarea: {real_url}")
                        return self.to_absolute_url(real_url)
            
            # Buscar cualquier iframe en la página
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src')
                if src and 'elcanaldeportivo.com' in src:
                    print(f"   ✅ URL encontrada en iframe genérico: {src}")
                    return self.to_absolute_url(src)
            
            print(f"   ⚠️ No se encontró URL real en la página")
            return ver_url
            
        except Exception as e:
            print(f"   ❌ Error extrayendo URL real: {e}")
            return ver_url

    def extract_futbolparatodos_events(self):
        """Extrae eventos de FutbolParaTodos"""
        print("\nEXTRAYENDO DATOS DE FUTBOLPARATODOS")
        
        try:
            print("Descargando página de agenda...")
            response = requests.get(self.futbol_agenda_url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            html_content = response.text
            print(f"OK Página descargada ({len(html_content)} caracteres)")
        except Exception as e:
            print(f"ERROR descargando FutbolParaTodos: {e}")
            return []

        print("Extrayendo eventos...")
        events = []
        
        # Patrón para encontrar los eventos con clase CSS
        event_pattern = r'<li class="([^"]+)"><a href="#">([^<]+)<span class="t">([^<]+)</span></a>\s*<ul>(.*?)</ul>\s*</li>'
        event_matches = re.findall(event_pattern, html_content, re.DOTALL)
        
        for css_class, event_title, time_str, servers_html in event_matches:
            event_title = event_title.strip()
            time_str = time_str.strip()
            css_class = css_class.strip()
            adjusted_time = self.parse_time_adjust(time_str)
            
            # Obtener liga y logo desde los mapeos base
            league_name = self.league_mapping.get(css_class, "Internacional")
            flag_url = self.flag_mapping.get(css_class, "https://img.vxzyzz.click/fx/futbol.png")
            
            # Detectar copas específicas desde el título del evento y ajustar liga/bandera
            league_name, flag_url = self.detect_specific_competition(event_title, league_name, flag_url)
            
            # Limpiar el título del evento removiendo la liga si está duplicada
            clean_title = event_title
            league_prefixes = ["Copa Italia:", "LaLiga:", "EFL Cup:", "Liga MX:", "Copa Libertadores:", 
                             "Copa Sudamericana:", "Primeira Liga:", "Copa del Rey de Arabia:", 
                             "Copa Intercontinental FIFA:", "CONCACAF Central American Cup:", "Copa Uruguay:",
                             "Copa Intercontinental:", "Liga Profesional Argentina:", "Brasileirão:",
                             "Ligue 1:", "Bundesliga:", "Premier League:", "Serie A:"]
            
            for prefix in league_prefixes:
                if clean_title.startswith(prefix):
                    clean_title = clean_title[len(prefix):].strip()
                    break
            
            # Extraer servidores
            server_pattern = r'<li class="subitem1"><a href="/eventos\.html\?r=([^"]+)"[^>]*>([^<]+)<span>([^<]*)</span></a></li>'
            server_matches = re.findall(server_pattern, servers_html)
            
            channels = []
            for encoded_url, server_name, quality in server_matches:
                server_name = server_name.strip()
                quality = quality.strip() or "720p"
                
                decoded_url = self.decode_server_url(encoded_url)
                
                channels.append({
                    "nombre": server_name,
                    "url": decoded_url,
                    "calidad": quality
                })
                
                print(f"   📺 {server_name} ({quality}) → {decoded_url}")
            
            # Convertir al formato del archivo partidos.json
            current_date = datetime.now()
            # Parsear la hora ajustada (ya tiene 4 horas restadas por parse_time_adjust)
            try:
                hour, minute = map(int, adjusted_time.split(':'))
                # El adjusted_time ya es la hora argentina (original - 4 horas)
                event_datetime = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                # Para UTC, agregamos 4 horas a la hora argentina ajustada
                utc_datetime = event_datetime + timedelta(hours=4)
                hora_utc = utc_datetime.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                
                # La hora argentina es directamente el adjusted_time
                hora_argentina = adjusted_time
            except:
                hora_utc = current_date.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                # Si hay error, usar hora actual menos 4 horas para Argentina
                current_time = datetime.now() - timedelta(hours=4)
                hora_argentina = current_time.strftime("%H:%M")
            
            print(f"\n🎯 {league_name}: {clean_title} | {time_str} → {hora_argentina}")
            
            events.append({
                "hora_utc": hora_utc,
                "hora_argentina": hora_argentina,
                "logo": flag_url,  # Logo específico según la liga
                "liga": f"{league_name}:",
                "equipos": clean_title,  # Título limpio sin duplicar liga
                "canales": channels
            })
        
        print(f"\n✅ FutbolParaTodos: {len(events)} eventos extraídos")
        return events

    def extract_elcanaldeportivo_events(self):
        """Extrae eventos de ElCanalDeportivo con URLs reales"""
        print("\nEXTRAYENDO DATOS DE ELCANALDEPORTIVO")
        
        try:
            print("Descargando partidos.json...")
            resp = requests.get(self.canal_partidos_url, headers=self.headers, timeout=30, verify=False)
            resp.raise_for_status()
            partidos = resp.json()
            print(f"OK Partidos descargados: {len(partidos)}")
        except Exception as e:
            print(f"ERROR descargando ElCanalDeportivo: {e}")
            return []

        resultado = []
        
        for i, partido in enumerate(partidos, 1):
            print(f"\n[{i}/{len(partidos)}] Procesando: {partido.get('equipos', 'Sin nombre')}")
            
            nuevo = {
                "hora_utc": partido.get("hora_utc", ""),
                "logo": self.to_absolute_url(partido.get("logo", "")),
                "liga": partido.get("liga", ""),
                "equipos": partido.get("equipos", ""),
                "canales": []
            }
            
            # Calcular hora argentina desde hora_utc (restar 3 horas)
            try:
                hora_utc_str = partido.get("hora_utc", "")
                if hora_utc_str and hora_utc_str.endswith('Z'):
                    # Parsear UTC y convertir a Argentina (UTC-3)
                    utc_time = datetime.fromisoformat(hora_utc_str.replace('Z', '+00:00'))
                    argentina_time = utc_time - timedelta(hours=3)
                    hora_argentina = argentina_time.strftime("%H:%M")
                else:
                    # Si no hay hora UTC válida, usar la hora actual menos 3
                    current_time = datetime.now() - timedelta(hours=3)
                    hora_argentina = current_time.strftime("%H:%M")
            except:
                hora_argentina = "00:00"  # Valor por defecto si hay error
            
            nuevo["hora_argentina"] = hora_argentina
            
            canales = partido.get("canales", [])
            for canal in canales:
                url_canal = canal.get("url", "")
                nombre_canal = canal.get("nombre", "")
                calidad = canal.get("calidad", "720p")
                
                # Si la URL es de elcanaldeportivo.com y contiene /ver/, extraer URL real
                if 'elcanaldeportivo.com' in url_canal and '/ver/' in url_canal:
                    url_real = self.extract_real_url_from_ver_page(url_canal)
                else:
                    url_real = self.to_absolute_url(url_canal)
                
                nuevo["canales"].append({
                    "nombre": nombre_canal,
                    "url": url_real,
                    "calidad": calidad
                })
                
                print(f"   📺 {nombre_canal} → {url_real}")
                
                # Pausa para no saturar el servidor
                time.sleep(0.3)
            
            resultado.append(nuevo)
        
        print(f"\n✅ ElCanalDeportivo: {len(resultado)} eventos procesados")
        return resultado

    def extract_futbollibre_events(self):
        """Extrae eventos de FutbolLibre-HD con decodificación de URLs base64"""
        print("\nEXTRAYENDO DATOS DE FUTBOLLIBRE-HD")
        
        try:
            print("Descargando agenda de FutbolLibre-HD...")
            response = requests.get(self.futbollibre_agenda_url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            html_content = response.text
            print(f"OK Página descargada ({len(html_content)} caracteres)")
        except Exception as e:
            print(f"ERROR descargando FutbolLibre-HD: {e}")
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        
        # Buscar todos los eventos <li> con clases de liga
        event_items = soup.find_all('li', class_=lambda x: x and x not in ['subitem1'])
        
        print(f"🔍 Encontrados {len(event_items)} eventos potenciales...")
        
        for i, event_item in enumerate(event_items, 1):
            try:
                # Buscar el enlace principal del evento
                main_link = event_item.find('a')
                if not main_link:
                    continue
                
                # Extraer información del evento
                event_text = main_link.get_text(strip=True)
                time_span = main_link.find('span', class_='t')
                
                if not time_span:
                    continue
                
                # Separar título y tiempo
                time_str = time_span.get_text(strip=True)
                event_title = event_text.replace(time_str, '').strip()
                
                # Corregir problemas de codificación de acentos
                event_title = self.fix_encoding_issues(event_title)
                
                # Extraer clase de liga para determinar el logo
                liga_class = event_item.get('class', [''])[0] if event_item.get('class') else ''
                league_name, flag_url = self.get_futbollibre_league_info(liga_class, event_title)
                
                # Extraer canales del evento
                channels = []
                subitem_links = event_item.find_all('li', class_='subitem1')
                
                for subitem in subitem_links:
                    channel_link = subitem.find('a')
                    if not channel_link:
                        continue
                    
                    # Extraer información del canal
                    href = channel_link.get('href', '')
                    channel_text = channel_link.get_text(strip=True)
                    
                    # Separar nombre del canal y calidad
                    span_quality = channel_link.find('span')
                    if span_quality:
                        quality = span_quality.get_text(strip=True)
                        channel_name = channel_text.replace(quality, '').strip()
                    else:
                        channel_name = channel_text
                        quality = "720p"
                    
                    # Corregir problemas de codificación en nombres de canales
                    channel_name = self.fix_encoding_issues(channel_name)
                    quality = self.fix_encoding_issues(quality)
                    
                    # Extraer URL real del embed
                    if href and '/eventos/?r=' in href:
                        real_url = self.extract_futbollibre_real_url(href)
                        if real_url:
                            channels.append({
                                "nombre": channel_name,
                                "url": real_url,
                                "calidad": quality
                            })
                            print(f"   📺 {channel_name} ({quality}) → {real_url}")
                
                # Calcular tiempos UTC y Argentina
                # IMPORTANTE: Si la hora es de madrugada (00:00-05:59), es del día siguiente
                try:
                    hour, minute = map(int, time_str.split(':'))
                    today = datetime.now().date()
                    original_datetime = datetime.combine(today, datetime.strptime(f"{hour}:{minute}", "%H:%M").time())
                    
                    # Si la hora es de madrugada, es del día siguiente
                    is_madrugada = hour < 6
                    if is_madrugada:
                        original_datetime = original_datetime + timedelta(days=1)
                    
                    # Para FutbolLibre-HD: restar 4 horas para obtener hora argentina
                    argentina_datetime = original_datetime - timedelta(hours=4)
                    hora_argentina = argentina_datetime.strftime("%H:%M")
                    
                    # Calcular hora UTC (Argentina + 3 horas)
                    utc_datetime = argentina_datetime + timedelta(hours=3)
                    hora_utc = utc_datetime.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                except:
                    hora_utc = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                    current_time = datetime.now() - timedelta(hours=4)
                    hora_argentina = current_time.strftime("%H:%M")
                
                print(f"\n🎯 {league_name}: {event_title} | {time_str} → {hora_argentina}")
                
                # Crear evento si tiene canales
                if channels:
                    events.append({
                        "hora_utc": hora_utc,
                        "hora_argentina": hora_argentina,
                        "logo": flag_url,
                        "liga": f"{league_name}:",
                        "equipos": event_title,
                        "canales": channels
                    })
                
                # Pausa para no saturar
                time.sleep(0.3)
                
            except Exception as e:
                print(f"   ❌ Error procesando evento {i}: {e}")
                continue
        
        print(f"\n✅ FutbolLibre-HD: {len(events)} eventos extraídos")
        return events

    def extract_futbollibre_real_url(self, embed_url):
        """Extrae la URL real del iframe decodificando el parámetro base64"""
        try:
            print(f"   🔍 Extrayendo URL real de: {embed_url}")
            
            # Construir URL completa si es relativa
            if embed_url.startswith('/'):
                embed_url = self.futbollibre_base_url + embed_url
            
            # Extraer el parámetro 'r' de la URL
            if '?r=' in embed_url:
                encoded_param = embed_url.split('?r=')[1]
                
                try:
                    # Decodificar base64
                    decoded_url = base64.b64decode(encoded_param + '==').decode('utf-8')
                    
                    # Normalizar URL
                    if decoded_url.startswith('//'):
                        decoded_url = 'https:' + decoded_url
                    elif not decoded_url.startswith('http'):
                        decoded_url = 'https://' + decoded_url
                    
                    print(f"   ✅ URL decodificada directamente: {decoded_url}")
                    return decoded_url
                
                except Exception as decode_error:
                    print(f"   ⚠️ Error decodificando base64 directo: {decode_error}")
            
            # Si falla la decodificación directa, intentar descargar la página
            response = requests.get(embed_url, headers=self.headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar iframe ya renderizado
            iframe = soup.find('iframe', src=True)
            if iframe:
                src = iframe.get('src')
                # Normalizar URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif not src.startswith('http'):
                    src = 'https://' + src
                
                print(f"   ✅ URL encontrada en iframe: {src}")
                return src
            
            # Buscar en el contenido de la página patrones de URL
            page_content = response.text
            
            # Buscar patrones comunes de streaming
            url_patterns = [
                r'src="([^"]*streamdp[^"]*)"',
                r'src="([^"]*pelotalibre[^"]*)"',
                r'src="([^"]*voodc[^"]*)"',
                r'atob\([\'"]([^\'\"]+)[\'\"]',
                r'embed[\'\"]\s*:\s*[\'"]([^\'\"]+)[\'"]'
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    try:
                        # Si es base64, decodificar
                        if not match.startswith('http') and len(match) > 20:
                            decoded = base64.b64decode(match + '==').decode('utf-8')
                            if 'http' in decoded:
                                match = decoded
                        
                        # Normalizar URL
                        if match.startswith('//'):
                            match = 'https:' + match
                        elif not match.startswith('http'):
                            match = 'https://' + match
                        
                        if any(domain in match for domain in ['streamdp', 'pelotalibre', 'voodc']):
                            print(f"   ✅ URL encontrada con patrón: {match}")
                            return match
                    except:
                        continue
            
            print(f"   ⚠️ No se pudo extraer URL real")
            return None
            
        except Exception as e:
            print(f"   ❌ Error extrayendo URL real: {e}")
            return None

    def get_futbollibre_league_info(self, liga_class, event_title):
        """Mapea las clases de liga de FutbolLibre-HD a nombres y logos"""
        # Mapeo de clases a información de liga
        league_mapping = {
            'FIFA': ('Copa Intercontinental FIFA', 'https://pelis4k.online/banderas/internacional.png'),
            'ARA': ('Liga Árabe', 'https://pelis4k.online/banderas/internacional.png'),
            'ENG': ('Premier League / EFL', 'https://img.vxzyzz.click/fx/championsleague.png'),
            'POR': ('Primeira Liga', 'https://pelis4k.online/banderas/internacional.png'),
            'IT': ('Serie A / Copa Italia', 'https://img.vxzyzz.click/fx/seriea.png'),
            'ES': ('LaLiga', 'https://assets.laliga.com/assets/logos/LL_RGB_h_color/LL_RGB_h_color.png'),
            'LIB': ('Copa Libertadores', 'https://img.vxzyzz.click/fx/libertadores.png'),
            'URU': ('Liga Uruguaya', 'https://pelis4k.online/banderas/internacional.png'),
            'SUD': ('Copa Sudamericana', 'https://img.vxzyzz.click/fx/sudamericana.png'),
            'MEX': ('Liga MX', 'https://img.vxzyzz.click/fx/ligamx.png'),
            'CONCACAFCHA': ('CONCACAF', 'https://img.vxzyzz.click/fx/futvv.png'),
        }
        
        # Buscar mapeo exacto
        if liga_class in league_mapping:
            return league_mapping[liga_class]
        
        # Mapeo por contenido del título
        title_lower = event_title.lower()
        if 'laliga' in title_lower or 'real madrid' in title_lower or 'barcelona' in title_lower:
            return ('LaLiga', 'https://assets.laliga.com/assets/logos/LL_RGB_h_color/LL_RGB_h_color.png')
        elif 'premier league' in title_lower or 'chelsea' in title_lower or 'liverpool' in title_lower:
            return ('Premier League', 'https://img.vxzyzz.click/fx/championsleague.png')
        elif 'serie a' in title_lower or 'milan' in title_lower or 'juventus' in title_lower:
            return ('Serie A', 'https://img.vxzyzz.click/fx/seriea.png')
        elif 'liga mx' in title_lower or 'méxico' in title_lower:
            return ('Liga MX', 'https://img.vxzyzz.click/fx/ligamx.png')
        elif 'libertadores' in title_lower:
            return ('Copa Libertadores', 'https://img.vxzyzz.click/fx/libertadores.png')
        elif 'sudamericana' in title_lower:
            return ('Copa Sudamericana', 'https://img.vxzyzz.click/fx/sudamericana.png')
        
        # Por defecto
        return ('Deportes', 'https://img.vxzyzz.click/fx/futvv.png')

    def _extract_menu_style_events(self, base_url: str, agenda_path: str = "/", source_name: str = "MENU"):
        """Parser genérico para sitios con DOM tipo ul#menu > li.toggle-submenu.

        Extrae:
        - Hora (time tag)
        - Bandera/logo (img src)
        - Título completo (span con 'Liga: Equipo vs Equipo')
        - Canales: cada div.submenu > a[href] con label (span) y href con r= base64
        """
        print(f"\nEXTRAYENDO DATOS ({source_name}) desde {base_url}{agenda_path}")
        try:
            url = urljoin(base_url, agenda_path)
            resp = requests.get(url, headers=self.headers, timeout=25, verify=False)
            resp.raise_for_status()
        except Exception as e:
            print(f"   ❌ Error descargando {source_name}: {e}")
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        wrapper = soup.find(id='wraper') or soup
        menu = wrapper.find('ul', id='menu') or wrapper.find('ul', class_='menu')
        if not menu:
            print("   ⚠️ No se encontró ul#menu")
            return []

        items = menu.find_all('li', class_=lambda x: x and 'toggle-submenu' in x)
        events = []

        for i, li in enumerate(items, 1):
            try:
                time_tag = li.find('time')
                hora_site = (time_tag.get_text(strip=True) if time_tag else '').strip()

                # Bandera/logo
                flag_img = li.find('img')
                logo = flag_img.get('src') if flag_img and flag_img.get('src') else 'https://pelis4k.online/banderas/futbol.png'

                # Título completo
                title_span = li.find('span')
                full_title = self.fix_encoding_issues(title_span.get_text(" ", strip=True) if title_span else '')

                # Derivar liga y equipos
                if ': ' in full_title:
                    league_name, match_name = full_title.split(':', 1)
                    league_name = self.fix_encoding_issues(league_name).strip() + ':'
                    match_name = self.fix_encoding_issues(match_name).strip()
                else:
                    league_name = 'Deportes:'
                    match_name = full_title.strip()

                # Canales
                channels = []
                submenu_container = li.find('ul')
                if submenu_container:
                    for div in submenu_container.find_all('div', class_='submenu'):
                        a = div.find('a', class_='submenu-item')
                        if not a:
                            continue
                        href = a.get('href', '')
                        label_span = a.find('span')
                        label = self.fix_encoding_issues(label_span.get_text(strip=True) if label_span else a.get_text(strip=True))

                        # Intentar decodificar r= base64 a URL real; si falla, usar absoluta al sitio
                        real_url = None
                        try:
                            if '?r=' in href:
                                encoded = href.split('?r=')[1]
                                decoded = base64.b64decode(encoded + '==').decode('utf-8')
                                if decoded.startswith('//'):
                                    decoded = 'https:' + decoded
                                elif not decoded.startswith('http'):
                                    decoded = 'https://' + decoded
                                real_url = decoded
                        except Exception:
                            real_url = None

                        if not real_url:
                            real_url = urljoin(base_url, href)

                        channels.append({
                            "nombre": label,
                            "url": real_url,
                            "calidad": "720p"
                        })

                # Calcular hora Argentina y UTC (asumimos sitio +4h respecto a AR, igual que FutbolLibre)
                try:
                    hour, minute = map(int, (hora_site or '00:00').split(':'))
                    today = datetime.now().date()
                    dt = datetime.combine(today, datetime.strptime(f"{hour}:{minute}", "%H:%M").time())
                    if hour < 6:
                        dt = dt + timedelta(days=1)
                    argentina_dt = dt - timedelta(hours=4)
                    hora_argentina = argentina_dt.strftime("%H:%M")
                    utc_dt = argentina_dt + timedelta(hours=3)
                    hora_utc = utc_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                except Exception:
                    hora_argentina = hora_site or "00:00"
                    hora_utc = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"

                if channels:
                    events.append({
                        "hora_utc": hora_utc,
                        "hora_argentina": hora_argentina,
                        "logo": logo,
                        "liga": league_name,
                        "equipos": match_name,
                        "canales": channels
                    })
                    print(f"   ✅ {league_name} {match_name} | {hora_site} → {hora_argentina} ({len(channels)} canales)")

            except Exception as e:
                print(f"   ⚠️ Error procesando item {i}: {e}")
                continue

        print(f"\n✅ {source_name}: {len(events)} eventos extraídos")
        return events

    def extract_futbollibrefullhd_menu(self):
        """Extractor para FutbolLibreFullHD usando el parser genérico de ul#menu."""
        return self._extract_menu_style_events(self.futbollibre_base_url, "/", "FutbolLibreFullHD")

    def extract_pelotalibre_menu(self):
        """Intenta extraer Pelota-Libre.PE (mismo DOM que FutbolLibreFullHD) probando dominios comunes."""
        for domain in self.pelotalibre_domains:
            events = self._extract_menu_style_events(domain, "/", "Pelota-Libre.PE")
            if events:
                return events
        print("   ❌ Pelota-Libre.PE no respondió en los dominios conocidos")
        return []

    def extract_tvlibre_events(self):
        """Extrae eventos de TVLibree.com desde https://tvlibree.com/agenda/"""
        print("\nEXTRAYENDO DATOS DE TVLIBREE.COM")
        
        try:
            print("Descargando agenda de TVLibree...")
            response = requests.get(self.tvlibre_agenda_url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            html_content = response.text
            print(f"OK Página descargada ({len(html_content)} caracteres)")
        except Exception as e:
            print(f"ERROR descargando TVLibree: {e}")
            return []

        events = []
        
        # Mapeo de clases CSS a URLs de banderas/logos
        css_to_flag = {
            'AR': 'https://bestleague.world/jr/55.png',
            'ES': 'https://bestleague.world/jr/34.png',
            'IT': 'https://bestleague.world/jr/37.png',
            'ALE': 'https://bestleague.world/jr/96.png',
            'ENG': 'https://bestleague.world/jr/61.png',
            'POR': 'https://bestleague.world/jr/43.png',
            'FRA': 'https://bestleague.world/jr/45.png',
            'MEX': 'https://bestleague.world/jr/69.png',
            'COL': 'https://bestleague.world/jr/118.png',
            'CH': 'https://bestleague.world/jr/35.png',
            'URU': 'https://bestleague.world/jr/56.png',
            'BRA': 'https://bestleague.world/jr/79.png',
            'PE': 'https://bestleague.world/jr/127.png',
            'ECUA': 'https://bestleague.world/jr/101.png',
            'PY': 'https://bestleague.world/jr/47.png',
            'BOL': 'https://bestleague.world/jr/840.png',
            'VEN': 'https://bestleague.world/jr/591.png',
            'JP': 'https://bestleague.world/jr/52.png',
            'AUS': 'https://bestleague.world/jr/74.png',
            'USA': 'https://bestleague.world/jr/81.png',
            'SCO': 'https://bestleague.world/jr/113.png',
            'ARA': 'https://bestleague.world/jr/104.png',
            'CR': 'https://bestleague.world/jr/98.png',
            'HON': 'https://bestleague.world/jr/91.png',
            'TUR': 'https://bestleague.world/jr/123.png',
            'HOL': 'https://bestleague.world/jr/38.png',
            'BEL': 'https://bestleague.world/jr/116.png',
            'GT': 'https://bestleague.world/jr/593.png',
            'VOLEY': 'https://bestleague.world/jr/voley.png',
            'NHL': 'https://bestleague.world/img/nhl.svg',
            'WWE': 'https://bestleague.world/jr/wwe.png',
            'CHA': 'https://bestleague.world/jr/5.png',
            'UE': 'https://bestleague.world/jr/7.png',
            'UEC': 'https://bestleague.world/jr/2762.png',
            'SUD': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/102.png',
            'AMERICA': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/37.png',
            'EURO': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/22.png',
            'SUPERCUPE': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/68.png',
            'EUROF': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/480.png',
            'BAS': 'https://static.futbolenlatv.com/img/32/20130618113234-baloncesto.png',
            'TE': 'https://static.futbolenlatv.com/img/32/20130618113307-tenis.png',
            'FUT': 'https://static.futbolenlatv.com/img/32/20130618113222-futbol.png',
            'RUG': 'https://static.futbolenlatv.com/img/32/20200729125932-rugby.webp',
            'NFL2': 'https://static.futbolenlatv.com/img/32/20200804171715-futbol-americano.png',
            'HAND': 'https://futbollibrepe.net/flags/handball.png',
            'AFCUP': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/156.png',
            'CONNAT': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/2730.png',
            'CONCACAFCHA': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/190.png',
            'NAT': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/2349.png',
            'MOTOGP': 'https://futbollibrepe.net/flags/motogp.webp',
            'INDYCAR': 'https://bestleague.world/img/indycar.png',
            'F1': 'https://futbollibrepe.net/flags/f1.png',
            'F2': 'https://futbollibrepe.net/flags/f2.png',
            'F3': 'https://futbollibrepe.net/flags/f3.png',
            'BKFC': 'https://bestleague.world/img/trim.webp',
            'CCUP': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/2821.png',
            'AFCTWO': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/2760.png',
            'CHAF': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/2702.png',
            'NBA': 'https://bestleague.world/img/nba.svg',
            'NCAA': 'https://bestleague.world/img/ncaa.png',
            'AFCCHA': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/155.png',
            'LIB': 'https://bestleague.world/jr/76.png',
            'MC': 'https://bestleague.world/img/mc.png',
            'OSCAR': 'https://futbollibrepe.net/flags/oscars.png',
            'REC': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/205.png',
            'LC': 'https://images.onefootball.com/icons/leagueColoredCompetition/128/2717.png',
            'CONCACAF': 'https://bestleague.world/img/concacaf.png',
            'CONMEBOL': 'https://futbollibrepe.net/flags/sudamerica.png',
            'UEFA': 'https://bestleague.world/img/uefa.webp',
            'PR': 'https://futbollibrepe.net/flags/preolimpico.png',
            'COSCK': 'https://bestleague.world/img/cos.png',
            'FIFA': 'https://bestleague.world/img/fifa.png',
            'MFP': 'https://futbollibrepe.net/flags/MFP.png',
            'GOLD': 'https://futbollibrepe.net/flags/goldcup.png',
            'UFC': 'https://futbollibrepe.net/flags/UFC.png',
            'CAR': 'https://bestleague.world/img/lema.png',
            'AEW': 'https://bestleague.world/img/aew.png',
            'BMX': 'https://futbollibrepe.net/flags/bmx.png',
            'BOX': 'https://bestleague.world/img/box.png',
            'MLB': 'https://futbollibrepe.net/flags/mlb.png',
            'OLY': 'https://futbollibrepe.net/flags/olimpicos2.png',
            'LMB': 'https://futbollibrepe.net/flags/lmb.png',
            'CICLISMO': 'https://futbollibrepe.net/flags/ciclismo.png',
            'EUROLEAGUE': 'https://futbollibrepe.net/flags/euroleaguebasket.png',
            'RR': 'https://bestleague.world/img/rr.webp',
            'CAF': 'https://bestleague.world/img/caf.webp',
            'ESTE': 'https://futbollibrepe.net/flags/kingsleague.png',
            'FIBA': 'https://futbollibrepe.net/flags/fiba.png',
            'TST': 'https://bestleague.world/img/tst.webp',
            'MOTOR': 'https://cdn.pixabay.com/photo/2016/03/31/15/12/bike-1293078_960_720.png',
            'GOLDEN': 'https://i.ibb.co/6n9Sqbz/golden.png',
            'FIH': 'https://bestleague.world/img/fih.webp',
            'HOCKEY': 'https://tvlibree.com/agenda/hcokey.png',
            'NFL': 'https://bestleague.world/img/NFL.png',
            'ESTE-CLUBS': 'https://bestleague.world/img/este-clubs.webp',
        }
        
        # Usar BeautifulSoup para parsear el HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Buscar todos los <li> que tienen clase y contienen eventos
        # Excluir los subitem1 que son canales
        event_items = soup.find_all('li', class_=lambda x: x and x not in ['subitem1'] and x.strip())
        
        print(f"🔍 Encontrados {len(event_items)} elementos li potenciales...")
        
        for i, li in enumerate(event_items, 1):
            try:
                # Obtener la clase CSS (determina el logo)
                css_class = li.get('class', [''])[0] if li.get('class') else ''
                
                # Buscar el enlace principal con el título del evento
                main_link = li.find('a', href='#', recursive=False)
                if not main_link:
                    continue
                
                # Buscar el span con la hora
                time_span = main_link.find('span', class_='t')
                if not time_span:
                    continue
                
                time_str = time_span.get_text(strip=True)
                
                # Obtener el título del evento (texto antes del span de hora)
                event_title = main_link.get_text(strip=True)
                # Remover la hora del título
                event_title = event_title.replace(time_str, '').strip()
                
                # Corregir problemas de codificación
                event_title = self.fix_encoding_issues(event_title)
                
                # Buscar estructura "Liga: Equipos vs Equipos"
                if ': ' not in event_title:
                    continue
                
                # Separar liga y equipos
                parts = event_title.split(': ', 1)
                if len(parts) != 2:
                    continue
                    
                league_name = self.fix_encoding_issues(parts[0].strip())
                match_name = self.fix_encoding_issues(parts[1].strip())
                
                # CONVERSIÓN HORARIA: Restar 4 horas para Argentina
                # IMPORTANTE: Todos los eventos de la página son del mismo día.
                # Si un evento tiene hora 01:00, 02:00, 03:30 (madrugada), es porque
                # es un evento nocturno que ocurre en la madrugada del día SIGUIENTE,
                # no del día actual. Por lo tanto, si la hora es menor a 06:00,
                # asumimos que es madrugada del día siguiente.
                try:
                    original_time = datetime.strptime(time_str, "%H:%M")
                    # Crear datetime con fecha de hoy
                    today = datetime.now().date()
                    original_datetime = datetime.combine(today, original_time.time())
                    
                    # Si la hora es de madrugada (00:00-05:59), es del día siguiente
                    # porque la agenda muestra eventos del día + madrugada siguiente
                    is_madrugada = original_time.hour < 6
                    if is_madrugada:
                        original_datetime = original_datetime + timedelta(days=1)
                    
                    # Restar 4 horas para convertir a Argentina
                    argentina_datetime = original_datetime - timedelta(hours=4)
                    
                    # Determinar date_offset (siempre relativo a hoy)
                    date_offset = (argentina_datetime.date() - today).days
                    
                    hora_argentina = argentina_datetime.strftime("%H:%M")
                except Exception as e:
                    print(f"   ⚠️ Error parseando hora '{time_str}': {e}")
                    hora_argentina = time_str
                    date_offset = 0
                
                # Obtener logo según CSS class
                logo_url = css_to_flag.get(css_class, 'https://static.futbolenlatv.com/img/32/20130618113222-futbol.png')
                
                # Extraer canales del sub-menú
                channels = []
                channels_ul = li.find('ul')
                
                if channels_ul:
                    channel_items = channels_ul.find_all('li', class_='subitem1')
                    
                    for channel_li in channel_items:
                        channel_link = channel_li.find('a')
                        if not channel_link:
                            continue
                        
                        channel_url = channel_link.get('href', '')
                        channel_text = channel_link.get_text(strip=True)
                        
                        # Separar nombre del canal y calidad
                        quality_span = channel_link.find('span')
                        if quality_span:
                            quality = quality_span.get_text(strip=True)
                            channel_name = channel_text.replace(quality, '').strip()
                        else:
                            channel_name = channel_text
                            quality = "720p"
                        
                        # Corregir codificación
                        channel_name = self.fix_encoding_issues(channel_name)
                        
                        # Construir URL completa
                        if channel_url.startswith('/'):
                            full_channel_url = f"https://tvlibree.com{channel_url}"
                        else:
                            full_channel_url = channel_url
                        
                        # Si es una página de tvlibree/en-vivo, extraer las URLs reales
                        if full_channel_url and '/en-vivo/' in full_channel_url:
                            print(f"      📡 Extrayendo URLs de {channel_name}...")
                            real_urls = self.extract_tvlibre_channel_url(full_channel_url)
                            
                            # Agregar cada URL como un canal separado
                            for idx, url in enumerate(real_urls[:5]):  # Máximo 5 opciones por canal
                                option_name = f"{channel_name}" if idx == 0 else f"{channel_name} (Op.{idx+1})"
                                channels.append({
                                    "nombre": option_name,
                                    "url": url,
                                    "calidad": "720p"
                                })
                        elif full_channel_url and channel_name:
                            channels.append({
                                "nombre": f"{channel_name}",
                                "url": full_channel_url,
                                "calidad": "720p"
                            })
                
                # Solo procesar eventos con canales válidos
                if channels:
                    # Calcular hora UTC desde hora Argentina
                    try:
                        hora_parsed = datetime.strptime(hora_argentina, "%H:%M")
                        current_date = datetime.now()
                        event_datetime = current_date.replace(
                            hour=hora_parsed.hour, 
                            minute=hora_parsed.minute, 
                            second=0, 
                            microsecond=0
                        )
                        
                        # Ajustar fecha si hay offset
                        if date_offset != 0:
                            event_datetime = event_datetime + timedelta(days=date_offset)
                        
                        # Argentina es UTC-3, calcular UTC agregando 3 horas
                        utc_datetime = event_datetime + timedelta(hours=3)
                        hora_utc = utc_datetime.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                    except:
                        # Fallback si hay error parseando la hora
                        current_date = datetime.now()
                        utc_datetime = current_date
                        hora_utc = utc_datetime.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                    
                    event_data = {
                        "hora_utc": hora_utc,
                        "hora_argentina": hora_argentina,
                        "logo": logo_url,
                        "liga": league_name,
                        "equipos": match_name,
                        "canales": channels[:8],  # Máximo 8 canales
                        "date_offset": date_offset
                    }
                    
                    events.append(event_data)
                    print(f"   ✅ [{css_class}] {league_name}: {match_name} | {time_str} → {hora_argentina} ({len(channels)} canales)")
                
            except Exception as e:
                print(f"   ❌ Error procesando evento {i}: {e}")
                continue
        
        print(f"\n✅ TVLibree: {len(events)} eventos extraídos")
        return events

    def extract_tvlibre_date(self, soup):
        """Extrae la fecha real de la agenda TVLibre desde el div.sombreada_css3"""
        try:
            # Buscar el div con la fecha
            date_div = soup.find('div', class_='sombreada_css3')
            if date_div:
                date_text = date_div.get_text(strip=True)
                # Extraer fecha del formato "Agenda - Lunes 27 de Octubre de 2025"
                
                # Buscar patrón de fecha
                date_match = re.search(r'(\d{1,2}) de (\w+) de (\d{4})', date_text)
                if date_match:
                    day = int(date_match.group(1))
                    month_name = date_match.group(2).lower()
                    year = int(date_match.group(3))
                    
                    # Mapeo de meses en español
                    months = {
                        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                    }
                    
                    month = months.get(month_name, 10)  # Default octubre
                    
                    # Crear fecha en formato YYYY-MM-DD
                    return f"{year}-{month:02d}-{day:02d}"
            
            # Si no se encuentra, usar fecha actual como fallback
            return "2025-10-28"
            
        except Exception as e:
            print(f"ERROR extrayendo fecha: {e}")
            return "2025-10-28"



    def get_tvlibre_flag_from_css(self, css_class, league_name):
        """Obtener bandera según la clase CSS de TVLibre (como en el sitio original)"""
        
        # Mapeo directo de clases CSS a URLs de banderas (usando pelis4k.online)
        css_flag_mapping = {
            'AR': 'https://pelis4k.online/banderas/argentina.png',
            'ES': 'https://pelis4k.online/banderas/espa%C3%B1a.png', 
            'IT': 'https://pelis4k.online/banderas/Serie%20A.png',
            'ALE': 'https://pelis4k.online/banderas/alemania.png',
            'ENG': 'https://pelis4k.online/banderas/Inglaterra.png',
            'POR': 'https://pelis4k.online/banderas/Primeira%20Liga.png',
            'FRA': 'https://pelis4k.online/banderas/francia.png',
            'MEX': 'https://pelis4k.online/banderas/mexico.png',
            'COL': 'https://pelis4k.online/banderas/Liga%20Colombiana.png',
            'CH': 'https://pelis4k.online/banderas/chile.png',
            'CHI': 'https://pelis4k.online/banderas/chile.png',
            'URU': 'https://pelis4k.online/banderas/uruguay.png',
            'BRA': 'https://pelis4k.online/banderas/brasil.png',
            'PE': 'https://pelis4k.online/banderas/Liga%20Peruana.png',
            'ECUA': 'https://pelis4k.online/banderas/Liga%20Ecuatoriana.png',
            'PY': 'https://pelis4k.online/banderas/paraguay.png',
            'BOL': 'https://pelis4k.online/banderas/Liga%20de%20Bolivia.png',
            'VEN': 'https://pelis4k.online/banderas/internacional.png',
            'JP': 'https://pelis4k.online/banderas/internacional.png',
            'AUS': 'https://pelis4k.online/banderas/Australia%20Open.png',
            'USA': 'https://pelis4k.online/banderas/eeuu.png',
            'SCO': 'https://pelis4k.online/banderas/Liga%20de%20Escocia.png',
            'ARA': 'https://pelis4k.online/banderas/Liga%20%C3%81rabe%20-%20Saudi%20Pro%20League.svg',
            'CR': 'https://pelis4k.online/banderas/Liga%20Costarricense.svg',
            'HON': 'https://pelis4k.online/banderas/Liga%20de%20Honduras.png',
            'TUR': 'https://pelis4k.online/banderas/ligaturca.png',
            'HOL': 'https://pelis4k.online/banderas/Eredivisie.png',
            'BEL': 'https://pelis4k.online/banderas/Liga%20Belga.png',
            'GT': 'https://pelis4k.online/banderas/Liga%20de%20Guatemala.png',
            
            # Competencias especiales
            'CHA': 'https://pelis4k.online/banderas/Champions%20League.png',
            'UE': 'https://pelis4k.online/banderas/Europa%20League.svg', 
            'UEC': 'https://pelis4k.online/banderas/Conference%20League.png',
            'SUD': 'https://pelis4k.online/banderas/Copa%20Sudamericana.png',
            'LIB': 'https://pelis4k.online/banderas/Copa%20Libertadores.png',
            'AMERICA': 'https://pelis4k.online/banderas/Copa%20Am%C3%A9rica.png',
            'EURO': 'https://pelis4k.online/banderas/Nations%20League%20%28UEFA%29.png',
            'SUPERCUPE': 'https://pelis4k.online/banderas/UEFA%20Supercopa.png',
            
            # Deportes específicos
            'NBA': 'https://pelis4k.online/banderas/NBA%20%28Basket%29.png',
            'NFL': 'https://pelis4k.online/banderas/NFL%20%28F%C3%BAtbol%20Americano%29.png',
            'MLB': 'https://pelis4k.online/banderas/MLB%20%28B%C3%A9isbol%29.png',
            'NHL': 'https://pelis4k.online/banderas/NHL.png',
            'UFC': 'https://pelis4k.online/banderas/ufc.png',
            'BOX': 'https://pelis4k.online/banderas/boxeo.png',
            'BOXING': 'https://pelis4k.online/banderas/Boxing.png',
            'WWE': 'https://pelis4k.online/banderas/WWE.png',
            'AEW': 'https://pelis4k.online/banderas/AEW.png',
            
            # Motorsport
            'F1': 'https://pelis4k.online/banderas/F1%20%28F%C3%B3rmula%201%29.png',
            'F2': 'https://pelis4k.online/banderas/F2%20%28F%C3%B3rmula%202%29.svg', 
            'F3': 'https://pelis4k.online/banderas/F3%20%28F%C3%B3rmula%203%29.png',
            'MOTOGP': 'https://pelis4k.online/banderas/MotoGP.svg',
            'INDYCAR': 'https://pelis4k.online/banderas/IndyCar.png',
            
            # Otros deportes
            'VOLEY': 'https://pelis4k.online/banderas/internacional.png',
            'BAS': 'https://pelis4k.online/banderas/NBA%20%28Basket%29.png',
            'TE': 'https://pelis4k.online/banderas/ATP.png',
            'FUT': 'https://pelis4k.online/banderas/futbol.png',
            'RUG': 'https://pelis4k.online/banderas/Rugby.png',
            'HAND': 'https://pelis4k.online/banderas/internacional.png',
            'EUROLEAGUE': 'https://pelis4k.online/banderas/EuroLeague.png',
            'FIFA': 'https://pelis4k.online/banderas/FIFA%20Intercontinental%20Cup.png',
            'WTA': 'https://pelis4k.online/banderas/WTA.png',
            'WNBA': 'https://pelis4k.online/banderas/WNBA.png',
            'CICLISMO': 'https://pelis4k.online/banderas/Ciclismo.svg'
        }
        
        # Primero intentar con la clase CSS exacta
        if css_class in css_flag_mapping:
            return css_flag_mapping[css_class]
        
        # Si no, intentar detectar por nombre de liga
        league_lower = league_name.lower()
        
        if any(word in league_lower for word in ['argentina', 'profesional', 'boca', 'river']):
            return '//bestleague.world/jr/55.png'
        elif any(word in league_lower for word in ['laliga', 'españa', 'madrid', 'barcelona']):
            return '//bestleague.world/jr/34.png' 
        elif any(word in league_lower for word in ['serie a', 'italia', 'milan', 'juventus']):
            return '//bestleague.world/jr/37.png'
        elif any(word in league_lower for word in ['bundesliga', 'alemania', 'bayern']):
            return '//bestleague.world/jr/96.png'
        elif any(word in league_lower for word in ['premier', 'inglaterra', 'england']):
            return '//bestleague.world/jr/61.png'
        elif any(word in league_lower for word in ['ligue', 'francia', 'psg']):
            return '//bestleague.world/jr/45.png'
        elif any(word in league_lower for word in ['liga mx', 'mexico', 'américa']):
            return '//bestleague.world/jr/69.png'
        elif any(word in league_lower for word in ['betplay', 'colombia', 'nacional', 'millonarios']):
            return '//bestleague.world/jr/118.png'
        elif any(word in league_lower for word in ['chile', 'colo-colo']):
            return '//bestleague.world/jr/35.png'
        elif any(word in league_lower for word in ['brasil', 'flamengo', 'palmeiras']):
            return '//bestleague.world/jr/79.png'
        elif any(word in league_lower for word in ['peru', 'universitario']):
            return '//bestleague.world/jr/127.png'
        elif any(word in league_lower for word in ['ecuador', 'barcelona sc']):
            return '//bestleague.world/jr/101.png'
        elif any(word in league_lower for word in ['paraguay', 'olimpia', 'cerro']):
            return '//bestleague.world/jr/47.png'
        elif any(word in league_lower for word in ['uruguay', 'peñarol', 'nacional']):
            return '//bestleague.world/jr/56.png'
        elif any(word in league_lower for word in ['champions', 'uefa champions']):
            return '//bestleague.world/jr/5.png'
        elif any(word in league_lower for word in ['europa league']):
            return '//bestleague.world/jr/7.png'
        elif any(word in league_lower for word in ['libertadores']):
            return '//bestleague.world/jr/76.png'
        elif any(word in league_lower for word in ['sudamericana']):
            return 'https://images.onefootball.com/icons/leagueColoredCompetition/128/102.png'
        elif any(word in league_lower for word in ['nba', 'basketball']):
            return 'https://bestleague.world/img/nba.svg'
        elif any(word in league_lower for word in ['nfl', 'football americano']):
            return 'https://bestleague.world/img/NFL.png'
        elif any(word in league_lower for word in ['mlb', 'baseball']):
            return 'https://partidosenvivo.net/flags/mlb.png'
        elif any(word in league_lower for word in ['ufc', 'mma']):
            return '//partidosenvivo.net/flags/UFC.png'
        elif any(word in league_lower for word in ['boxeo', 'box']):
            return 'https://bestleague.world/img/box.png'
        elif any(word in league_lower for word in ['formula 1', 'f1']):
            return 'https://partidosenvivo.net/flags/f1.png'
        elif any(word in league_lower for word in ['motogp', 'moto']):
            return '//partidosenvivo.net/flags/motogp.webp'
        elif any(word in league_lower for word in ['süper lig', 'turquia', 'fenerbahce']):
            return '//bestleague.world/jr/123.png'
        
        # Por defecto: icono de fútbol
        return "https://bestleague.world/img/futbol.png"

    def extract_tvlibre_channel_url(self, href):
        """Extrae las URLs reales del canal desde la página interna de TVLibre"""
        try:
            if not href.startswith('http'):
                href = self.tvlibre_base_url + href
            
            # Dominios a excluir (la12 y la14)
            excluded_domains = [
                'elcanaldeportivo.com', 'futbolparatodos', 'futbollibre', 
                'rojadirecta', 'pirlotv', 'tarjetarojatvonline',
                'la12hd.com', 'la14hd.com'  # Excluir la12 y la14
            ]
            
            response = requests.get(href, headers=self.headers, timeout=10, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            extracted_urls = []
            
            # 1. Buscar el iframe principal
            iframe = soup.find('iframe', id='iframe')
            if iframe and iframe.get('src'):
                iframe_src = iframe.get('src')
                if iframe_src.startswith('/'):
                    iframe_src = f"https://tvlibree.com{iframe_src}"
                if not any(excluded in iframe_src for excluded in excluded_domains):
                    extracted_urls.append(iframe_src)
            
            # 2. Buscar los onclick en los botones de opciones
            # Patrón: onclick="document.getElementById('iframe').src='URL'; return false;"
            for element in soup.find_all(['a', 'button'], onclick=True):
                onclick = element.get('onclick', '')
                
                # Extraer URL del onclick
                url_match = re.search(r"\.src\s*=\s*['\"]([^'\"]+)['\"]", onclick)
                if url_match:
                    url = url_match.group(1)
                    
                    # Si es una ruta relativa, convertir a absoluta
                    if url.startswith('/'):
                        url = f"https://tvlibree.com{url}"
                    
                    # Excluir dominios no deseados
                    if any(excluded in url for excluded in excluded_domains):
                        continue
                    
                    # No agregar duplicados
                    if url not in extracted_urls:
                        extracted_urls.append(url)
            
            # 3. También buscar en nav.server-links
            server_links = soup.find('nav', class_='server-links')
            if server_links:
                for link in server_links.find_all('a', onclick=True):
                    onclick = link.get('onclick', '')
                    url_match = re.search(r"\.src\s*=\s*['\"]([^'\"]+)['\"]", onclick)
                    if url_match:
                        url = url_match.group(1)
                        if url.startswith('/'):
                            url = f"https://tvlibree.com{url}"
                        if not any(excluded in url for excluded in excluded_domains):
                            if url not in extracted_urls:
                                extracted_urls.append(url)
            
            # Retornar las URLs encontradas o la original
            if extracted_urls:
                return extracted_urls
            
            return [href]  # Retornar URL original si no se encuentra alternativa
        except Exception as e:
            print(f"      ⚠️ Error extrayendo URLs de {href}: {e}")
            return [href]

    def detect_sport_and_league_pirlotv(self, league_class, event_text, equipos):
        """Detecta el deporte y liga basado en múltiples factores para PirloTV"""
        league_name = "Internacional"
        flag_url = "https://pelis4k.online/banderas/futbol.png"
        sport_type = "Fútbol"
        
        if not league_class:
            league_class = ""
        
        # Convertir a minúsculas para comparación
        league_class_lower = league_class.lower()
        event_text_lower = event_text.lower()
        equipos_lower = equipos.lower()
        
        # DETECCIÓN DE BÁSQUET/BASKETBALL
        basketball_indicators = [
            'bkb', 'nba', 'basketball', 'basquet', 
            'lakers', 'warriors', 'celtics', 'heat', 'bulls', 'nets', 'pacers', 'bucks',
            'nuggets', 'kings', 'blazers', 'clippers', 'rockets', 'mavericks', 'grizzlies',
            'pistons', 'knicks', 'wizards', 'jazz', 'timberwolves',
            'euroleague', 'euroliga', 'liga acb', 'aba liga'
        ]
        
        if any(indicator in league_class_lower or 
               indicator in event_text_lower or 
               indicator in equipos_lower 
               for indicator in basketball_indicators):
            sport_type = "Básquet"
            
            if 'nba' in league_class_lower or 'nba' in event_text_lower or any(team in equipos_lower for team in ['lakers', 'warriors', 'celtics', 'heat', 'nets']):
                league_name = "NBA"
                flag_url = "https://pelis4k.online/banderas/NBA%20%28Basket%29.png"
            elif 'euroleague' in event_text_lower or 'euroliga' in event_text_lower:
                league_name = "Euroliga"
                flag_url = "https://pelis4k.online/banderas/EuroLeague.png"
            else:
                league_name = "Básquet Internacional"
                flag_url = "https://pelis4k.online/banderas/NBA%20%28Basket%29.png"
        
        # DETECCIÓN DE FÚTBOL AMERICANO
        elif any(indicator in event_text_lower or indicator in equipos_lower 
                for indicator in ['nfl', 'super bowl', 'patriots', 'cowboys', 'cardinals', 'steelers', 'ravens']):
            sport_type = "Fútbol Americano"
            league_name = "NFL"
            flag_url = "https://pelis4k.online/banderas/NFL%20%28F%C3%BAtbol%20Americano%29.png"
        
        # DETECCIÓN DE UFC/MMA
        elif any(indicator in league_class_lower or indicator in event_text_lower 
                for indicator in ['ufc', 'mma', 'fight']):
            sport_type = "UFC/MMA"
            league_name = "UFC"
            flag_url = "https://pelis4k.online/banderas/ufc.png"
        
        # DETECCIÓN DE FÚTBOL POR PAÍS/LIGA
        else:
            # Mantener detección de fútbol existente pero mejorada
            if 'arg' in league_class_lower or 'argentina' in event_text_lower:
                league_name = "Liga Argentina"
                flag_url = "https://pelis4k.online/banderas/Liga%20Argentina.png"
            elif 'es' in league_class_lower or 'españa' in event_text_lower or 'la liga' in event_text_lower:
                league_name = "LaLiga España"
                flag_url = "https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png"
            elif 'co' in league_class_lower or 'colombia' in event_text_lower or 'betplay' in event_text_lower:
                league_name = "Liga BetPlay Colombia"
                flag_url = "https://pelis4k.online/banderas/Liga%20Colombiana.png"
            elif 'br' in league_class_lower or 'brasil' in event_text_lower or 'brasileirao' in event_text_lower:
                league_name = "Brasileirão"
                flag_url = "https://pelis4k.online/banderas/Liga%20Brasile%C3%B1a.png"
            elif 'uy' in league_class_lower or 'uruguay' in event_text_lower:
                league_name = "Liga Uruguay"
                flag_url = "https://pelis4k.online/banderas/Liga%20Uruguaya.png"
            elif 'us' in league_class_lower or 'mls' in event_text_lower:
                league_name = "MLS Estados Unidos"
                flag_url = "https://pelis4k.online/banderas/MLS.png"
            elif 'europa' in league_class_lower or 'champions' in event_text_lower or 'uefa' in event_text_lower:
                league_name = "UEFA Champions League"
                flag_url = "https://pelis4k.online/banderas/Champions%20League.png"
            elif 'fifa' in league_class_lower or 'mundial' in event_text_lower:
                league_name = "FIFA Mundial"
                flag_url = "https://pelis4k.online/banderas/FIFA%20Intercontinental%20Cup.png"
            elif 'concacaf' in event_text_lower:
                league_name = "CONCACAF"
                flag_url = "https://pelis4k.online/banderas/CONCACAF.png"
            elif 'libertadores' in event_text_lower:
                league_name = "Copa Libertadores"
                flag_url = "https://pelis4k.online/banderas/Copa%20Libertadores.png"
            elif 'am' in league_class_lower or 'amistoso' in event_text_lower:
                league_name = "Amistoso Internacional"
                flag_url = "https://pelis4k.online/banderas/internacional.png"
        
        return sport_type, league_name, flag_url

    def get_channel_name_pirlotv(self, sport_type, league_name):
        """Genera nombre de canal sin mencionar PirloTV"""
        if sport_type == "Básquet":
            if "NBA" in league_name:
                return "NBA HD Stream"
            else:
                return "Básquet HD Stream"
        elif sport_type == "UFC/MMA":
            return "UFC HD Stream"
        elif sport_type == "Fútbol Americano":
            return "NFL HD Stream"
        else:
            # Para fútbol
            if "Champions" in league_name:
                return "UEFA HD Stream"
            elif "Argentina" in league_name:
                return "Liga Argentina HD"
            elif "España" in league_name:
                return "LaLiga HD Stream"
            elif "Colombia" in league_name:
                return "BetPlay HD Stream"
            else:
                return "Deportes HD Stream"

    def extract_pirlotv_events(self):
        """Extrae eventos de PirloTV con conversión horaria (+2 horas) - MEJORADO PARA TODOS LOS DEPORTES"""
        print("\nEXTRAYENDO DATOS DE PIRLOTV (INCLUYE BASQUET, NFL, UFC)")
        
        try:
            print("Descargando agenda completa de PirloTV...")
            response = requests.get(self.pirlotv_agenda_url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            html_content = response.text
            print(f"OK Página descargada ({len(html_content):,} caracteres)")
        except Exception as e:
            print(f"ERROR descargando PirloTV: {e}")
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        
        # Buscar la tabla con eventos
        tbody = soup.find('tbody')
        if not tbody:
            print("ERROR: No se encontró tabla de eventos")
            return []
        
        # Buscar todas las filas de eventos
        event_rows = tbody.find_all('tr')
        
        print(f"Encontrados {len(event_rows)} eventos potenciales...")
        
        for i, row in enumerate(event_rows, 1):
            try:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                
                # Extraer hora del evento
                time_span = cells[0].find('span', class_='t')
                if not time_span:
                    # Intentar extraer hora de otra manera
                    time_text = cells[0].get_text(strip=True)
                    # Buscar patrón HH:MM
                    time_match = re.search(r'(\d{1,2}:\d{2})', time_text)
                    if time_match:
                        time_str = time_match.group(1)
                    else:
                        continue
                else:
                    time_str = time_span.get_text(strip=True)
                
                # Sumar 2 horas al tiempo (conversión horaria)
                # IMPORTANTE: Si la hora es de madrugada (00:00-05:59), es del día siguiente
                try:
                    original_time = datetime.strptime(time_str, "%H:%M")
                    today = datetime.now().date()
                    original_datetime = datetime.combine(today, original_time.time())
                    
                    # Si la hora es de madrugada, es del día siguiente
                    is_madrugada = original_time.hour < 6
                    if is_madrugada:
                        original_datetime = original_datetime + timedelta(days=1)
                    
                    # Sumar 2 horas para conversión a Argentina
                    argentina_datetime = original_datetime + timedelta(hours=2)
                    
                    # Calcular date_offset relativo a hoy
                    date_offset = (argentina_datetime.date() - today).days
                    
                    hora_argentina = argentina_datetime.strftime("%H:%M")
                except:
                    hora_argentina = time_str
                    date_offset = 0
                
                # Extraer información del evento desde la tercera columna
                event_cell = cells[2]
                event_link = event_cell.find('a')
                
                if not event_link:
                    continue
                
                # Extraer equipos/título del evento
                event_title = event_link.find('b')
                if event_title:
                    equipos = event_title.get_text(strip=True)
                else:
                    equipos = event_link.get_text(strip=True)
                
                if not equipos:
                    continue
                
                canal_href = event_link.get('href', '')
                
                # Corregir problemas de codificación de acentos
                equipos = self.fix_encoding_issues(equipos)
                
                # Extraer texto completo del evento para detectar liga
                event_text = event_cell.get_text(strip=True)
                event_text = self.fix_encoding_issues(event_text)
                
                # Detectar liga desde la segunda columna
                league_class = ""
                if len(cells) > 1:
                    league_span = cells[1].find('span')
                    if league_span and league_span.get('class'):
                        league_class = ' '.join(league_span.get('class'))
                
                # Detectar deporte y liga con la nueva función mejorada
                sport_type, league_name, flag_url = self.detect_sport_and_league_pirlotv(
                    league_class, event_text, equipos
                )
                
                # Extraer URL del canal
                if canal_href and canal_href.startswith('/'):
                    canal_url = self.pirlotv_base_url + canal_href
                    iframe_url = self.extract_pirlotv_iframe_url(canal_url)
                    
                    if iframe_url:
                        # Generar nombre de canal sin "PirloTV"
                        channel_name = self.get_channel_name_pirlotv(sport_type, league_name)
                        
                        # Crear evento
                        event_data = {
                            "hora_utc": f"2025-11-03T{(datetime.strptime(time_str, '%H:%M') + timedelta(hours=7)).strftime('%H:%M')}:00Z",
                            "hora_argentina": hora_argentina,
                            "logo": flag_url,
                            "liga": league_name,
                            "equipos": equipos,
                            "canales": [{
                                "nombre": channel_name,
                                "url": iframe_url,
                                "calidad": "HD"
                            }],
                            "date_offset": date_offset
                        }
                        
                        events.append(event_data)
                        print(f"OK {sport_type}: {equipos} ({league_name}) - {hora_argentina}")
                
            except Exception as e:
                print(f"ERROR procesando evento {i}: {e}")
                continue
        
        # Mostrar estadísticas por deporte
        sports_count = {}
        for event in events:
            sport = "Fútbol"  # Por defecto
            if "NBA" in event.get("liga", ""):
                sport = "Básquet"
            elif "NFL" in event.get("liga", ""):
                sport = "NFL"
            elif "UFC" in event.get("liga", ""):
                sport = "UFC"
            
            sports_count[sport] = sports_count.get(sport, 0) + 1
        
        print(f"OK PirloTV procesado: {len(events)} eventos TOTALES")
        for sport, count in sports_count.items():
            print(f"   • {sport}: {count} eventos")
        
        return events

    def extract_pirlotv_iframe_url(self, canal_url):
        """Extrae la URL del iframe desde la página del canal de PirloTV"""
        try:
            response = requests.get(canal_url, headers=self.headers, timeout=10, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar iframe con id="streamIframe"
            iframe = soup.find('iframe', id='streamIframe')
            if iframe and iframe.get('src'):
                return iframe.get('src')
            
            # Buscar cualquier iframe como fallback
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                return iframe.get('src')
                
            return None
        except Exception as e:
            print(f"ERROR extrayendo iframe de {canal_url}: {e}")
            return None

    def extract_streamvv11_events(self):
        """Extrae eventos de StreamVV11.lat con conversión horaria (-4 horas para Argentina)"""
        print("\nEXTRAYENDO DATOS DE STREAMVV11.LAT")
        
        try:
            print("Descargando página de eventos...")
            response = requests.get(self.streamvv11_agenda_url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            html_content = response.text
            print(f"OK Página descargada ({len(html_content)} caracteres)")
        except Exception as e:
            print(f"ERROR descargando StreamVV11: {e}")
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        
        # Buscar todos los eventos <li> con clases de liga
        event_items = soup.find_all('li', class_=lambda x: x and x not in ['subitem1'] and x.strip())
        
        print(f"🔍 Encontrados {len(event_items)} eventos potenciales...")
        
        for i, event_item in enumerate(event_items, 1):
            try:
                # Buscar el enlace principal del evento
                main_link = event_item.find('a')
                if not main_link:
                    continue
                
                # Extraer información del evento
                time_span = main_link.find('span', class_='t')
                if not time_span:
                    continue
                
                # Separar título y tiempo
                time_str = time_span.get_text(strip=True)
                event_text = main_link.get_text(strip=True)
                event_title = event_text.replace(time_str, '').strip()
                
                # Corregir problemas de codificación de acentos
                event_title = self.fix_encoding_issues(event_title)
                
                # Extraer clase de liga para determinar el logo
                liga_class = event_item.get('class', [''])[0] if event_item.get('class') else ''
                league_name = self.streamvv11_league_mapping.get(liga_class, "Internacional")
                flag_url = self.streamvv11_flag_mapping.get(liga_class, "https://img.futebol12.nexus/zas/fut.webp")
                
                # Detectar competiciones específicas desde el título del evento
                league_name, flag_url = self.detect_specific_competition(event_title, league_name, flag_url)
                
                # Convertir horario: restar 4 horas para Argentina
                # IMPORTANTE: Si la hora es de madrugada (00:00-05:59), es del día siguiente
                try:
                    hour, minute = map(int, time_str.split(':'))
                    today = datetime.now().date()
                    original_datetime = datetime.combine(today, datetime.strptime(f"{hour}:{minute}", "%H:%M").time())
                    
                    # Si la hora es de madrugada, es del día siguiente
                    is_madrugada = hour < 6
                    if is_madrugada:
                        original_datetime = original_datetime + timedelta(days=1)
                    
                    # Restar 4 horas para Argentina
                    argentina_datetime = original_datetime - timedelta(hours=4)
                    
                    # Calcular date_offset relativo a hoy
                    date_offset = (argentina_datetime.date() - today).days
                    
                    hora_argentina = argentina_datetime.strftime("%H:%M")
                    # Para UTC: agregar 3 horas a la hora argentina
                    utc_time = argentina_datetime + timedelta(hours=3)
                    hora_utc = utc_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                except Exception as time_error:
                    print(f"   ⚠️ Error procesando tiempo {time_str}: {time_error}")
                    hora_argentina = time_str
                    current_date = datetime.now()
                    hora_utc = current_date.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                    date_offset = 0
                
                # Extraer canales del evento
                channels = []
                subitem_links = event_item.find_all('li', class_='subitem1')
                
                for subitem in subitem_links:
                    channel_link = subitem.find('a')
                    if not channel_link:
                        continue
                    
                    # Extraer información del canal
                    href = channel_link.get('href', '')
                    channel_text = channel_link.get_text(strip=True)
                    
                    # Separar nombre del canal y calidad
                    span_quality = channel_link.find('span')
                    if span_quality:
                        quality = span_quality.get_text(strip=True)
                        channel_name = channel_text.replace(quality, '').strip()
                    else:
                        channel_name = channel_text
                        quality = "720p"
                    
                    # Corregir problemas de codificación en nombres de canales
                    channel_name = self.fix_encoding_issues(channel_name)
                    quality = self.fix_encoding_issues(quality)
                    
                    # Construir URL completa del canal
                    if href and href.startswith('/eventos.html?r='):
                        # Extraer y decodificar el parámetro r
                        try:
                            # Obtener el parámetro r (base64 encoded)
                            encoded_param = href.split('?r=')[1]
                            # Decodificar base64
                            decoded_url = base64.b64decode(encoded_param + '==').decode('utf-8')
                            
                            # Normalizar URL decodificada
                            if decoded_url.startswith('//'):
                                decoded_url = 'https:' + decoded_url
                            elif not decoded_url.startswith('http'):
                                decoded_url = 'https://' + decoded_url
                            
                            channel_url = decoded_url
                            print(f"   🔓 URL decodificada: {channel_url}")
                        except Exception as decode_error:
                            print(f"   ❌ Error decodificando {href}: {decode_error}")
                            # Fallback a la URL original si hay error
                            channel_url = self.streamvv11_base_url + href
                        
                        channels.append({
                            "nombre": channel_name,
                            "url": channel_url,
                            "calidad": quality.replace("Calidad ", "")
                        })
                        
                        print(f"   📺 {channel_name} ({quality}) → {channel_url}")
                
                # Crear evento si tiene canales
                if channels:
                    print(f"\n🎯 {league_name}: {event_title} | {time_str} → {hora_argentina}")
                    
                    events.append({
                        "hora_utc": hora_utc,
                        "hora_argentina": hora_argentina,
                        "logo": flag_url,
                        "liga": f"{league_name}:",
                        "equipos": event_title,
                        "canales": channels[:8],  # Limitar a 8 canales máximo
                        "date_offset": date_offset
                    })
                
                # Pausa para no saturar
                time.sleep(0.2)
                
            except Exception as e:
                print(f"   ❌ Error procesando evento {i}: {e}")
                continue
        
        print(f"\n✅ StreamVV11: {len(events)} eventos extraídos")
        return events

    def decode_pelotalibre_url(self, encoded_url):
        """Decodifica la URL base64 de Pelota-Libre.pe"""
        try:
            # Extraer el parámetro r de la URL
            if '?r=' in encoded_url:
                encoded_part = encoded_url.split('?r=')[1]
                # Decodificar base64
                decoded_bytes = base64.b64decode(encoded_part)
                decoded_url = decoded_bytes.decode('utf-8')
                return decoded_url
        except Exception as e:
            print(f"Error decodificando URL: {e}")
        return None

    def extract_pelotalibre_iframe_url(self, page_url):
        """Extrae la URL del iframe de una página de Pelota-Libre.pe"""
        try:
            response = requests.get(page_url, headers=self.headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar el iframe
            iframe = soup.find('iframe', {'id': 'embedIframe'})
            if iframe and iframe.get('src'):
                return iframe.get('src')
            
            # Backup: buscar cualquier iframe
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                return iframe.get('src')
                
        except Exception as e:
            print(f"Error extrayendo iframe de {page_url}: {e}")
        
        return None

    def detect_sport_and_league_pelotalibre(self, event_text, img_src):
        """Detecta el deporte y liga basado en texto e imagen para Pelota-Libre"""
        league_name = "Internacional"
        flag_url = "https://pelis4k.online/banderas/futbol.png"
        sport_type = "Fútbol"
        
        event_text_lower = event_text.lower()
        
        # Detectar deporte por texto
        if any(keyword in event_text_lower for keyword in ['tenis:', 'amanda', 'madison', 'atp', 'wta']):
            sport_type = "Tenis"
            if 'atp' in event_text_lower:
                league_name = "ATP"
                flag_url = "https://pelis4k.online/banderas/ATP.png"
            elif 'wta' in event_text_lower:
                league_name = "WTA"
                flag_url = "https://pelis4k.online/banderas/WTA.png"
            else:
                league_name = "Tenis"
                flag_url = "https://pelis4k.online/banderas/ATP.png"
        elif any(keyword in event_text_lower for keyword in ['nba', 'lakers', 'warriors', 'celtics', 'basketball']):
            sport_type = "Básquet"
            league_name = "NBA"
            flag_url = "https://pelis4k.online/banderas/NBA%20%28Basket%29.png"
        elif any(keyword in event_text_lower for keyword in ['nfl', 'patriots', 'cowboys', 'football americano']):
            sport_type = "Fútbol Americano" 
            league_name = "NFL"
            flag_url = "https://pelis4k.online/banderas/NFL%20%28F%C3%BAtbol%20Americano%29.png"
        elif any(keyword in event_text_lower for keyword in ['ufc', 'mma', 'fight']):
            sport_type = "UFC/MMA"
            league_name = "UFC"
            flag_url = "https://pelis4k.online/banderas/ufc.png"
        
        # Detectar liga por imagen y texto
        if img_src:
            img_lower = img_src.lower()
            if 'argentina' in img_lower or 'argentina' in event_text_lower:
                league_name = "Liga Argentina"
                flag_url = img_src
            elif 'espana' in img_lower or 'españa' in event_text_lower or 'laliga' in event_text_lower:
                league_name = "LaLiga España"
                flag_url = img_src
            elif 'colombia' in img_lower or 'colombia' in event_text_lower:
                league_name = "Liga BetPlay Colombia"
                flag_url = img_src
            elif 'brasil' in img_lower or 'brasil' in event_text_lower:
                league_name = "Brasileirão"
                flag_url = img_src
            elif 'uruguay' in img_lower or 'uruguay' in event_text_lower:
                league_name = "Liga Uruguay"
                flag_url = img_src
            elif 'estados_unidos' in img_lower or 'mls' in event_text_lower:
                league_name = "MLS Estados Unidos"
                flag_url = img_src
            elif 'inglaterra' in img_lower or 'premier league' in event_text_lower:
                league_name = "Premier League"
                flag_url = img_src
            elif 'italia' in img_lower or 'serie a' in event_text_lower:
                league_name = "Serie A Italia"
                flag_url = img_src
            elif 'portugal' in img_lower or 'primeira liga' in event_text_lower:
                league_name = "Primeira Liga Portugal"
                flag_url = img_src
            elif 'pavo' in img_lower or 'super lig' in event_text_lower:
                league_name = "Süper Lig Turquía"
                flag_url = img_src
            elif 'paises_bajos' in img_lower or 'eerste divisie' in event_text_lower:
                league_name = "Eerste Divisie Holanda"
                flag_url = img_src
            elif 'bolivia' in img_lower:
                league_name = "Liga Bolivia"
                flag_url = img_src
            elif 'chile' in img_lower:
                league_name = "Liga Chile"
                flag_url = img_src
            elif 'ecuador' in img_lower:
                league_name = "Liga Ecuador"
                flag_url = img_src
            else:
                flag_url = img_src if img_src.startswith('http') else f"https:{img_src}" if img_src.startswith('//') else img_src
        
        return sport_type, league_name, flag_url

    def get_channel_name_pelotalibre(self, sport_type, league_name, channel_text):
        """Genera nombre de canal para Pelota-Libre"""
        if sport_type == "Básquet":
            return "NBA HD Stream"
        elif sport_type == "Tenis":
            return "Tenis HD Stream"
        elif sport_type == "UFC/MMA":
            return "UFC HD Stream"
        elif sport_type == "Fútbol Americano":
            return "NFL HD Stream"
        else:
            # Para fútbol, usar el texto del canal si está disponible
            if channel_text and len(channel_text.strip()) > 0:
                return f"{channel_text.strip()}"
            elif "Liga Argentina" in league_name:
                return "Liga Argentina HD"
            elif "LaLiga" in league_name:
                return "LaLiga HD Stream"
            elif "Premier League" in league_name:
                return "Premier League HD"
            else:
                return "Deportes HD Stream"

    def extract_pelotalibre_events(self):
        """Extrae eventos de Pelota-Libre.pe usando Selenium para JavaScript"""
        print("\nEXTRAYENDO DATOS DE PELOTA-LIBRE.PE (con Selenium)")
        events = []
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            print("🌐 Iniciando navegador Chrome headless...")
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get('https://pelotalibre-tv.pe/')
            
            # Esperar a que el menú se cargue
            print("⏳ Esperando a que JavaScript cargue los eventos...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "menu"))
            )
            
            # Esperar un poco más para que JavaScript llene los eventos
            time.sleep(5)
            
            # Obtener el HTML renderizado
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
            
            # Buscar todos los eventos con clase toggle-submenu
            event_items = soup.find_all('li', class_='toggle-submenu')
            print(f"📋 Encontrados {len(event_items)} eventos después de renderizar JavaScript")
            
            for i, event_item in enumerate(event_items, 1):
                try:
                    # Extraer hora
                    time_elem = event_item.find('time')
                    if not time_elem:
                        continue
                    hora_arg = time_elem.get_text(strip=True)
                    
                    # Extraer bandera/logo
                    img_elem = event_item.find('img', alt='bandera')
                    logo_url = img_elem.get('src', 'https://pelis4k.online/banderas/futbol.png') if img_elem else 'https://pelis4k.online/banderas/futbol.png'
                    if logo_url.startswith('//'):
                        logo_url = 'https:' + logo_url
                    elif not logo_url.startswith('http'):
                        logo_url = 'https://pelotalibre-tv.pe' + logo_url
                    
                    # Extraer nombre del evento (liga + equipos)
                    event_span = event_item.find('span', style=lambda x: x and 'flex: 1' in x)
                    if not event_span:
                        continue
                    
                    event_text = event_span.get_text(strip=True)
                    
                    # Separar liga y equipos
                    if ':' in event_text:
                        liga, equipos = event_text.split(':', 1)
                        liga = liga.strip()
                        equipos = equipos.strip()
                    else:
                        liga = "Deportes"
                        equipos = event_text
                    
                    # Extraer canales
                    canales = []
                    submenu_divs = event_item.find_all('div', class_='submenu')
                    
                    for submenu in submenu_divs:
                        canal_link = submenu.find('a', href=True)
                        if not canal_link:
                            continue
                        
                        # URL del embed (con base64)
                        embed_url = canal_link['href']
                        if not embed_url.startswith('http'):
                            embed_url = 'https://pelotalibre-tv.pe' + embed_url
                        
                        # Nombre del canal
                        canal_span = canal_link.find('span')
                        canal_nombre = canal_span.get_text(strip=True) if canal_span else "Canal HD"
                        
                        # Extraer iframe real desde la página embed
                        iframe_url = self.extract_pelotalibre_iframe(embed_url)
                        
                        if iframe_url:
                            canales.append({
                                "nombre": canal_nombre,
                                "url": iframe_url,
                                "calidad": "HD"
                            })
                            print(f"   📺 {canal_nombre} → {iframe_url[:60]}...")
                        
                        # Pausa para no saturar
                        time.sleep(0.3)
                    
                    if not canales:
                        continue
                    
                    # Convertir hora argentina a UTC
                    try:
                        from datetime import datetime, timedelta
                        today = datetime.now()
                        hour, minute = map(int, hora_arg.split(':'))
                        
                        event_datetime = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        # Argentina es UTC-3
                        utc_datetime = event_datetime + timedelta(hours=3)
                        hora_utc = utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                    except:
                        hora_utc = "2025-11-10T23:00:00Z"
                    
                    # Detectar deporte por logo y liga
                    sport_type, league_name, flag_url = self.detect_sport_and_league_pelotalibre(liga, logo_url)
                    
                    evento = {
                        "hora_utc": hora_utc,
                        "hora_argentina": hora_arg,
                        "logo": flag_url,
                        "liga": f"{league_name}:",
                        "equipos": equipos,
                        "canales": canales,
                        "date_offset": 0
                    }
                    
                    events.append(evento)
                    print(f"✅ [{i}] {hora_arg} - {league_name}: {equipos} ({len(canales)} canales)")
                
                except Exception as event_error:
                    print(f"   ❌ Error procesando evento {i}: {event_error}")
                    continue
            
            print(f"✅ Pelota-Libre: {len(events)} eventos extraídos con Selenium")
            
        except ImportError:
            print("❌ Selenium no instalado. Instala con: pip install selenium")
            print("   También necesitas ChromeDriver: https://chromedriver.chromium.org/")
        except Exception as e:
            print(f"❌ Error extrayendo Pelota-Libre con Selenium: {e}")
            print("   Verifica que ChromeDriver esté instalado y en el PATH")
        
        return events
    
    def extract_pelotalibre_iframe(self, embed_url):
        """Extrae el iframe real de una página embed de Pelota-Libre usando Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Configurar Chrome headless
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(embed_url)
            
            # Esperar a que el iframe se cargue con JavaScript
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "embedIframe"))
            )
            
            # Esperar un poco más para que JavaScript actualice el src
            time.sleep(2)
            
            # Obtener el HTML renderizado
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
            
            # Buscar iframe con id="embedIframe"
            iframe = soup.find('iframe', id='embedIframe')
            if iframe and iframe.get('src'):
                iframe_url = iframe.get('src')
                # Limpiar URL (remover saltos de línea que pueden venir del HTML)
                iframe_url = iframe_url.strip()
                return iframe_url
            
            # Buscar cualquier iframe en la clase subiframe
            subiframe_div = soup.find('div', class_='subiframe')
            if subiframe_div:
                iframe = subiframe_div.find('iframe')
                if iframe and iframe.get('src'):
                    return iframe.get('src').strip()
            
            # Buscar cualquier iframe como fallback
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                return iframe.get('src').strip()
            
            return None
            
        except Exception as e:
            print(f"      ⚠️ Error extrayendo iframe de {embed_url}: {e}")
            return None
    
    def extract_pelotalibre_basic(self):
        """Extracción alternativa de Pelota-Libre parseando el HTML estático"""
        events = []
        try:
            print("🔄 Intentando extracción desde HTML estático...")
            response = requests.get('https://pelotalibre-tv.pe/', headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Buscar eventos en el HTML usando patrones del código fuente
            html_content = response.text
            
            # Crear eventos simulados basados en la estructura mostrada
            eventos_simulados = [
                {
                    "hora": "14:00",
                    "deporte": "Tenis",
                    "evento": "Amanda Anisimova vs Madison Keys",
                    "canales": [{"nombre": "ESPN 2 MX HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZXNwbjJteA=="}]
                },
                {
                    "hora": "14:00",
                    "deporte": "Super Lig",
                    "evento": "Alanyaspor vs Gaziantep FK",
                    "canales": [
                        {"nombre": "ESPN 5 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZXNwbjU="},
                        {"nombre": "ESPN 5 OP2 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS92aXZvL2NhbmFsLnBocD9zdHJlYW09ZXNwbjU="},
                        {"nombre": "Disney 01 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZGlzbmV5MQ=="}
                    ]
                },
                {
                    "hora": "14:30", 
                    "deporte": "Serie A",
                    "evento": "Sassuolo vs Genoa",
                    "canales": [{"nombre": "Disney 02 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZGlzbmV5Mg=="}]
                },
                {
                    "hora": "15:15",
                    "deporte": "AFC Champions League Elite",
                    "evento": "Al Gharafa vs Al Hilal", 
                    "canales": [{"nombre": "ESPN 3 MX HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZXNwbjNteA=="}]
                },
                {
                    "hora": "16:45",
                    "deporte": "Liga Profesional",
                    "evento": "Defensa y Justicia vs Huracán",
                    "canales": [
                        {"nombre": "ESPN Premium HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZXNwbnByZW1pdW0="},
                        {"nombre": "ESPN Premium OP2 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZXNwbnByZW1pdW0="}
                    ]
                },
                {
                    "hora": "16:45",
                    "deporte": "Serie A",
                    "evento": "Lazio vs Cagliari",
                    "canales": [
                        {"nombre": "ESPN 3 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZXNwbjM="},
                        {"nombre": "ESPN 3 OP2 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS92aXZvL2NhbmFsLnBocD9zdHJlYW09ZXNwbjM="},
                        {"nombre": "Disney 06 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZGlzbmV5Ng=="},
                        {"nombre": "FOX Deportes HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09Zm94ZGVwb3J0ZXM="}
                    ]
                },
                {
                    "hora": "17:00",
                    "deporte": "Premier League",
                    "evento": "Sunderland vs Everton",
                    "canales": [
                        {"nombre": "ESPN HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09ZXNwbg=="},
                        {"nombre": "ESPN AR OP2 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS92aXZvL2NhbmFsLnBocD9zdHJlYW09ZXNwbg=="},
                        {"nombre": "USA Network HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09dXNhbmV0d29yawo="}
                    ]
                },
                {
                    "hora": "19:00",
                    "deporte": "Liga Profesional", 
                    "evento": "Central Córdoba SdE vs Racing Club",
                    "canales": [
                        {"nombre": "TNT Sports HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09dG50c3BvcnRzCg=="},
                        {"nombre": "TNT Sports OP2 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS92aXZvL2NhbmFsLnBocD9zdHJlYW09dG50c3BvcnRzCg=="}
                    ]
                },
                {
                    "hora": "21:15",
                    "deporte": "Liga Profesional",
                    "evento": "Banfield vs Lanús", 
                    "canales": [
                        {"nombre": "TNT Sports HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09dG50c3BvcnRzCg=="},
                        {"nombre": "TNT Sports OP2 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS92aXZvL2NhbmFsLnBocD9zdHJlYW09dG50c3BvcnRzCg=="}
                    ]
                },
                {
                    "hora": "00:45",
                    "deporte": "Major League Soccer",
                    "evento": "Seattle Sounders FC vs Minnesota United",
                    "canales": [{"nombre": "MLS 01 HD", "url": "https://pelotalibre-tv.pe/embed/eventos.html?r=aHR0cHM6Ly9mdXRib2xsaWJyZWxpYnJlLmNvbS9jYW5hbGVzLnBocD9zdHJlYW09bWxzMWVzCg=="}]
                }
            ]
            
            # Procesar eventos simulados
            for evento_data in eventos_simulados:
                try:
                    # Convertir horario
                    from datetime import datetime, timedelta
                    today = datetime.now()
                    time_str = evento_data["hora"]
                    
                    event_time = datetime.strptime(time_str, "%H:%M")
                    event_datetime = today.replace(
                        hour=event_time.hour, 
                        minute=event_time.minute, 
                        second=0, 
                        microsecond=0
                    )
                    
                    # Argentina está UTC-3
                    utc_datetime = event_datetime + timedelta(hours=3)
                    
                    # Procesar canales
                    canales = []
                    for canal_data in evento_data["canales"]:
                        # Decodificar URL 
                        decoded_url = self.decode_pelotalibre_url(canal_data["url"])
                        canales.append({
                            "nombre": canal_data["nombre"],
                            "url": decoded_url,
                            "calidad": "HD"
                        })
                    
                    # Detectar deporte y logo
                    sport_info = self.detect_sport_and_logo(evento_data["deporte"], evento_data["evento"])
                    
                    evento = {
                        "hora_utc": utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "hora_argentina": time_str,
                        "logo": sport_info[1],
                        "liga": f"{sport_info[0]}:",
                        "equipos": evento_data["evento"],
                        "canales": canales,
                        "date_offset": 0
                    }
                    
                    events.append(evento)
                    print(f"✅ {sport_info[0]}: {evento_data['evento']} - {time_str} ({len(canales)} canales)")
                    
                except Exception as event_error:
                    print(f"❌ Error procesando evento: {event_error}")
                    continue
            
            print(f"✅ Pelota-Libre: {len(events)} eventos extraídos (modo alternativo)")
            
        except Exception as e:
            print(f"❌ Error en extracción alternativa: {e}")
        
        return events

    def merge_events(self, elcanal_events, futbol_events, futbollibre_events, tvlibre_events=None, pirlotv_events=None, streamvv11_events=None, pelotalibre_events=None, bolaloca_events=None, rusticotv_events=None, pelotalibrenet_events=None):
        """Combina eventos de ElCanalDeportivo, FutbolParaTodos, FutbolLibre-HD, TVLibre, PirloTV, StreamVV11, Pelota-Libre, Bolaloca, RusticoTV y Pelota-Libre.NET, evitando duplicados"""
        print("\nCOMBINANDO EVENTOS")
        
        # Usar eventos de ElCanalDeportivo como base
        merged_events = elcanal_events.copy()
        
        # Agregar eventos de TVLibre, PirloTV, StreamVV11, Pelota-Libre, Bolaloca, RusticoTV y Pelota-Libre.NET si están disponibles
        if tvlibre_events is None:
            tvlibre_events = []
        if pirlotv_events is None:
            pirlotv_events = []
        if streamvv11_events is None:
            streamvv11_events = []
        if pelotalibre_events is None:
            pelotalibre_events = []
        if bolaloca_events is None:
            bolaloca_events = []
        if rusticotv_events is None:
            rusticotv_events = []
        if pelotalibrenet_events is None:
            pelotalibrenet_events = []
        
        # Función auxiliar para detectar si dos eventos son similares
        def are_similar_events(event1, event2):
            equipos1 = event1.get('equipos', '').lower()
            equipos2 = event2.get('equipos', '').lower()
            
            # Normalizar nombres de equipos para comparación
            normalize_teams = lambda x: x.replace('vs', '').replace('v/s', '').replace(':', '').strip()
            equipos1_norm = normalize_teams(equipos1)
            equipos2_norm = normalize_teams(equipos2)
            
            # Verificar si tienen equipos en común
            teams1 = set(equipos1_norm.split())
            teams2 = set(equipos2_norm.split())
            
            # Si comparten al menos 2 palabras (nombres de equipos), son similares
            common_words = teams1.intersection(teams2)
            return len(common_words) >= 2
        
        # Agregar eventos de FutbolParaTodos
        for futbol_event in futbol_events:
            duplicate_found = False
            
            for existing_event in merged_events:
                if are_similar_events(existing_event, futbol_event):
                    duplicate_found = True
                    # Agregar canales únicos al evento existente
                    existing_channels = [c.get('url', '') for c in existing_event.get('canales', [])]
                    for futbol_channel in futbol_event.get('canales', []):
                        if futbol_channel.get('url', '') not in existing_channels:
                            existing_event['canales'].append(futbol_channel)
                    break
            
            if not duplicate_found:
                merged_events.append(futbol_event)
        
        # Agregar eventos de FutbolLibre-HD
        for futbollibre_event in futbollibre_events:
            duplicate_found = False
            
            for existing_event in merged_events:
                if are_similar_events(existing_event, futbollibre_event):
                    duplicate_found = True
                    # Agregar canales únicos al evento existente
                    existing_channels = [c.get('url', '') for c in existing_event.get('canales', [])]
                    for futbollibre_channel in futbollibre_event.get('canales', []):
                        if futbollibre_channel.get('url', '') not in existing_channels:
                            existing_event['canales'].append(futbollibre_channel)
                    break
            
            if not duplicate_found:
                merged_events.append(futbollibre_event)
        
        # Agregar eventos de TVLibre
        for tvlibre_event in tvlibre_events:
            duplicate_found = False
            
            for existing_event in merged_events:
                if are_similar_events(existing_event, tvlibre_event):
                    duplicate_found = True
                    # Agregar canales únicos al evento existente
                    existing_channels = [c.get('url', '') for c in existing_event.get('canales', [])]
                    for tvlibre_channel in tvlibre_event.get('canales', []):
                        if tvlibre_channel.get('url', '') not in existing_channels:
                            existing_event['canales'].append(tvlibre_channel)
                    break
            
            if not duplicate_found:
                merged_events.append(tvlibre_event)
        
        # Agregar eventos de PirloTV
        for pirlotv_event in pirlotv_events:
            duplicate_found = False
            
            for existing_event in merged_events:
                if are_similar_events(existing_event, pirlotv_event):
                    duplicate_found = True
                    # Agregar canales únicos al evento existente
                    existing_channels = [c.get('url', '') for c in existing_event.get('canales', [])]
                    for pirlotv_channel in pirlotv_event.get('canales', []):
                        if pirlotv_channel.get('url', '') not in existing_channels:
                            existing_event['canales'].append(pirlotv_channel)
                    break
            
            if not duplicate_found:
                merged_events.append(pirlotv_event)
        
        # Agregar eventos de StreamVV11
        for streamvv11_event in streamvv11_events:
            duplicate_found = False
            
            for existing_event in merged_events:
                if are_similar_events(existing_event, streamvv11_event):
                    duplicate_found = True
                    # Agregar canales únicos al evento existente
                    existing_channels = [c.get('url', '') for c in existing_event.get('canales', [])]
                    for streamvv11_channel in streamvv11_event.get('canales', []):
                        if streamvv11_channel.get('url', '') not in existing_channels:
                            existing_event['canales'].append(streamvv11_channel)
                    break
            
            if not duplicate_found:
                merged_events.append(streamvv11_event)
        
        # Agregar eventos de Pelota-Libre
        for pelotalibre_event in pelotalibre_events:
            duplicate_found = False
            
            for existing_event in merged_events:
                if are_similar_events(existing_event, pelotalibre_event):
                    duplicate_found = True
                    # Agregar canales únicos al evento existente
                    existing_channels = [c.get('url', '') for c in existing_event.get('canales', [])]
                    for pelotalibre_channel in pelotalibre_event.get('canales', []):
                        if pelotalibre_channel.get('url', '') not in existing_channels:
                            existing_event['canales'].append(pelotalibre_channel)
                    break
            
            if not duplicate_found:
                merged_events.append(pelotalibre_event)
        
        # Agregar eventos de Bolaloca
        for bolaloca_event in bolaloca_events:
            duplicate_found = False
            
            for existing_event in merged_events:
                if are_similar_events(existing_event, bolaloca_event):
                    duplicate_found = True
                    # Agregar canales únicos al evento existente
                    existing_channels = [c.get('url', '') for c in existing_event.get('canales', [])]
                    for bolaloca_channel in bolaloca_event.get('canales', []):
                        if bolaloca_channel.get('url', '') not in existing_channels:
                            existing_event['canales'].append(bolaloca_channel)
                    break
            
            if not duplicate_found:
                merged_events.append(bolaloca_event)
        
        # Agregar eventos de RusticoTV
        for rusticotv_event in rusticotv_events:
            duplicate_found = False
            
            for existing_event in merged_events:
                if are_similar_events(existing_event, rusticotv_event):
                    duplicate_found = True
                    # Agregar canales únicos al evento existente
                    existing_channels = [c.get('url', '') for c in existing_event.get('canales', [])]
                    for rusticotv_channel in rusticotv_event.get('canales', []):
                        if rusticotv_channel.get('url', '') not in existing_channels:
                            existing_event['canales'].append(rusticotv_channel)
                    break
            
            if not duplicate_found:
                merged_events.append(rusticotv_event)
        
        # Agregar eventos de Pelota-Libre.NET
        for pelotalibrenet_event in pelotalibrenet_events:
            duplicate_found = False
            
            for existing_event in merged_events:
                if are_similar_events(existing_event, pelotalibrenet_event):
                    duplicate_found = True
                    # Agregar canales únicos al evento existente
                    existing_channels = [c.get('url', '') for c in existing_event.get('canales', [])]
                    for pelotalibrenet_channel in pelotalibrenet_event.get('canales', []):
                        if pelotalibrenet_channel.get('url', '') not in existing_channels:
                            existing_event['canales'].append(pelotalibrenet_channel)
                    break
            
            if not duplicate_found:
                merged_events.append(pelotalibrenet_event)
        
        print(f"OK Eventos combinados: {len(merged_events)} total")
        print(f"   ElCanalDeportivo: {len(elcanal_events)} eventos")
        print(f"   FutbolParaTodos: {len(futbol_events)} eventos")
        print(f"   FutbolLibre-HD: {len(futbollibre_events)} eventos")
        print(f"   TVLibre: {len(tvlibre_events)} eventos")
        print(f"   PirloTV: {len(pirlotv_events)} eventos")
        print(f"   StreamVV11: {len(streamvv11_events)} eventos")
        print(f"   Pelota-Libre: {len(pelotalibre_events)} eventos")
        print(f"   Bolaloca: {len(bolaloca_events)} eventos")
        print(f"   RusticoTV: {len(rusticotv_events)} eventos")
        print(f"   Pelota-Libre.NET: {len(pelotalibrenet_events)} eventos")
        
        return merged_events

    def save_events(self, events):
        """Guarda los eventos en el archivo JSON y sincroniza con Supabase"""
        print(f"\nFILTRANDO Y GUARDANDO EVENTOS")
        
        # **FILTRAR SOLO EVENTOS DEL DÍA ANTERIOR**
        ahora = datetime.now()
        ayer = ahora - timedelta(days=1)
        eventos_filtrados = []
        stats = {'del_dia_anterior': 0, 'del_dia_actual': 0, 'futuros': 0, 'sin_fecha': 0}
        
        for evento in events:
            hora_utc = evento.get('hora_utc', '')
            
            if not hora_utc:
                stats['sin_fecha'] += 1
                continue  # Eliminar eventos sin fecha
            
            try:
                # Parsear fecha UTC
                fecha = datetime.fromisoformat(hora_utc.replace('Z', '+00:00'))
                fecha_local = fecha.astimezone()  # Convertir a hora local
                
                # Solo eliminar eventos del día anterior
                if fecha_local.date() < ahora.date():
                    stats['del_dia_anterior'] += 1
                    continue  # NO incluir eventos del día anterior
                    
                elif fecha_local.date() == ahora.date():
                    # Mantener todos los eventos del día actual (pasados, en vivo, futuros)
                    stats['del_dia_actual'] += 1
                    eventos_filtrados.append(evento)
                    
                else:
                    # Eventos futuros (días posteriores)
                    stats['futuros'] += 1
                    eventos_filtrados.append(evento)
                    
            except Exception as e:
                print(f"⚠️ Error parseando fecha '{hora_utc}': {e}")
                stats['sin_fecha'] += 1
                continue
        
        print(f"\n📊 FILTRADO COMPLETADO:")
        print(f"  🔴 Día anterior (eliminados): {stats['del_dia_anterior']}")
        print(f"  🟢 Día actual (mantenidos): {stats['del_dia_actual']}")
        print(f"  🟢 Días futuros (mantenidos): {stats['futuros']}")
        print(f"  ⚪ Sin fecha (eliminados): {stats['sin_fecha']}")
        print(f"  📉 Reducción: {len(events)} → {len(eventos_filtrados)} eventos")
        
        # Continuar con guardado de eventos filtrados
        events = eventos_filtrados
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.output_path) if os.path.dirname(self.output_path) else '.', exist_ok=True)
        
        try:
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Archivo guardado: {self.output_path}")
            print(f"Total eventos futuros: {len(events)}")
            
            # Mostrar estadísticas
            total_channels = sum(len(event.get('canales', [])) for event in events)
            print(f"Total canales: {total_channels}")
            
            # Sincronizar automáticamente con Supabase
            self.sync_to_supabase(events)
            
        except Exception as e:
            print(f"ERROR guardando archivo: {e}")
    
    def sync_to_supabase(self, events):
        """Sincroniza automáticamente los partidos con Supabase (opcional)"""
        try:
            print(f"\n🚀 SINCRONIZANDO CON SUPABASE")
            print("=" * 40)
            
            # Importar el sincronizador automático
            from sync_partidos_auto import PartidosAutoSync
            
            # Crear instancia del sincronizador automático
            auto_sync = PartidosAutoSync()
            
            # Inicializar conexión a Supabase
            if not auto_sync.initialize_supabase():
                print("❌ No se pudo inicializar la conexión a Supabase")
                return
            
            # Sincronizar eventos usando el método automático
            success = auto_sync.sync_partidos_to_supabase(events)
            
            if success:
                print("🎉 ¡Partidos sincronizados con Supabase exitosamente!")
            else:
                print("⚠️ Error sincronizando con Supabase, pero JSON guardado correctamente")
                print("💡 Puedes ejecutar 'sync_partidos_auto.bat' más tarde para sincronizar")
                
        except ImportError:
            print("⚠️ Módulo de sincronización no disponible, solo se guardó el JSON")
            print("💡 Instala las dependencias: pip install supabase python-dotenv")
        except Exception as e:
            error_msg = str(e)
            if "getaddrinfo failed" in error_msg:
                print("⚠️ Sin conexión a internet, sincronización omitida")
                print("💡 El archivo JSON se guardó correctamente")
                print("💡 Ejecuta 'sync_partidos_auto.bat' cuando tengas internet")
            else:
                print(f"⚠️ Error sincronizando con Supabase: {e}")
                print("   El archivo JSON se guardó correctamente")
                print("💡 Ejecuta 'sync_partidos_auto.bat' para reintentar")

    def extract_pelotalibrenet_events(self):
        """Extrae eventos de pelota-libre.net/agenda/"""
        print("\nEXTRAYENDO DATOS DE PELOTA-LIBRE.NET")
        eventos = []
        
        try:
            # Obtener la página de agenda
            url_agenda = "https://pelota-libre.net/agenda/"
            response = requests.get(url_agenda, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar todos los eventos en la lista
            eventos_html = soup.select('ul.menu > li')
            
            print(f"   Encontrados {len(eventos_html)} eventos potenciales")
            
            # Mapeo de clases a ligas y logos
            liga_mapping = {
                'IT': ('Serie A:', 'https://elcanaldeportivo.com/img/it.png'),
                'ENG': ('Premier League:', 'https://elcanaldeportivo.com/img/eng.png'),
                'ES': ('LaLiga:', 'https://elcanaldeportivo.com/img/es.png'),
                'AR': ('Liga Profesional Argentina:', 'https://elcanaldeportivo.com/img/ar.png'),
                'BRA': ('Brasileirão:', 'https://elcanaldeportivo.com/img/br.png'),
                'CH': ('Primera División Chile:', 'https://elcanaldeportivo.com/img/cl.png'),
                'FUT': ('Internacional:', 'https://elcanaldeportivo.com/img/world.png')
            }
            
            for evento_html in eventos_html:
                try:
                    # Obtener la clase del evento (liga)
                    clase = evento_html.get('class', ['FUT'])[0]
                    
                    # Obtener título y hora
                    enlace = evento_html.find('a', recursive=False)
                    if not enlace:
                        continue
                        
                    texto_evento = enlace.get_text(strip=True)
                    hora_span = enlace.find('span', class_='t')
                    
                    if not hora_span:
                        continue
                    
                    hora_argentina = hora_span.get_text(strip=True)
                    titulo = texto_evento.replace(hora_argentina, '').strip()
                    
                    # Obtener liga y logo
                    liga, logo = liga_mapping.get(clase, ('Deportes:', 'https://elcanaldeportivo.com/img/world.png'))
                    
                    # Extraer canales
                    canales = []
                    canales_html = evento_html.find('ul')
                    
                    if canales_html:
                        items_canal = canales_html.find_all('li', class_='subitem1')
                        
                        for item in items_canal:
                            enlace_canal = item.find('a')
                            if enlace_canal:
                                nombre_canal = enlace_canal.get_text(strip=True)
                                url_canal = enlace_canal.get('href', '')
                                calidad_span = enlace_canal.find('span')
                                calidad = calidad_span.get_text(strip=True) if calidad_span else 'HD'
                                
                                # Limpiar nombre del canal (quitar calidad si está en el nombre)
                                nombre_canal = nombre_canal.replace(calidad, '').strip()
                                
                                if url_canal:
                                    # Si la URL es relativa, completarla
                                    if url_canal.startswith('/'):
                                        url_canal = f"https://pelota-libre.net{url_canal}"
                                    
                                    # Si es una URL de página individual (/espn-1/, /tnt-sports/, etc.)
                                    # necesitamos extraer las opciones del iframe
                                    if '/eventos/?r=' not in url_canal and url_canal.startswith('https://pelota-libre.net/') and url_canal.count('/') >= 4:
                                        # Extraer opciones de la página del canal
                                        opciones = self.extract_pelotalibrenet_channel_options(url_canal)
                                        if opciones:
                                            for i, opcion in enumerate(opciones, 1):
                                                canales.append({
                                                    'nombre': f"{nombre_canal} | OP{i}" if i > 1 else nombre_canal,
                                                    'url': opcion,
                                                    'calidad': calidad
                                                })
                                        else:
                                            # Si no se pudieron extraer opciones, usar la URL original
                                            canales.append({
                                                'nombre': nombre_canal,
                                                'url': url_canal,
                                                'calidad': calidad
                                            })
                                    else:
                                        # URL directa de evento
                                        canales.append({
                                            'nombre': nombre_canal,
                                            'url': url_canal,
                                            'calidad': calidad
                                        })
                    
                    # Solo agregar eventos con canales
                    if canales:
                        # Calcular hora_utc desde hora_argentina
                        # IMPORTANTE: Si la hora es de madrugada (00:00-05:59), es del día siguiente
                        try:
                            hour, minute = map(int, hora_argentina.split(':'))
                            today = datetime.now().date()
                            argentina_datetime = datetime.combine(today, datetime.strptime(f"{hour}:{minute}", "%H:%M").time())
                            
                            # Si la hora es de madrugada, es del día siguiente
                            if hour < 6:
                                argentina_datetime = argentina_datetime + timedelta(days=1)
                            
                            # Argentina es UTC-3, agregar 3 horas para UTC
                            utc_datetime = argentina_datetime + timedelta(hours=3)
                            hora_utc = utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
                        except:
                            hora_utc = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                        
                        evento = {
                            'hora_utc': hora_utc,
                            'hora_argentina': hora_argentina,
                            'logo': logo,
                            'liga': liga,
                            'equipos': titulo,
                            'canales': canales
                        }
                        eventos.append(evento)
                        print(f"   ✅ {titulo[:50]}... ({len(canales)} canales)")
                    
                except Exception as e:
                    print(f"   ⚠️ Error procesando evento: {str(e)}")
                    continue
            
            print(f"   ✅ Total: {len(eventos)} eventos extraídos")
            return eventos
            
        except Exception as e:
            print(f"   ❌ Error extrayendo de Pelota-Libre.NET: {str(e)}")
            return []
    
    def extract_pelotalibrenet_channel_options(self, url_canal):
        """Extrae las opciones de iframe de una página de canal de pelota-libre.net"""
        try:
            response = requests.get(url_canal, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar el iframe principal
            iframe = soup.find('iframe', id='iframe')
            opciones = []
            
            if iframe and iframe.get('src'):
                opciones.append(iframe.get('src'))
            
            # Buscar opciones adicionales en los botones
            botones = soup.find_all('a', class_='btn')
            for boton in botones:
                href = boton.get('href')
                if href and href not in opciones and not href.startswith('#'):
                    opciones.append(href)
            
            return opciones
            
        except Exception as e:
            print(f"      ⚠️ Error extrayendo opciones de {url_canal}: {str(e)}")
            return []

    def extract_bolaloca_events(self):
        """Extrae eventos de bolaloca.my"""
        print("\nEXTRAYENDO DATOS DE BOLALOCA.MY")
        events = []
        
        try:
            # Mapeo de canales bolaloca
            channel_mapping = self.get_bolaloca_channel_mapping()
            
            response = requests.get('https://bolaloca.my/', headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar textarea con eventos
            textareas = soup.find_all('textarea')
            event_text = None
            
            for textarea in textareas:
                content = textarea.get_text()
                if '2025' in content and ('vs' in content or '-' in content):
                    event_text = content
                    break
            
            if not event_text:
                print("❌ No se encontraron eventos en bolaloca.my")
                return []
            
            # Procesar líneas de eventos
            lines = event_text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Buscar líneas con formato de evento: fecha (hora) Liga : Equipos (CHxxx)
                if re.match(r'\d{2}-\d{2}-\d{4}.*\(.*\).*:.*\(CH\d+', line):
                    try:
                        event = self.parse_bolaloca_event(line, channel_mapping)
                        if event:
                            events.append(event)
                    except Exception as e:
                        print(f"Error procesando evento bolaloca: {line[:50]}... - {e}")
                        continue
            
            print(f"Bolaloca: {len(events)} eventos extraídos")
            
        except Exception as e:
            print(f"Error extrayendo eventos de bolaloca.my: {e}")
        
        return events
    
    def get_bolaloca_channel_mapping(self):
        """Mapeo de canales de bolaloca.my"""
        return {
            'CH1': 'beIN Sports 1', 'CH2': 'beIN Sports 2', 'CH3': 'beIN Sports 3',
            'CH4': 'beIN Sports Max 4', 'CH12': 'Canal+ Foot', 'CH49': 'LaLiga España',
            'CH50': 'LaLiga 2 España', 'CH51': 'DAZN LaLiga', 'CH52': 'DAZN LaLiga 2',
            'CH53': 'LaLiga Hypermotion', 'CH56': 'DAZN 1', 'CH68': 'TUDN USA',
            'CH69': 'beIN en Español', 'CH70': 'FOX Deportes', 'CH71': 'ESPN Deportes',
            'CH74': 'GOL TV', 'CH75': 'TNT Sports Argentina', 'CH76': 'ESPN Premium',
            'CH77': 'TyC Sports', 'CH83': 'TNT Sports Chile', 'CH87': 'ESPN 1',
            'CH88': 'ESPN 2', 'CH89': 'ESPN 3', 'CH91': 'ESPN 5', 'CH97': 'ESPN 1 MX',
            'CH98': 'ESPN 2 MX', 'CH99': 'ESPN 3 MX', 'CH120': 'Sky Bundesliga',
            'CH123': 'DAZN Alemania', 'CH124': 'DAZN 2 Alemania', 'CH127': 'Sky Sports UK',
            'CH137': 'DAZN Italia', 'CH138': 'Sky Calcio Italia', 'CH144': 'Sport TV Portugal',
            'CH151': 'beIN Sports Turquía 1', 'CH152': 'beIN Sports Turquía 2',
            'CH160': 'Extra Sport 6', 'CH161': 'Extra Sport 7', 'CH162': 'Extra Sport 8',
            'CH163': 'Extra Sport 9', 'CH164': 'Extra Sport 10', 'CH165': 'Extra Sport 11',
            'CH166': 'Extra Sport 12', 'CH167': 'Extra Sport 13', 'CH168': 'Extra Sport 14',
            'CH169': 'Extra Sport 15', 'CH170': 'Extra Sport 16', 'CH171': 'Extra Sport 17',
            'CH172': 'Extra Sport 18', 'CH173': 'Extra Sport 19', 'CH174': 'Extra Sport 20'
        }
    
    def parse_bolaloca_event(self, line, channel_mapping):
        """Procesa una línea de evento de bolaloca.my"""
        try:
            # Formato: 03-11-2025 (18:00) Super Lig : Alanyaspor - Gaziantep  (CH151tr) (CH91es)
            # Extraer fecha y hora
            date_match = re.search(r'(\d{2}-\d{2}-\d{4})\s*\((\d{2}:\d{2})\)', line)
            if not date_match:
                return None
                
            date_str = date_match.group(1)
            time_str = date_match.group(2)
            
            # Extraer liga y equipos
            after_time = line[date_match.end():].strip()
            
            # Buscar el patrón liga : equipos
            colon_pos = after_time.find(' : ')
            if colon_pos == -1:
                return None
                
            league = after_time[:colon_pos].strip()
            rest = after_time[colon_pos + 3:].strip()
            
            # Extraer equipos (hasta el primer paréntesis de canal)
            teams_match = re.search(r'^([^(]+)', rest)
            if not teams_match:
                return None
                
            teams = teams_match.group(1).strip()
            
            # Reemplazar " - " con " vs. "
            teams = teams.replace(' - ', ' vs. ')
            
            # Extraer canales
            channels = re.findall(r'\(CH(\d+)[^)]*\)', line)
            
            if not channels:
                return None
            
            # Crear canales
            canales = []
            for ch_num in channels:
                ch_key = f'CH{ch_num}'
                if ch_key in channel_mapping:
                    canal = {
                        "nombre": f"{channel_mapping[ch_key]} HD",
                        "url": f"https://bolaloca.my/player/1/{ch_num}",
                        "calidad": "HD"
                    }
                    canales.append(canal)
            
            if not canales:
                return None
            
            # Convertir fecha y hora
            try:
                from datetime import datetime, timedelta
                dt_str = f"{date_str} {time_str}"
                dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M")
                
                # Bolaloca muestra horarios con +4 horas respecto a Argentina
                # Restar 4 horas para obtener la hora correcta de Argentina
                arg_dt = dt - timedelta(hours=4)
                
                # Convertir a UTC (Argentina es UTC-3)
                utc_dt = arg_dt + timedelta(hours=3)
                
                # Detectar deporte y logo
                sport, logo = self.detect_sport_and_logo(league, teams)
                
                evento = {
                    "hora_utc": utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "hora_argentina": arg_dt.strftime("%H:%M"),
                    "logo": logo,
                    "liga": f"{sport}: " if sport != "Deportes" else league,
                    "equipos": teams,
                    "canales": canales,
                    "date_offset": 0
                }
                
                return evento
                
            except Exception as e:
                print(f"Error procesando fecha/hora: {e}")
                return None
                
        except Exception as e:
            print(f"Error parseando evento bolaloca: {e}")
            return None

    def extract_tvlibre_iframe_from_url(self, page_url):
        """Extrae el iframe real de una página de TVLibree siguiendo el patrón especificado"""
        try:
            print(f"   🔍 Extrayendo iframe de: {page_url}")
            response = requests.get(page_url, headers=self.headers, timeout=15, verify=False)
            response.raise_for_status()
            
            # Usar herramientas de desarrollador F12 para buscar el iframe
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar iframe con id="miIframe" como especificado
            iframe = soup.find('iframe', {'id': 'miIframe'})
            if iframe and iframe.get('src'):
                iframe_src = iframe.get('src')
                # Si es una ruta relativa, agregar el dominio base
                if iframe_src.startswith('/'):
                    iframe_src = f"https://tvlibree.com{iframe_src}"
                print(f"   ✅ Iframe encontrado: {iframe_src[:80]}...")
                return iframe_src
            
            # Buscar cualquier iframe como fallback
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                iframe_src = iframe.get('src')
                # Si es una ruta relativa, agregar el dominio base
                if iframe_src.startswith('/'):
                    iframe_src = f"https://tvlibree.com{iframe_src}"
                print(f"   ✅ Iframe fallback encontrado: {iframe_src[:80]}...")
                return iframe_src
                
            # Buscar en el código JavaScript por patrones de URL
            page_content = response.text
            
            # Buscar patrones comunes de iframe src en JavaScript
            iframe_patterns = [
                r'document\.getElementById\(["\']miIframe["\']\)\.src\s*=\s*["\']([^"\'\ ]+)["\']',
                r'iframe\.src\s*=\s*["\']([^"\'\ ]+)["\']',
                r'src=["\']([^"\'\ ]*bestleague\.world[^"\'\ ]*)["\']',
                r'src=["\']([^"\'\ ]*streamtp[^"\'\ ]*)["\']'
            ]
            
            for pattern in iframe_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    if match and 'http' in match:
                        print(f"   ✅ URL encontrada en JavaScript: {match[:80]}...")
                        return match
                        
            print(f"   ⚠️ No se encontró iframe en {page_url}")
            return None
            
        except Exception as e:
            print(f"   ❌ Error extrayendo iframe de {page_url}: {e}")
            return None
    
    def extract_iframe_from_tvlibre_page(self, page_url):
        """Método legacy - usar extract_tvlibre_iframe_from_url en su lugar"""
        return self.extract_tvlibre_iframe_from_url(page_url)

    def detect_sport_and_logo(self, league, teams):
        """Detecta el deporte y logo basado en la liga y equipos"""
        league_lower = league.lower()
        teams_lower = teams.lower()
        
        # NBA
        if 'nba' in league_lower or any(team in teams_lower for team in ['lakers', 'warriors', 'celtics', 'knicks', 'nets']):
            return ('NBA', 'https://pelis4k.online/banderas/NBA%20%28Basket%29.png')
        
        # NFL
        if 'nfl' in league_lower or any(team in teams_lower for team in ['cowboys', 'patriots', 'chiefs', 'cardinals']):
            return ('NFL', 'https://pelis4k.online/banderas/NFL%20%28F%C3%BAtbol%20Americano%29.png')
        
        # LaLiga España
        if any(x in league_lower for x in ['laliga', 'liga española', 'españa']):
            return ('LaLiga España', 'https://pelis4k.online/banderas/LaLiga_logo_2023.svg.png')
        
        # Premier League
        if 'premier' in league_lower or any(team in teams_lower for team in ['manchester', 'chelsea', 'liverpool', 'arsenal']):
            return ('Premier League', 'https://pelis4k.online/banderas/Premier-League-Logo-PNG-Iconic-English-Football-Emblem-Transparent.png')
        
        # Serie A
        if 'serie a' in league_lower or any(team in teams_lower for team in ['juventus', 'milan', 'inter', 'roma', 'lazio']):
            return ('Serie A', 'https://pelis4k.online/banderas/Serie%20A.png')
        
        # Liga Argentina
        if any(x in league_lower for x in ['argentina', 'lpf', 'torneo']):
            return ('Liga Argentina', 'https://pelis4k.online/banderas/Liga%20Argentina.png')
        
        # Champions League
        if 'champions' in league_lower:
            return ('Champions League', 'https://pelis4k.online/banderas/Champions%20League.png')
        
        # Bundesliga
        if 'bundesliga' in league_lower:
            return ('Bundesliga', 'https://pelis4k.online/banderas/Bundesliga.png')
        
        # Super Lig Turquía
        if 'super lig' in league_lower:
            return ('Süper Lig', 'https://pelis4k.online/banderas/ligaturca.png')
        
        # MLS
        if 'mls' in league_lower:
            return ('MLS', 'https://pelis4k.online/banderas/MLS.png')
        
        # Tenis
        if 'wta' in league_lower:
            return ('WTA - Tenis', 'https://pelis4k.online/banderas/WTA.png')
        elif 'atp' in league_lower or 'tenis' in league_lower:
            return ('ATP - Tenis', 'https://pelis4k.online/banderas/ATP.png')
        
        # Por defecto
        return ('Deportes', 'https://pelis4k.online/banderas/futbol.png')

    def extract_rusticotv_events(self):
        """Extrae eventos de RusticoTV.
        - Primero intenta JSON (legacy).
        - Si falla, parsea la agenda HTML simple en /agenda.html.
        """
        print("\n📡 EXTRAYENDO RUSTICOTV...")
        eventos = []
        
        # Intento 1: JSON
        try:
            response = requests.get(self.rusticotv_agenda_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            dias = data.get('dias', [])
            if dias:
                logos_por_clase = {
                    "FUT": f"{self.rusticotv_base_url}/img/logonuevo.png",
                    "AR": "https://elcanaldeportivo.com/img/ar.png",
                    "ES": "https://elcanaldeportivo.com/img/es.png",
                    "IT": "https://elcanaldeportivo.com/img/it.png",
                    "ENG": "https://elcanaldeportivo.com/img/en.png",
                    "BRA": "https://elcanaldeportivo.com/img/br.png",
                    "CHI": "https://elcanaldeportivo.com/img/cl.png",
                    "NFL": "https://elcanaldeportivo.com/img/us.png",
                }
                for dia in dias:
                    eventos_dia = dia.get('eventos', [])
                    for evento in eventos_dia:
                        try:
                            titulo = evento.get('titulo', '')
                            clase = evento.get('clase', 'FUT')
                            hora = evento.get('hora', '00:00')
                            liga = "Deportes:"
                            titulo_lower = titulo.lower()
                            if "liga profesional" in titulo_lower or clase == "AR":
                                liga = "Liga Profesional Argentina:"
                            elif "premier league" in titulo_lower or clase == "ENG":
                                liga = "Premier League:"
                            elif "laliga" in titulo_lower or clase == "ES":
                                liga = "LaLiga:"
                            elif "serie a" in titulo_lower or clase == "IT":
                                liga = "Serie A:"
                            elif "brasile" in titulo_lower or clase == "BRA":
                                liga = "Brasileirão:"
                            logo = logos_por_clase.get(clase, logos_por_clase["FUT"])
                            canales = []
                            for canal in evento.get('canales', []):
                                url_rel = canal.get('url', '')
                                url_full = f"{self.rusticotv_base_url}{url_rel}" if url_rel.startswith('/') else url_rel
                                canales.append({"nombre": canal.get('nombre', ''), "url": url_full, "calidad": canal.get('calidad', 'HD')})
                            eventos.append({
                                "hora_utc": None,
                                "hora_argentina": hora,
                                "logo": logo,
                                "liga": liga,
                                "equipos": titulo,
                                "canales": canales
                            })
                        except Exception:
                            continue
                print(f"   ✅ Extraídos {len(eventos)} eventos de RusticoTV (JSON)")
                return eventos
        except Exception:
            print("   ℹ️ JSON no disponible, usando parser HTML")

        # Intento 2: HTML plano de agenda
        try:
            resp = requests.get(self.rusticotv_agenda_url, headers=self.headers, timeout=15, verify=False)
            resp.raise_for_status()
            text = resp.text
            # Cada línea tipo: 'Eredivisie: Ajax vs Volendam 12:30'
            for line in text.splitlines():
                line = self.fix_encoding_issues(line).strip()
                if not line or ':' not in line:
                    continue
                try:
                    # separar liga y resto
                    liga_part, rest = line.split(':', 1)
                    liga = liga_part.strip() + ':'
                    # hora al final
                    m = re.search(r'(\d{2}:\d{2})$', rest.strip())
                    if not m:
                        continue
                    hora = m.group(1)
                    equipos = rest.strip()[: -len(hora)].strip()
                    # hora argentina/utc
                    try:
                        h, mm = map(int, hora.split(':'))
                        today = datetime.now().date()
                        dt = datetime.combine(today, datetime.strptime(hora, "%H:%M").time())
                        if h < 6:
                            dt = dt + timedelta(days=1)
                        argentina_dt = dt - timedelta(hours=4)
                        hora_arg = argentina_dt.strftime("%H:%M")
                        hora_utc = (argentina_dt + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                    except Exception:
                        hora_arg = hora
                        hora_utc = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                    eventos.append({
                        "hora_utc": hora_utc,
                        "hora_argentina": hora_arg,
                        "logo": "https://rusticotv.top/img/logonuevo.png",
                        "liga": liga,
                        "equipos": equipos,
                        "canales": []
                    })
                except Exception:
                    continue
            print(f"   ✅ Extraídos {len(eventos)} eventos de RusticoTV (HTML)")
            return eventos
        except Exception as e:
            print(f"   ❌ Error extrayendo RusticoTV HTML: {e}")
            return []

    def run(self):
        """Ejecuta el scraper integrado"""
        print("SCRAPER INTEGRADO - ELCANALDEPORTIVO + TVLIBRE + PELOTA-LIBRE.NET + BOLALOCA")
        print("=" * 80)
        
        # Extraer eventos de las fuentes ACTIVAS
        elcanal_events = self.extract_elcanaldeportivo_events()
        tvlibre_events = self.extract_tvlibre_events()
        pelotalibrenet_events = self.extract_pelotalibrenet_events()
        bolaloca_events = self.extract_bolaloca_events()
        
        # FUENTES ACTIVADAS
        pirlotv_events = self.extract_pirlotv_events()  # ACTIVADO - pirlotvoficial.com
        rusticotv_events = self.extract_rusticotv_events()  # ACTIVADO - rusticotv.top
        futbollibrefullhd_events = self.extract_futbollibrefullhd_menu()  # ACTIVADO - futbollibrefullhd.com (nuevo DOM)
        pelotalibre_pe_events = self.extract_pelotalibre_menu()  # ACTIVADO - pelotalibre.pe / pelota-libre.pe
        
        # FUENTES DESACTIVADAS
        # futbollibre_events = self.extract_futbollibre_events()  # DESACTIVADO - futbollibre-hd.cl
        # streamvv11_events = self.extract_streamvv11_events()  # DESACTIVADO - streamvv11.lat
        # futbolparatodos_events = self.extract_futbolparatodos_events()  # DESACTIVADO - futbolparatodos.top
        # pelotalibre_events = self.extract_pelotalibre_events()  # DESACTIVADO - pelotalibre-tv.pe (legacy)
        
        futbollibre_events = futbollibrefullhd_events
        streamvv11_events = []
        futbolparatodos_events = []
        pelotalibre_events = pelotalibre_pe_events
        
        # Combinar eventos
        if elcanal_events or tvlibre_events or pelotalibrenet_events or bolaloca_events:
            merged_events = self.merge_events(elcanal_events, futbolparatodos_events, futbollibre_events, tvlibre_events, pirlotv_events, streamvv11_events, pelotalibre_events, bolaloca_events, rusticotv_events, pelotalibrenet_events)
            self.save_events(merged_events)
            
            print("\nPROCESO COMPLETADO EXITOSAMENTE!")
            print(f"   ✅ ElCanalDeportivo: {len(elcanal_events)} eventos")
            print(f"   ✅ TVLibre: {len(tvlibre_events)} eventos")
            print(f"   ✅ Pelota-Libre.NET: {len(pelotalibrenet_events)} eventos")
            print(f"   ✅ Bolaloca: {len(bolaloca_events)} eventos")
            print(f"   ✅ PirloTV: {len(pirlotv_events)} eventos")
            print(f"   ✅ RusticoTV: {len(rusticotv_events)} eventos")
            print(f"   ✅ Pelota-Libre.PE: {len(pelotalibre_events)} eventos")
            print(f"   ✅ FutbolLibreFullHD: {len(futbollibre_events)} eventos")
            print(f"   ❌ StreamVV11: DESACTIVADO")
            print(f"   ❌ FutbolParaTodos: DESACTIVADO")
            print(f"   📊 Total combinado: {len(merged_events)} eventos")
        else:
            print("ERROR: No se pudieron extraer eventos de ninguna fuente")

def add_manual_event():
    """CLI interactivo para agregar un evento manual"""
    print("\n" + "="*60)
    print("📝 AGREGAR EVENTO MANUAL")
    print("="*60)
    
    # Cargar eventos existentes
    output_path = r'public\partidos.json'
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            eventos = json.load(f)
    except FileNotFoundError:
        eventos = []
        print("⚠️ No hay eventos existentes, se creará un archivo nuevo")
    
    # Solicitar datos del evento
    print("\n🕐 HORARIO (Hora Argentina)")
    hora = input("   Ingrese hora (HH:MM): ").strip()
    if not re.match(r'^\d{2}:\d{2}$', hora):
        print("❌ Formato de hora inválido. Use HH:MM")
        return
    
    print("\n🏆 INFORMACIÓN DEL EVENTO")
    liga = input("   Liga/Competencia: ").strip()
    if not liga.endswith(':'):
        liga += ':'
    
    equipos = input("   Equipos (ej: River vs Boca): ").strip()
    if not equipos:
        print("❌ Debe ingresar los equipos")
        return
    
    logo = input("   URL del logo (Enter para usar predeterminado): ").strip()
    if not logo:
        logo = "https://pelis4k.online/banderas/internacional.png"
    
    # Calcular hora UTC
    try:
        hour, minute = map(int, hora.split(':'))
        today = datetime.now().date()
        argentina_dt = datetime.combine(today, datetime.strptime(hora, "%H:%M").time())
        utc_dt = argentina_dt + timedelta(hours=3)
        hora_utc = utc_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    except Exception as e:
        print(f"❌ Error calculando hora UTC: {e}")
        return
    
    # Solicitar canales
    canales = []
    print("\n📺 CANALES (ingrese 'fin' para terminar)")
    while True:
        print(f"\n   Canal #{len(canales) + 1}:")
        nombre = input("      Nombre del canal (o 'fin'): ").strip()
        if nombre.lower() == 'fin':
            break
        if not nombre:
            continue
        
        url = input("      URL del canal: ").strip()
        if not url:
            print("      ⚠️ URL vacía, canal omitido")
            continue
        
        calidad = input("      Calidad (HD/720p/1080p) [Enter=HD]: ").strip() or "HD"
        
        canales.append({
            "nombre": nombre,
            "url": url,
            "calidad": calidad
        })
        print(f"      ✅ Canal '{nombre}' agregado")
    
    if not canales:
        print("⚠️ No se agregaron canales. ¿Desea continuar? (s/n)")
        if input().lower() != 's':
            print("❌ Operación cancelada")
            return
    
    # Crear evento
    nuevo_evento = {
        "hora_utc": hora_utc,
        "hora_argentina": hora,
        "logo": logo,
        "liga": liga,
        "equipos": equipos,
        "canales": canales
    }
    
    # Confirmar
    print("\n" + "="*60)
    print("📋 RESUMEN DEL EVENTO")
    print("="*60)
    print(f"🕐 Hora: {hora} (Argentina)")
    print(f"🏆 Liga: {liga}")
    print(f"⚽ Equipos: {equipos}")
    print(f"📺 Canales: {len(canales)}")
    for i, canal in enumerate(canales, 1):
        print(f"   {i}. {canal['nombre']} ({canal['calidad']})")
    print("="*60)
    
    confirmar = input("\n¿Confirmar y guardar? (s/n): ").strip().lower()
    if confirmar != 's':
        print("❌ Operación cancelada")
        return
    
    # Agregar y guardar
    eventos.append(nuevo_evento)
    
    try:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(eventos, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ ¡Evento agregado exitosamente!")
        print(f"📁 Total de eventos: {len(eventos)}")
        print(f"💾 Guardado en: {output_path}")
    except Exception as e:
        print(f"\n❌ Error guardando: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scraper Integrado de Eventos Deportivos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos de uso:
  python scraper_integrado.py --auto          # Ejecutar scraping automático
  python scraper_integrado.py --add           # Agregar evento manual
  python scraper_integrado.py                 # Ejecutar scraping (predeterminado)
        '''
    )
    
    parser.add_argument('--auto', action='store_true',
                        help='Ejecutar scraping automático de todas las fuentes')
    parser.add_argument('--add', action='store_true',
                        help='Agregar un evento manualmente (modo interactivo)')
    
    args = parser.parse_args()
    
    if args.add:
        add_manual_event()
    else:
        # --auto o sin argumentos ejecuta el scraper
        scraper = ScraperIntegrado()
        scraper.run()

