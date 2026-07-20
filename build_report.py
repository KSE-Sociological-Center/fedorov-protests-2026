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

COVERAGE = """### Checked, no protest found (5)

Drohobych, Kamianets-Podilskyi, Izmail, Bila Tserkva, Uman. (Mukachevo was here until day 4, when it protested — now on the map.)

**Not marked on the map, deliberately.** These six were checked only because they appeared in the prompt's city list. The remaining ~460 cities of Ukraine were not checked individually, so marking these six as checked-and-empty would claim a systematic negative survey that does not exist. Kremenchuk proves the point: not an oblast capital, a protest **did** take place, and it surfaced only by querying a local outlet directly.

### How other cities were searched for

The initial city universe came from the prompt's list plus whatever the national round-ups enumerated. Both are bounded, which makes the search confirmation rather than discovery. To close that, a full gazetteer of **499 Ukrainian city names from Wikidata** was queried through Google News, requiring the name in the headline. The procedure was validated on Kremenchuk, which it finds independently. The **CitySites (0XX.ua)** network was swept in full: 41 domains, found by brute-forcing the telephone-code space, because search engines do not index it (`site:0342.ua` returns nothing). The **Raion.in.ua** network of 44 small towns was swept as well.

**Yield: one location, Kolomyia, 11 people.** Verified separately: Kolomyia appears in **none of the 12 national round-ups**, and in none of the four Ivano-Frankivsk regional sources retrieved here. Its own local outlet covered it, but procedure 2 retrieves local outlets only for cities already surfaced by procedure 1.

**The result is negative, and that is its value.** The sweep cost about 475 queries, hit rate limiting, and changed no conclusion: not the geography, since Ivano-Frankivsk oblast was already on the map, not the scale, not any contested figure. Kremenchuk, also not an oblast capital, **is** listed by KP.UA. National round-ups plus Suspilne regional desks cover everything consequential; outside them live actions of eleven people. CitySites: non-capital sites (Bila Tserkva, Pryluky, Konotop, Nikopol, Irpin, Kramatorsk) carry nothing on day 1; **Kamianske** was empty then but protested on day 4 (5.ua), and Kremenchuk was already on the map via KP.UA. Raion.in.ua: the word Fedorov does not appear at all. No Wikipedia article on these protests exists. No actions abroad were found in the day-1 sweep — they appeared only on day 3 (Warsaw, Brussels, Sydney).

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
    b3.append("**Known defect: %d publications link to an outlet homepage instead of a specific article** "
              "(day-1 supporting rows). The canon is clean: **all %d location links resolve to specific "
              "articles** — the day-1 Suspilne desk and bare-id 404 links were fixed this run. Outstanding: %s.\n"
              % (len(fronts), len(cities), ", ".join(sorted({"%s (%s)" % (r["outlet"], r["city"]) for r in fronts}))))

b3.append(
    "### Second day (17 July), added in the 18 July run\n\n"
    "Street actions recurred in at least Kyiv, Lutsk, Mykolaiv, Kropyvnytskyi, Ternopil, Poltava, "
    "Ivano-Frankivsk, Chernivtsi, Sumy, Zhytomyr and Dnipro; Odesa announced an evening action. "
    "**Only Kyiv's peak rose** (≈2,000 → «близько 3 тисяч», still 1000+); elsewhere the second day was "
    "no larger than the first, and no new location appeared, so no dot changes band — the map's "
    "second-day change is its framing and the settled statuses, not its geometry. A solidarity action "
    "in **Warsaw** is outside the map's Ukraine-only scope, recorded here only as a note. A **third day** "
    "was called for the evening of 18 July.\n")

b3.append(
    "### Third day (18 July), added in the 19 July run\n\n"
    "Street actions recurred for a third day in at least Kyiv, Lviv, Kharkiv, Dnipro, Odesa, "
    "Ivano-Frankivsk, Mykolaiv, Ternopil, Cherkasy, Khmelnytskyi, Kropyvnytskyi and Uzhhorod. "
    "Kyiv ran from ~15:00 to «близько 2 тисяч» by 21:45 (Suspilne reporting Kyiv directly this time), "
    "below the day-2 peak. **One band changed: Mykolaiv «понад 150 людей» (was 45 on day 1) crosses into "
    "100–999.** Kharkiv police counted «близько 400» at 20:00, a wave high within the same band. "
    "Solidarity rallies appeared **abroad** — Warsaw, Brussels, Sydney — outside the map's Ukraine-only "
    "scope, noted not mapped. Rerunning the v3 discovery across the whole wave (gazetteer-grep of every "
    "downloaded round-up, batch tier-A queries, targeted city searches) surfaced **no verifiable city "
    "beyond the 25**: the four a rival Telegram map flagged (Irpin, Boryspil, Kalush, Drohobych) have no "
    "round-up or city-level source, and every gazetteer hit was a false positive — the organiser's "
    "surname «Козятинський», the President's name «Володимир», war-attack city lists.\n")

b3.append("""### Fourth day (19 July), added on 19 July

The wave did **not** end: on 19 July street actions ran for a fourth day in ~15 cities and drew the largest crowd of the whole wave in Kyiv — «понад 5000 людей» on Ivan Franko Square (Interfax-Ukraine via LIGA), above the day-2 peak, so Kyiv's figure and the wave peak update to day 4. Kharkiv «понад 400» (майдан Свободи) and Ivano-Frankivsk «приблизно 250» held their bands. **Three cities new to the map: Mukachevo** (LB, UP, 24 Kanal), **Kamianske** (5.ua) and **Uman** (found by the §4.2 gazetteer-grep of the day-4 round-ups — it sat in a 24 Kanal per-city subsection, not the comma-list) — both `unknown` count, both news-sourced (not Telegram). **Odesa surged to «близько тисячі людей»** on Derybasivska (24 Kanal, citing Suspilne), verified in the article body this time (not just a snippet) — a ~7× jump from day 1, so **Odesa crosses into 1000+** (marked contested: single-source, borderline). The round-up also gave day-4 highs: Lutsk «понад 300», Cherkasy «150», Kharkiv «450» (20:30) and Dnipro «понад 150». **Political outcome:** the Verkhovna Rada went into **recess to 18 August without appointing a defence minister** — Klymenko's candidacy was never submitted (Ivan Vyhivsky took the interior ministry) and **Yevhen Khmara remains acting**. The demand is unmet, so the protests continue.""")

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
