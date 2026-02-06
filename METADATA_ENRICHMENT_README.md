# Enriquecimiento de Metadata - Series, Películas y Anime

Este módulo agrega información adicional (poster, backdrop, géneros en español) a los archivos JSON existentes de series, películas y anime utilizando la API de The Movie Database (TMDB).

## 🎯 Características

- **Posters**: URLs de imágenes de poster (500px de ancho)
- **Backdrops**: URLs de imágenes de fondo (500px de ancho)  
- **Géneros en español**: Lista de géneros traducidos al español
- **Sinopsis mejorada**: Actualiza overview vacío con versión en español
- **Ratings**: Complementa ratings faltantes con datos de TMDB

## 📁 Archivos Incluidos

### Scripts Principales
- `enrich_metadata_scraper.py` - Script principal para enriquecimiento completo
- `selective_metadata_enricher.py` - Enriquecimiento selectivo con opciones avanzadas
- `test_metadata_enricher.py` - Script de prueba (procesa solo 3 elementos)

### Archivos Batch (Ejecutables)
- `run_metadata_enricher.bat` - Ejecuta el enriquecimiento completo
- `test_metadata_enricher.bat` - Ejecuta las pruebas

## 🚀 Uso Rápido

### 1. Prueba Inicial (Recomendado)
```bash
# Opción 1: Usar el archivo .bat
test_metadata_enricher.bat

# Opción 2: Ejecutar directamente
python test_metadata_enricher.py
```

### 2. Enriquecimiento Completo
```bash
# Opción 1: Usar el archivo .bat
run_metadata_enricher.bat

# Opción 2: Ejecutar directamente
python enrich_metadata_scraper.py
```

### 3. Enriquecimiento Selectivo
```bash
# Solo películas
python selective_metadata_enricher.py --type movies

# Solo las primeras 100 series
python selective_metadata_enricher.py --type series --start 0 --end 100

# Forzar actualización de anime (incluso si ya está enriquecido)
python selective_metadata_enricher.py --type anime --force

# Procesar películas desde el índice 50 al 150
python selective_metadata_enricher.py --type movies --start 50 --end 150
```

## 📊 Estructura de Datos Resultante

### Antes del Enriquecimiento
```json
{
  "tmdb_id": 123456,
  "title": "Película Ejemplo",
  "year": "2025",
  "genres": ["Action"]
}
```

### Después del Enriquecimiento
```json
{
  "tmdb_id": 123456,
  "title": "Película Ejemplo",
  "year": "2025",
  "genres": ["Action"],
  "poster_url": "https://image.tmdb.org/t/p/w500/poster123.jpg",
  "backdrop_url": "https://image.tmdb.org/t/p/w500/backdrop123.jpg",
  "genres_spanish": ["Acción", "Aventura"],
  "overview": "Sinopsis en español...",
  "rating": 7.5
}
```

## ⚙️ Opciones del Script Selectivo

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--type` | Tipo de contenido (`movies`, `series`, `anime`, `all`) | `--type movies` |
| `--start` | Índice de inicio (0-based) | `--start 100` |
| `--end` | Índice de fin (0-based, exclusivo) | `--end 200` |
| `--force` | Forzar actualización de elementos ya enriquecidos | `--force` |

### Ejemplos de Uso Selectivo

```bash
# Procesar solo los primeros 50 elementos de cada tipo
python selective_metadata_enricher.py --end 50

# Continuar desde donde se quedó (índice 500 en adelante)
python selective_metadata_enricher.py --start 500

# Re-procesar películas específicas (índices 100-200)
python selective_metadata_enricher.py --type movies --start 100 --end 200 --force

# Procesar solo anime desde el índice 1000
python selective_metadata_enricher.py --type anime --start 1000
```

## 🔧 Configuración

### API Key de TMDB
Los scripts usan la clave: `201d333198374a91c81dba3c443b1a8e`

Si necesitas cambiarla, modifica la variable `TMDB_API_KEY` en cada script.

### Rate Limiting
Los scripts incluyen un delay de 0.25 segundos entre requests para respetar los límites de la API de TMDB.

## 📈 Monitoreo y Logs

### Información Mostrada
- ✅ Elementos procesados exitosamente
- ❌ Errores encontrados
- 📊 Estadísticas finales
- ⏱️ Tiempo total de ejecución
- 💾 Ubicación de archivos backup

### Backups Automáticos
Antes de cualquier modificación, se crean backups automáticos:
- `series_backup_YYYYMMDD_HHMMSS.json`
- `peliculas_backup_YYYYMMDD_HHMMSS.json`
- `anime_backup_YYYYMMDD_HHMMSS.json`

## 📁 Archivos Procesados

| Archivo | Descripción | Media Type TMDB |
|---------|-------------|-----------------|
| `series.json` | Series de TV | `tv` |
| `anime.json` | Series de anime | `tv` |
| `peliculas.json` | Películas | `movie` |

## ⚠️ Consideraciones

### Requisitos Previos
- Los archivos JSON deben existir en `PELICULAS-SERIES-ANIME/`
- Cada elemento debe tener un `tmdb_id` válido
- Conexión a internet para acceder a la API de TMDB

### Limitaciones
- Solo funciona con elementos que tengan `tmdb_id`
- Dependiente de la disponibilidad de la API de TMDB
- Los géneros dependen de la traducción disponible en TMDB

### Reinicio Seguro
Si el proceso se interrumpe:
1. Los backups están disponibles
2. Puedes usar el script selectivo con `--start` para continuar desde donde se quedó
3. Los elementos ya enriquecidos se saltan automáticamente (usa `--force` para re-procesar)

## 🎯 Ejemplos Prácticos

### Workflow Completo
```bash
# 1. Prueba inicial
python test_metadata_enricher.py

# 2. Si las pruebas son exitosas, ejecutar completo
python enrich_metadata_scraper.py

# 3. O procesar por lotes pequeños
python selective_metadata_enricher.py --type movies --end 100
python selective_metadata_enricher.py --type movies --start 100 --end 200
# ... continuar hasta completar
```

### Recuperación de Errores
```bash
# Si el proceso falló en el índice 1500, continuar desde ahí
python selective_metadata_enricher.py --start 1500

# Re-procesar solo elementos con errores (después de revisar logs)
python selective_metadata_enricher.py --start [índice] --end [índice+50] --force
```

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs de salida
2. Verifica que los archivos JSON existan y tengan `tmdb_id`
3. Usa el script de prueba para validar conexión a TMDB
4. Los backups permiten revertir cambios si es necesario