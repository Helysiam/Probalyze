@echo off
setlocal EnableDelayedExpansion
title Déploiement Probalyze

set NAS_IP=192.168.1.28
set NAS_USER=admin
set NAS_PATH=/volume1/web/Probalyze
set NAS_SMB=\\192.168.1.28\web\Probalyze
set APP_DIR=C:\Users\Jerem\Desktop\Probalyze

echo.
echo ============================================
echo   DEPLOIEMENT PROBALYZE
echo   probalyze.picsnature.fr
echo ============================================
echo.

:: ─── VERIFICATION .env ─────────────────────────────────────────────────────────
if not exist "%APP_DIR%\.env" (
    echo [ERREUR] Fichier .env introuvable dans %APP_DIR%
    echo Copie .env.example en .env et renseigne les variables.
    pause
    exit /b 1
)

:: ─── ETAPE 1 : GIT PUSH ────────────────────────────────────────────────────────
echo [1/4] Push Git...
cd /d "%APP_DIR%"
git add -A
git diff --cached --quiet
if %ERRORLEVEL% equ 0 (
    echo   Rien a committer, on continue.
) else (
    git commit -m "deploy: %DATE% %TIME%"
    if !ERRORLEVEL! neq 0 (
        echo [ERREUR] Git commit echoue.
        pause
        exit /b 1
    )
)
git push
if %ERRORLEVEL% neq 0 (
    echo [AVERTISSEMENT] Git push echoue - on continue quand meme.
)
echo [1/4] Git OK
echo.

:: ─── ETAPE 2 : CREATION DOSSIER NAS ───────────────────────────────────────────
echo [2/4] Preparation dossier NAS...

ssh %NAS_USER%@%NAS_IP% "mkdir -p %NAS_PATH%/apps/api %NAS_PATH%/apps/worker %NAS_PATH%/apps/web %NAS_PATH%/services/scrapers %NAS_PATH%/services/models %NAS_PATH%/services/odds %NAS_PATH%/packages/db %NAS_PATH%/packages/utils %NAS_PATH%/infra/supabase/migrations %NAS_PATH%/logs"
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Impossible de creer les dossiers sur le NAS via SSH.
    echo Verifie que SSH est activé sur le NAS (DSM > Terminal).
    pause
    exit /b 1
)
echo [2/4] Dossiers NAS OK
echo.

:: ─── ETAPE 3 : COPIE DES FICHIERS ─────────────────────────────────────────────
echo [3/4] Copie des fichiers vers le NAS...

:: Verifier que le partage SMB est accessible
if not exist "%NAS_SMB%" (
    echo [ERREUR] Partage SMB inaccessible : %NAS_SMB%
    echo Verifie que le partage "web" existe sur le NAS.
    pause
    exit /b 1
)

:: Fonction de copie robuste via PowerShell
echo   - Copie fichiers racine...
powershell -Command ^
    "$src='%APP_DIR%'; $dst='%NAS_SMB%'; " ^
    "@('docker-compose.yml','.env','.gitignore','pyproject.toml','README.md') | ForEach-Object { " ^
    "  if (Test-Path \"$src\$_\") { [System.IO.File]::WriteAllBytes(\"$dst\$_\", [System.IO.File]::ReadAllBytes(\"$src\$_\")) } " ^
    "}; Write-Host 'racine OK'"

echo   - Copie apps/api...
powershell -Command ^
    "robocopy '%APP_DIR%\apps\api' '%NAS_SMB%\apps\api' /E /XD __pycache__ .venv /XF '*.pyc' '*.pyo' /NFL /NDL /NJH /NJS /nc /ns /np" 2>nul
if !ERRORLEVEL! geq 8 (
    echo [ERREUR] Copie apps/api echouee.
    pause
    exit /b 1
)

echo   - Copie apps/worker...
powershell -Command ^
    "robocopy '%APP_DIR%\apps\worker' '%NAS_SMB%\apps\worker' /E /XD __pycache__ /XF '*.pyc' '*.pyo' /NFL /NDL /NJH /NJS /nc /ns /np" 2>nul

echo   - Copie apps/web (hors node_modules)...
powershell -Command ^
    "robocopy '%APP_DIR%\apps\web' '%NAS_SMB%\apps\web' /E /XD node_modules .next /NFL /NDL /NJH /NJS /nc /ns /np" 2>nul

echo   - Copie services...
powershell -Command ^
    "robocopy '%APP_DIR%\services' '%NAS_SMB%\services' /E /XD __pycache__ /XF '*.pyc' /NFL /NDL /NJH /NJS /nc /ns /np" 2>nul

echo   - Copie packages...
powershell -Command ^
    "robocopy '%APP_DIR%\packages' '%NAS_SMB%\packages' /E /XD __pycache__ /XF '*.pyc' /NFL /NDL /NJH /NJS /nc /ns /np" 2>nul

echo   - Copie infra/supabase...
powershell -Command ^
    "robocopy '%APP_DIR%\infra' '%NAS_SMB%\infra' /E /NFL /NDL /NJH /NJS /nc /ns /np" 2>nul

echo [3/4] Copie OK
echo.

:: ─── ETAPE 4 : DOCKER COMPOSE SUR LE NAS ──────────────────────────────────────
echo [4/4] Deploiement Docker sur le NAS...

ssh %NAS_USER%@%NAS_IP% ^
    "cd %NAS_PATH% && docker compose pull 2>/dev/null; docker compose down --remove-orphans; docker compose up --build -d; docker compose ps"

if %ERRORLEVEL% neq 0 (
    echo [AVERTISSEMENT] Commande Docker retournee avec erreur.
    echo Verifie les logs : ssh %NAS_USER%@%NAS_IP% "cd %NAS_PATH% && docker compose logs --tail=50"
) else (
    echo [4/4] Docker OK
)

echo.
echo ============================================
echo   DEPLOIEMENT TERMINE
echo.
echo   Web  : http://probalyze.picsnature.fr
echo   API  : http://probalyze.picsnature.fr/api
echo   Docs : http://probalyze.picsnature.fr/api/docs
echo.
echo   Logs : ssh %NAS_USER%@%NAS_IP% "cd %NAS_PATH% && docker compose logs -f"
echo ============================================
echo.
pause
