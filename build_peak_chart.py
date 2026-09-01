# -*- coding: utf-8 -*-
"""data/<event>/by_day.csv -> data/<event>/chart_peak_by_day.png

Daily peak crowd estimates for Kyiv, continuing the project's original
6 August column chart.  The Kyiv row in by_day.csv is the single source of
truth.  Blank cells remain blank: they are not converted to zeroes.
"""
import csv
import io
import json
import os
import sys
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = os.path.dirname(os.path.abspath(__file__))
DS = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "data/2026-07-16-fedorov"
ds = lambda n: os.path.join(HERE, DS, n)
META = json.load(io.open(ds("meta.json"), encoding="utf-8"))
YEAR = int(META["date"][:4])
OUT = ds("chart_peak_by_day.png")

INK = "#0b0b0b"
SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"
BLUE = "#2a78d6"
NAVY = "#0d366b"
ORANGE = "#e2a414"
EVENT = "#b86455"

plt.rcParams.update({
    "font.family": "Segoe UI",
    "font.size": 11,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": SECONDARY,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "savefig.facecolor": SURFACE,
})


def fmt(n):
    return format(int(n), ",")


def label_date(d):
    return "%d %s" % (d.day, {7: "Jul", 8: "Aug", 9: "Sep"}[d.month])


with io.open(ds("by_day.csv"), encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    daycols = [c for c in (reader.fieldnames or []) if c and c != "city"]
    rows = list(reader)

kyiv = next((r for r in rows if r.get("city") == "Kyiv"), None)
if kyiv is None:
    raise SystemExit("Kyiv row is missing from by_day.csv")

raw = [(kyiv.get(c) or "").strip() for c in daycols]
nonblank = [i for i, v in enumerate(raw) if v]
if not nonblank:
    raise SystemExit("Kyiv has no numeric daily estimates")

# The series ends at Kyiv's last usable estimate, not at a later action in another city.
last_i = max(nonblank)
daycols = daycols[:last_i + 1]
raw = raw[:last_i + 1]
dates = [datetime.strptime("%d-%s" % (YEAR, c), "%Y-%m-%d").date() for c in daycols]
values = [int(v) if v else np.nan for v in raw]
x = np.arange(len(dates))

for a, b in zip(dates, dates[1:]):
    if (b - a).days != 1:
        raise SystemExit("by_day.csv is not continuous at %s..%s" % (a, b))

fig = plt.figure(figsize=(15, 8.4), dpi=100)
ax = fig.add_axes([0.075, 0.225, 0.895, 0.555])

colors = []
for d in dates:
    key = d.strftime("%m-%d")
    colors.append(ORANGE if key == "07-31" else NAVY if key == "07-19" else BLUE)

bars = ax.bar(x, np.nan_to_num(values, nan=0.0), width=0.72, color=colors,
              linewidth=0, zorder=3)
for bar, value in zip(bars, values):
    if np.isnan(value):
        bar.set_visible(False)

# Sparse horizontal guides are retained because the user needs to compare 300 with 6,000.
ax.set_ylim(0, 7000)
ax.set_yticks([0, 2000, 4000, 6000])
ax.set_yticklabels(["0", "2,000", "4,000", "6,000"])
ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
ax.xaxis.grid(False)
ax.tick_params(axis="both", length=0)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.axhline(0, color=GRID, linewidth=0.8, zorder=1)
ax.set_xlim(-0.75, len(dates) - 0.25)

tick_idx = list(range(0, len(dates), 4))
if len(dates) - 1 not in tick_idx:
    tick_idx.append(len(dates) - 1)
ax.set_xticks(tick_idx)
ax.set_xticklabels([label_date(dates[i]) for i in tick_idx])

# Keep the QA set separate from axes/title text: these are the movable labels whose
# pairwise collisions matter.  The peak and repeat-march values are integrated into
# their annotations, so they cannot compete with a second label over the same bar.
qa_texts = []

def track(name, artist):
    qa_texts.append((name, artist))
    return artist


# Direct values on the major days, plus the last recorded Kyiv estimate.
for i, value in enumerate(values):
    if np.isnan(value) or (value < 1000 and i != len(values) - 1):
        continue
    if daycols[i] in ("07-31", "08-16"):
        continue
    color = ORANGE if daycols[i] == "07-31" else NAVY if daycols[i] == "07-19" else BLUE
    track("value %s" % daycols[i],
          ax.text(i, value + 105, fmt(value), ha="center", va="bottom",
                  fontsize=11.5, fontweight="semibold", color=color))

def index_of(mmdd):
    return daycols.index(mmdd) if mmdd in daycols else None


# Protest annotations identify the exceptional marches without turning the title into a claim.
peak_i = index_of("07-31")
if peak_i is not None:
    track("31 Jul march",
          ax.annotate("31 Jul · all-Ukrainian march · 6,000",
                      xy=(peak_i, values[peak_i]), xytext=(peak_i - 1.15, 6680),
                      ha="right", va="top", color=ORANGE, fontsize=10.5,
                      arrowprops=dict(arrowstyle="-", color=ORANGE, lw=0.9,
                                      connectionstyle="angle3")))

repeat_i = index_of("08-16")
if repeat_i is not None:
    track("16 Aug march",
          ax.annotate("16 Aug · repeat march · 1,500",
                      xy=(repeat_i, values[repeat_i]), xytext=(repeat_i - 1.1, 2300),
                      ha="right", va="center", color=SECONDARY, fontsize=10.2,
                      arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8,
                                      connectionstyle="angle3")))

vigils_i = index_of("07-23")
if vigils_i is not None:
    track("daily vigils",
          ax.annotate("daily vigils:\n300–500 people",
                      xy=(vigils_i, values[vigils_i]), xytext=(vigils_i - 1.4, 1320),
                      ha="center", va="center", color=SECONDARY, fontsize=9.8,
                      arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7,
                                      connectionstyle="angle3")))

# Political context uses thin dashed rules and staggered labels.
events = [
    ("07-22", 5200, "22 Jul · Syrskyi removed; Drapatyi appointed", "left", 0.55),
    ("08-18", 4750, "18 Aug · Fedorov calls for\nan election mechanism", "right", -0.45),
    ("08-19", 3900, "19 Aug · Khmara appointed\n(312 votes)", "right", -0.45),
]
for mmdd, yy, text, ha, dx in events:
    i = index_of(mmdd)
    if i is None:
        continue
    ax.axvline(i, color=EVENT, linewidth=0.9, linestyle=(0, (4, 4)), zorder=1)
    track("event %s" % mmdd,
          ax.text(i + dx, yy, text, ha=ha, va="center", fontsize=9.8,
                  linespacing=1.2, color=EVENT))

fig.text(0.075, 0.935, "Reported peak crowd at Kyiv protests by day",
         fontsize=21, fontweight="semibold", color=INK, ha="left")
fig.text(0.075, 0.892,
         "Body-level daily estimates, %s — %s %d" %
         (label_date(dates[0]), label_date(dates[-1]), YEAR),
         fontsize=12.5, color=SECONDARY, ha="left")

fig.lines.append(plt.Line2D([0.075, 0.97], [0.835, 0.835], transform=fig.transFigure,
                            color=INK, linewidth=0.7))
fig.lines.append(plt.Line2D([0.025, 0.975], [0.145, 0.145], transform=fig.transFigure,
                            color=GRID, linewidth=0.7))
fig.text(0.025, 0.112,
         "Blank days mean no usable Kyiv estimate; bars show body-level daily peaks.",
         fontsize=9.3, color=MUTED, ha="left")
fig.text(0.025, 0.081,
         "Chart: Valentyn Hatsko, TG: @gorbach_squad. Source: Ukrainian media, retrieved September 2026.",
         fontsize=9.3, fontweight="semibold", color=INK, ha="left")
fig.text(0.025, 0.050,
         "Data, code and method: github.com/KSE-Sociological-Center/fedorov-protests-2026",
         fontsize=9.3, color=MUTED, ha="left")

fig.canvas.draw()
renderer = fig.canvas.get_renderer()
overflow = []
for text in fig.findobj(match=lambda a: isinstance(a, matplotlib.text.Text) and a.get_text()):
    box = text.get_window_extent(renderer=renderer)
    if box.x0 < -2 or box.x1 > fig.bbox.width + 2 or box.y0 < -2 or box.y1 > fig.bbox.height + 2:
        overflow.append(text.get_text().replace("\n", " / "))
collisions = []
label_boxes = [(name, artist.get_window_extent(renderer=renderer))
               for name, artist in qa_texts]
for i, (name1, box1) in enumerate(label_boxes):
    for name2, box2 in label_boxes[i + 1:]:
        # A four-pixel breathing margin catches labels that almost touch after
        # downsampling, which is what the previous bounds-only check missed.
        separated = (box1.x1 + 4 <= box2.x0 or box2.x1 + 4 <= box1.x0 or
                     box1.y1 + 4 <= box2.y0 or box2.y1 + 4 <= box1.y0)
        if not separated:
            collisions.append("%s × %s" % (name1, name2))
print("Kyiv daily estimates: %d | %s..%s | blanks: %d" %
      (sum(not np.isnan(v) for v in values), daycols[0], daycols[-1], sum(np.isnan(v) for v in values)))
print("text overflow:", overflow or "none")
print("label collisions:", collisions or "none")
if overflow or collisions:
    raise SystemExit("chart text QA failed")

fig.savefig(OUT, dpi=100, facecolor=SURFACE)
plt.close(fig)
print("saved:", OUT, os.path.getsize(OUT) // 1024, "KB")
