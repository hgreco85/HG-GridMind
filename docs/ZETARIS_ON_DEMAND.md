# Zetaris bajo demanda (PC Windows de Hernán)

Fecha: 2026-10-27 (ART). Zetaris 2.4.3.1, proyecto compose `zetaris`
(`%USERPROFILE%\hg-sandbox\zetaris\zetaris-platform\docker-compose.yml` + `.override.yml`).

## Uso
```powershell
scripts\zetaris\zetaris_on.ps1    # docker compose start + espera health (driver/api/postgres/ui) + puerto 10000
$env:GRIDMIND_ZETARIS_REAL=1      # GridMind usa el motor real (jdbc:zetaris:lightning@localhost:10000)
scripts\zetaris\zetaris_off.ps1   # docker compose stop + restart=no (no borra nada)
```
Sin Zetaris encendido, GridMind cae al mock y lo etiqueta (comportamiento existente).

## Estado aplicado
- 7 contenedores detenidos (`stop`, no `down`/`rm`/`-v`/`prune`); restart policy `unless-stopped` -> `no`.
- Volúmenes conservados: `zetaris_customer-data`, `zetaris_driver-data`, `zetaris_driver-logs`, `zetaris_pgdata`,
  y el anónimo de `gridmind-demo-pg` (`b6a55c8b…`, reusado porque `start` no recrea contenedores).
- Sin tareas programadas, entradas Startup/Run ni entrada del manifest de HG System Manager que arranquen Zetaris
  (el manifest solo recupera Docker Desktop si está ausente).

## Evidencia (real, host Windows)
- Pre-chequeo: 0 conexiones a :10000, sin OBS/ffmpeg ni procesos GridMind; últimos logs del driver sin consultas por ~10 min.
- Ciclo real: `zetaris_on` -> healthy + :10000 abierto en 23 s (arranque en frío ~2 min); `zetaris_off` -> 7/7 Exited, restart=no.
- RAM libre del host: 0,75 GB antes -> 2,21 GB inmediatamente tras el stop (WSL devuelve más memoria de forma gradual).
- Post-chequeo: HG System Manager `health` overall=healthy, essential_unhealthy=[]; Ollama qwen3.5-4b generó "OK" (think=false).
