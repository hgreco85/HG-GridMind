# zetaris_off.ps1 - apaga Zetaris sin borrar nada (stop: no rm, no down, no -v, no prune)
$ErrorActionPreference = 'Continue'  # docker escribe progreso en stderr
$proj = 'zetaris'
$cfgDir = if ($env:ZETARIS_DIR) { $env:ZETARIS_DIR } else { "$env:USERPROFILE\hg-sandbox\zetaris\zetaris-platform" }
$conn = Get-NetTCPConnection -LocalPort 10000 -State Established -ErrorAction SilentlyContinue
if ($conn -and -not $args.Contains('-Force')) { Write-Error 'Hay conexiones activas al puerto 10000; usa -Force si igual queres apagar'; exit 3 }
Push-Location $cfgDir
try { docker compose -p $proj stop 2>&1 | Out-Host } finally { Pop-Location }
# modo bajo demanda: que no vuelva solo al reiniciar Docker/Windows
$ids = docker ps -a -q --filter "label=com.docker.compose.project=$proj"
if ($ids) { docker update --restart=no $ids | Out-Null }
$running = docker ps -q --filter "label=com.docker.compose.project=$proj"
if ($running) { Write-Error 'Quedaron contenedores corriendo'; exit 1 }
Write-Host 'ZETARIS OFF: contenedores detenidos, restart=no, volumenes intactos'

