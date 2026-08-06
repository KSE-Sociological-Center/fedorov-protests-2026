# -*- coding: utf-8 -*-
"""Verify that every artifact shows THE SAME THING.

Divergence between them was the original problem: the data used to live in four
copies. Run after each build_*.py. A non-zero exit code means they disagree.
"""
import csv, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DS = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "data/2026-07-16-fedorov"
ds = lambda n: os.path.join(HERE, DS, n)

cities = list(csv.DictReader(io.open(ds("cities.csv"), encoding="utf-8")))
pubs   = list(csv.DictReader(io.open(ds("publications.csv"), encoding="utf-8")))
canon  = {c["city"]: c["category"] for c in cities}

errors, warns = [], []

# 1. arithmetic: the distribution must sum to the row count
from collections import Counter
dist = Counter(c["category"] for c in cities)
if sum(dist.values()) != len(cities):
    errors.append("distribution %d does not match %d locations" % (sum(dist.values()), len(cities)))

# 2. every city in publications must exist in the canon
orphans = sorted({r["city"] for r in pubs} - set(canon))
if orphans:
    errors.append("cities in publications missing from canon: %s" % ", ".join(orphans))

# 3. every canon city needs at least one publication
silent = sorted(set(canon) - {r["city"] for r in pubs})
if silent:
    errors.append("canon cities with no publication: %s" % ", ".join(silent))

# 4. date filter: the July 2025 protests share the same keywords
bad = [r["city"] for r in pubs if "2025" in r["published"]]
if bad:
    errors.append("rows dated 2025 (different protests): %s" % ", ".join(bad))

# 5. every link must resolve to an article, not a homepage
fronts = [(r["city"], r["link"]) for r in pubs
          if len(r["link"].rstrip("/").split("/")) <= 3 and r["link"].startswith("http")]
if fronts:
    warns.append("links to homepage instead of article: %s" % fronts[:5])

# 6. LABEL_DIR in build_map.py must cover the canon
src = io.open(os.path.join(HERE, "build_map.py"), encoding="utf-8").read()
dirs = set(re.findall(r'"([^"]+)":\s*"(?:up|down|left|right)"', src))
missing_dir = sorted(set(canon) - dirs)
if missing_dir:
    errors.append("no label direction in build_map.py: %s" % ", ".join(missing_dir))

# 7. the HTML page must carry the same cities and categories
html_path = ds("map.html")
if os.path.exists(html_path):
    html = io.open(html_path, encoding="utf-8").read()
    for m, cat in canon.items():
        if ('"%s"' % m) not in html:
            errors.append("artifact missing city: %s" % m)
        elif not re.search(r'"%s".{0,220}?"%s"' % (re.escape(m), re.escape(cat)), html, re.S):
            errors.append("artifact: category for %s differs from canon (%s)" % (m, cat))
else:
    warns.append("HTML not generated yet")

# 8. the report's Table 2 must match the canon
rep_path = ds("report.md")
if os.path.exists(rep_path):
    rep = io.open(rep_path, encoding="utf-8").read()
    m = re.search(r"<!-- TABLE2:START -->(.*?)<!-- TABLE2:END -->", rep, re.S)
    if m:
        listed = dict(re.findall(r"^\|\s*\*\*([^*|]+)\*\*\s*\|[^|]*\|\s*\*\*([^*|]+)\*\*", m.group(1), re.M))
        for city, cat in canon.items():
            got = listed.get(city)
            if got is None:
                errors.append("Table 2 missing city: %s" % city)
            elif got.strip() != cat:
                errors.append("Table 2: %s = %s, canon = %s" % (city, got.strip(), cat))
    else:
        warns.append("no TABLE2 markers in report")

# 9. by_day.csv (chart source): cities in the canon, day columns a gapless date run
bd_path = ds("by_day.csv")
DAYS = []
if os.path.exists(bd_path):
    with io.open(bd_path, encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        DAYS = [c for c in rdr.fieldnames if c and c != "city"]
        bd = list(rdr)
    bd_orphans = sorted({r["city"] for r in bd} - set(canon))
    if bd_orphans:
        errors.append("by_day.csv cities missing from canon: %s" % ", ".join(bd_orphans))
    if not any(r["city"] == "Kyiv" for r in bd):
        warns.append("by_day.csv has no Kyiv row")
    import datetime
    try:
        ds_dates = [datetime.date(2026, int(c[:2]), int(c[3:])) for c in DAYS]
    except Exception:
        errors.append("by_day.csv day columns are not MM-DD dates: %s" % DAYS[:3])
        ds_dates = []
    for a, b in zip(ds_dates, ds_dates[1:]):
        if (b - a).days != 1:
            errors.append("by_day.csv skips a day between %s and %s" % (a, b))
    if ds_dates:
        first = min(c["first_day"] for c in cities if c.get("first_day"))
        if first[5:] != DAYS[0]:
            warns.append("by_day starts %s, earliest city first_day is %s" % (DAYS[0], first))
    for r in bd:
        for c in DAYS:
            v = (r.get(c) or "").strip()
            if v and not v.isdigit():
                errors.append("by_day.csv non-numeric value %r for %s %s" % (v, r["city"], c))

# 10. duration fields must be internally consistent and inside the period
if DAYS and cities and "days_active" in cities[0]:
    span = len(DAYS)
    for c in cities:
        n = c.get("days_active", "")
        if not n.isdigit():
            errors.append("%s: days_active is not a number (%r)" % (c["city"], n))
            continue
        if int(n) > span:
            errors.append("%s: days_active %s exceeds the %d-day period" % (c["city"], n, span))
        lo, hi = "2026-" + DAYS[0], "2026-" + DAYS[-1]
        for f in ("first_day", "last_day", "peak_day"):
            v = c.get(f, "")
            if v and not (lo <= v <= hi):
                errors.append("%s: %s = %s falls outside %s..%s" % (c["city"], f, v, lo, hi))
        if c.get("first_day") and c.get("last_day") and c["first_day"] > c["last_day"]:
            errors.append("%s: first_day after last_day" % c["city"])
        if int(n) == 0:
            errors.append("%s: days_active is 0 but the city is in the canon" % c["city"])

print("canon: %d locations | publications: %d" % (len(cities), len(pubs)))
print("distribution: " + " · ".join("%s %d" % kv for kv in dist.most_common()) + " = %d" % sum(dist.values()))
for w in warns: print("  WARNING:", w)
if errors:
    print("\nMISMATCH (%d):" % len(errors))
    for e in errors: print("  ✗", e)
    sys.exit(1)
print("\nOK - all artifacts agree")
