@echo off
echo =========================================
echo   COMPILANDO SCRAPER A EJECUTABLE
echo =========================================
echo.

REM Verificar si PyInstaller está instalado
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

echo.
echo Compilando scraper_integrado.py...
echo.

REM Compilar con PyInstaller
pyinstaller --onefile ^
    --name="ScraperDeportivo" ^
    --icon=NONE ^
    --add-data="public;public" ^
    --hidden-import=requests ^
    --hidden-import=bs4 ^
    --hidden-import=urllib3 ^
    --hidden-import=json ^
    --hidden-import=re ^
    --hidden-import=datetime ^
    --hidden-import=base64 ^
    --noconsole ^
    scraper_integrado.py

echo.
if exist "dist\ScraperDeportivo.exe" (
    echo ========================================
    echo   ✅ COMPILACION EXITOSA
    echo ========================================
    echo.
    echo Ejecutable generado en: dist\ScraperDeportivo.exe
    echo.
    echo Uso:
    echo   ScraperDeportivo.exe          - Ejecutar scraping
    echo   ScraperDeportivo.exe --add    - Agregar evento manual
    echo   ScraperDeportivo.exe --auto   - Scraping automatico
    echo.
) else (
    echo ========================================
    echo   ❌ ERROR EN LA COMPILACION
    echo ========================================
)

pause
