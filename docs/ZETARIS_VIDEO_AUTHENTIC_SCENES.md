# Reemplazo de escenas conceptuales por ejecución auténtica (video 3:50)

Objetivo: que ninguna escena del video afirme algo que no se pueda señalar en un archivo de evidencia.
Cada bloque del storyboard (`docs/VIDEO_STORYBOARD_4_MINUTES.md`) se mapea a un clip o still **real**
grabado el **2026-10-28** con el motor Zetaris 2.4.3.1 corriendo en Docker local (costo USD 0).

## Insumos auténticos disponibles

| ID | Archivo | Tipo | Duración | Contenido verificable |
|---|---|---|---|---|
| A | `docs/evidence/zetaris/zetaris_ui_live_20261028T145726Z.webm` | video 1920×1080 | 44.7 s | UI real de Zetaris: login (password enmascarado) → Data Explorer → SQL Workspace → se tipea la consulta federada → `Execute` → grilla con `Success · Total Count: 10 · Query Time: 1.456 s` |
| B | `docs/evidence/zetaris/gridmind_e2e_transcript_20261028T150347Z.webm` | video 1920×1080 | 30.6 s | Traza E2E de GridMind (desde `07_e2e_trace_INC8812.json`): fuentes, SQL, filas citables, hipótesis falsadas, causa raíz, gate, ACK |
| C | `docs/evidence/zetaris/ui_live_20261028T145726Z_05_results.png` | still | — | Grilla de resultados con `SCADA-ROW-44012`, `MNT-7002 (WATCH_HOT_SPOT)`, `TKT-9001/9002` |
| D | `integrations/zetaris/evidence/05_live_verified.json` | JSON | — | Versión/build del motor, contenedores, SQL, filas, latencias, timestamps |
| E | `docs/evidence/zetaris/ui_live_20261028T145726Z_03_catalog_tree.png` | still | — | Catálogo real: `gridmind_scada_pg` (PostgreSQL) + `gridmind_files` (CSV) |

Regla de honestidad aplicada en pantalla: el material del motor se rotula **REAL ZETARIS ENGINE / LOCAL
DOCKER**, y el clip B dice explícitamente que es la transcripción de una ejecución registrada (no un
diagrama). Cuando GridMind cae al camino offline, la evidencia lo dice: `is_simulation: true` y
`simulation_disclosure`.

## Mapa escena por escena

| Storyboard | Qué había (conceptual) | Reemplazo auténtico | In/Out sugerido |
|---|---|---|---|
| **Bloque 1** `00:00–00:25` El problema | "Tablero SCADA ficticio" | Still C (grilla real con el neutro a 37.5 A) con zoom lento al par `SCADA-ROW-44012` + `TKT-9002` | C, 0–5 s de paneo |
| **Bloque 2** `00:25–01:00` Integración Zetaris | "Diagrama de silos conectándose" + `execute_federated_query` | **Clip A completo** (44.7 s → recortar a 35 s): 0–8 s login/home, 8–18 s árbol de catálogo (E), 18–28 s SQL tipeado, 28–35 s resultado con `Total Count: 10` | A `00:02 → 00:37` |
| **Bloque 3** `01:00–02:05` Razonamiento causal | "Ejecución en vivo de investigate_incident()" (texto) | **Clip B** desde `[2] SQL EJECUTADO` hasta `[5] EVIDENCIA`: muestra filas reales y después las hipótesis falsadas | B `00:06 → 00:24`, luego congelar en C |
| **Bloque 4** `02:05–02:50` El "por qué" + gate | Texto de `IncidentDiagnosis` | **Clip B** tramo `[6] CAUSA RAIZ` → `[7] GATE + ACK` (causa, acción, `approval_required=True`, ACK `HG-GRIDMIND-ACK-73DEBE338B326F29`) | B `00:22 → 00:30` |
| **Bloque 5** `03:00–03:30` Datos faltantes | Caso sintético sin datos | Ejecutar `run_e2e_demo.py --fixture fixtures/incident_INC_2026_UTIL_5501.json` (traza `06_e2e_trace_TR102.json`, ya generada): abstención explícita + 10 filas reales que el fixture no tenía | still de `06_e2e_trace_TR102.json` (sección `root_cause`) |
| **Bloque 6** `03:30–03:50` Sponsors y cierre | Logos | Still C + E y una tarjeta con: motor `Zetaris 2.4.3.1 build cb88df0b`, costo `USD 0`, licencia MIT | C/E, 3 s |

## Ajustes de narración (para no sobreafirmar)

- Bloque 2: decir **"consulta ejecutada en el motor Zetaris local; 10 filas federadas en 1.46 s (UI) / ~4.1 s
  por JDBC"**. No decir "en vivo contra la nube" (es local, y así está documentado).
- Bloque 3: aclarar que **las filas que alimentan el razonamiento son el fixture sintético** y que la
  evidencia del motor es **adicional y trazable** por `row_id`. Esto ya está en `docs/ZETARIS_REAL_VS_MOCK.md`.
- Bloque 5: la abstención es del caso `INC-5501` (fixture con telemetría incompleta) — **no** del motor.

## Pendiente (requiere decisión humana, sin costo)

1. Montar el corte final de 3:50 (no hay editor instalado: se compuso el material, no el master).
2. Si se quiere capturar también la terminal (no solo el navegador), instalar OBS Studio o autorizar
   `winget install OBSProject.OBSStudio`; hoy no está en la máquina y **no se instaló**.
