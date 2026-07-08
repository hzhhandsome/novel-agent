$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"
$LogDir = Join-Path $RepoRoot "runtime-logs"
$DatabaseUrl = "postgresql+psycopg://novel:novel@localhost:55432/novel_agent"

New-Item -ItemType Directory -Force $LogDir | Out-Null

Write-Host "Starting PostgreSQL middleware..."
Push-Location $RepoRoot
docker compose up -d postgres
Pop-Location

Write-Host "Applying database migrations..."
$env:NOVEL_AGENT_DATABASE_URL = $DatabaseUrl
$env:PYTHONPATH = "$BackendDir"
python -c "from alembic.config import Config; from alembic import command; cfg=Config(r'$BackendDir\alembic.ini'); cfg.set_main_option('script_location', r'$BackendDir\alembic'); command.upgrade(cfg, 'head')"

Write-Host "Starting backend on http://127.0.0.1:8000 ..."
$BackendCommand = "& { `$env:NOVEL_AGENT_DATABASE_URL = '$DatabaseUrl'; Set-Location '$BackendDir'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 }"
Start-Process -WindowStyle Hidden -FilePath powershell -ArgumentList @("-NoProfile", "-Command", $BackendCommand) -RedirectStandardOutput "$LogDir\backend.log" -RedirectStandardError "$LogDir\backend.err"

Write-Host "Starting frontend on http://127.0.0.1:5173 ..."
$FrontendCommand = "& { `$env:VITE_API_PROXY_TARGET = 'http://127.0.0.1:8000'; Set-Location '$FrontendDir'; npm run dev -- --host 127.0.0.1 }"
Start-Process -WindowStyle Hidden -FilePath powershell -ArgumentList @("-NoProfile", "-Command", $FrontendCommand) -RedirectStandardOutput "$LogDir\frontend.log" -RedirectStandardError "$LogDir\frontend.err"

Write-Host ""
Write-Host "Novel Agent is starting."
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend:  http://127.0.0.1:8000/health"
Write-Host "Logs:     $LogDir"
