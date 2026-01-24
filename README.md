# 🏆 Scraper Integrado de Eventos Deportivos

Extractor automático de partidos desde múltiples fuentes: **ElCanalDeportivo**, **TVLibree**, **PirloTV**, **FutbolLibreFullHD**, **Pelota-Libre.PE**, **RusticoTV**, **Bolaloca**, y más.

## 🚀 Características

✅ Extracción automática desde 8+ fuentes  
✅ CLI para agregar eventos manualmente  
✅ Automatización cada 30 minutos (GitHub Actions)  
✅ Sincronización con Supabase (opcional)  
✅ Ejecutable Windows (.exe)  
✅ Filtrado automático de eventos pasados  
✅ Deduplicación inteligente de eventos  

## 📦 Instalación

### Requisitos
```bash
pip install requests beautifulsoup4 python-dotenv
pip install supabase  # Opcional, para sincronización
```

### Clonar repositorio
```bash
git clone <tu-repo>
cd SCRAPPERS
```

## 🎮 Uso

### 1. Scraping Automático
```bash
python scraper_integrado.py --auto
```
Extrae eventos de todas las fuentes y guarda en `public/partidos.json`

### 2. Agregar Evento Manual
```bash
python scraper_integrado.py --add
```
CLI interactivo para agregar un evento personalizado:
- ⏰ Hora (formato Argentina)
- 🏆 Liga/Competencia
- ⚽ Equipos
- 🖼️ Logo (URL)
- 📺 Canales (múltiples)

### 3. Ejecutar scraping sin argumentos
```bash
python scraper_integrado.py
```
Comportamiento predeterminado (igual que `--auto`)

## 🤖 Automatización (GitHub Actions)

### Configuración
1. **Sube el proyecto a GitHub**
2. **Configura secretos** (opcional, para Supabase):
   - Ve a `Settings` → `Secrets and variables` → `Actions`
   - Agrega:
     - `SUPABASE_URL`: Tu URL de Supabase
     - `SUPABASE_KEY`: Tu clave de Supabase

3. **Activa GitHub Actions**:
   - El workflow en `.github/workflows/scraper.yml` se ejecutará automáticamente cada **30 minutos**
   - Los resultados se commitean a `public/partidos.json`

### Ejecución manual
Ve a `Actions` → `Scraper Automático` → `Run workflow`

## 📦 Generar Ejecutable Windows

### Compilar a .exe
```bash
compilar_exe.bat
```

Esto genera `dist/ScraperDeportivo.exe` que puedes distribuir sin Python.

### Uso del ejecutable
```cmd
ScraperDeportivo.exe          # Ejecutar scraping
ScraperDeportivo.exe --add    # Agregar evento manual
ScraperDeportivo.exe --auto   # Scraping automático
```

## 📁 Estructura de Archivos

```
SCRAPPERS/
├── scraper_integrado.py       # Script principal
├── public/
│   └── partidos.json          # Salida de eventos
├── .github/
│   └── workflows/
│       └── scraper.yml        # Workflow de automatización
├── compilar_exe.bat           # Script para compilar .exe
├── sync_partidos_auto.py      # Sincronización Supabase (opcional)
└── README.md                  # Este archivo
```

## 🌐 Fuentes Soportadas

| Fuente | Estado | Eventos Típicos |
|--------|--------|-----------------|
| **ElCanalDeportivo** | ✅ Activo | 30-40 |
| **TVLibree** | ✅ Activo | 20-30 |
| **PirloTV** | ✅ Activo | 80-100 |
| **FutbolLibreFullHD** | ✅ Activo | Variable |
| **Pelota-Libre.PE** | ✅ Activo | Variable |
| **RusticoTV** | ✅ Activo | Variable |
| **Bolaloca** | ⚠️ Intermitente | Variable |
| **Pelota-Libre.NET** | ⚠️ Intermitente | Variable |

## 🔧 Configuración Avanzada

### Supabase (opcional)
Crea un archivo `.env`:
```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-clave-aqui
```

### Modificar frecuencia de scraping
Edita `.github/workflows/scraper.yml`:
```yaml
schedule:
  - cron: '*/30 * * * *'  # Cada 30 min
  # - cron: '0 */1 * * *'  # Cada hora
  # - cron: '0 * * * *'    # Cada hora en punto
```

## 📊 Formato de Salida (JSON)

```json
[
  {
    "hora_utc": "2026-01-24T20:00:00Z",
    "hora_argentina": "17:00",
    "logo": "https://...",
    "liga": "Liga Profesional Argentina:",
    "equipos": "River Plate vs Boca Juniors",
    "canales": [
      {
        "nombre": "ESPN Premium",
        "url": "https://...",
        "calidad": "HD"
      }
    ]
  }
]
```

## 🆓 Hosting Gratuito

### Opciones recomendadas:
1. **GitHub Actions** (30 min) - ✅ **Ya configurado**
2. **Railway.app** (500h/mes gratis)
3. **Render.com** (750h/mes gratis)
4. **Fly.io** (Gratis con límites)

## 🐛 Solución de Problemas

### Error: "No se encontró ul#menu"
- La página cambió su estructura DOM
- Verifica que el sitio esté accesible

### Error: "getaddrinfo failed"
- Sin conexión a internet
- El dominio no responde

### Sincronización Supabase falla
- Verifica que `.env` tenga credenciales correctas
- Instala: `pip install supabase python-dotenv`

## 📝 Licencia

MIT License - Uso libre

## 🤝 Contribuir

Pull requests bienvenidos. Para cambios grandes, abre un issue primero.

---

**Desarrollado con ❤️ para la comunidad deportiva**
