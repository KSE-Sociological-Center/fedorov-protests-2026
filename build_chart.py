# -*- coding: utf-8 -*-
"""data/<event>/by_day.csv -> data/<event>/chart_by_day.png

Approximate aggregate turnout over the wave. Black-and-white, matches map.png. The per-day
per-city figures live in by_day.csv (the single source of truth); they are approximate
midpoints of the reported crowd sizes. Kyiv is drawn as a separate base band because it
dominates every day and is the cleanest day-by-day signal; the rest is the summed reported
figures of the other cities.

The days come from the CSV header (columns named MM-DD), not from a list in this file.
Days where no city published a figure are gaps, not zeroes, and are drawn as such — the
wave did not necessarily stop on those days; the counting did.
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
W, H = 1500, 910

def font(names, size):
    for n in names:
        p = os.path.join(FDIR, n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size * S)
    raise SystemExit("no font: " + repr(names))

F_TITLE = font(["segoeuib.ttf", "seguisb.ttf"], 31)
F_SUB   = font(["segoeui.ttf"], 16)
F_PEAK  = font(["segoeuib.ttf", "seguisb.ttf"], 19)
F_DAY   = font(["seguisb.ttf"], 13)
F_MON   = font(["seguisb.ttf"], 14)
F_SEG   = font(["segoeui.ttf"], 12)
F_AXIS  = font(["segoeui.ttf"], 13)
F_LEG   = font(["segoeui.ttf"], 14)
F_NOTE  = font(["segoeui.ttf"], 13)
F_FOOT  = font(["segoeui.ttf"], 13)
F_AUTH  = font(["seguisb.ttf", "segoeui.ttf"], 13)

WHITE = (255, 255, 255); BLACK = (17, 17, 17)
GREY = (105, 105, 105); GREY_L = (150, 150, 150)
KYIV = (72, 72, 72); REST = (204, 204, 204)          # two greys
GRID = (232, 232, 232)
EVENT = (126, 126, 126)
MON_UK = {"07": "July", "08": "August", "09": "September"}

def num(v):
    return format(int(v), ",").replace(",", " ")      # thin-space thousands

# ---- data --------------------------------------------------------------------
with io.open(ds("by_day.csv"), encoding="utf-8") as f:
    rdr = csv.DictReader(f)
    DAYCOLS = [c for c in rdr.fieldnames if c and c != "city"]
    rows = list(rdr)

def val(r, k):
    v = (r.get(k) or "").strip()
    return int(v) if v else 0

tot   = {k: sum(val(r, k) for r in rows) for k in DAYCOLS}
kyiv  = {k: next((val(r, k) for r in rows if r["city"] == "Kyiv"), 0) for k in DAYCOLS}
rest  = {k: tot[k] - kyiv[k] for k in DAYCOLS}
ncity = {k: sum(1 for r in rows if val(r, k) > 0) for k in DAYCOLS}
counted = [k for k in DAYCOLS if tot[k] > 0]         # days with at least one figure

img = Image.new("RGB", (W * S, H * S), WHITE)
d = ImageDraw.Draw(img)
qa_boxes = []

def T(x, y, s, f, fill, anchor="ls"):
    d.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor)

def QT(name, x, y, s, f, fill, anchor="ls", inside_plot=False):
    """Draw and register plot text for collision/bounds checks."""
    T(x, y, s, f, fill, anchor)
    box = tuple(v / S for v in d.textbbox((x * S, y * S), s, font=f, anchor=anchor))
    qa_boxes.append((name, box, inside_plot))

def line(pts, fill, w=1):
    d.line([(x * S, y * S) for x, y in pts], fill=fill, width=max(1, int(w * S)))
def dashed_vline(x, y0, y1, fill=EVENT, w=1, on=5, off=5):
    y = y0
    while y < y1:
        line([(x, y), (x, min(y + on, y1))], fill, w)
        y += on + off

# ---- masthead ----------------------------------------------------------------
T(28, 58, "Approximate reported protest turnout by day", F_TITLE, BLACK)
T(28, 86, "%s. Only city figures stated in page bodies; Kyiv is shown separately."
          % META["subtitle_en"], F_SUB, GREY)
line([(28, 102), (W - 28, 102)], BLACK, 1)

# ---- plot area ---------------------------------------------------------------
PX0, PX1, PY0, PY1 = 108, W - 40, 196, 700
maxY = max(tot.values()) * 1.20 or 1
sy = lambda v: PY1 - (PY1 - PY0) * v / maxY
n = len(DAYCOLS)
sx = lambda i: PX0 + (PX1 - PX0) * (i / (n - 1)) if n > 1 else (PX0 + PX1) / 2

step = 1000 if maxY > 3000 else 250
g = 0
while g <= maxY:
    yy = sy(g)
    line([(PX0, yy), (PX1, yy)], GRID, 1)
    T(PX0 - 12, yy + 5, num(g), F_AXIS, GREY_L, anchor="rs")
    g += step
line([(PX0, PY1), (PX1, PY1)], BLACK, 1)

# ---- stacked area ------------------------------------------------------------
# each run of consecutive counted days is its own polygon, so gaps stay gaps
runs, cur = [], []
for i, k in enumerate(DAYCOLS):
    if tot[k] > 0:
        cur.append(i)
    elif cur:
        runs.append(cur); cur = []
if cur:
    runs.append(cur)

for run in runs:
    if len(run) == 1:
        i = run[0]; x = sx(i)
        line([(x, PY1), (x, sy(tot[DAYCOLS[i]]))], REST, 2.2)
        line([(x, PY1), (x, sy(kyiv[DAYCOLS[i]]))], KYIV, 2.2)
        continue
    top = [(sx(i), sy(tot[DAYCOLS[i]])) for i in run]
    mid = [(sx(i), sy(kyiv[DAYCOLS[i]])) for i in run]
    base = [(sx(i), PY1) for i in reversed(run)]
    d.polygon([(x * S, y * S) for x, y in top + list(reversed(mid))], fill=REST)
    d.polygon([(x * S, y * S) for x, y in mid + base], fill=KYIV)
    line(top, BLACK, 1.3)
    line(mid, BLACK, 1.0)

# ---- day markers and totals --------------------------------------------------
# The two crests: the sum peaks once early, when most cities were still being counted,
# and again on the day of the all-Ukrainian march. Both are labelled, because the
# difference between them is coverage, not turnout.
crests = sorted(counted, key=lambda k: -tot[k])[:2]
important_ticks = {"07-31", "08-16", "08-18", "08-19", DAYCOLS[-1]}
for i, k in enumerate(DAYCOLS):
    x = sx(i)
    if i % 2 == 0 or k in important_ticks:
        T(x, PY1 + 22, k[3:], F_DAY, BLACK if tot[k] else GREY_L, anchor="ms")
    if tot[k] == 0:
        T(x, PY1 + 40, "·", F_SEG, GREY_L, anchor="ms")
        continue
    y = sy(tot[k])
    d.ellipse([(x - 2.6) * S, (y - 2.6) * S, (x + 2.6) * S, (y + 2.6) * S],
              fill=WHITE, outline=BLACK, width=max(1, int(1.2 * S)))
    T(x, PY1 + 40, str(ncity[k]), F_SEG, GREY, anchor="ms")
    if k in crests:
        QT("total " + k, x, y - 16, "~" + num(tot[k]), F_PEAK, BLACK, anchor="ms")
    elif tot[k] >= 1200 or i in (0, n - 1):
        QT("total " + k, x, y - 12, "~" + num(tot[k]), F_SEG, BLACK, anchor="ms")

# month bands under the day numbers
seg, prev = [], None
for i, k in enumerate(DAYCOLS):
    if k[:2] != prev:
        seg.append([i, i]); prev = k[:2]
    else:
        seg[-1][1] = i
for a, b in seg:
    xa, xb = sx(a), sx(b)
    line([(xa, PY1 + 52), (xb, PY1 + 52)], GREY_L, 1)
    T((xa + xb) / 2, PY1 + 70, MON_UK.get(DAYCOLS[a][:2], DAYCOLS[a][:2]), F_MON, GREY, anchor="ms")
T(PX0 - 12, PY1 + 40, "cities", F_SEG, GREY_L, anchor="rs")

# ---- annotations -------------------------------------------------------------
# Labels identify selected protest events without turning the title into a conclusion.
MARCH = "07-31"
if MARCH in DAYCOLS and tot[MARCH]:
    px, py = sx(DAYCOLS.index(MARCH)), sy(tot[MARCH])
    note = "31 July · Kyiv march: ~6 000 (police)"
    nx = min(px + 18, PX1 - F_NOTE.getbbox(note)[2] / S)
    ny = max(PY0 + 8, py - 42)
    QT("31 July march", nx, ny, note, F_NOTE, BLACK, inside_plot=True)
    line([(px, py - 5), (nx, ny + 5)], GREY_L, 1)

# Protest-event labels use short leaders and occupy the otherwise empty right half
# of the data region. Political context keeps the full-height dashed rules, but its
# labels also live in the plot instead of consuming two extra bands below it.
event_notes = [
    ("08-16", 530, "16 Aug · repeat march", "rs"),
    ("08-19", 610, "18–19 Aug · final coordinated actions", "ls"),
    (DAYCOLS[-1], 650, "29 Aug · late Dnipro action (~15)", "rs"),
]
for k, yy, txt, anchor in event_notes:
    if k not in DAYCOLS:
        continue
    xx = sx(DAYCOLS.index(k))
    tx = xx - 7 if anchor == "rs" else xx + 7
    data_y = sy(tot[k]) if tot[k] else PY1
    line([(xx, data_y - 5), (tx, yy + 5)], GREY_L, 1)
    QT("protest " + k, tx, yy, txt, F_NOTE, BLACK, anchor=anchor, inside_plot=True)

political_events = [
    ("07-22", 332, "22 Jul · Syrskyi removed; Drapatyi appointed", "ls"),
    ("08-18", 284, "18 Aug · Fedorov calls for an election mechanism", "rs"),
    ("08-19", 326, "19 Aug · Khmara appointed (312 votes)", "rs"),
]
for k, yy, txt, anchor in political_events:
    if k not in DAYCOLS:
        continue
    xx = sx(DAYCOLS.index(k))
    tx = xx - 7 if anchor == "rs" else xx + 7
    dashed_vline(xx, PY0, PY1, EVENT, 1, on=4, off=5)
    QT("political " + k, tx, yy, txt, F_NOTE, EVENT, anchor=anchor, inside_plot=True)

# ---- legend ------------------------------------------------------------------
lx, ly = PX0 + 16, 150
for j, (fill, lab) in enumerate([(KYIV, "Kyiv"), (REST, "other cities (sum)")]):
    yy = ly + j * 22
    d.rectangle([lx * S, yy * S, (lx + 16) * S, (yy + 12) * S],
                fill=fill, outline=BLACK, width=max(1, S))
    T(lx + 24, yy + 11, lab, F_LEG, BLACK, anchor="ls")

# ---- footer ------------------------------------------------------------------
line([(28, H - 86), (W - 28, H - 86)], (221, 221, 221), 1)
CAV = ("Approximate body-level figures; the number under a day is the number of cities counted. "
       "Blank days mean no usable city estimate, not necessarily no protest.")
CREDIT = "Chart: Valentyn Hatsko, TG: @gorbach_squad. Source: Ukrainian media, retrieved September 2026."
REPO = "github.com/KSE-Sociological-Center/fedorov-protests-2026"
T(28, H - 60, CAV, F_FOOT, GREY)
T(28, H - 38, CREDIT, F_AUTH, BLACK)
T(28, H - 17, REPO, F_FOOT, GREY)

# ---- self-check: totals + text width -----------------------------------------
over = []
if 28 + F_FOOT.getbbox(CAV)[2] / S > W - 28:
    over.append("caveat overflows")
if 2 * (PX1 - PX0) / max(1, n - 1) < F_DAY.getbbox("00")[2] / S + 2:
    over.append("day labels collide")
for name, box, inside_plot in qa_boxes:
    if inside_plot and (box[0] < PX0 or box[1] < PY0 or box[2] > PX1 or box[3] > PY1):
        over.append("%s outside plot" % name)
for i, (name_a, a, _) in enumerate(qa_boxes):
    for name_b, b, _ in qa_boxes[i + 1:]:
        gap = 4
        separated = (a[2] + gap <= b[0] or b[2] + gap <= a[0]
                     or a[3] + gap <= b[1] or b[3] + gap <= a[1])
        if not separated:
            over.append("text collision: %s / %s" % (name_a, name_b))
print("days: %d (%s..%s) | counted: %d" % (n, DAYCOLS[0], DAYCOLS[-1], len(counted)))
for k in crests:
    print("  crest %s = %d (Kyiv %d, %d cities counted)" % (k, tot[k], kyiv[k], ncity[k]))
print("series:", " ".join("%s=%d" % (k, tot[k]) for k in DAYCOLS))
print("text overflow:", over or "none")
if over:
    raise SystemExit("chart QA failed: " + "; ".join(over))
img.resize((W, H), Image.LANCZOS).save(ds("chart_by_day.png"), "PNG", optimize=True)
print("saved:", ds("chart_by_day.png"), os.path.getsize(ds("chart_by_day.png")) // 1024, "KB")
