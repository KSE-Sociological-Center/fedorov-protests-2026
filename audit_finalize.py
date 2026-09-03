"""Build the audited tables and ledgers from the immutable 3 Sep baseline.

This script never writes the three canonical CSV files.  It emits a JSON matrix
payload that is authored into CSV by the artifact-tool builder, plus transparent
JSON/Markdown audit ledgers.  Running it repeatedly is deterministic.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from audit_decisions import DAILY, PUBLICATION, RECOVERED_EVIDENCE, CONTESTED_CITIES, CITY_AUDIT_NOTES
from audit_full import AUDIT, BASE, DS, ROOT, body_for, candidate_passages, event_date, flat, norm_url, read_csv, source_id
from audit_source_reviews import REVIEWS
from audit_small_count_reviews import REVIEWS as SMALL_COUNT_REVIEWS

START = date(2026, 7, 16)
END = date(2026, 8, 29)
AUDIT_DATE = "2026-09-03"
MONTH = {7: "Jul", 8: "Aug"}


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def band(value):
    if value is None:
        return "unknown"
    value = int(value)
    if value >= 5000:
        return "5000+"
    if value >= 1000:
        return "1000–4999"
    if value >= 100:
        return "100–999"
    return "<100"


def a1_col(n):
    out = ""
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def exact_in_body(quote, body):
    if not quote or quote.lower() in {"невідомо", "unknown"}:
        return True
    q = flat(quote).strip('«»"')
    return bool(q and q in flat(body))


def provenance_for(qualifier, current):
    q = (qualifier or "").lower()
    if "police" in q:
        return "police"
    if "organiser" in q:
        return "organiser"
    if "relay" in q:
        return "relay"
    return current or "own correspondent"


def pub_day_text(value):
    match = re.match(r"\s*(\d{1,2})\.(\d{1,2})", value or "")
    return f"2026-{int(match.group(2)):02d}-{int(match.group(1)):02d}" if match else None


def mark_event_date(published, event_iso, explicit_none=False):
    base = re.sub(r"\s*\(подія\s+(?:\d{1,2}\.\d{1,2}|не датована)\)\s*", " ", published or "").strip()
    if explicit_none:
        return f"{base} (подія не датована)"
    if event_iso and event_iso != pub_day_text(base):
        d = date.fromisoformat(event_iso)
        return f"{base} (подія {d.day:02d}.{d.month:02d})"
    return base


def outlet_from(source, fallback=""):
    if fallback:
        return fallback
    host = urlsplit(source.get("final_url") or source.get("requested_url") or "").netloc
    return host.removeprefix("www.") or "Recovered source"


def publication_date_from_source(source, event_iso):
    for raw in source.get("published_metadata", []):
        match = re.match(r"(2026)-(\d\d)-(\d\d)(?:T(\d\d):(\d\d))?", raw)
        if match:
            day = f"{int(match.group(3)):02d}.{int(match.group(2)):02d}"
            return day + (f", {match.group(4)}:{match.group(5)}" if match.group(4) else "")
    d = date.fromisoformat(event_iso)
    return f"{d.day:02d}.{d.month:02d}"


def decision_map():
    result = {}
    for item in DAILY:
        key = (item[0], item[1])
        if key in result:
            raise ValueError(f"duplicate daily decision: {key}")
        result[key] = {
            "city": item[0], "day": item[1], "value": item[2], "ref": item[3],
            "quote": item[4], "qualifier": item[5], "reason": item[6],
        }
    return result


def effective_event(orig, patch, review):
    city = patch.get("city", orig["city"])
    if "event_date" in patch:
        return patch["event_date"], patch["event_date"] is None
    event_dates = review.get("event_dates", {})
    if city in event_dates:
        return event_dates[city], event_dates[city] is None
    if "event_date" in review:
        return review["event_date"], review["event_date"] is None
    if review.get("outcome") in {"unresolved_date", "unresolved_inaccessible", "unresolved_aggregator_only", "unresolved_wrong_body"}:
        return None, True
    return event_date({**orig, **patch}), False


def make_publications(pubs, sources, daily):
    final = []
    ledger = []
    effective_dates = {}
    daily_by_row = defaultdict(list)
    daily_by_sid_key = defaultdict(list)
    for d in daily.values():
        if isinstance(d["ref"], int):
            daily_by_row[d["ref"]].append(d)
        else:
            daily_by_sid_key[(d["ref"], d["city"], "2026-" + d["day"])].append(d)
    for city, day, value, sid, quote, qualifier, reason in RECOVERED_EVIDENCE:
        daily_by_sid_key[(sid, city, "2026-" + day)].append({
            "city":city,"day":day,"value":value,"ref":sid,"quote":quote,"qualifier":qualifier,"reason":reason,
        })

    for row_id, orig in enumerate(pubs, 1):
        sid = source_id(orig["link"])
        source = sources[sid]
        review = REVIEWS[sid]
        patch = copy.deepcopy(PUBLICATION.get(row_id, {}))
        reason_bits = [x for x in (patch.get("reason"), review.get("notes")) if x]
        remove = bool(patch.get("remove")) or review.get("outcome", "").startswith("rejected")
        if remove:
            outcome = "removed_duplicate" if patch.get("duplicate_of") else "removed_unrelated"
            ledger.append({
                "baseline_row": row_id, "source_id": sid, "screening_outcome": outcome,
                "original": orig, "final": None, "supporting_url": orig["link"],
                "exact_quote": "", "reason": " ".join(reason_bits),
            })
            continue

        row = copy.deepcopy(orig)
        for key, value in patch.items():
            if key not in {"reason", "remove", "duplicate_of", "event_date"}:
                row[key] = value
        if review.get("action_status"):
            row["status"] = review["action_status"]
        ev, explicit_none = effective_event(orig, patch, review)

        reviewed_count = review.get("counts", {}).get(row_id)
        selected = daily_by_row.get(row_id, []) or daily_by_sid_key.get((sid, row["city"], ev), [])
        if reviewed_count:
            value, quote, qualifier = reviewed_count
            row["category"] = band(value)
            row["quote_uk"] = quote
            row["provenance"] = provenance_for(qualifier, row.get("provenance"))
            row["provenance_detail_uk"] = (row.get("provenance_detail_uk", "") + f"; audit qualifier: {qualifier}").strip("; ")
        if selected:
            # A row may support several dates only through source-level recovery;
            # row-addressed decisions are expected to identify one event.
            d = selected[-1]
            row["category"] = band(d["value"])
            row["quote_uk"] = d["quote"] or "невідомо"
            row["provenance"] = provenance_for(d["qualifier"], row.get("provenance"))
            row["provenance_detail_uk"] = (row.get("provenance_detail_uk", "") + f"; audit qualifier: {d['qualifier']}").strip("; ")
            ev = "2026-" + d["day"]
            explicit_none = False
            reason_bits.append(d["reason"])

        if explicit_none and row.get("category") not in {"unknown", "online"}:
            row["category"] = "unknown"
            reason_bits.append("No dated current action can be assigned from this article; its count must not become a daily estimate.")
        body = body_for(source)
        if not exact_in_body(row.get("quote_uk", ""), body):
            reason_bits.append("Legacy quotation was not a literal body substring after whitespace normalization; downgraded instead of treating a paraphrase as evidence.")
            row["quote_uk"] = "невідомо"
            if row.get("category") not in {"unknown", "online"}:
                row["category"] = "unknown"
        if review.get("outcome", "").startswith("unresolved") and not exact_in_body(row.get("quote_uk", ""), body):
            row["category"] = "unknown"
            row["quote_uk"] = "невідомо"

        row["published"] = mark_event_date(row.get("published", ""), ev, explicit_none)
        final_index = len(final)
        final.append(row)
        effective_dates[final_index] = None if explicit_none else ev
        changed = any(row.get(k) != orig.get(k) for k in orig)
        if review.get("outcome", "").startswith("unavailable") or review.get("outcome", "").startswith("unresolved"):
            outcome = "unresolved_retained"
        elif changed:
            outcome = "corrected"
        elif row.get("category") == "unknown":
            outcome = "screened_no_numeric_count"
        else:
            outcome = "verified"
        ledger.append({
            "baseline_row": row_id, "source_id": sid, "screening_outcome": outcome,
            "original": orig, "final": row, "event_date": effective_dates[final_index],
            "supporting_url": row["link"], "exact_quote": row.get("quote_uk", ""),
            "reason": " ".join(dict.fromkeys(reason_bits)),
        })

    # Add recovered evidence only when the source/city/event combination is not
    # represented after corrections.  Distinct dates in a retrospective article
    # remain distinct observations, not same-run duplicates.
    existing = set()
    for idx, row in enumerate(final):
        existing.add((source_id(row["link"]), row["city"], effective_dates[idx]))
    for (sid, city, ev), decisions in sorted(daily_by_sid_key.items()):
        if (sid, city, ev) in existing:
            continue
        d = decisions[-1]
        source = sources[sid]
        url = source.get("final_url") or source.get("requested_url")
        qualifier = d["qualifier"]
        row = {
            "city": city,
            "outlet": outlet_from(source),
            "headline_uk": source.get("headline") or f"Recovered evidence for {city}, {d['day']}",
            "link": url,
            "published": mark_event_date(publication_date_from_source(source, ev), ev),
            "quote_uk": d["quote"],
            "category": band(d["value"]),
            "status": "took place",
            "provenance": provenance_for(qualifier, "own correspondent"),
            "provenance_detail_uk": f"Додано під час аудиту 3 Sep; audit qualifier: {qualifier}",
            "run": "3 Sep",
        }
        if not exact_in_body(row["quote_uk"], body_for(source)):
            raise ValueError(f"new row has non-literal quote: {sid} {city} {ev}")
        idx = len(final)
        final.append(row)
        effective_dates[idx] = ev
        existing.add((sid, city, ev))
        ledger.append({
            "baseline_row": None, "source_id": sid, "screening_outcome": "added_recovered_evidence",
            "original": None, "final": row, "event_date": ev, "supporting_url": url,
            "exact_quote": d["quote"], "reason": d["reason"],
        })

    # Remove only confirmed same-run equivalents: normalized source, city, event
    # date and run must all agree.  Cross-run observations remain untouched.
    deduped, dedup_dates, seen = [], {}, {}
    for idx, row in enumerate(final):
        key = (source_id(row["link"]), row["city"], effective_dates[idx], row["run"])
        if key in seen:
            entry = next(x for x in ledger if x.get("final") is row)
            entry["screening_outcome"] = "removed_duplicate"
            entry["reason"] += f" Confirmed same-run equivalent of final row {seen[key] + 1}."
            entry["final"] = None
            continue
        seen[key] = len(deduped)
        dedup_dates[len(deduped)] = effective_dates[idx]
        deduped.append(row)
    return deduped, dedup_dates, ledger


def make_daily(base_rows, daily, pubs, sources):
    headers = list(base_rows[0])
    base_by_city = {r["city"]: r for r in base_rows}
    rows = copy.deepcopy(base_rows)
    out_by_city = {r["city"]: r for r in rows}
    for (city, day), d in daily.items():
        if city not in out_by_city:
            row = {h: "" for h in headers}
            row["city"] = city
            rows.append(row)
            out_by_city[city] = row
        out_by_city[city][day] = "" if d["value"] is None else int(d["value"])

    ledger = []
    for key, d in sorted(daily.items()):
        city, day = key
        original = base_by_city.get(city, {}).get(day, "")
        original_value = int(original) if str(original).isdigit() else None
        final_value = d["value"]
        if original_value is None and final_value is not None:
            verdict = "recovered"
        elif original_value is not None and final_value is None:
            verdict = "unsupported_blank"
        elif original_value != final_value:
            verdict = "corrected"
        elif d["qualifier"].startswith("normalized"):
            verdict = "normalized_retained"
        else:
            verdict = "verified_retained"
        if isinstance(d["ref"], int):
            url = pubs[d["ref"] - 1]["link"]
            sid = source_id(url)
        else:
            sid = d["ref"]
            url = sources[sid].get("final_url") or sources[sid].get("requested_url")
        ledger.append({
            "city": city, "event_date": "2026-" + day, "original_value": original_value,
            "final_value": final_value, "verdict": verdict, "source_id": sid,
            "supporting_url": url, "exact_quote": d["quote"], "qualifier": d["qualifier"],
            "selection_rationale": d["reason"],
        })
    return rows, ledger


def claim_values(base_pubs, daily, pub_dates):
    claims = defaultdict(list)
    for sid, review in REVIEWS.items():
        for row_id, (value, quote, qualifier) in review.get("counts", {}).items():
            orig = base_pubs[row_id - 1]
            patch = PUBLICATION.get(row_id, {})
            if patch.get("remove"):
                continue
            city = patch.get("city", orig["city"])
            ev, explicit_none = effective_event(orig, patch, review)
            if ev and not explicit_none:
                claims[(city, ev[5:])].append({"value": value, "quote": quote, "qualifier": qualifier, "row": row_id})
    return claims


def make_cities(base_cities, daily, daily_ledger, final_pubs, effective_dates, base_pubs, sources):
    values = defaultdict(dict)
    for (city, day), d in daily.items():
        if d["value"] is not None:
            values[city][day] = int(d["value"])
    actions = defaultdict(set)
    for idx, row in enumerate(final_pubs):
        ev = effective_dates.get(idx)
        if ev and row["status"] not in {"announced", "refuted"} and START.isoformat() <= ev <= END.isoformat():
            actions[row["city"]].add(ev)
    for city, by_day in values.items():
        actions[city].update("2026-" + day for day in by_day)
    claims = claim_values(base_pubs, daily, effective_dates)
    daily_ledger_by_key = {(x["city"], x["event_date"][5:]): x for x in daily_ledger}
    result, ledger = [], []
    for original in base_cities:
        row = copy.deepcopy(original)
        city = row["city"]
        dates = sorted(actions.get(city, set()))
        row["first_day"] = dates[0] if dates else ""
        row["last_day"] = dates[-1] if dates else ""
        row["days_active"] = str(len(dates))
        if values.get(city):
            peak = max(values[city].values())
            peak_days = sorted(day for day, value in values[city].items() if value == peak)
            peak_day = peak_days[0]
            selected = daily[(city, peak_day)]
            evidence = daily_ledger_by_key[(city, peak_day)]
            row["category"] = band(peak)
            row["quote_uk"] = selected["quote"]
            q = selected["qualifier"]
            if "lower_bound" in q:
                row["quote_en"] = f"at least {peak:,} participants"
            elif "upper_bound" in q:
                row["quote_en"] = f"up to {peak:,} participants"
            elif "normalized" in q:
                row["quote_en"] = f"normalized estimate: {peak:,} participants"
            else:
                row["quote_en"] = f"approximately {peak:,} participants"
            row["peak_day"] = "2026-" + peak_day
            d = date.fromisoformat(row["peak_day"])
            row["time"] = f"{d.day} {MONTH[d.month]} 2026; {q.replace('_', ' ')}"
            sid = evidence["source_id"]
            source = sources[sid]
            fallback = ""
            if isinstance(selected["ref"], int):
                fallback = base_pubs[selected["ref"] - 1]["outlet"]
            row["source"] = f"{outlet_from(source, fallback)} ({q.replace('_', ' ')})"
            row["link"] = evidence["supporting_url"]
            alternatives = sorted({c["value"] for c in claims.get((city, peak_day), []) if c["value"] != peak})
            contested = city in CONTESTED_CITIES
            row["contested"] = "yes" if contested else "no"
            alt_text = f" Published alternatives for the peak date: {', '.join(map(str, alternatives))}." if alternatives else ""
            row["note"] = (f"3 Sep 2026 audit: selected peak {peak:,} on {row['peak_day']} ({q.replace('_', ' ')})."
                           f" Documented actions: {len(dates)} dates, {row['first_day']} to {row['last_day']}.{alt_text} "
                           + CITY_AUDIT_NOTES.get(city, selected["reason"]))
        else:
            row["category"] = "online" if city == "Kherson" else "unknown"
            row["peak_day"] = ""
            row["contested"] = "no"
            candidates = [p for p in final_pubs if p["city"] == city and p["status"] not in {"announced", "refuted"}]
            if candidates:
                chosen = next((p for p in candidates if p["quote_uk"] not in {"", "невідомо", "unknown"}), candidates[0])
                row["quote_uk"] = chosen["quote_uk"] or "невідомо"
                row["link"] = chosen["link"]
                row["source"] = chosen["outlet"]
                row["time"] = chosen["published"]
            if city == "Kherson":
                row["status"] = "online"
                row["quote_en"] = "participation was online because street assembly was unsafe"
            else:
                row["status"] = "ended"
                row["quote_en"] = "no supported numerical turnout estimate recovered"
            row["note"] = (f"3 Sep 2026 audit: action evidence screened, but no supported numerical turnout estimate was recovered. "
                           f"Documented action dates: {len(dates)}; {row['first_day'] or 'unresolved'} to {row['last_day'] or 'unresolved'}. Blank is not zero.")
        if city != "Kherson":
            row["status"] = "ended"
        result.append(row)
        changed = {k: {"original": original.get(k), "final": row.get(k)} for k in row if original.get(k) != row.get(k)}
        ledger.append({
            "city": city, "audit_verdict": "corrected" if changed else "verified",
            "original": original, "final": row, "changed_fields": changed,
        })
    return result, ledger


def main():
    base_pubs = read_csv(BASE / "publications.csv")
    base_daily = read_csv(BASE / "by_day.csv")
    base_cities = read_csv(BASE / "cities.csv")
    sources = {s["source_id"]: s for s in json.loads((AUDIT / "sources.json").read_text(encoding="utf-8"))}
    daily = decision_map()
    missing_sources = sorted({source_id(r["link"]) for r in base_pubs} - set(sources))
    missing_reviews = sorted({source_id(r["link"]) for r in base_pubs} - set(REVIEWS))
    if missing_sources or missing_reviews:
        raise ValueError({"missing_sources": missing_sources, "missing_reviews": missing_reviews})

    final_pubs, pub_dates, pub_ledger = make_publications(base_pubs, sources, daily)
    final_daily, daily_ledger = make_daily(base_daily, daily, base_pubs, sources)
    final_cities, city_ledger = make_cities(base_cities, daily, daily_ledger, final_pubs, pub_dates, base_pubs, sources)

    schemas = {
        "by_day.csv": list(base_daily[0]),
        "cities.csv": list(base_cities[0]),
        "publications.csv": list(base_pubs[0]),
    }
    files = []
    for name, rows, sheet_name in (
        ("by_day.csv", final_daily, "ByDay"),
        ("cities.csv", final_cities, "Cities"),
        ("publications.csv", final_pubs, "Publications"),
    ):
        headers = schemas[name]
        files.append({
            "name": name, "sheetName": sheet_name, "headers": headers,
            "rows": [[row.get(h, "") for h in headers] for row in rows],
            "lastColumn": a1_col(len(headers)),
            "outputPath": str((DS / name).resolve()),
        })
    payload = {"files": files}
    dump(ROOT / "scratch/audit_workbook/audit_render_payload.json", payload)

    source_ledger = []
    baseline_sids = {source_id(r["link"]) for r in base_pubs}
    used_sids = baseline_sids | {x["source_id"] for x in daily_ledger} | {source_id(r["link"]) for r in final_pubs}
    for sid in sorted(sources):
        s = sources[sid]
        review = REVIEWS.get(sid, {})
        if sid in baseline_sids:
            role = "baseline_source"
            outcome = review.get("outcome")
        elif sid in used_sids:
            role = "targeted_recovery_used"
            outcome = "targeted_recovery_used"
        else:
            role = "targeted_discovery_not_selected"
            outcome = "targeted_discovery_not_selected"
        source_ledger.append({
            "source_id": sid, "requested_url": s.get("requested_url"), "final_url": s.get("final_url"),
            "retrieved_at": s.get("retrieved_at"), "http_status": s.get("http_status"),
            "body_sha256": s.get("body_sha256"), "body_hash_encoding": s.get("body_hash_encoding"),
            "body_file_sha256": s.get("body_file_sha256"), "raw_sha256": s.get("raw_sha256"),
            "evidence_method": s.get("evidence_method"), "scope_role": role,
            "review_outcome": outcome, "review_notes": review.get("notes", ""),
            "body_available": bool(body_for(s)),
        })

    outcomes = Counter(x["screening_outcome"] for x in pub_ledger)
    daily_outcomes = Counter(x["verdict"] for x in daily_ledger)
    source_outcomes = Counter(x["review_outcome"] for x in source_ledger)
    summary = {
        "audit_date": AUDIT_DATE,
        "event_window": {"start": START.isoformat(), "end": END.isoformat()},
        "publication_cutoff": "2026-09-01",
        "baseline": {
            "numeric_city_days": sum(1 for r in base_daily for k, v in r.items() if k != "city" and v),
            "cities": len(base_cities), "publication_city_records": len(base_pubs),
            "raw_urls": len({r["link"] for r in base_pubs}),
            "normalized_sources": len(baseline_sids),
            "unknown_records_screened": sum(r["category"] == "unknown" for r in base_pubs),
            "raw_url_count_note": "The preserved baseline recount is538 exact URL strings, rather than537 stated in the plan;536 normalized sources. No baseline rows were altered to force the planned count.",
        },
        "final": {
            "numeric_city_days": sum(1 for r in final_daily for k, v in r.items() if k != "city" and v != ""),
            "cities": len(final_cities), "publication_city_records": len(final_pubs),
            "added_run_3_sep": sum(r["run"] == "3 Sep" for r in final_pubs),
        },
        "daily_verdicts": dict(sorted(daily_outcomes.items())),
        "publication_screening": dict(sorted(outcomes.items())),
        "source_review_outcomes": dict(sorted(source_outcomes.items())),
        "unresolved_sources": [x for x in source_ledger if x["scope_role"] == "baseline_source" and
                               (x["review_outcome"].startswith("unresolved") or not x["body_available"])],
        "scope_note": "Targeted recovery of evidence gaps; this audit does not claim exhaustive news coverage.",
    }
    small_passages = []
    for sid, paragraph in sorted(SMALL_COUNT_REVIEWS):
        source = sources[sid]
        candidates = {x["paragraph"]: x for x in candidate_passages(body_for(source), True)
                      if x not in candidate_passages(body_for(source), False)}
        if paragraph not in candidates:
            raise ValueError(f"small-number review no longer matches capture: {sid} paragraph {paragraph}")
        verdict, reason = SMALL_COUNT_REVIEWS[(sid, paragraph)]
        small_passages.append({"source_id": sid, "paragraph": paragraph,
                               "exact_passage": candidates[paragraph]["text"],
                               "context": candidates[paragraph]["context"],
                               "manual_verdict": verdict, "reason": reason})
    if len(small_passages) != 23:
        raise ValueError(f"expected 23 supplemental small-number passages, got {len(small_passages)}")

    dump(AUDIT / "audit_ledger.json", {
        "version": "2026-09-03", "summary": summary,
        "daily_estimates": daily_ledger, "city_summaries": city_ledger,
        "publication_records": pub_ledger, "sources": source_ledger,
        "supplemental_small_number_screening": small_passages,
    })
    dump(AUDIT / "audit_summary.json", summary)

    unresolved = summary["unresolved_sources"]
    md = [
        "# Targeted full audit — 3 September 2026", "",
        "The audit preserves the 16 July–29 August event window and the 1 September publication cutoff. "
        "3 September is the audit date, not an extension of news coverage.", "",
        "## Reconciliation", "",
        f"- Baseline: {summary['baseline']['numeric_city_days']} numeric city-days, {summary['baseline']['cities']} cities, "
        f"{summary['baseline']['publication_city_records']} publication×city records, {summary['baseline']['raw_urls']} distinct raw URLs.",
        f"- Final: {summary['final']['numeric_city_days']} numeric city-days, {summary['final']['cities']} cities, "
        f"{summary['final']['publication_city_records']} publication×city records.",
        f"- New audit-run evidence rows: {summary['final']['added_run_3_sep']}.",
        f"- Daily verdicts: {', '.join(f'{k} {v}' for k, v in summary['daily_verdicts'].items())}.",
        f"- Publication screening: {', '.join(f'{k} {v}' for k, v in summary['publication_screening'].items())}.", "",
        "## Unresolved evidence", "",
        f"{len(unresolved)} sources remain inaccessible or unresolved. They are preserved in the baseline and source ledger; "
        "unsupported canonical daily cells are blank rather than zero.", "",
        "## Scope", "",
        summary["scope_note"], "",
        "## Reproduction and validation", "",
        "Run `python audit_finalize.py`, author the CSV payload with `node audit_tools/audit_csv_builder.mjs`, "
        "then run `python -m unittest test_audit_full.py -v`, `python validate_audit.py`, and "
        "`python check_consistency.py data\\2026-07-16-fedorov`. The finalizer and CSV builder are idempotent.", "",
        "The immutable `baseline/` directory and `baseline_manifest.json` preserve all starting files and hashes. "
        "`audit_ledger.json` contains every daily, city, publication and source verdict, plus the manual 23-passage small-number screen.", "",
        "The latest executed-check record is `validation_results.json`.", "",
    ]
    (AUDIT / "README.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
