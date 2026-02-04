# 📺 Scraper de Series desde PoseidonHD2

Scraper automático de series desde **poseidonhd2.co** con extracción completa de:
- Información de la serie (título, año, rating, géneros)
- Temporadas disponibles
- Episodios por temporada
- Servidores por episodio con idiomas (latino, english, spanish, subtitulado)

## ✨ Características

✅ **Extracción completa:**
- Listado de series desde página principal
- Información detallada de cada serie (TMDB ID, calificación, géneros)
- Estructu estructura de temporadas y episodios
- Servidores con URLs y idiomas disponibles

✅ **Sincronización automática:**
- Push automático a GitHub después de scraping
- Sincronización a Supabase
- Manejo de conflictos remotos
- Logging detallado

## 📋 Estructura de datos

```json
{
  "tmdb_id": 287231,
  "title": "Desaparecida",
  "year": "2026",
  "overview": "Las románticas vacaciones de Alice Monroe...",
  "rating": 7.3,
  "genres": ["Drama", "Misterio"],
  "seasons": [
    {
      "number": 1,
      "episodes": [
        {
          "title": "Desaparecida 1x1",
          "number_text": "1x1",
          "servers": {
            "latino": [
              {
                "url": "https://player.poseidonhd2.co/player.php?h=...",
                "server": "streamwish",
                "quality": "HD",
                "language": "latino"
              }
            ],
            "english": [...],
            "spanish": [...],
            "subtitulado": [...]
          }
        }
      ]
    }
  ]
}
```

## 🚀 Uso

### Opción 1: Script ejecutable Windows (RECOMENDADO)
```
Doble click en: run_scraper_series.bat
```

### Opción 2: Línea de comando
```bash
python scraper_poseidonhd2_series.py --max-series 5 --max-episodes 10
```

### Opción 3: Especificar parámetros
```bash
python scraper_poseidonhd2_series.py --max-series 10 --max-episodes 5 --output ../series_custom.json
```

## 📊 Parámetros

- `--max-series`: Número máximo de series a scrapear (default: 5)
- `--max-episodes`: Máximo de episodios por temporada (default: 10)
- `--output`: Ruta del archivo JSON de salida (default: ../series.json)

## ⚙️ Configuración

### Variables de entorno (.env)
Crear archivo `.env` en raíz del proyecto:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anonymous-key
```

### Dependencias
```bash
pip install requests beautifulsoup4 python-dotenv supabase
```

## 📈 Ejemplo de ejecución

```
2026-02-04 16:30:15 - INFO - Iniciando scraper de poseidonhd2.co series...
2026-02-04 16:30:18 - INFO - Se encontraron 24 series en la página
2026-02-04 16:30:45 - INFO - --- Serie 1/5 ---
2026-02-04 16:30:47 - INFO - Procesando: Desaparecida
2026-02-04 16:30:50 - INFO -   Procesando temporada 1...
2026-02-04 16:30:52 - INFO -     Procesando episodio 1/1...
2026-02-04 16:31:10 - INFO -     Encontrados 6 servidores
2026-02-04 16:31:12 - INFO - ✅ Serie agregada: Desaparecida - 1 temporada(s)
2026-02-04 16:31:15 - INFO - ✅ Guardadas 5 series en .../series.json
```

## 🔄 Flujo automático

```
Obtener lista de series
    ↓
Para cada serie:
    ├─ Extraer información (TMDB, rating, géneros)
    ├─ Obtener temporadas disponibles
    └─ Para cada temporada:
        ├─ Obtener episodios
        └─ Para cada episodio:
            └─ Extraer servidores (múltiples idiomas)
    ↓
Guardar en JSON
    ↓
Push a GitHub
    ↓
Sincronizar a Supabase
```

## ⏱️ Tiempos típicos

- 5 series × 1 temporada × 5 episodios: ~3-4 minutos
- 10 series × 1 temporada × 10 episodios: ~6-8 minutos

(Incluye pausas para no saturar servidores)

## 📝 Notas importantes

- El scraper respeta los servidores con pausas entre requests
- Extrae solo el número de episodios especificado por temporada
- Los datos se fusionan con datos existentes (sin duplicados por tmdb_id)
- Todos los videos se organizan por idioma disponible

## 🐛 Solución de problemas

### Error: "No se encontró section.home-movies"
- Posible cambio en estructura HTML del sitio
- Verificar visualmente la página y actualizar selectores

### Sin servidores encontrados
- Algunos episodios pueden no tener servers disponibles
- El sitio cambia dinámicamente los contenidos

### Sincronización falla
- Verificar conexión a internet
- Revisar variables de entorno (.env)
- Verificar credenciales de GitHub y Supabase

---

**Creado:** 4 de febrero, 2026
**Versión:** 1.0
**Estado:** Funcionando
