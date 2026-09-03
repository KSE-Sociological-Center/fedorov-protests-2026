# -*- coding: utf-8 -*-
"""data/<event>/cities.csv -> data/<event>/map.png

Protest map with an ordered blue scale for reported crowd bands. Data comes
from the CSV, which is the single source of truth; this file holds
presentation only. Borders: Natural Earth 10m admin_1 (geo.py).
"""
import csv, io, math, os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from geo import COUNTRY, REGIONS

HERE = os.path.dirname(os.path.abspath(__file__))
import json, sys

# Dataset path as an argument, otherwise data/<event>/ buys nothing: the next
# event would still require code edits.
DS = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "data/2026-07-16-fedorov"
ds = lambda n: os.path.join(HERE, DS, n)
META = json.load(io.open(ds("meta.json"), encoding="utf-8"))

CSV_PATH = ds("cities.csv")
OUT = ds("map.png")
SNAPSHOT = META["snapshot"]
AUTHOR = META["author_en"]
S = 3
W, H = 1500, 1204
FDIR = r"C:\Windows\Fonts"

# Label direction is PRESENTATION, so it lives here rather than in the data.
LABEL_DIR = {
    "Kyiv": "up", "Kharkiv": "right", "Dnipro": "right", "Lviv": "left",
    "Odesa": "down", "Ivano-Frankivsk": "left", "Ternopil": "up",
    "Khmelnytskyi": "down", "Lutsk": "left", "Cherkasy": "down",
    "Poltava": "up", "Zaporizhzhia": "right", "Kropyvnytskyi": "down",
    "Uzhhorod": "right", "Rivne": "right", "Mykolaiv": "left",
    "Chernivtsi": "down", "Zhytomyr": "up", "Sumy": "right", "Kolomyia": "down",
    "Vinnytsia": "right", "Chernihiv": "up", "Kryvyi Rih": "down",
    "Kremenchuk": "down", "Kherson": "down",
    "Mukachevo": "down", "Kamianske": "up", "Uman": "down",
    "Izmail": "left", "Kalush": "up", "Sheptytskyi": "left",
    "Oleksandriia": "left", "Kamianets-Podilskyi": "down",
}

def font(names, size):
    for n in names:
        p = os.path.join(FDIR, n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size * S)
    raise SystemExit("no font: " + repr(names))

F_TITLE = font(["segoeuib.ttf", "seguisb.ttf"], 34)
F_SUB   = font(["segoeui.ttf"], 17)
F_META  = font(["seguisb.ttf", "segoeui.ttf"], 15)
F_CITY  = font(["seguisb.ttf", "segoeui.ttf"], 17)
F_NUM   = font(["segoeui.ttf"], 13)
F_LEGH  = font(["seguisb.ttf"], 13)
F_LEG   = font(["segoeui.ttf"], 15)
F_FOOT  = font(["segoeui.ttf"], 13)
F_AUTH  = font(["seguisb.ttf", "segoeui.ttf"], 13)

WHITE  = (255, 255, 255)
BLACK  = (17, 17, 17)
OBLAST = (196, 196, 196)
BORDER = (34, 34, 34)
GREY   = (105, 105, 105)
GREY_L = (150, 150, 150)
BLUE_EDGE = (14, 54, 103)
CONTESTED = (226, 92, 45)
ONLINE_FILL = (224, 235, 246)
PALETTE = {
    "5000+": (13, 54, 107),
    "1000–4999": (42, 120, 214),
    "100–999": (86, 152, 231),
    "<100": (134, 182, 239),
}
DOT_A  = 218

# ---- data --------------------------------------------------------------------
with io.open(CSV_PATH, encoding="utf-8") as f:
    CITIES = list(csv.DictReader(f))
for c in CITIES:
    c["lat"], c["lon"] = float(c["lat"]), float(c["lon"])
    c["dir"] = LABEL_DIR.get(c["city"], "down")
with io.open(ds("by_day.csv"), encoding="utf-8") as f:
    _day_fields = csv.DictReader(f).fieldnames or []
DAYCOLS = [c for c in _day_fields if c and c != "city"]
NDAYS = len(DAYCOLS)
LAST_ACTION = max(c["last_day"] for c in CITIES if c.get("last_day"))
LAST_ACTION_EN = datetime.strptime(LAST_ACTION, "%Y-%m-%d").strftime("%-d %B") if os.name != "nt" else datetime.strptime(LAST_ACTION, "%Y-%m-%d").strftime("%#d %B")
COORDINATED_END = datetime.strptime(META["coordinated_end"], "%Y-%m-%d")
COORDINATED_END_EN = COORDINATED_END.strftime("%-d %B") if os.name != "nt" else COORDINATED_END.strftime("%#d %B")
LAST_CITIES = ", ".join(c["city"] for c in CITIES if c.get("last_day") == LAST_ACTION)

# ---- projection ----------------------------------------------------------------
KX = math.cos(math.radians(48.4))
LON0, LON1, LAT0, LAT1 = 21.7, 40.35, 52.45, 44.3
BX, BY, BW, BH = 26, 152, 1448, 966
sc = min(BW / ((LON1 - LON0) * KX), BH / (LAT0 - LAT1))
ox = BX + (BW - (LON1 - LON0) * KX * sc) / 2
oy = BY + (BH - (LAT0 - LAT1) * sc) / 2
px = lambda lon: (ox + (lon - LON0) * KX * sc) * S
py = lambda lat: (oy + (LAT0 - lat) * sc) * S

R = {"5000+": 24, "1000–4999": 17, "100–999": 12.5, "<100": 6.5,
     "unknown": 6.5, "online": 6.5}

img = Image.new("RGB", (W * S, H * S), WHITE)
d = ImageDraw.Draw(img)

def dashed_circle(dr, cx, cy, r, color, width, on=6, off=6):
    step = 360.0 * (on + off) / max(2 * math.pi * r, 1)
    a = 0.0
    while a < 360:
        dr.arc([cx - r, cy - r, cx + r, cy + r], a,
               min(a + step * on / (on + off), 360), fill=color, width=width)
        a += step

# ---- land: oblasts, then the national border ----------------------------------
for _, rings in REGIONS:
    for ring in rings:
        pts = [(px(a), py(b)) for a, b in ring]
        if len(pts) > 2:
            d.polygon(pts, fill=WHITE, outline=OBLAST, width=S)
for ring in COUNTRY:
    pts = [(px(a), py(b)) for a, b in ring]
    d.line(pts + [pts[0]], fill=BORDER, width=int(2.2 * S), joint="curve")

def place(cx, cy, r, dr_):
    GAP, LINE = 6 * S, 11 * S
    if dr_ == "up":   return cx, "ms", cy - r - GAP - LINE, cy - r - GAP
    if dr_ == "down": return cx, "ms", cy + r + GAP + LINE, cy + r + GAP + LINE * 2
    if dr_ == "left": return cx - r - GAP, "rs", cy + S, cy + S + LINE
    return cx + r + GAP, "ls", cy + S, cy + S + LINE

def halo(dr, xy, txt, fnt, fill, anchor, hw):
    x, y = xy
    for dx in range(-hw, hw + 1):
        for dy in range(-hw, hw + 1):
            if dx * dx + dy * dy <= hw * hw:
                dr.text((x + dx, y + dy), txt, font=fnt, fill=WHITE, anchor=anchor)
    dr.text((x, y), txt, font=fnt, fill=fill, anchor=anchor)

boxes = []
def note(x, y, txt, fnt, anchor):
    l, t, r_, b = fnt.getbbox(txt)
    w, h = r_ - l, b - t
    if anchor[0] == "m": x -= w / 2
    elif anchor[0] == "r": x -= w
    boxes.append((txt, x, y - h, w, h))

# The prompt's six blank-spot towns are NOT drawn. Exactly those six were checked,
# and only because the prompt listed them. Marking them would claim a systematic
# negative survey of hundreds of non-capitals that does not exist. See Block 3.

# ---- dots ----------------------------------------------------------------
ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
od = ImageDraw.Draw(ov)
for c in sorted(CITIES, key=lambda c: -R[c["category"]]):
    if c["category"] in ("unknown", "online"): continue
    cx, cy, r = px(c["lon"]), py(c["lat"]), R[c["category"]] * S
    od.ellipse([cx - r, cy - r, cx + r, cy + r],
               fill=PALETTE[c["category"]] + (DOT_A,))
img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
d = ImageDraw.Draw(img)

for c in sorted(CITIES, key=lambda c: -R[c["category"]]):
    cat, cont = c["category"], c["contested"] == "yes"
    cx, cy, r = px(c["lon"]), py(c["lat"]), R[cat] * S
    if cat == "unknown":
        dashed_circle(d, cx, cy, r, BLACK, max(2, int(1.4 * S)), on=4, off=4)
    elif cat == "online":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ONLINE_FILL)
        dashed_circle(d, cx, cy, r, GREY, max(2, int(1.4 * S)), on=2, off=4)
    else:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=BLUE_EDGE,
                  width=max(2, int(1.4 * S)))
    if cont:
        dashed_circle(d, cx, cy, r + int(4.5 * S), CONTESTED,
                      max(2, int(1.2 * S)), on=3, off=4)
    rr = r + int(4.5 * S) if cont else r
    x, anc, y1, y2 = place(cx, cy, rr, c["dir"])
    dim = cat in ("unknown", "online")
    halo(d, (x, y1), c["city"], F_CITY, GREY if dim else BLACK, anc, hw=2 * S)
    note(x, y1, c["city"], F_CITY, anc)
    if not dim:
        halo(d, (x, y2), cat, F_NUM, GREY, anc, hw=2 * S)
        note(x, y2, cat, F_NUM, anc)

# ---- masthead -------------------------------------------------------------------
def T(x, y, s, f, fill, anchor="ls"):
    d.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor)

n_live = sum(1 for c in CITIES if c["status"].startswith("ongoing"))
TITLE = "Documented protest locations and peak crowd bands"
SUBLINE = "%s. %d locations over a %d-day calendar span." % (
    META["subtitle_en"], len(CITIES), NDAYS)
LIVELINE = ("Coverage through %s; audited %s. Coordinated actions: %s; "
            "latest confirmed local action: %s, %s."
            % (SNAPSHOT, META.get("audit_date", SNAPSHOT), COORDINATED_END_EN, LAST_CITIES, LAST_ACTION_EN))
T(28, 62, TITLE, F_TITLE, BLACK)
T(28, 92, SUBLINE, F_SUB, GREY)
T(28, 117, LIVELINE, F_META, BLACK)
d.line([28 * S, 136 * S, (W - 28) * S, 136 * S], fill=BLACK, width=max(1, S))

# ---- legend -----------------------------------------------------------------
LX, LY = 44, 812
T(LX, LY, "LEGEND", F_LEGH, BLACK)
# Vertical offsets are DERIVED from the radii, not written down: adding a band used to
# mean hand-shifting every row below it, and forgetting to made them overlap.
SPEC = [
    (R["5000+"],     "solid", False, "5000+ participants", "5000+"),
    (R["1000–4999"], "solid", False, "1000–4999 participants", "1000–4999"),
    (R["100–999"],   "solid", False, "100–999 participants", "100–999"),
    (R["<100"],      "solid", False, "fewer than 100", "<100"),
    (6.5,             "dash",  False, "protest held, no count published", None),
    (6.5,             "dot",   False, "online action (Kherson)", "online"),
    (R["100–999"],   "solid", True,  "contested: sources disagree", "100–999"),
]
GAP = 14
rows, y = [], 0.0
for i, (r_, kind, ring, lab, cat) in enumerate(SPEC):
    eff = r_ + (4.5 if ring else 0)          # the contested ring sits outside the dot
    y = eff + 16 if i == 0 else y + prev_eff + eff + GAP
    rows.append((y, r_, kind, ring, lab, cat))
    prev_eff = eff

for dy, r_, kind, ring, lab, cat in rows:
    cx, cy = (LX + 22) * S, (LY + dy) * S
    rr = r_ * S
    if kind == "solid":
        o2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(o2).ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                                   fill=PALETTE[cat] + (DOT_A,))
        img.paste(Image.alpha_composite(img.convert("RGBA"), o2).convert("RGB"), (0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=BLUE_EDGE,
                  width=max(2, int(1.4 * S)))
    elif kind == "dash":
        dashed_circle(d, cx, cy, rr, BLACK, max(2, int(1.4 * S)), on=4, off=4)
    else:
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=ONLINE_FILL)
        dashed_circle(d, cx, cy, rr, GREY, max(2, int(1.4 * S)), on=2, off=4)
    if ring:
        dashed_circle(d, cx, cy, rr + int(4.5 * S), CONTESTED,
                      max(2, int(1.2 * S)), on=3, off=4)
    d.text(((LX + 56) * S, (LY + dy + 5) * S), lab, font=F_LEG, fill=BLACK, anchor="ls")

# ---- footer -------------------------------------------------------------------
# One line. The rule is already in the subtitle and «contested» in the legend; the
# full method lives in the report. Only the required note and border credit remain.
d.line([28 * S, (H - 66) * S, (W - 28) * S, (H - 66) * S], fill=(221, 221, 221), width=max(1, S))
METHOD = "City dots show peak crowd bands; missing locations remain possible. Borders: Natural Earth 10m."
CREDIT = "Chart: Valentyn Hatsko, TG: @gorbach_squad. Source: Ukrainian media, retrieved September 2026."
REPO = "Data, code and method: github.com/KSE-Sociological-Center/fedorov-protests-2026"
T(28, H - 46, METHOD, F_FOOT, GREY)
T(28, H - 27, CREDIT, F_AUTH, BLACK)
T(28, H - 9, REPO, F_FOOT, GREY)

# ---- self-check: does the masthead/footer text fit the canvas ------------------
over = []
for label, txt, fnt in [("subtitle", SUBLINE, F_SUB), ("live line", LIVELINE, F_META)]:
    w = fnt.getbbox(txt)[2] / S
    if 28 + w > W - 28: over.append("%s (+%dpx)" % (label, int(28 + w - (W - 28))))
for label, txt, fnt in [("method", METHOD, F_FOOT), ("credit", CREDIT, F_AUTH), ("repository", REPO, F_FOOT)]:
    if 28 + fnt.getbbox(txt)[2] / S > W - 28:
        over.append("%s footer line overflows" % label)
# and does the land run into the footer
land_bottom = (oy + (LAT0 - LAT1) * sc)
if land_bottom > H - 66 - 6: over.append("land overlaps footer (+%dpx)" % int(land_bottom - (H - 72)))
# legend rows must not overlap each other or run past the footer rule
for (y1, r1, _, g1, l1, _), (y2, r2, _, g2, l2, _) in zip(rows, rows[1:]):
    if (LY + y1) + r1 + (4.5 if g1 else 0) >= (LY + y2) - r2 - (4.5 if g2 else 0):
        over.append("legend rows overlap: %s / %s" % (l1, l2))
last_y, last_r, _, last_ring, _, _ = rows[-1]
if LY + last_y + last_r + (4.5 if last_ring else 0) > H - 66:
    over.append("legend runs past the footer rule")
print("text overflowing canvas:", over or "none")

# ---- self-check: label collisions -------------------------------------------------
hits = []
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        (t1, x1, y1, w1, h1), (t2, x2, y2, w2, h2) = boxes[i], boxes[j]
        oxx = min(x1 + w1, x2 + w2) - max(x1, x2)
        oyy = min(y1 + h1, y2 + h2) - max(y1, y2)
        if oxx > 2 * S and oyy > 2 * S:
            hits.append("%s x %s" % (t1, t2))
print("cities:", len(CITIES), "| active at close:", n_live)
print("label collisions:", hits or "none")
img.resize((W, H), Image.LANCZOS).save(OUT, "PNG", optimize=True)
print("saved:", OUT, os.path.getsize(OUT) // 1024, "KB")
