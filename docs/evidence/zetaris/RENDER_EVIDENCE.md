# Final video — render evidence (Zetaris Demo Challenge)

Deliverable: **`HG-STACK_281026.mp4`** (repository root), rendered on 2026-10-28 from evidence that was
already committed on this branch. Nothing was re-recorded, re-installed or re-run for the video.

| Property | Value |
|---|---|
| File | `HG-STACK_281026.mp4` (16.9 MB) |
| SHA-256 | `5c933a5305d3e7b18c2d7d7fcb1cc17b70df82464e1a4c01d4b250d9dbd85cca` |
| Duration | 85.680 s (2142 frames @ 25 fps) |
| Video | H.264 High, `yuv420p`, 1920×1080, 25 fps, ~1.45 Mb/s |
| Audio | AAC-LC, 48 kHz, stereo, ~175 kb/s; narration starts at 5.000 s; integrated loudness −16.4 LUFS, true peak −4.4 dBFS |
| Container | MP4 with `+faststart` (plays in a browser tab) |
| Cost | USD 0, local only |

Machine-readable twin: `HG-STACK_281026.render.json` (same folder as the video).

## Inputs (all pre-existing on `feat/zetaris-real-engine`)

| Input | Role |
|---|---|
| `docs/evidence/zetaris/zetaris_ui_live_20261028T145726Z.webm` (44.68 s, 1080p25) | real Zetaris UI: login → Data Explorer → SQL Workspace → execute → results grid |
| `docs/evidence/zetaris/gridmind_e2e_transcript_20261028T150347Z.webm` (28.20 s, 1080p25) | E2E trace: sources, SQL, 10 rows, falsified hypotheses, citations, root cause, gate, ACK |
| `integrations/zetaris/evidence/07_e2e_trace_INC8812.json` | every number and identifier printed on the three designed cards |

## Timeline

| # | In → out | Frames | Content |
|---|---|---|---|
| 1 | 0.00 → 5.00 | 125 | Title card: *A real Zetaris engine, federating grid evidence* (3 sources · 10 rows · 1.456 s · USD 0) |
| 2 | 5.00 → 17.00 | 300 | `01 · REAL ENGINE` — authentic Data Gateway UI on Docker, 7 containers |
| 3 | 17.00 → 31.00 | 350 | `02 · FEDERATED QUERY` — the three-way SQL, executed |
| 4 | 31.00 → 45.48 | 362 | `03 · 10 ROWS IN 1.456 s` — results grid + status bar magnified 2× |
| 5 | 45.48 → 57.48 | 300 | `04 · SAME ROWS, TRACEABLE` — `engine=Zetaris Lightning (real, docker compose) · rows=10 · 711 ms` |
| 6 | 57.48 → 71.68 | 355 | `05 · FALSIFICATION` → `06 · HUMAN GATE` — hypotheses, citations, root cause, `approval_required=True authorized=True`, ACK |
| 7 | 71.68 → 78.68 | 175 | Proof card: row identifiers, gate, ACK, provenance disclosure |
| 8 | 78.68 → 85.68 | 175 | Closing card: engine, evidence paths, provenance, cost, repo/PR |

- **Narration window:** 5.000 → 57.500 s (52.50 s), reserved and currently empty.
- **“Why Zetaris” segment:** 5.00 → 57.48 s (52.48 s) — inside the organizer's 40–60 s band and marked
  on screen by a persistent `WHY ZETARIS` pill for the whole window.
- Silent demo + closing: 57.48 → 85.68 s.

## QC performed

- `ffprobe -count_frames` → 2142 decoded frames, `duration=85.680000`, no truncated segment.
- Frame grabs at t = 2, 9, 20, 24, 29, 36, 50, 57, 62, 74, 82 s inspected for legibility, caption
  overflow and overlay collisions. The caption band sits at the **top** for the terminal clip so the
  `approval_required / audit ACK / Trazabilidad` lines stay uncovered (they sit ~70–150 px from the
  bottom of that clip).
- Readability: the Zetaris status bar is re-cropped from the clip itself and shown at 2× (1400×80)
  rather than described in text, so `Success · Total Count: 10 · Query Time: 1.456 s` is legible at
  1080p and in the mobile player.

## Honesty constraints baked into the picture

- The engine rows (10) are real; the hypotheses, citations and root cause come from the deterministic
  **fixture** reasoning layer. Stated on the proof card in two lines and on the closing card as
  `engine rows: real · reasoning rows: synthetic fixture (labelled)`.
- `5 timestamps × 2 tickets = 10 joined rows (not 10 distinct facts)` is printed on the proof card.
- Every segment over a clip carries `synthetic data · non-production`; nothing claims production data.
- No claim that the hypotheses were computed on the engine's 10 rows.

## Reproduce

```powershell
# Pillow required (free): pip install pillow
python docs/evidence/zetaris/render/render_final_video.py `
  --ffmpeg <path-to>\ffmpeg.exe --date 281026 --crf 19 --preset slow --force
```

The script needs any FFmpeg build with `libx264`, `aac`, `overlay`, `drawbox` and `fade`. The
Playwright-cached binary is **not** usable (built `--disable-everything`, VP9/PNG only); a portable
GPL build was used instead (`N-128121`), no install and no admin rights.

## Narration

Source: `HG GridMind - Zetaris.mp3` (ElevenLabs, 52.51 s, 44.1 kHz mono, 128 kb/s), found inside
`HG_GridMind_Zetaris_RENDER_KIT.zip` in the user's Downloads. The MP3 itself is **not committed**
(audio is never versioned or published); keep it outside the repo and pass its path to the script.

- Measured source loudness: −24.3 LUFS, true peak −3.6 dBFS. Normalised with two-pass EBU R128
  (linear gain, target −16 LUFS, true peak −1.5 dBTP) → final −16.4 LUFS, peak −4.4 dBFS.
- Placed at `adelay=5000` → speech starts at 5.000 s and ends at ~57.5 s, where the silent demo begins.
- Verified on the final file: silence before 5.0 s (max −91 dB), speech level right after 5.0 s, audio
  stream ends at the end of the narration, video runs to 85.68 s.

Full command used:

```powershell
python docs/evidence/zetaris/render/render_final_video.py `
  --ffmpeg <ffmpeg.exe> --date 281026 --crf 19 --preset slow `
  --narration "<path>\HG GridMind - Zetaris.mp3"
```

Do **not** add `-shortest` to any manual mux: it would cut the film at 57.5 s.

## Open checks for the user (by ear, not verifiable here)

- The kit's own README flags that the supplied transcript spelled the product as "Zatarus"; confirm the
  narration says "Zetaris".
- The contest email asks for a 40–60 s explanation of *why Zetaris is amazing*. The narration is 52.5 s
  and includes non-Zetaris framing at the start. The on-screen `WHY ZETARIS` window covers the whole
  narration (5.00–57.48 s); if you need a strictly Zetaris-only cut, the narration's Zetaris lines must
  be identified by ear and the window retimed in the script.
- The kit README gives a different deadline and filename date (Tue 3 Nov 2026, `HG-STACK_031126.mp4`)
  than issue #8 (Thu 29 Oct). Confirm the official date before naming or uploading.

## Organizer-facing notes

- File name convention `HG-STACK_DDMMYY` (date of the actual upload): today → `HG-STACK_281026.mp4`;
  if uploaded on 29 Oct 2026, rename to `HG-STACK_291026.mp4` (no re-encode needed).
- One-line submission text (EN):

  > HG-GridMind turns a real Zetaris 2.4.3.1 engine into grid incident evidence: one federated SQL
  > query across PostgreSQL SCADA and two filestores returns 10 real rows, two hypotheses are
  > falsified with row-level citations, and the remediation plan stops at a human approval gate —
  > local, USD 0, synthetic data.

- Draft PR #10 only. No merge, no submission, no spend.
