yyy@echo off
REM Scraper de peliculas desde poseidonhd2.co/peliculas
REM Ejecuta: python scraper_poseidon_movies.py --max-pages 5

title Scraper Peliculas - PoseidonHD2
color 0A

cd /d "%~dp0"

chcp 65001 >nul

echo.
echo ============================================================
echo  SCRAPER DE PELICULAS DESDE POSEIDONHD2.CO
echo ============================================================
echo.
echo Caracteristicas:
echo  - Extrae peliculas desde poseidonhd2.co
echo  - Obtiene servidores desde player.poseidonhd2.co
echo  - Actualiza peliculas.json en el root del workspace
echo.

REM Pedir número de páginas
set /p PAGES="Cuantas paginas deseas scrapear? (default: 5): "
if "%PAGES%"=="" set PAGES=5

set /p MOVIES="Cuantas peliculas deseas scrapear? (Enter = todas): "

echo.
echo Iniciando scraper con %PAGES% páginas...
echo.

if "%MOVIES%"=="" (
	set MOVIES_ARG=
) else (
	set MOVIES_ARG=--max-movies %MOVIES%
)

python scraper_poseidon_movies.py --max-pages %PAGES% %MOVIES_ARG%

echo.
echo ============================================================
echo  PROCESO COMPLETADO
echo ============================================================
echo.
pause
