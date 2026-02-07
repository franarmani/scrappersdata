@echo off
REM Scraper de series desde poseidonhd2.co/series

title Scraper Series - PoseidonHD2
color 0A

cd /d "%~dp0"

chcp 65001 >nul

echo.
echo ============================================================
echo  SCRAPER DE SERIES DESDE POSEIDONHD2.CO
echo ============================================================
echo.
echo Caracteristicas:
echo  - Navega grids de series
echo  - Extrae temporadas y episodios (sin temporada 0)
echo  - Obtiene servidores por episodio
echo  - Actualiza series.json en el root del workspace
echo.

set /p PAGES="Cuantas paginas deseas scrapear? (Enter = todas): "
set /p SERIES="Cuantas series deseas scrapear? (Enter = todas): "
set /p EPISODES="Maximo de episodios a extraer (Enter = sin limite): "

echo.
if "%PAGES%"=="" (
  set PAGES_ARG=
) else (
  set PAGES_ARG=--max-pages %PAGES%
)

if "%SERIES%"=="" (
  set SERIES_ARG=
) else (
  set SERIES_ARG=--max-series %SERIES%
)

if "%EPISODES%"=="" (
  set EPISODES_ARG=
) else (
  set EPISODES_ARG=--max-episodes %EPISODES%
)

echo Iniciando scraper...
python scraper_poseidon_series.py %PAGES_ARG% %SERIES_ARG% %EPISODES_ARG%

echo.
echo Subiendo cambios a GitHub...
pushd "%~dp0\..\.."
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo No se detecto un repositorio git. Saltando push.
  popd
) else (
  git add series.json >nul 2>nul
  git diff --cached --quiet
  if errorlevel 1 (
    for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set TS=%%i
    git commit -m "Update series.json %TS%"
    git push
  ) else (
    echo No hay cambios nuevos para commitear.
  )
  popd
)

echo.
echo ============================================================
echo  PROCESO COMPLETADO
echo ============================================================
echo.
pause
