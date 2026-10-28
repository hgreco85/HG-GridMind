# zetaris_on.ps1 - enciende Zetaris bajo demanda (no recrea contenedores, conserva volumenes)
param([int]$TimeoutSec = 420)
$ErrorActionPreference = 'Continue'  # docker escribe progreso en stderr
$proj = 'zetaris'
$cfgDir = if ($env:ZETARIS_DIR) { $env:ZETARIS_DIR } else { "$env:USERPROFILE\hg-sandbox\zetaris\zetaris-platform" }
docker info *> $null
if ($LASTEXITCODE -ne 0) { Write-Error 'Docker Desktop no esta corriendo'; exit 2 }
# 'start' reusa los contenedores existentes (y sus volumenes, incluido el anonimo de gridmind-demo-pg)
Push-Location $cfgDir
try { docker compose -p $proj start 2>&1 | Out-Host } finally { Pop-Location }
$deadline = (Get-Date).AddSeconds($TimeoutSec)
$svc = 'zetaris-driver-1','zetaris-api-1','zetaris-postgres-1','zetaris-ui-1'
do {
  Start-Sleep 5
  $h = $svc | ForEach-Object { docker inspect --format '{{.State.Health.Status}}' $_ 2>$null }
  $allHealthy = -not ($h | Where-Object { $_ -ne 'healthy' })
  $port = (Test-NetConnection 127.0.0.1 -Port 10000 -WarningAction SilentlyContinue).TcpTestSucceeded
} until (($allHealthy -and $port) -or (Get-Date) -gt $deadline)
if ($allHealthy -and $port) {
  Write-Host "ZETARIS ON: healthy ($($svc -join ', ')) + JDBC thrift 127.0.0.1:10000 abierto"
  Write-Host 'Para GridMind: $env:GRIDMIND_ZETARIS_REAL=1'
  exit 0
}
Write-Error "ZETARIS NO SANO tras ${TimeoutSec}s: health=$($h -join ',') port10000=$port"; exit 1

