# -*- coding: utf-8 -*-
"""Generate report tables and computed coverage aggregates.

Narrative chronology and methodological notes live in prose.md. This generator reads
CSV data, fills the marked table/aggregate blocks, and does not own event prose.
"""
import csv, io, json, os, sys
from collections import Counter, OrderedDict
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DS = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "data/2026-07-16-fedorov"
ds = lambda n: os.path.join(HERE, DS, n)

META = json.load(io.open(ds("meta.json"), encoding="utf-8"))
cities = list(csv.DictReader(io.open(ds("cities.csv"), encoding="utf-8")))
pubs = list(csv.DictReader(io.open(ds("publications.csv"), encoding="utf-8")))
prose = io.open(ds("prose.md"), encoding="utf-8").read()
with io.open(ds("by_day.csv"), encoding="utf-8") as f:
    DAYS = [c for c in csv.DictReader(f).fieldnames if c and c != "city"]

ORDER = {"5000+": 0, "1000–4999": 1, "100–999": 2, "<100": 3,
         "unknown": 4, "online": 5}
cities.sort(key=lambda c: (ORDER.get(c["category"], 9), c["city"]))

def esc(value):
    return (value or "").replace("|", "\\|").strip()

def inject(text, tag, payload):
    start, end = "<!-- %s:START -->" % tag, "<!-- %s:END -->" % tag
    i, j = text.index(start) + len(start), text.index(end)
    return text[:i] + "\n" + payload.rstrip() + "\n" + text[j:]

by_city = OrderedDict((c["city"], []) for c in cities)
for row in pubs:
    by_city.setdefault(row["city"], []).append(row)

# Table 1: one publication × city.
t1 = []
for city in cities:
    name = city["city"]
    flag = " ⚠️ contested" if city["contested"] == "yes" else ""
    t1.append("### %s — %s%s\n" % (name, city["category"], flag))
    t1.append("| Outlet | Headline | Link | Published | Quote (verbatim) | Cat. | Status | Provenance | Run |")
    t1.append("|---|---|---|---|---|---|---|---|---|")
    for row in sorted(by_city.get(name, []), key=lambda r: (r["run"], r["published"], r["outlet"])):
        t1.append("| %s | %s | [link](%s) | %s | %s | %s | %s | %s | %s |" % (
            esc(row["outlet"]), esc(row["headline_uk"]), row["link"], esc(row["published"]),
            esc(row["quote_uk"]) or "unknown", esc(row["category"]) or "—",
            esc(row["status"]) or "—", esc(row["provenance"]) or "not stated",
            esc(row["run"])))
    if city["note"].strip():
        t1.append("\n> **Verdict:** %s\n" % city["note"].strip())

# Table 2: canonical location summary.
t2 = [
    "| City | Oblast | Category | Quote (verbatim) | Peak | Days | Contested | Status | Source |",
    "|---|---|---|---|---|---|---|---|---|",
]
for city in cities:
    span = "%s–%s" % (city["first_day"][5:], city["last_day"][5:])
    days = "**%s** (%s)" % (city["days_active"], span)
    t2.append("| **%s** | %s | **%s** | «%s» | %s | %s | %s | %s | [%s](%s) |" % (
        city["city"], city["oblast"], city["category"], esc(city["quote_uk"]),
        city["time"], days, "⚠️ **yes**" if city["contested"] == "yes" else "no",
        esc(city["status"]), esc(city["source"]), city["link"]))

dist = Counter(c["category"] for c in cities)
t2.extend([
    "",
    "**Distribution:** " + " · ".join("%s — %d" % (k, dist.get(k, 0))
        for k in ORDER) + " · **total — %d**" % len(cities),
    "",
    "**Most persistent locations** (distinct documented action days): " +
    " · ".join("%s %d" % (name, days) for days, name in sorted(
        [(int(c["days_active"]), c["city"]) for c in cities], reverse=True)[:8]),
])

# Block 3: computed aggregates only. Search narrative and chronology stay in prose.md.
domains = sorted({urlparse(r["link"]).netloc.removeprefix("www.")
                  for r in pubs if r["link"].startswith("http")})
single = sorted(c["city"] for c in cities if len(by_city.get(c["city"], [])) == 1)
live = sorted(c["city"] for c in cities if c["status"].startswith("ongoing"))
fronts = [r for r in pubs if r["link"].startswith("http")
          and len(r["link"].rstrip("/").split("/")) <= 3]
runs = Counter(r["run"] for r in pubs)
statuses = Counter(r["status"] for r in pubs)
provenance = Counter(r["provenance"] for r in pubs)

b3 = [
    "**Processed:** %d publications across %d domains and %d locations." %
        (len(pubs), len(domains), len(cities)),
    "",
    "**Calendar span:** %d days (%s–%s); collection checked through %s." %
        (len(DAYS), DAYS[0], DAYS[-1], META["snapshot"]),
    "",
    "**Audit:** completed 3 September 2026 without extending the event window or publication cutoff. "
    "See `audit/2026-09-03/` for row-level verdicts, exact evidence and unresolved sources.",
    "",
    "**Status at close:** %s" % (", ".join(live) if live else
        "no location remained active; the last documented coordinated multi-city actions were on %s, "
        "and the latest documented local action was on %s." %
        (META["coordinated_end"], META["last_action"])),
    "",
    "**Runs:** " + " · ".join("%s — %d" % item for item in sorted(runs.items())),
    "",
    "**Publication statuses:** " + " · ".join("%s — %d" % item for item in sorted(statuses.items())),
    "",
    "**Provenance:** " + " · ".join("%s — %d" % item for item in sorted(provenance.items())),
    "",
    "**Single-source locations:** " + (", ".join(single) if single else "none"),
    "",
    "**Article-link audit:** %d homepage links remain." % len(fronts),
    "",
    "**Domains:** " + ", ".join("`%s`" % d for d in domains),
]

out = prose.replace("{N}", str(len(cities))).replace("{LIVE}", str(len(live)))
out = out.replace("{DAYS}", str(len(DAYS))).replace("{LAST}", META["last_action"])
out = inject(out, "TABLE1", "\n".join(t1))
out = inject(out, "TABLE2", "\n".join(t2))
out = inject(out, "BLOCK3", "\n".join(b3))
io.open(ds("report.md"), "w", encoding="utf-8").write(out)

print("cities: %d | publications: %d | domains: %d | active at close: %d" %
      (len(cities), len(pubs), len(domains), len(live)))
print("distribution: " + " · ".join("%s %d" % item for item in dist.items()) +
      " = %d" % sum(dist.values()))
print("saved: %s/report.md (%d KB)" % (DS, len(out.encode("utf-8")) // 1024))
