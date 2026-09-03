# Targeted full audit — 3 September 2026

The audit preserves the 16 July–29 August event window and the 1 September publication cutoff. 3 September is the audit date, not an extension of news coverage.

## Reconciliation

- Baseline: 151 numeric city-days, 33 cities, 929 publication×city records, 538 distinct raw URLs.
- Final: 200 numeric city-days, 33 cities, 890 publication×city records.
- New audit-run evidence rows: 15.
- Daily verdicts: corrected 11, normalized_retained 8, recovered 52, unsupported_blank 3, verified_retained 129.
- Publication screening: added_recovered_evidence 15, corrected 468, removed_duplicate 41, removed_unrelated 13, screened_no_numeric_count 287, unresolved_retained 44, verified 76.

## Unresolved evidence

25 sources remain inaccessible or unresolved. They are preserved in the baseline and source ledger; unsupported canonical daily cells are blank rather than zero.

## Scope

Targeted recovery of evidence gaps; this audit does not claim exhaustive news coverage.

## Reproduction and validation

Run `python audit_finalize.py`, author the CSV payload with `node audit_tools/audit_csv_builder.mjs`, then run `python -m unittest test_audit_full.py -v`, `python validate_audit.py`, and `python check_consistency.py data\2026-07-16-fedorov`. The finalizer and CSV builder are idempotent.

The immutable `baseline/` directory and `baseline_manifest.json` preserve all starting files and hashes. `audit_ledger.json` contains every daily, city, publication and source verdict, plus the manual 23-passage small-number screen.

The latest executed-check record is `validation_results.json`.
