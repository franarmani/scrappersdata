@echo off
echo.
echo ==========================================
echo    ENRIQUECIMIENTO DE METADATA 
echo    Agregando posters, backdrops y generos
echo ==========================================
echo.

cd /d "%~dp0"

echo Iniciando enriquecimiento de metadata...
python enrich_metadata_scraper.py

echo.
echo Presiona cualquier tecla para salir...
pause >nul