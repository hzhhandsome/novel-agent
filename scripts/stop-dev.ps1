$ErrorActionPreference = "SilentlyContinue"

foreach ($port in 5173, 8000) {
  Get-NetTCPConnection -LocalPort $port | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
    Stop-Process -Id $_ -Force
  }
}

Write-Host "Stopped local frontend/backend dev servers on ports 5173 and 8000."
