@echo off
REM Scraper de series desde poseidonhd2.co con sincronización automática

title Scraper Series - PoseidonHD2
color 0A

cd /d "%~dp0"

echo.
echo ============================================================
echo  SCRAPER DE SERIES DESDE POSEIDONHD2.CO
echo ============================================================
echo.
echo Características:
echo  ✅ Extrae series desde poseidonhd2.co
echo  ✅ Navega temporadas y episodios
echo  ✅ Extrae servidores con idiomas
echo  ✅ Sincroniza automáticamente a GitHub
echo  ✅ Sincroniza automáticamente a Supabase
echo.

REM Pedir número de series
set /p SERIES="¿Cuántas series deseas scrapear? (default: 5): "
if "%SERIES%"=="" set SERIES=5

REM Pedir número de episodios
set /p EPISODES="¿Máximo de episodios por temporada? (default: 10): "
if "%EPISODES%"=="" set EPISODES=10

echo.
echo Iniciando scraper con %SERIES% series y %EPISODES% episodios...
echo.

python scraper_poseidonhd2_series.py --max-series %SERIES% --max-episodes %EPISODES%

echo.
echo ============================================================
echo  ✅ PROCESO COMPLETADO
echo ============================================================
echo.
pause
