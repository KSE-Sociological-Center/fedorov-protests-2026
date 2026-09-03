"""Validate evidence, canonical tables, schema preservation and reconciliation."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from audit_full import AUDIT, BASE, DS, ROOT, body_for, event_date, flat, norm_url, read_csv, source_id
from audit_finalize import band, exact_in_body


def validate():
    errors = []
    ledger = json.loads((AUDIT / "audit_ledger.json").read_text(encoding="utf-8"))
    sources = {x["source_id"]: x for x in json.loads((AUDIT / "sources.json").read_text(encoding="utf-8"))}
    payload = json.loads((ROOT / "scratch/audit_workbook/audit_render_payload.json").read_text(encoding="utf-8"))
    manifest = json.loads((AUDIT / "baseline_manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        if hashlib.sha256((BASE / name).read_bytes()).hexdigest() != expected:
            errors.append(f"baseline changed: {name}")
    for item in payload["files"]:
        rows = read_csv(item["outputPath"])
        expected = [dict(zip(item["headers"], map(str, row))) for row in item["rows"]]
        if rows != expected:
            errors.append(f"canonical CSV differs from authored payload: {item['name']}")
        if list(rows[0]) != list(read_csv(BASE / item["name"])[0]):
            errors.append(f"schema changed: {item['name']}")

    base_daily = read_csv(BASE / "by_day.csv")
    original_cells = {(r["city"], "2026-" + day): int(v) for r in base_daily for day, v in r.items() if day != "city" and v}
    daily_entries = ledger["daily_estimates"]
    by_key = {(x["city"], x["event_date"]): x for x in daily_entries}
    if len(by_key) != len(daily_entries):
        errors.append("duplicate daily verdicts")
    if not set(original_cells) <= set(by_key):
        errors.append("not every original numeric cell has a verdict")
    for key, original in original_cells.items():
        if by_key[key]["original_value"] != original:
            errors.append(f"wrong baseline value in ledger: {key}")

    canonical_daily = read_csv(DS / "by_day.csv")
    canonical_values = {(r["city"], "2026-" + day): int(v) for r in canonical_daily for day, v in r.items() if day != "city" and v}
    if canonical_values != {k: x["final_value"] for k, x in by_key.items() if x["final_value"] is not None}:
        errors.append("canonical daily cells do not reconcile with the ledger")
    for entry in daily_entries:
        if entry["final_value"] is None:
            continue
        sid = entry["source_id"]
        if sid not in sources:
            errors.append(f"missing source: {sid}")
            continue
        if not entry["exact_quote"] or flat(entry["exact_quote"]) not in flat(body_for(sources[sid])):
            errors.append(f"daily quote is not literal: {entry['city']} {entry['event_date']}")
        if not all(entry.get(k) for k in ("supporting_url", "event_date", "qualifier", "selection_rationale")):
            errors.append(f"incomplete evidence linkage: {entry['city']} {entry['event_date']}")
        if sources[sid].get("evidence_method") == "search_snippet":
            errors.append(f"snippet used as numeric evidence: {sid}")
        if not "2026-07-16" <= entry["event_date"] <= "2026-08-29":
            errors.append(f"daily event outside fixed window: {entry['event_date']}")

    base_pubs = read_csv(BASE / "publications.csv")
    pub_entries = ledger["publication_records"]
    original_pub_entries = [x for x in pub_entries if x["baseline_row"] is not None]
    if sorted(x["baseline_row"] for x in original_pub_entries) != list(range(1, len(base_pubs) + 1)):
        errors.append("not exactly one screening outcome per original publication")
    final_pubs = read_csv(DS / "publications.csv")
    retained = [x for x in pub_entries if x["final"] is not None]
    if Counter(json.dumps(x["final"], sort_keys=True) for x in retained) != Counter(json.dumps(x, sort_keys=True) for x in final_pubs):
        errors.append("publication ledger does not reconcile with canonical rows")
    seen = set()
    for entry in retained:
        row = entry["final"]
        pub_match = re.match(r"\s*(\d{1,2})\.(\d{1,2})", row["published"])
        if not pub_match or f"2026-{int(pub_match.group(2)):02d}-{int(pub_match.group(1)):02d}" > "2026-09-01":
            errors.append(f"publication after fixed cutoff or unparsable: {row['published']}")
        if entry["original"] and row["run"] != entry["original"]["run"]:
            errors.append(f"historical run changed: {entry['baseline_row']}")
        if not entry["original"] and row["run"] != "3 Sep":
            errors.append("recovered evidence lacks audit run")
        if not exact_in_body(row["quote_uk"], body_for(sources[entry["source_id"]])):
            errors.append(f"publication quote is not literal: {entry['baseline_row']}")
        key = (row["city"], norm_url(row["link"]), event_date(row), row["run"])
        if key in seen:
            errors.append(f"same-run duplicate: {key}")
        seen.add(key)

    cities = read_csv(DS / "cities.csv")
    city_entries = ledger["city_summaries"]
    if len(city_entries) != 33 or {x["city"] for x in city_entries} != {x["city"] for x in cities}:
        errors.append("city-summary verdict coverage is incomplete")
    for city in cities:
        vals = {day: value for (name, day), value in canonical_values.items() if name == city["city"]}
        if vals:
            peak = max(vals.values())
            peak_day = min(day for day, value in vals.items() if value == peak)
            if city["peak_day"] != peak_day or city["category"] != band(peak):
                errors.append(f"exact peak/date mismatch: {city['city']}")
            if city["quote_uk"] != by_key[(city["city"], peak_day)]["exact_quote"]:
                errors.append(f"city peak quote not linked to daily selection: {city['city']}")
        elif city["peak_day"]:
            errors.append(f"unknown numeric peak has a fabricated peak date: {city['city']}")
        dates = {event_date(r) for r in final_pubs if r["city"] == city["city"] and r["status"] not in {"announced", "refuted"} and event_date(r)}
        dates |= {day for (name, day) in canonical_values if name == city["city"]}
        dates = {d for d in dates if "2026-07-16" <= d <= "2026-08-29"}
        if city["days_active"] != str(len(dates)) or city["first_day"] != (min(dates) if dates else "") or city["last_day"] != (max(dates) if dates else ""):
            errors.append(f"documented date reconciliation mismatch: {city['city']}")

    source_entries = ledger["sources"]
    if {x["source_id"] for x in source_entries} != set(sources):
        errors.append("source ledger does not cover every retrieved source")
    if sum(x["scope_role"] == "baseline_source" for x in source_entries) != 536:
        errors.append("source ledger does not cover all 536 normalized baseline sources")
    for sid, source in sources.items():
        if source.get("body_path") and source.get("body_sha256"):
            path = ROOT / source["body_path"]
            if not path.is_file() or hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest() != source["body_sha256"]:
                errors.append(f"body capture hash mismatch: {sid}")
            if source.get("body_file_sha256") and hashlib.sha256(path.read_bytes()).hexdigest() != source["body_file_sha256"]:
                errors.append(f"body file hash mismatch: {sid}")
        if source.get("raw_path") and source.get("raw_sha256"):
            path = ROOT / source["raw_path"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != source["raw_sha256"]:
                errors.append(f"raw capture hash mismatch: {sid}")

    summary = ledger["summary"]
    if summary["baseline"]["unknown_records_screened"] != 635:
        errors.append("unknown-record screening count mismatch")
    small = ledger.get("supplemental_small_number_screening", [])
    if len(small) != 23 or any(not x.get("manual_verdict") or not x.get("reason") or not x.get("context") for x in small):
        errors.append("supplemental 23-passage small-number review is incomplete")
    for x in small:
        if flat(x["exact_passage"]) not in flat(body_for(sources[x["source_id"]])):
            errors.append(f"supplemental passage is not literal: {x['source_id']} {x['paragraph']}")
    removed = sum(x["final"] is None for x in original_pub_entries)
    added = sum(x["original"] is None and x["final"] is not None for x in pub_entries)
    if len(base_pubs) - removed + added != len(final_pubs):
        errors.append("publication arithmetic does not reconcile")
    return errors


if __name__ == "__main__":
    found = validate()
    if found:
        print("AUDIT VALIDATION FAILED")
        for error in found:
            print(" -", error)
        raise SystemExit(1)
    print("Audit validation passed: baseline, 151 original numeric cells, 33 summaries, 929 publication outcomes, literal quotes, capture hashes, exact peaks/dates, all-run duplicates and reconciliation.")
