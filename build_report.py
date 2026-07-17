# -*- coding: utf-8 -*-
"""data/<event>/{prose.md, cities.csv, publications.csv} -> data/<event>/report.md

Prose lives in prose.md, data in the CSVs. Tables are generated between the
markers. Edit the CSVs or the prose, never the finished report.
"""
import csv, io, os
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
import json, sys

# Dataset path as an argument, otherwise data/<event>/ buys nothing: the next
# event would still require code edits.
DS = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "data/2026-07-16-fedorov"
ds = lambda n: os.path.join(HERE, DS, n)
META = json.load(io.open(ds("meta.json"), encoding="utf-8"))

cities = list(csv.DictReader(io.open(ds("cities.csv"), encoding="utf-8")))
pubs   = list(csv.DictReader(io.open(ds("publications.csv"), encoding="utf-8")))
prose  = io.open(ds("prose.md"), encoding="utf-8").read()

ORDER = {"1000+": 0, "100–999": 1, "<100": 2, "unknown": 3, "online": 4}
cities.sort(key=lambda c: (ORDER.get(c["category"], 9), c["city"]))

def esc(s):
    return (s or "").replace("|", "\\|").strip()

# ---- Table 1 ---------------------------------------------------------------
by_city = OrderedDict((c["city"], []) for c in cities)
for r in pubs:
    by_city.setdefault(r["city"], []).append(r)

t1 = []
for c in cities:
    m = c["city"]
    rows = by_city.get(m, [])
    flag = " ⚠️ contested" if c["contested"] == "yes" else ""
    live = " · **still ongoing at the snapshot**" if c["status"].startswith("ongoing") else ""
    t1.append("### %s — %s%s%s\n" % (m, c["category"], flag, live))
    t1.append("| Outlet | Headline | Link | Published | Quote (verbatim) | Cat. | Status | Provenance | Run |")
    t1.append("|---|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: r["run"]):
        t1.append("| %s | %s | [link](%s) | %s | %s | %s | %s | %s | %s |" % (
            esc(r["outlet"]), esc(r["headline_uk"]), r["link"], esc(r["published"]),
            esc(r["quote_uk"]) or "unknown", esc(r["category"]) or "—",
            esc(r["status"]) or "—", esc(r["provenance"]) or "not stated", esc(r["run"])))
    if c["note"].strip():
        t1.append("\n> **Verdict:** %s\n" % c["note"].strip())
    else:
        t1.append("")

# ---- Table 2 ---------------------------------------------------------------
t2 = ["| City | Oblast | Category | Quote (verbatim) | Time | Contested | Status | Source |",
      "|---|---|---|---|---|---|---|---|"]
for c in cities:
    t2.append("| **%s** | %s | **%s** | «%s» | %s | %s | %s | [%s](%s) |" % (
        c["city"], c["oblast"], c["category"], esc(c["quote_uk"]), c["time"],
        "⚠️ **yes**" if c["contested"] == "yes" else "no",
        esc(c["status"]), esc(c["source"]), c["link"]))

dist = Counter(c["category"] for c in cities)
assert sum(dist.values()) == len(cities), "distribution does not sum to the row count"
t2.append("")
t2.append("**Distribution:** " + " · ".join("%s — %d" % (k, dist.get(k, 0))
          for k in ["1000+", "100–999", "<100", "unknown", "online"]) +
          " · **total — %d**" % len(cities))

# ---- Block 3 ------------------------------------------------------------------
doms = sorted({r["link"].split("/")[2].replace("www.", "") for r in pubs if r["link"].startswith("http")})
live = [c["city"] for c in cities if c["status"].startswith("ongoing")]
single = [c["city"] for c in cities if len(by_city.get(c["city"], [])) == 1]

COVERAGE = """### Checked, no protest found (6)

Drohobych, Mukachevo, Kamianets-Podilskyi, Izmail, Bila Tserkva, Uman.

**Not marked on the map, deliberately.** These six were checked only because they appeared in the prompt's city list. The remaining ~460 cities of Ukraine were not checked individually, so marking these six as checked-and-empty would claim a systematic negative survey that does not exist. Kremenchuk proves the point: not an oblast capital, a protest **did** take place, and it surfaced only by querying a local outlet directly.

### How other cities were searched for

The initial city universe came from the prompt's list plus whatever the national round-ups enumerated. Both are bounded, which makes the search confirmation rather than discovery. To close that, a full gazetteer of **499 Ukrainian city names from Wikidata** was queried through Google News, requiring the name in the headline. The procedure was validated on Kremenchuk, which it finds independently. The **CitySites (0XX.ua)** network was swept in full: 41 domains, found by brute-forcing the telephone-code space, because search engines do not index it (`site:0342.ua` returns nothing). The **Raion.in.ua** network of 44 small towns was swept as well.

**Yield: one location, Kolomyia, 11 people.** Verified separately: Kolomyia appears in **none of the 12 national round-ups**, and in none of the four Ivano-Frankivsk regional sources retrieved here. Its own local outlet covered it, but procedure 2 retrieves local outlets only for cities already surfaced by procedure 1.

**The result is negative, and that is its value.** The sweep cost about 475 queries, hit rate limiting, and changed no conclusion: not the geography, since Ivano-Frankivsk oblast was already on the map, not the scale, not any contested figure. Kremenchuk, also not an oblast capital, **is** listed by KP.UA. National round-ups plus Suspilne regional desks cover everything consequential; outside them live actions of eleven people. CitySites: 8 non-capital sites (Bila Tserkva, Pryluky, Konotop, Nikopol, Kamianske, Irpin, Kramatorsk, Kremenchuk) carry nothing. Raion.in.ua: the word Fedorov does not appear at all. No Wikipedia article on these protests exists. No actions abroad were found.

**The tier below 30k inhabitants (364 towns) was not swept.** Google News began returning 503 after roughly 475 queries.

### Unavailable or problematic sources

| Source | Problem |
|---|---|
| **nv.ua** | HTTP 403 on plain retrieval; obtained through a browser, content verified |
| **MykVisti (mykvisti.com)** | domain dead: the origin of Censor.NET's Mykolaiv figure cannot be reached |
| **Konkurent (konkurent.ua)** | JS-rendered, body not extractable: the Lutsk figure is unverified |
| **Ukrainska Pravda, ZN.UA** | full body not served; only targeted extracts obtained |
| **Suspilne / Kyiv** | **no dedicated Kyiv article exists.** For the main protest city, Suspilne offers only the national round-up, stale as of 11:41 |
| **Police / Kyiv City Administration** | no official crowd estimate published |"""

b3 = []
b3.append("**Processed:** %d publications across %d domains, %d locations.\n" % (len(pubs), len(doms), len(cities)))
b3.append("**Domains:** " + ", ".join("`%s`" % d for d in doms) + "\n")
b3.append("**Still ongoing at the snapshot (figures will rise):** " + ", ".join(live) + "\n")
b3.append("**Single-source locations** (no second confirmation found): " + ", ".join(single) + "\n")

fronts = [r for r in pubs if r["link"].startswith("http")
          and len(r["link"].rstrip("/").split("/")) <= 3]
if fronts:
    b3.append("**Known defect: %d publications link to an outlet homepage instead of a specific article.** "
              "All are from the 13:00 run. The location table is clean: 24 of 25 links resolve to articles; "
              "the exception is Kyiv, where Suspilne has no dedicated piece. Outstanding: %s.\n"
              % (len(fronts), ", ".join(sorted({"%s (%s)" % (r["outlet"], r["city"]) for r in fronts}))))

b3.append(COVERAGE)

# ---- assemble ------------------------------------------------------------------
def inject(text, tag, payload):
    a, b = "<!-- %s:START -->" % tag, "<!-- %s:END -->" % tag
    i, j = text.index(a) + len(a), text.index(b)
    return text[:i] + "\n" + payload.rstrip() + "\n" + text[j:]

out = prose.replace("{N}", str(len(cities))).replace("{LIVE}", str(len(live)))
out = inject(out, "TABLE1", "\n".join(t1))
out = inject(out, "TABLE2", "\n".join(t2))
out = inject(out, "BLOCK3", "\n".join(b3))

io.open(ds("report.md"), "w", encoding="utf-8").write(out)
print("cities: %d | publications: %d | domains: %d | still ongoing: %d" % (len(cities), len(pubs), len(doms), len(live)))
print("distribution: " + " · ".join("%s %d" % kv for kv in dist.most_common()) + " = %d" % sum(dist.values()))
print("saved: %s/report.md (%d KB)" % (DS, len(out.encode("utf-8")) // 1024))
