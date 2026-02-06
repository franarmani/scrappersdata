@echo off
echo.
echo ==========================================
echo    PRUEBA DE ENRIQUECIMIENTO DE METADATA
echo    Procesando solo 3 elementos de cada tipo
echo ==========================================
echo.

cd /d "%~dp0"

echo Ejecutando pruebas de enriquecimiento...
python test_metadata_enricher.py

echo.
echo Presiona cualquier tecla para salir...
pause >nul