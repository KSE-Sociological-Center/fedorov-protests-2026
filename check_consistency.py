# -*- coding: utf-8 -*-
"""Verify that every artifact shows THE SAME THING.

Divergence between them was the original problem: the data used to live in four
copies. Run after each build_*.py. A non-zero exit code means they disagree.
"""
import csv, io, json, os, re, sys, datetime
from urllib.parse import urlsplit, urlunsplit

HERE = os.path.dirname(os.path.abspath(__file__))
DS = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "data/2026-07-16-fedorov"
ds = lambda n: os.path.join(HERE, DS, n)

cities = list(csv.DictReader(io.open(ds("cities.csv"), encoding="utf-8")))
pubs   = list(csv.DictReader(io.open(ds("publications.csv"), encoding="utf-8")))
meta   = json.load(io.open(ds("meta.json"), encoding="utf-8"))
canon  = {c["city"]: c["category"] for c in cities}

errors, warns = [], []

# 1. arithmetic: the distribution must sum to the row count
from collections import Counter
dist = Counter(c["category"] for c in cities)
if sum(dist.values()) != len(cities):
    errors.append("distribution %d does not match %d locations" % (sum(dist.values()), len(cities)))

ALLOWED_CATS = {"5000+", "1000–4999", "100–999", "<100", "unknown", "online"}
ALLOWED_CITY_STATUS = {"ended", "online"}
ALLOWED_PUB_STATUS = {"announced", "ongoing", "online", "refuted", "took place"}
bad_city_cat = sorted({c["category"] for c in cities} - ALLOWED_CATS)
bad_pub_cat = sorted({r["category"] for r in pubs} - ALLOWED_CATS)
bad_city_status = sorted({c["status"] for c in cities} - ALLOWED_CITY_STATUS)
bad_pub_status = sorted({r["status"] for r in pubs} - ALLOWED_PUB_STATUS)
if bad_city_cat: errors.append("invalid city categories: %s" % bad_city_cat)
if bad_pub_cat: errors.append("invalid publication categories: %s" % bad_pub_cat)
if bad_city_status: errors.append("invalid final city statuses: %s" % bad_city_status)
if bad_pub_status: errors.append("invalid publication statuses: %s" % bad_pub_status)

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

def event_date(row):
    # Prefer an explicit event-date note over the publication timestamp.
    m = re.search(r"подія\s+(\d{1,2})\.(\d{1,2})", row["published"], re.I)
    if not m:
        m = re.match(r"\s*(\d{1,2})\.(\d{1,2})", row["published"])
    return datetime.date(2026, int(m.group(2)), int(m.group(1))) if m else None

CONTROL_START = datetime.date(2026, 7, 15)
CONTROL_END = datetime.datetime.strptime(meta["snapshot"], "%d %B %Y").date()
bad_dates = [(r["city"], r["published"]) for r in pubs
             if event_date(r) is None or not (CONTROL_START <= event_date(r) <= CONTROL_END)]
if bad_dates:
    errors.append("publication/event dates outside 15 Jul–1 Sep 2026: %s" % bad_dates[:8])

def norm_url(value):
    p = urlsplit(value.strip())
    return urlunsplit((p.scheme.lower(), p.netloc.lower().removeprefix("www."),
                       p.path.rstrip("/"), "", ""))

seen_new, dup_new = set(), []
for row in (r for r in pubs if r["run"] == "1 Sep"):
    key = (row["city"], norm_url(row["link"]))
    if key in seen_new:
        dup_new.append(key)
    seen_new.add(key)
    if not row["quote_uk"].strip() or row["quote_uk"].strip().lower() in {"unknown", "невідомо"}:
        errors.append("1 Sep row has no body quote: %s %s" % (row["city"], row["link"]))
if dup_new:
    errors.append("duplicate city + URL pairs inside run 1 Sep: %s" % dup_new[:8])

# 5. every link must resolve to an article, not a homepage
fronts = [(r["city"], r["link"]) for r in pubs
          if len(r["link"].rstrip("/").split("/")) <= 3 and r["link"].startswith("http")]
if fronts:
    errors.append("links to homepage instead of article: %s" % fronts[:5])

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
        latest = max(c["last_day"] for c in cities if c.get("last_day"))
        if latest[5:] != DAYS[-1]:
            errors.append("by_day ends %s, latest city last_day is %s" % (DAYS[-1], latest))
        if latest != meta["last_action"]:
            errors.append("meta last_action %s differs from latest city last_day %s" %
                          (meta["last_action"], latest))
    for r in bd:
        for c in DAYS:
            v = (r.get(c) or "").strip()
            if v and not v.isdigit():
                errors.append("by_day.csv non-numeric value %r for %s %s" % (v, r["city"], c))

    bands = [(0, 99, "<100"), (100, 999, "100–999"),
             (1000, 4999, "1000–4999"), (5000, 10**9, "5000+")]
    by_name = {r["city"]: r for r in bd}
    for city, cat in canon.items():
        vals = [int(by_name[city][day]) for day in DAYS
                if city in by_name and (by_name[city].get(day) or "").strip().isdigit()]
        if not vals:
            continue
        peak = max(vals)
        peak_band = next(label for lo, hi, label in bands if lo <= peak <= hi)
        if cat in {"<100", "100–999", "1000–4999", "5000+"} and peak_band != cat:
            errors.append("%s: by_day peak %d gives %s, canon is %s" %
                          (city, peak, peak_band, cat))

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
        numeric_days = 0
        if 'by_name' in locals() and c["city"] in by_name:
            numeric_days = sum(1 for day in DAYS if (by_name[c["city"]].get(day) or "").strip().isdigit())
        if int(n) < numeric_days:
            errors.append("%s: days_active %s is below %d numeric by_day dates" %
                          (c["city"], n, numeric_days))

# 11. days_active must cover unique documented event dates in the publication table.
for c in cities:
    dates = {event_date(r) for r in pubs if r["city"] == c["city"]
             and r["status"] not in {"announced", "refuted"} and event_date(r)}
    if len(dates) > int(c["days_active"]):
        errors.append("%s: %d unique publication event dates exceed days_active %s" %
                      (c["city"], len(dates), c["days_active"]))

print("canon: %d locations | publications: %d" % (len(cities), len(pubs)))
print("distribution: " + " · ".join("%s %d" % kv for kv in dist.most_common()) + " = %d" % sum(dist.values()))
for w in warns: print("  WARNING:", w)
if errors:
    print("\nMISMATCH (%d):" % len(errors))
    for e in errors: print("  ✗", e)
    sys.exit(1)
print("\nOK - all artifacts agree")
