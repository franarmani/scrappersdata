@echo off
title Scraper Deportivo - Menu Principal
color 0A

:menu
cls
echo ========================================
echo   🏆 SCRAPER DEPORTIVO
echo ========================================
echo.
echo   1. 🤖 Ejecutar Scraping Automatico
echo   2. ➕ Agregar Evento Manual
echo   3. 📦 Compilar a .EXE
echo   4. 📊 Ver partidos.json
echo   5. ❌ Salir
echo.
echo ========================================
set /p opcion="Seleccione una opcion (1-5): "

if "%opcion%"=="1" goto scraping
if "%opcion%"=="2" goto agregar
if "%opcion%"=="3" goto compilar
if "%opcion%"=="4" goto ver
if "%opcion%"=="5" goto salir

echo.
echo ❌ Opcion invalida
timeout /t 2 >nul
goto menu

:scraping
cls
echo ========================================
echo   🤖 EJECUTANDO SCRAPING...
echo ========================================
echo.
python scraper_integrado.py --auto
echo.
echo ========================================
pause
goto menu

:agregar
cls
echo ========================================
echo   ➕ AGREGAR EVENTO MANUAL
echo ========================================
echo.
python scraper_integrado.py --add
echo.
pause
goto menu

:compilar
cls
echo ========================================
echo   📦 COMPILANDO A .EXE
echo ========================================
echo.
call compilar_exe.bat
goto menu

:ver
cls
echo ========================================
echo   📊 CONTENIDO DE partidos.json
echo ========================================
echo.
if exist "public\partidos.json" (
    type "public\partidos.json"
) else (
    echo ❌ Archivo no encontrado
)
echo.
echo ========================================
pause
goto menu

:salir
cls
echo.
echo 👋 ¡Hasta luego!
echo.
timeout /t 2 >nul
exit
