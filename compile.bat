@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "BUILD_DIR=build\nuitka-zig"
set "MODE=standalone"
set "APP_NAME=api-consulta"

if /I "%~1"=="onefile" set "MODE=onefile"
if /I "%~1"=="standalone" set "MODE=standalone"

echo.
echo === API Consulta CPF - Nuitka + Zig (%MODE%) ===
echo Saida: %BUILD_DIR%
echo.

where zig >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Zig nao encontrado no PATH.
    echo Instale em https://ziglang.org/download/ e adicione zig.exe ao PATH.
    exit /b 1
)

where uv >nul 2>&1
if errorlevel 1 (
    echo [ERRO] uv nao encontrado no PATH.
    echo Instale em https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

echo [1/4] Sincronizando dependencias...
call uv sync --group build
if errorlevel 1 exit /b 1

echo.
echo [2/4] Preparando runtime desktop do Flet...
call uv run python scripts\prepare_flet_desktop.py
if errorlevel 1 exit /b 1

echo.
echo [3/4] Criando pasta de saida...
if not exist "build" mkdir "build"
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

echo.
echo [4/4] Compilando com Nuitka (--zig)...
call uv run python -m nuitka ^
    --zig ^
    --assume-yes-for-downloads ^
    --output-dir=%BUILD_DIR% ^
    --mode=%MODE% ^
    --output-filename=%APP_NAME%.exe ^
    --include-package=app ^
    --include-package=flet ^
    --include-package=flet_desktop ^
    --include-package=httpx ^
    --include-package=httpx._transports ^
    --include-package=anyio ^
    --include-package=certifi ^
    --include-package=dotenv ^
    --include-package-data=flet_desktop ^
    --include-data-dir=assets=assets ^
    --user-package-configuration-file=scripts\nuitka_flet.yml ^
    --windows-icon-from-ico=assets\icon_windows.png ^
    --product-name="API Consulta CPF" ^
    --file-description="Consultas CPF, CNPJ e CEP - Hub do Desenvolvedor" ^
    --company-name="Paitom TIC" ^
    main.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo Compilacao concluida em %BUILD_DIR%
    if /I "%MODE%"=="standalone" (
        echo Executavel: %BUILD_DIR%\main.dist\%APP_NAME%.exe
        echo Copie a pasta main.dist inteira para distribuir.
    ) else (
        echo Executavel: %BUILD_DIR%\%APP_NAME%.exe
    )
    echo.
    echo Uso: %APP_NAME%.exe --desktop
) else (
    echo [ERRO] Compilacao falhou com codigo %EXIT_CODE%.
)

endlocal
exit /b %EXIT_CODE%
