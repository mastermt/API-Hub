@echo off
REM Executa testes, cobertura, pylint e mypy (requer grupo dev instalado).
cd /d "%~dp0.."
set FAILED=0

echo === pytest ===
call uv run pytest --cov=app --cov-report=term-missing
if errorlevel 1 set FAILED=1

echo.
echo === pylint ===
call uv run pylint app main.py
if errorlevel 1 set FAILED=1

echo.
echo === mypy ===
call uv run mypy
if errorlevel 1 set FAILED=1

if %FAILED%==1 (
    echo.
    echo Verificacao de desenvolvimento falhou.
    exit /b 1
)

echo.
echo Verificacao de desenvolvimento concluida com sucesso.
