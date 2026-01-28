# CHANGELOG

## [Última versión] - 27/01/2026

### 🆕 Agregar
- **StreamTPCloud**: Nueva fuente de eventos (eventos.json)
  - Soporte para 8 eventos simultáneos de Fútbol y Basquetbol
  - Limpieza automática de caracteres Unicode malformados
  - Decodificación de URLs con slashes escapados

- **Base64 URL Decoder para TVLibree**:
  - Nueva función xtract_iframe_from_base64_tvlibre()
  - Extrae URLs desde parámetro ?r= en base64
  - Ej: ?r=aHR0cHM6Ly9zdHJlYW10cGNsb3VkLmNvbS9nbG9iYWwxLnBocD9zdHJlYW09cHJlbWllcmUx

- **Documentación Completa**:
  - README.md mejorado con ejemplos y tablas
  - Instrucciones de instalación paso a paso
  - Guía de troubleshooting

### 🔧 Cambios
- Mejorar deduplicación inteligente de eventos
- Agregar StreamTPCloud a merge_events()
- Optimizar limpieza de datos malformados
- Actualizar función run() para incluir StreamTPCloud

### 📊 Estadísticas
- **Fuentes soportadas**: 8+
- **Eventos por ejecución**: 80-150 típicamente
- **Tiempo de ejecución**: ~30-60 segundos
- **Líneas de código**: 3300+

## [v1.0.0] - 24/01/2026

### 🎉 Inicial
- Extracción de TVLibree
- Extracción de FTVHD
- Merge inteligente de eventos
- Filtrado de eventos pasados
- Guardado en JSON
- Ejecutable Windows (.exe)
