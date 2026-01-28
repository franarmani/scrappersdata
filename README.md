# 🏆 Scraper Integrado de Eventos Deportivos

Extractor automático de partidos desde múltiples fuentes: TVLibree, FTVHD, StreamTPCloud, PirloTV, FutbolLibreFullHD, Pelota-Libre, RusticoTV, y más.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)

## 🚀 Características

- ✅ Extracción automática desde **8+ fuentes** de eventos deportivos
- ✅ CLI para agregar eventos manualmente
- ✅ Automatización cada 30 minutos vía GitHub Actions
- ✅ Sincronización con Supabase (opcional)
- ✅ Ejecutable Windows (.exe) incluido
- ✅ Filtrado automático de eventos pasados
- ✅ Deduplicación inteligente de eventos
- ✅ Soporte para base64 encoding (TVLibree)
- ✅ Limpieza de caracteres Unicode malformados

## 📋 Requisitos

- Python 3.8+
- pip

## 📦 Instalación

### 1. Clonar repositorio
``ash
git clone https://github.com/franarmani/SCRAPPERS.git
cd SCRAPPERS
``

### 2. Instalar dependencias
``ash
pip install -r requirements.txt
``

O manualmente:
``ash
pip install requests beautifulsoup4 python-dotenv
pip install supabase  # Opcional, para sincronización
``

## 🎮 Uso

### 1. Scraping Automático
``ash
python scraper_integrado.py
``
Extrae eventos de todas las fuentes activas y guarda en public/partidos.json

### 2. Agregar Evento Manual
``ash
python scraper_integrado.py --add
``
CLI interactivo para crear un evento personalizado

## 🌐 Fuentes Soportadas

| Fuente | Estado | Eventos Típicos |
|--------|--------|-----------------|
| TVLibree | ✅ Activo | 20-30 |
| FTVHD | ✅ Activo | 15-25 |
| StreamTPCloud | ✅ Activo | 8-15 |
| PirloTV | ✅ Activo | 80-100 |
| FutbolLibreFullHD | ✅ Activo | Variable |
| Pelota-Libre.NET | ⚠️ Intermitente | Variable |
| RusticoTV | ⚠️ Intermitente | Variable |

## 📁 Estructura de Archivos

``
SCRAPPERS/
├── scraper_integrado.py           # Script principal
├── requirements.txt               # Dependencias
├── public/
│   └── partidos.json              # Salida de eventos (JSON)
├── .github/
│   └── workflows/
│       └── scraper.yml            # Workflow de automatización
├── README.md                      # Este archivo
``

## 📝 Licencia

MIT License - Uso libre

Desarrollado con ❤️ para la comunidad deportiva latinoamericana.

**Última actualización**: 27/01/2026
