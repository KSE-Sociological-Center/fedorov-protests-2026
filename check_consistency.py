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

print("canon: %d locations | publications: %d" % (len(cities), len(pubs)))
print("distribution: " + " · ".join("%s %d" % kv for kv in dist.most_common()) + " = %d" % sum(dist.values()))
for w in warns: print("  WARNING:", w)
if errors:
    print("\nMISMATCH (%d):" % len(errors))
    for e in errors: print("  ✗", e)
    sys.exit(1)
print("\nOK - all artifacts agree")
