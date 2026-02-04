# Scraper de Películas con Sincronización Automática

## 🎬 Descripción

Scraper automático de películas desde **verpeliculasultra.com** con sincronización integrada a **GitHub** y **Supabase**.

### Características

✅ **Extracción de datos:**
- Títulos y años de películas
- Búsqueda automática de IDs en TMDB
- Extracción de servidores con URLs completas
- Información de idiomas disponibles

✅ **Sincronización automática:**
- Push automático a GitHub después de cada scraping
- Sincronización de datos a Supabase
- Manejo de cambios remotos (rebase)
- Logging detallado de cada paso

✅ **Estructura de datos unificada:**
```json
{
  "tmdb_id": 1054867,
  "title": "Una batalla tras otra",
  "year": "2025",
  "servers": [
    {
      "url": "https://hglink.to/e/...",
      "server": "hglink.to",
      "language": "Español"
    }
  ]
}
```

## 📋 Requisitos

### Instalación de dependencias

```bash
pip install -r requirements.txt
```

**Dependencias principales:**
- `requests` - Solicitudes HTTP
- `beautifulsoup4` - Parsing HTML
- `undetected-chromedriver` - Navegación web sin detección
- `selenium` - Automatización web
- `python-dotenv` - Variables de entorno
- `supabase` - Cliente de Supabase

### Variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anonymous-key
```

### Configuración de Git

Asegurarse de que Git esté configurado:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

## 🚀 Uso

### Ejecución básica (1 página)

```bash
python scraper_pelisplushd_movies.py
```

### Scraping de múltiples páginas

```bash
python scraper_pelisplushd_movies.py --max-pages 5
```

### Especificar archivo de salida

```bash
python scraper_pelisplushd_movies.py --max-pages 3 --output custom_path/peliculas.json
```

### Prueba rápida

```bash
python test_scraper_auto.py
```

## 📊 Flujo de ejecución

1. **Extracción** → Scraping de datos desde verpeliculasultra.com
2. **Enriquecimiento** → Búsqueda de metadatos en TMDB
3. **Guardado** → Almacenamiento en JSON local
4. **GitHub** → Commit y push automático
5. **Supabase** → Sincronización de base de datos

## 📝 Logs y Monitoreo

El script genera logs detallados:

```
2026-02-04 16:30:15 - INFO - Iniciando scraper de verpeliculasultra.com...
2026-02-04 16:30:18 - INFO - Se encontraron 24 películas en la página
2026-02-04 16:30:45 - INFO - ✅ Guardadas 47 películas en .../peliculas.json
2026-02-04 16:30:47 - INFO - 🚀 SINCRONIZANDO CON GITHUB
2026-02-04 16:30:52 - INFO - 🎉 ¡Push a GitHub exitoso!
2026-02-04 16:30:55 - INFO - 🚀 SINCRONIZANDO CON SUPABASE
2026-02-04 16:31:20 - INFO - 🎉 ¡Películas sincronizadas con Supabase exitosamente!
```

## ⚠️ Manejo de errores

El scraper es robusto frente a errores comunes:

- **Sin conexión a GitHub:** Guarda el JSON y avisa de forma amigable
- **Sin acceso a Supabase:** Continúa con el guardado local
- **Película no encontrada en TMDB:** La omite y continúa
- **Servidor sin respuesta:** Reintentos automáticos con timeout

## 📦 Estructura de archivos

```
peliculas/
├── scraper_pelisplushd_movies.py    # Scraper principal
├── sync_movies_supabase.py          # Módulo Supabase
├── test_scraper_auto.py             # Script de prueba
├── SCRAPER_PELICULAS_README.md      # Este archivo
└── scrappersdata/
    └── peliculas.json               # Base de datos local
```

## 🔧 Personalización

### Modificar páginas a extraer

En `scraper_pelisplushd_movies.py`, línea ~300:

```python
parser.add_argument('--max-pages', type=int, default=1, help='Número máximo de páginas a scrapear')
```

### Cambiar tabla Supabase

En `sync_movies_supabase.py`, línea ~14:

```python
self.table_name = 'tu_tabla_aqui'  # Cambiar nombre de tabla
```

### Filtrar por idioma

Agregar en `extraer_servidores()`:

```python
if idioma == 'Español':  # Filtrar solo español
    servidores.append(servidor_info)
```

## 🐛 Solución de problemas

### Error: "pathspec did not match any files"

```bash
git add .
git status
```

### Error: "untracked working tree files would be overwritten"

```bash
git clean -fd
git pull origin master
```

### Supabase connection refused

- Verificar variables de entorno: `echo $SUPABASE_URL`
- Verificar conexión a internet
- Verificar credenciales en Supabase Dashboard

### TMDB API errors

- Verificar que `TMDB_API_KEY` es válida
- Verificar límite de requests (2500/day)
- Esperar 1 segundo entre requests (ya configurado)

## 📈 Estadísticas y métricas

Después de cada ejecución:

```
✅ Scraping completado. Total: 47 películas
  ➕ Insertadas: 23
  ✏️ Actualizadas: 24
  ❌ Errores: 0
```

## 🔄 Automatización (Windows)

Crear `run_scraper_auto.bat`:

```batch
@echo off
cd /d "C:\Users\franc\Desktop\SCRAPPERS\PELICULAS-SERIES-ANIME\peliculas"
python scraper_pelisplushd_movies.py --max-pages 5
pause
```

Programar con Task Scheduler para ejecución automática diaria.

## 📚 Recursos

- **TMDB API:** https://www.themoviedb.org/settings/api
- **Supabase Docs:** https://supabase.com/docs
- **Git Documentation:** https://git-scm.com/doc
- **BeautifulSoup:** https://www.crummy.com/software/BeautifulSoup/

## 📞 Soporte

Para problemas o mejoras:

1. Verificar logs detallados
2. Revisar archivo `.env`
3. Comprobar conexiones de red
4. Consultar documentación oficial de dependencias

## 📄 Licencia

Uso personal - Proyecto de scraping web

---

**Última actualización:** 4 de febrero, 2026
