#!/usr/bin/env python3
"""Render the Zetaris Demo Challenge video from the authentic evidence already in this repo.

Inputs (committed evidence, nothing is re-recorded):
  docs/evidence/zetaris/zetaris_ui_live_20261028T145726Z.webm    real Zetaris UI, 1920x1080 25 fps, 44.68 s
  docs/evidence/zetaris/gridmind_e2e_transcript_20261028T150347Z.webm  E2E trace, 1920x1080 25 fps, 28.20 s
  integrations/zetaris/evidence/07_e2e_trace_INC8812.json        every fact printed on screen

Output:
  HG-STACK_<DDMMYY>.mp4  H.264 High, yuv420p, 1920x1080, 25 fps, AAC 48 kHz stereo

Timeline (85.68 s = 2142 frames):
  0.00 -  5.00  title card
  5.00 - 17.00  real Zetaris UI: home -> catalog (narration starts exactly at 5.00)
 17.00 - 31.00  federated SQL typed + executed
 31.00 - 45.48  results grid, status bar magnified 2x  (WHY ZETARIS window 5.00-57.48 = 52.48 s)
 45.48 - 57.48  E2E trace: SQL line, 10 rows by row_id
 57.48 - 71.68  E2E trace: falsified hypotheses, citations, root cause, gate, ACK (silent demo)
 71.68 - 78.68  proof card: rows, identifiers, gate, ACK
 78.68 - 85.68  closing card

Usage:
  python render_final_video.py --ffmpeg <ffmpeg.exe> [--date 281026] [--narration narration.mp3]
                               [--crf 22] [--work <dir>] [--cards-only] [--force]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 25

# ----------------------------------------------------------------------------- palette
BG_TOP = (13, 20, 34)
BG_BOT = (7, 11, 20)
INK = (244, 247, 251)
INK_SOFT = (214, 224, 237)
MUTED = (150, 166, 188)
DIM = (110, 126, 148)
ORANGE = (255, 122, 24)
TEAL = (34, 211, 166)
RED = (255, 94, 99)
PANEL = (18, 27, 44)
PANEL_HI = (24, 35, 55)
STROKE = (46, 62, 86)

FONT_DIR = r"C:\Windows\Fonts"


def font(names: list[str], size: int) -> ImageFont.FreeTypeFont:
    for n in names:
        p = os.path.join(FONT_DIR, n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("arial.ttf", size)


def bold(size: int) -> ImageFont.FreeTypeFont:
    return font(["segoeuib.ttf", "arialbd.ttf", "segoeui.ttf", "arial.ttf"], size)


def semi(size: int) -> ImageFont.FreeTypeFont:
    return font(["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "arial.ttf"], size)


def reg(size: int) -> ImageFont.FreeTypeFont:
    return font(["segoeui.ttf", "arial.ttf"], size)


def mono(size: int, heavy: bool = False) -> ImageFont.FreeTypeFont:
    return font(["consolab.ttf", "consola.ttf"] if heavy else ["consola.ttf", "cour.ttf"], size)


def tw(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=f)


def fit(draw: ImageDraw.ImageDraw, text: str, maker, sizes: list[int], max_w: float):
    """Largest font from `sizes` (descending) that keeps `text` inside max_w."""
    for s in sizes:
        f = maker(s)
        if tw(draw, text, f) <= max_w:
            return f
    return maker(sizes[-1])


def tracked(draw: ImageDraw.ImageDraw, xy, text: str, f, fill, spacing: float = 3.0):
    """Draw text with letter-spacing (kerning-lite, for eyebrows)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += tw(draw, ch, f) + spacing
    return x


def tracked_w(draw: ImageDraw.ImageDraw, text: str, f, spacing: float = 3.0) -> float:
    return sum(tw(draw, ch, f) + spacing for ch in text) - spacing


# ----------------------------------------------------------------------------- backgrounds
def backdrop(w: int = W, h: int = H, glow: bool = True) -> Image.Image:
    img = Image.new("RGB", (w, h), BG_BOT)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOT)))
    # faint engineering grid
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, w, 64):
        gd.line([(x, 0), (x, h)], fill=(120, 150, 190, 9))
    for y in range(0, h, 64):
        gd.line([(0, y), (w, y)], fill=(120, 150, 190, 9))
    img = Image.alpha_composite(img.convert("RGBA"), grid)
    if glow:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.ellipse([w - 780, -520, w + 240, 460], fill=ORANGE + (46,))
        gd.ellipse([-420, h - 420, 420, h + 360], fill=TEAL + (22,))
        g = g.filter(ImageFilter.GaussianBlur(190))
        img = Image.alpha_composite(img, g)
    return img


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill=None, outline=None, width: int = 2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


# ----------------------------------------------------------------------------- clip overlays
BAND_TOP = 984


def band(text1: str, text2: str, num: str | None = None, title: str | None = None,
         pill: str | None = "WHY ZETARIS", pos: str = "bottom") -> Image.Image:
    """Caption band (bottom by default, top for the trace clip) + optional pill."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if pos == "top":
        top, bottom = 0, 104
        d.rectangle([0, top, W, bottom], fill=(7, 11, 20, 244))
        d.rectangle([0, bottom - 3, W, bottom], fill=ORANGE + (235,))
        y_num, y_cap = 10, 48
        maxw = 1330
    else:
        top, bottom = BAND_TOP, H
        d.rectangle([0, top, W, bottom], fill=(7, 11, 20, 244))
        d.rectangle([0, top, W, top + 3], fill=ORANGE + (235,))
        y_num, y_cap = top + 12, top + 50
        maxw = 1560

    if num and title:
        d.text((60, y_num), f"{num}  ·  {title}", font=bold(25), fill=ORANGE)

    f_cap = fit(d, text2, reg, [26, 25, 24, 23, 22, 21, 20], maxw)
    d.text((60, y_cap), text2, font=f_cap, fill=INK_SOFT)
    if text1:
        d.text((60, y_cap + 34), text1, font=reg(18), fill=DIM)

    f_wm = reg(17)
    if pos == "top":
        d.text((W - 56 - tw(d, "synthetic data · non-production", f_wm), 72),
               "synthetic data · non-production", font=f_wm, fill=DIM)
    else:
        d.text((W - 60 - tw(d, "synthetic data · non-production", f_wm), top + 20),
               "synthetic data · non-production", font=f_wm, fill=DIM)

    if pill:
        f = semi(21)
        pw = tw(d, pill, f)
        pad_l, pad_r, hgt = 20, 24, 42
        bx1 = W - 56 - (pw + pad_l + pad_r + 26)
        by = 12 if pos == "top" else 16
        box = [bx1, by, bx1 + pw + pad_l + pad_r + 26, by + hgt]
        rounded(d, box, 21, fill=(255, 122, 24, 26), outline=ORANGE + (200,), width=2)
        d.ellipse([bx1 + pad_l - 2, by + hgt // 2 - 5, bx1 + pad_l + 8, by + hgt // 2 + 5], fill=ORANGE)
        d.text((bx1 + pad_l + 18, by + 9), pill, font=f, fill=ORANGE)
    return img


# ----------------------------------------------------------------------------- full cards
def title_card() -> Image.Image:
    img = backdrop()
    d = ImageDraw.Draw(img)
    d.rectangle([140, 246, 208, 252], fill=ORANGE)
    f_eye = semi(28)
    tracked(d, (140, 286), "HG-GRIDMIND  ×  ZETARIS", f_eye, ORANGE, 3.4)

    d.text((136, 348), "A real Zetaris engine,", font=bold(88), fill=INK)
    d.text((136, 452), "federating grid evidence.", font=bold(88), fill=INK)

    d.rectangle([140, 590, 460, 593], fill=ORANGE + (200,))
    f_sub = reg(31)
    d.text((140, 620), "Zetaris 2.4.3.1 on local Docker · one federated SQL query across 3 sources",
           font=f_sub, fill=MUTED)
    d.text((140, 664), "10 real engine rows · cited evidence · a human on the approval gate",
           font=f_sub, fill=MUTED)

    # stat strip
    stats = [("3", "SOURCES"), ("10", "ENGINE ROWS"), ("1.456 s", "QUERY TIME"), ("USD 0", "COST")]
    x = 140
    for i, (big, lab) in enumerate(stats):
        d.text((x, 790), big, font=bold(58), fill=INK)
        d.text((x + 2, 866), lab, font=semi(19), fill=ORANGE)
        x += 350
        if i < len(stats) - 1:
            d.rectangle([x - 128, 792, x - 127, 878], fill=STROKE)

    d.rectangle([140, 952, W - 140, 953], fill=STROKE)
    d.text((140, 980), "Zetaris Demo Challenge · 28 October 2026", font=reg(23), fill=MUTED)
    f_w = reg(21)
    d.text((W - 140 - tw(d, "synthetic data · non-production", f_w), 982),
           "synthetic data · non-production", font=f_w, fill=DIM)
    return img.convert("RGB")


def proof_card() -> Image.Image:
    img = backdrop()
    d = ImageDraw.Draw(img)
    d.rectangle([140, 96, 208, 102], fill=ORANGE)
    tracked(d, (140, 126), "VERIFIABLE OUTPUT", semi(24), ORANGE, 3.2)
    d.text((136, 172), "What the engine actually returned", font=bold(66), fill=INK)
    d.text((140, 264), "07_e2e_trace_INC8812.json  →  real_engine_detail   ·   captured 2026-10-28 14:56 UTC",
           font=mono(23), fill=MUTED)

    stats = [("3", "FEDERATED SOURCES"), ("10", "ROWS RETURNED"), ("1.456 s", "UI QUERY TIME"), ("711 ms", "ADAPTER ELAPSED")]
    x = 140
    for i, (big, lab) in enumerate(stats):
        d.text((x, 322), big, font=bold(54), fill=TEAL)
        d.text((x + 2, 390), lab, font=semi(18), fill=MUTED)
        x += 415
        if i < len(stats) - 1:
            d.rectangle([x - 150, 322, x - 149, 404], fill=STROKE)

    # left panel: rows
    box = [140, 456, 1180, 872]
    rounded(d, box, 18, fill=PANEL + (255,), outline=STROKE, width=2)
    d.rectangle([140, 456, 148, 872], fill=TEAL)
    d.text((186, 484), "REAL ENGINE ROWS  (row_id, as returned)", font=semi(22), fill=TEAL)
    lines = [
        ("SCADA-ROW-44008…44012", "5 timestamps, 01:10 → 01:50"),
        ("MNT-7002", "dga_verdict WATCH_HOT_SPOT · C2H2 4.8 ppm"),
        ("TKT-9001", "RESIDUAL_CURRENT_TRIP · reported 01:45"),
        ("TKT-9002", "NEUTRAL_OVERLOAD_CALL · reported 01:58"),
        ("neutral_current_amps", "25.1 → 37.5 A  (5 steps of the same event)"),
    ]
    y = 536
    for k, v in lines:
        d.text((186, y), k, font=mono(24, heavy=True), fill=INK)
        d.text((186 + 350, y), v, font=mono(22), fill=INK_SOFT)
        y += 62

    d.text((186, 820), "5 timestamps × 2 tickets = 10 joined rows (not 10 distinct facts)",
           font=reg(20), fill=DIM)

    # right panel: human control
    box = [1220, 456, 1780, 872]
    rounded(d, box, 18, fill=PANEL + (255,), outline=STROKE, width=2)
    d.rectangle([1220, 456, 1228, 872], fill=ORANGE)
    d.text((1266, 484), "HUMAN CONTROL", font=semi(22), fill=ORANGE)
    lines = [
        ("gate.approval_required", "true"),
        ("gate.authorized", "true"),
        ("audit_ack", "HG-GRIDMIND-ACK-73DEBE338B326F29"),
        ("traceability", "integrations/zetaris/evidence/*.json"),
    ]
    y = 532
    for k, v in lines:
        d.text((1266, y), k, font=mono(21), fill=MUTED)
        vf = fit(d, v, mono, [21, 19, 18, 17, 16], 1780 - 1266 - 40)
        d.text((1266, y + 26), v, font=vf, fill=INK)
        y += 74
    d.text((1266, 838), "No action executed without the gate.", font=reg(20), fill=DIM)

    d.rectangle([140, 908, W - 140, 909], fill=STROKE)
    d.text((140, 934), "Synthetic fixture data — not production.  Engine rows are real (is_simulation_fallback = false);",
           font=reg(22), fill=MUTED)
    d.text((140, 966), "hypotheses and citations come from the fixture reasoning layer, not from the 10 engine rows.",
           font=reg(22), fill=MUTED)
    return img.convert("RGB")


def closing_card() -> Image.Image:
    img = backdrop()
    d = ImageDraw.Draw(img)
    d.rectangle([140, 120, 208, 126], fill=ORANGE)
    d.text((136, 156), "HG-GridMind × Zetaris", font=bold(78), fill=INK)
    d.text((140, 266), "A real engine, real evidence, and a human on the gate.", font=reg(34), fill=MUTED)

    rows = [
        ("ENGINE", "Zetaris 2.4.3.1 build cb88df0b · local Docker (7 containers) · real JDBC path"),
        ("EVIDENCE", "docs/evidence/zetaris/ — JSON traces, keyframes, 2 screen recordings"),
        ("PROVENANCE", "engine rows: real · reasoning rows: synthetic fixture (labelled)"),
        ("HUMAN GATE", "approval_required=True → authorized=True · ACK HG-GRIDMIND-ACK-73DEBE338B326F29"),
        ("COST", "USD 0 · local only · no public ports · no merge"),
    ]
    y = 372
    for k, v in rows:
        d.text((140, y + 4), k, font=semi(20), fill=ORANGE)
        vf = fit(d, v, reg, [27, 26, 25, 24, 23, 22, 21], 1780 - 400)
        d.text((400, y), v, font=vf, fill=INK_SOFT)
        d.rectangle([140, y + 52, 1780, y + 53], fill=(30, 42, 62))
        y += 88

    d.text((140, 900), "github.com/hgreco85/HG-GridMind · PR #10 (draft, not merged)",
           font=mono(25), fill=INK)
    d.text((140, 946), "Synthetic data — not production.", font=reg(22), fill=DIM)
    f_w = semi(22)
    d.text((W - 140 - tw(d, "Zetaris Demo Challenge", f_w), 946), "Zetaris Demo Challenge",
           font=f_w, fill=ORANGE)
    return img.convert("RGB")


# ----------------------------------------------------------------------------- helpers
def run(cmd: list[str], label: str) -> None:
    print(f"  · {label}", flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout[-3000:])
        print(p.stderr[-6000:])
        raise SystemExit(f"ffmpeg failed: {label}")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(ffprobe: str, path: str) -> dict:
    p = subprocess.run([ffprobe, "-v", "error", "-print_format", "json",
                        "-show_format", "-show_streams", path],
                       capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def normalize_audio(ffmpeg: str, src: str, dst: str, i_lufs: float, tp: float) -> dict:
    """Two-pass EBU R128 normalisation (linear gain + true-peak limit)."""
    filt = f"loudnorm=I={i_lufs}:TP={tp}:LRA=11:print_format=json"
    p = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", src, "-af", filt, "-f", "null", "NUL"],
                       capture_output=True, text=True)
    blob = p.stderr[p.stderr.rfind("{"):p.stderr.rfind("}") + 1]
    m = json.loads(blob)
    filt2 = (f"loudnorm=I={i_lufs}:TP={tp}:LRA=11:linear=true"
             f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
             f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
             f":offset={m['target_offset']},aresample=48000")
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-i", src, "-af", filt2,
         "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", "-y", dst], "normalise narration")
    return m


# ----------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffmpeg", required=True)
    ap.add_argument("--date", default="281026", help="upload date DDMMYY for the filename")
    ap.add_argument("--narration", default=None, help="52.5 s narration mp3 (optional)")
    ap.add_argument("--narration-offset", type=float, default=5.0)
    ap.add_argument("--no-normalize", action="store_true", help="skip EBU R128 normalisation")
    ap.add_argument("--loudness", type=float, default=-16.0, help="target integrated LUFS")
    ap.add_argument("--true-peak", type=float, default=-1.5, help="target true peak dBTP")
    ap.add_argument("--crf", type=int, default=22)
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--work", default=None)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--cards-only", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    ev = os.path.join(root, "docs", "evidence", "zetaris")
    clip_a = os.path.join(ev, "zetaris_ui_live_20261028T145726Z.webm")
    clip_b = os.path.join(ev, "gridmind_e2e_transcript_20261028T150347Z.webm")
    for p in (clip_a, clip_b):
        if not os.path.exists(p):
            raise SystemExit(f"missing input clip: {p}")

    ffmpeg = args.ffmpeg
    ffprobe = os.path.join(os.path.dirname(ffmpeg), "ffprobe.exe")
    work = args.work or os.path.join(os.environ.get("TEMP", "."), "opencode", "render")
    cards_dir = os.path.join(work, "cards")
    seg_dir = os.path.join(work, "seg")
    os.makedirs(cards_dir, exist_ok=True)
    os.makedirs(seg_dir, exist_ok=True)
    outdir = args.outdir or root

    # ---- 1. cards
    print("cards:", flush=True)
    cards = {"title": title_card(), "proof": proof_card(), "closing": closing_card()}
    paths = {}
    for name, im in cards.items():
        p = os.path.join(cards_dir, f"{name}.png")
        im.save(p)
        paths[name] = p
        print(f"  · {name}.png {im.size}", flush=True)

    overlays = {
        "band_s2": band("", "Authentic Zetaris 2.4.3.1 Data Gateway on Docker — 7 containers, real JDBC path to the engine",
                        "01", "REAL ENGINE"),
        "band_s3": band("", "One SQL statement joins gridmind_scada_pg with two CSV filestore tables — no data movement",
                        "02", "FEDERATED QUERY"),
        "band_s4": band("", "Success · Total Count: 10 — rows SCADA-ROW-44008…44012 + MNT-7002 + TKT-9001/9002",
                        "03", "10 ROWS IN 1.456 s"),
        "band_s5": band("", "engine=Zetaris Lightning (real, docker compose) · rows=10 · 711 ms — 5 timestamps × 2 tickets",
                        "04", "SAME ROWS, TRACEABLE", pos="top"),
        "band_s6a": band("", "MAINT-ROW-99182: DGA normal (C2H2 0.1 ppm) · SCADA-ROW-55102: phases A/C still at normal load",
                         "05", "FALSIFICATION", pos="top"),
        "band_s6b": band("", "approval_required=True · authorized=True · ACK HG-GRIDMIND-ACK-73DEBE338B326F29",
                         "06", "HUMAN GATE", pos="top"),
    }
    for name, im in overlays.items():
        p = os.path.join(cards_dir, f"{name}.png")
        im.save(p)
        paths[name] = p
        print(f"  · {name}.png", flush=True)

    if args.cards_only:
        print("cards only - done")
        return

    # ---- 2. segments
    print("segments:", flush=True)
    enc = ["-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
           "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "50", "-an", "-movflags", "+faststart"]

    # (name, frames, source, ss, filter, overlay list)
    timeline = [
        ("s1_title", 125, None, 0.0, None, None),
        ("s2_engine", 300, clip_a, 4.0, None, "band_s2"),
        ("s3_query", 350, clip_a, 16.0, None, "band_s3"),
        ("s4_rows", 362, clip_a, 30.0, "inset", "band_s4"),
        ("s5_trace", 300, clip_b, 2.0, None, "band_s5"),
        ("s6_gate", 355, clip_b, 14.0, "twoband", None),
        ("s7_proof", 175, None, 0.0, None, None),
        ("s8_closing", 175, None, 0.0, None, None),
    ]
    total_frames = 0
    for name, frames, src, ss, special, ov in timeline:
        dur = frames / FPS
        outp = os.path.join(seg_dir, f"{name}.mp4")
        total_frames += frames
        if os.path.exists(outp) and not args.force:
            print(f"  · {name} (cached)", flush=True)
            continue
        if src is None:
            # designed card, slow push-in
            card = paths["title"] if name == "s1_title" else paths["proof"] if name == "s7_proof" else paths["closing"]
            vf = (f"scale=2016:1134:flags=lanczos,"
                  f"zoompan=z='1+0.045*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                  f"d=1:s={W}x{H}:fps={FPS},setsar=1")
            if name == "s1_title":
                vf += ",fade=t=in:st=0:d=0.7"
            if name == "s8_closing":
                vf += f",fade=t=out:st={dur-0.8:.3f}:d=0.8"
            cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS),
                   "-t", f"{dur:.3f}", "-i", card, "-vf", vf, *enc, "-t", f"{dur:.3f}", "-y", outp]
        else:
            inputs = ["-ss", f"{ss:.3f}", "-t", f"{dur:.3f}", "-i", src]
            fc = []
            if special == "inset":
                for nm in ("band_s4",):
                    inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", paths[nm]]
                fc.append(f"[0:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,split=2[b1][b2]")
                fc.append("[b2]crop=700:40:548:1040,scale=1400:80:flags=neighbor,"
                          "drawbox=x=0:y=0:w=iw:h=ih:color=0xFF7A18@1:t=3[cr]")
                fc.append("[b1][cr]overlay=260:887:enable='gte(t,1.2)'[wi]")
                fc.append(f"[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1[ov1]")
                fc.append("[wi][ov1]overlay=0:0:enable='gte(t,2.0)',format=yuv420p[v]")
            elif special == "twoband":
                for nm in ("band_s6a", "band_s6b"):
                    inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", paths[nm]]
                fc.append(f"[0:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1[base]")
                fc.append("[1:v]format=rgba,fade=t=in:st=0:d=0.35:alpha=1[ov1]")
                fc.append("[2:v]format=rgba[ov2]")
                fc.append("[base][ov1]overlay=0:0:enable='lt(t,7.0)'[o1]")
                fc.append("[o1][ov2]overlay=0:0:enable='gte(t,7.0)',format=yuv420p[v]")
            else:
                inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", paths[ov]]
                fc.append(f"[0:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1[base]")
                fc.append("[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1[ov]")
                fc.append("[base][ov]overlay=0:0,format=yuv420p[v]")
            cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", *inputs,
                   "-filter_complex", ";".join(fc), "-map", "[v]", *enc,
                   "-t", f"{dur:.3f}", "-y", outp]
        run(cmd, name)

    # ---- 3. concat
    print("concat:", flush=True)
    listp = os.path.join(seg_dir, "list.txt")
    with open(listp, "w", encoding="utf-8") as fh:
        for name, *_ in timeline:
            fh.write(f"file '{os.path.join(seg_dir, name + '.mp4').replace(os.sep, '/')}'\n")
    silent = os.path.join(work, "master_silent.mp4")
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", listp,
         "-c", "copy", "-movflags", "+faststart", "-y", silent], "master_silent.mp4")

    duration = total_frames / FPS
    final = os.path.join(outdir, f"HG-STACK_{args.date}.mp4")
    norm_info = None
    if args.narration:
        if not os.path.exists(args.narration):
            raise SystemExit(f"narration not found: {args.narration}")
        delay = int(round(args.narration_offset * 1000))
        src_audio = args.narration
        norm_info = None
        if not args.no_normalize:
            src_audio = os.path.join(work, "narration_normalised.wav")
            norm_info = normalize_audio(ffmpeg, args.narration, src_audio, args.loudness, args.true_peak)
        print("mux narration:", flush=True)
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-i", silent, "-i", src_audio,
             "-filter_complex", f"[1:a]adelay={delay}:all=1,aresample=48000[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-y", final], "final with narration")
        audio_note = os.path.basename(args.narration)
    else:
        print("mux silence (picture-locked master):", flush=True)
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-i", silent,
             "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
             "-shortest", "-t", f"{duration:.3f}", "-movflags", "+faststart", "-y", final],
            "final (silent)")
        audio_note = "SILENT (narration pending)"

    # ---- 4. manifest
    info = probe(ffprobe, final) if os.path.exists(ffprobe) else {}
    streams = info.get("streams", [])
    fmt = info.get("format", {})
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), {})
    ver = subprocess.run([ffmpeg, "-hide_banner", "-version"], capture_output=True, text=True).stdout.splitlines()[0]
    tl, start = [], 0.0
    for nm, fr, src, _ss, _sp, _ov in timeline:
        tl.append({
            "segment": nm,
            "start_s": round(start, 3),
            "end_s": round(start + fr / FPS, 3),
            "frames": fr,
            "source": os.path.basename(src) if src else "designed card",
        })
        start += fr / FPS
    manifest = {
        "video": os.path.basename(final),
        "sha256": sha256(final),
        "bytes": os.path.getsize(final),
        "duration_s": round(float(fmt.get("duration", duration)), 3),
        "video_stream": {k: v.get(k) for k in ("codec_name", "profile", "width", "height", "pix_fmt",
                                               "r_frame_rate", "avg_frame_rate", "bit_rate")},
        "audio_stream": {k: a.get(k) for k in ("codec_name", "sample_rate", "channels", "bit_rate")},
        "audio_source": audio_note,
        "audio_normalisation": None if not norm_info else {
            "target_I": args.loudness,
            "target_TP": args.true_peak,
            "measured_I": float(norm_info["input_i"]),
            "measured_TP": float(norm_info["input_tp"]),
            "measured_LRA": float(norm_info["input_lra"]),
        },
        "narration_offset_s": args.narration_offset if args.narration else None,
        "narration_window_s": [5.0, 57.5],
        "why_zetaris_window_s": [5.0, 57.48],
        "timeline": tl,
        "encoder": ver,
        "crf": args.crf,
        "preset": args.preset,
        "sources": {
            "ui_clip": os.path.basename(clip_a),
            "trace_clip": os.path.basename(clip_b),
            "facts": "integrations/zetaris/evidence/07_e2e_trace_INC8812.json",
        },
        "render_script": "docs/evidence/zetaris/render/render_final_video.py",
    }
    mp = os.path.join(os.path.dirname(final), f"HG-STACK_{args.date}.render.json")
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(json.dumps({k: manifest[k] for k in ("video", "sha256", "bytes", "duration_s",
                                              "video_stream", "audio_stream", "audio_source")},
                     indent=2, ensure_ascii=False))
    print(f"manifest: {mp}")


if __name__ == "__main__":
    main()
