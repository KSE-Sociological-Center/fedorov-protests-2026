# -*- coding: utf-8 -*-
"""data/<event>/by_day.csv -> data/<event>/chart_by_day.png

Approximate aggregate turnout by day. Black-and-white, matches map.png. The
per-day per-city figures live in by_day.csv (the single source of truth); they
are approximate midpoints of the reported crowd sizes. Kyiv is drawn as a
separate base band because it dominates every day and is the cleanest day-by-day
signal; the rest is the summed reported figures of the other cities.
"""
import csv, io, os, json, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DS = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "data/2026-07-16-fedorov"
ds = lambda n: os.path.join(HERE, DS, n)
META = json.load(io.open(ds("meta.json"), encoding="utf-8"))
AUTHOR = META["author_en"]
FDIR = r"C:\Windows\Fonts"
S = 3
W, H = 1500, 900

def font(names, size):
    for n in names:
        p = os.path.join(FDIR, n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size * S)
    raise SystemExit("no font: " + repr(names))

F_TITLE = font(["segoeuib.ttf", "seguisb.ttf"], 31)
F_SUB   = font(["segoeui.ttf"], 16)
F_TOT   = font(["segoeuib.ttf", "seguisb.ttf"], 21)
F_DAY   = font(["seguisb.ttf"], 18)
F_SEG   = font(["segoeui.ttf"], 13)
F_AXIS  = font(["segoeui.ttf"], 13)
F_LEG   = font(["segoeui.ttf"], 14)
F_FOOT  = font(["segoeui.ttf"], 13)
F_AUTH  = font(["seguisb.ttf", "segoeui.ttf"], 13)

WHITE = (255, 255, 255); BLACK = (17, 17, 17)
GREY = (105, 105, 105); GREY_L = (150, 150, 150)
KYIV = (72, 72, 72); REST = (204, 204, 204)          # two greys
GRID = (232, 232, 232)

def num(v):
    return format(int(v), ",").replace(",", " ")  # thin-space thousands

# ---- data --------------------------------------------------------------------
DAYS = [("d16", "16 Jul"), ("d17", "17 Jul"), ("d18", "18 Jul"), ("d19", "19 Jul")]
rows = list(csv.DictReader(io.open(ds("by_day.csv"), encoding="utf-8")))
def val(r, k):
    v = (r.get(k) or "").strip()
    return int(v) if v else 0
tot   = {k: sum(val(r, k) for r in rows) for k, _ in DAYS}
kyiv  = {k: next((val(r, k) for r in rows if r["city"] == "Kyiv"), 0) for k, _ in DAYS}
rest  = {k: tot[k] - kyiv[k] for k, _ in DAYS}
ncity = {k: sum(1 for r in rows if val(r, k) > 0) for k, _ in DAYS}

img = Image.new("RGB", (W * S, H * S), WHITE)
d = ImageDraw.Draw(img)
def T(x, y, s, f, fill, anchor="ls"):
    d.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor)

# ---- masthead ----------------------------------------------------------------
T(28, 58, "Approximate turnout by day — protests over Fedorov's departure", F_TITLE, BLACK)
T(28, 86, "%s. Summed reported crowd figures; Kyiv shown separately, as it dominates each day."
          % META["subtitle_en"], F_SUB, GREY)
d.line([28 * S, 102 * S, (W - 28) * S, 102 * S], fill=BLACK, width=max(1, S))

# ---- plot area ---------------------------------------------------------------
PX0, PX1, PY0, PY1 = 132, W - 60, 176, 726
maxY = max(tot.values()) * 1.16
sy = lambda v: PY1 - (PY1 - PY0) * v / maxY

g = 0
while g <= maxY:
    yy = sy(g)
    d.line([PX0 * S, yy * S, PX1 * S, yy * S], fill=GRID, width=max(1, S))
    T(PX0 - 12, yy + 5, num(g), F_AXIS, GREY_L, anchor="rs")
    g += 1000
d.line([PX0 * S, PY1 * S, PX1 * S, PY1 * S], fill=BLACK, width=max(1, S))

# ---- bars --------------------------------------------------------------------
n = len(DAYS); slot = (PX1 - PX0) / n; bw = slot * 0.46
for i, (dk, dlab) in enumerate(DAYS):
    cx = PX0 + slot * (i + 0.5); x0, x1 = cx - bw / 2, cx + bw / 2
    yk, yt = sy(kyiv[dk]), sy(tot[dk])
    if rest[dk] > 0:
        d.rectangle([x0 * S, yt * S, x1 * S, yk * S], fill=REST, outline=BLACK, width=max(1, int(1.2 * S)))
    d.rectangle([x0 * S, yk * S, x1 * S, PY1 * S], fill=KYIV, outline=BLACK, width=max(1, int(1.2 * S)))
    T(cx, yt - 10, "~" + num(tot[dk]), F_TOT, BLACK, anchor="ms")
    # Kyiv label inside its base band
    ky_mid = (PY1 + yk) / 2
    T(cx, ky_mid - 2, "Kyiv", F_SEG, WHITE, anchor="ms")
    T(cx, ky_mid + 16, num(kyiv[dk]), F_SEG, WHITE, anchor="ms")
    # rest label inside its band if tall enough
    if (yk - yt) / S > 34:
        rm = (yt + yk) / 2
        T(cx, rm + 6, num(rest[dk]), F_SEG, BLACK, anchor="ms")
    T(cx, PY1 + 28, dlab, F_DAY, BLACK, anchor="ms")
    T(cx, PY1 + 48, "%d cities counted" % ncity[dk], F_SEG, GREY, anchor="ms")

# ---- legend ------------------------------------------------------------------
lx, ly = PX1 - 250, 150
for j, (fill, lab) in enumerate([(KYIV, "Kyiv"), (REST, "other cities (sum)")]):
    yy = ly + j * 22
    d.rectangle([lx * S, yy * S, (lx + 16) * S, (yy + 12) * S], fill=fill, outline=BLACK, width=max(1, S))
    T(lx + 24, yy + 11, lab, F_LEG, BLACK, anchor="ls")

# ---- footer ------------------------------------------------------------------
d.line([28 * S, (H - 44) * S, (W - 28) * S, (H - 44) * S], fill=(221, 221, 221), width=max(1, S))
CAV = ("Approximate midpoints; days 2–4 undercount non-Kyiv cities (lower bounds). "
       "Unknown-count cities and online-only Kherson excluded.")
T(28, H - 24, CAV, F_FOOT, GREY)
d.text(((W - 28) * S, (H - 24) * S), AUTHOR, font=F_AUTH, fill=BLACK, anchor="rs")

# ---- self-check: totals + text width -----------------------------------------
over = []
auth_w = F_AUTH.getbbox(AUTHOR)[2] / S
if 28 + F_FOOT.getbbox(CAV)[2] / S + 24 > (W - 28) - auth_w:
    over.append("caveat collides with byline")
print("days:", " ".join("%s=%d(Kyiv %d, %d cities)" % (l, tot[k], kyiv[k], ncity[k]) for k, l in DAYS))
print("text overflow:", over or "none")
img.resize((W, H), Image.LANCZOS).save(ds("chart_by_day.png"), "PNG", optimize=True)
print("saved:", ds("chart_by_day.png"), os.path.getsize(ds("chart_by_day.png")) // 1024, "KB")
