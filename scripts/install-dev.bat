@echo off
REM Instala dependencias de desenvolvimento (pytest, pylint, mypy, cobertura).
cd /d "%~dp0.."

where uv >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [uv] Sincronizando grupo dev...
    uv sync --group dev
    goto :fim
)

echo [pip] Instalando requirements-dev.txt...
python -m pip install -r requirements-dev.txt

:fim
echo.
echo Ferramentas disponiveis:
echo   uv run pytest
echo   uv run pytest --cov=app --cov-report=term-missing
echo   uv run pylint app main.py
echo   uv run mypy
