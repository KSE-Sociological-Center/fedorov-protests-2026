"""Validate human evidence references without mutating canonical data."""
import json
import argparse
from collections import Counter
from audit_full import AUDIT, BASE, body_for, flat, read_csv, source_id
from audit_decisions import DAILY, PUBLICATION
from audit_source_reviews import REVIEWS
from audit_full import event_date, city_patterns

parser = argparse.ArgumentParser()
parser.add_argument("--claims", action="store_true")
parser.add_argument("--fields", action="store_true")
parser.add_argument("--start", type=int, default=0)
parser.add_argument("--limit", type=int, default=20)
args = parser.parse_args()

pubs = read_csv(BASE / "publications.csv")
sources = {s["source_id"]: s for s in json.loads((AUDIT/"sources.json").read_text(encoding="utf-8"))}
cells = {(r["city"], day): value for r in read_csv(BASE/"by_day.csv") for day,value in r.items() if day != "city" and value}
seen = set()
errors = []
for city, day, value, ref, quote, qualifier, reason in DAILY:
    key = (city, day)
    if key in seen:
        errors.append((key, "duplicate decision"))
    seen.add(key)
    sid = source_id(pubs[ref-1]["link"]) if isinstance(ref, int) else ref
    if quote and flat(quote) not in flat(body_for(sources[sid])):
        errors.append((key, ref, "quote not literal", quote))
print("Decisions", len(DAILY), "original cells covered", len(set(cells)&seen), "/", len(cells))
print("Remaining", [k for k in cells if k not in seen])
print("Quote errors", errors)
review_errors=[]
for sid, review in REVIEWS.items():
    for row_id, (value, quote, qualifier) in review.get("counts", {}).items():
        if sid not in sources or flat(quote) not in flat(body_for(sources[sid])):
            review_errors.append((sid,row_id,quote))
        if source_id(pubs[row_id-1]["link"]) != sid:
            review_errors.append((sid,row_id,"source mismatch"))
print("Review quote errors",review_errors)
print("Publication source reviews",len({source_id(r['link']) for r in pubs}&REVIEWS.keys()),"/",len({source_id(r['link']) for r in pubs}))
if args.claims:
    daily={(c,d):(v,ref) for c,d,v,ref,*_ in DAILY}
    claims=[]
    for sid,review in REVIEWS.items():
        for row_id,(value,quote,qualifier) in review.get("counts",{}).items():
            r={**pubs[row_id-1],**PUBLICATION.get(row_id,{})}
            if r.get('remove'): continue
            day=r.get('event_date',review.get('event_dates',{}).get(r['city'],review.get('event_date',event_date(r))))
            key=(r['city'],day[5:] if day else None)
            if daily.get(key,(None,))[0] != value:
                claims.append((row_id,key,value,qualifier,"current",daily.get(key),quote))
    for x in sorted(claims,key=lambda x:(x[1][0],x[1][1] or ''))[args.start:args.start+args.limit]: print(x)
    print("CLAIMS TO RECONCILE",len(claims))
if args.fields:
    patterns=city_patterns()
    flags=[]
    for i,orig in enumerate(pubs,1):
        patch=PUBLICATION.get(i,{})
        if patch.get('remove'): continue
        sid=source_id(orig['link']); review=REVIEWS.get(sid,{})
        if review.get('outcome','').startswith('rejected'): continue
        r={**orig,**patch}; body=body_for(sources[sid]); quote=r['quote_uk']
        count=review.get('counts',{}).get(i)
        if count: quote=count[1]
        # Approved selected quotes take precedence over legacy paraphrases.
        own=[d for d in DAILY if d[3]==i and d[4]]
        if own: quote=own[0][4]
        issue=[]
        if quote not in {'невідомо','unknown','цифри немає',''} and flat(quote).strip('«»"') not in flat(body): issue.append('quote')
        if body and not patterns[r['city']].search(body): issue.append('city_absent')
        if issue: flags.append((i,r['city'],r['published'],sid,issue,quote,r['category']))
    for x in flags[args.start:args.start+args.limit]: print(x)
    print('FIELD FLAGS',len(flags))
if errors or review_errors: raise SystemExit(1)
