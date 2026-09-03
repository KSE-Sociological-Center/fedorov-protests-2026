"""Read-only, compact human review of source passages and baseline rows."""
import argparse
import json
from collections import defaultdict
from audit_full import AUDIT, BASE, CACHE, ROOT, read_csv, body_for, source_id, flat, event_date, candidate_passages, city_patterns

parser = argparse.ArgumentParser()
parser.add_argument("--city")
parser.add_argument("--date")
parser.add_argument("--start", type=int, default=0)
parser.add_argument("--limit", type=int, default=20)
parser.add_argument("--unknown", action="store_true")
parser.add_argument("--source")
parser.add_argument("--full", action="store_true")
parser.add_argument("--daily", action="store_true")
parser.add_argument("--links", action="store_true")
parser.add_argument("--find")
parser.add_argument("--brief", action="store_true")
parser.add_argument("--pending", action="store_true")
parser.add_argument("--run")
parser.add_argument("--flagged", action="store_true")
args = parser.parse_args()
rows = read_csv(BASE / "publications.csv")
sources = {s["source_id"]: s for s in json.loads((AUDIT / "sources.json").read_text(encoding="utf-8"))}
patterns = city_patterns()

if args.find:
    import re
    expression = re.compile(args.find, re.I)
    for sid, s in sources.items():
        paras = [flat(x) for x in body_for(s).splitlines() if flat(x)]
        for i, p in enumerate(paras):
            if expression.search(p):
                print(sid, "P"+str(i), s.get("published_metadata"), s.get("headline"), "\n", "\n".join(paras[max(0,i-1):i+2]))
    raise SystemExit()

if args.daily:
    cells = json.loads((AUDIT / "daily_candidates.json").read_text(encoding="utf-8"))
    if args.city:
        cells = [c for c in cells if c["city"] == args.city]
    for c in cells[args.start:args.start+args.limit]:
        print("\nCELL", c["city"], c["date"], "OLD", c["original"])
        choices = [(i, rows[i-1], sources[source_id(rows[i-1]["link"])]) for i in c["rows"]]
        choices.sort(key=lambda x: (x[1]["category"] == "unknown", not bool(body_for(x[2])), x[1]["provenance"] not in {"police", "own correspondent"}, x[1]["outlet"].count("(") == 0, len(x[1]["quote_uk"])))
        used = set()
        for i, r, s in choices:
            if s["source_id"] in used:
                continue
            used.add(s["source_id"])
            print("ROW", i, "SOURCE", s["source_id"], r["outlet"], s.get("published_metadata"), "OLDQUOTE", r["quote_uk"])
            ps = candidate_passages(body_for(s))
            selected = [p for p in ps if patterns[c["city"]].search(p["context"])]
            if not selected:
                selected = ps
            for p in selected[:5]:
                print("P"+str(p["paragraph"])+":", p["text"])
            if len(used) == 2:
                break
    raise SystemExit()

if args.source:
    for sid, s in sources.items():
        if sid.startswith(args.source) or args.source in s["requested_url"]:
            print(sid, s["requested_url"], s.get("published_metadata"), s.get("headline"))
            if args.links and s.get("raw_path"):
                from bs4 import BeautifulSoup
                soup = BeautifulSoup((ROOT/s["raw_path"]).read_text(encoding="utf-8", errors="replace"), "html.parser")
                for a in soup.find_all("a", href=True):
                    if a.get_text(strip=True) and ("suspilne" in a["href"] or "Федоров" in a.get_text()):
                        print("LINK", a.get_text(" ", strip=True), a["href"])
                print("TIMES", [t.get_text(" ", strip=True) for t in soup.find_all("time")])
            for i, p in enumerate([flat(x) for x in body_for(s).splitlines() if flat(x)]):
                print(f"P{i}: {p}")
    raise SystemExit()

grouped = defaultdict(list)
for i, row in enumerate(rows, 1):
    if args.city and row["city"] != args.city:
        continue
    if args.date and event_date(row) != "2026-" + args.date:
        continue
    if args.unknown and row["category"] != "unknown":
        continue
    if args.run and row["run"] != args.run:
        continue
    grouped[source_id(row["link"])].append((i, row))

if args.pending:
    from audit_source_reviews import REVIEWS
    grouped = {k:v for k,v in grouped.items() if k not in REVIEWS}
if args.flagged:
    grouped = {k:v for k,v in grouped.items() if candidate_passages(body_for(sources.get(k, {})))}

for sid, selected in list(grouped.items())[args.start:args.start+args.limit]:
    s = sources.get(sid, {})
    body = body_for(s)
    print("\nSOURCE", sid, s.get("requested_url"), "HTTP", s.get("http_status"))
    print("TITLE", s.get("headline"), "DATE", s.get("published_metadata"))
    if args.brief:
        print("LEAD", flat(body)[:500])
        print("ROWS", [(i, r["city"], r["published"], r["category"]) for i,r in selected])
    else:
        for i, r in selected:
            print("ROW", i, r["city"], event_date(r), r["category"], r["provenance"], "QUOTE:", r["quote_uk"])
    for p in candidate_passages(body):
        if args.city and not patterns[args.city].search(p["context"]) and not patterns[args.city].search(s.get("headline", "")):
            continue
        print("P"+str(p["paragraph"])+":", p["context"] if args.full else p["text"])
print("\nTOTAL SOURCE GROUPS", len(grouped))
