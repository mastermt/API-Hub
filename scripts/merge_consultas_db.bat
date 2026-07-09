@echo off
REM Mescla consultas.db das 3 localizacoes em data\consultas.db
cd /d "%~dp0.."
uv run python scripts/merge_consultas_db.py %*
