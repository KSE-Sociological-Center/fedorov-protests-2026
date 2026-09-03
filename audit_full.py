"""Reproducible evidence retrieval and screening; never infer a crowd count.

Run init, fetch, screen. Human decisions are stored separately from suggestions.
Full publisher bodies stay in git-ignored scratch; short evidence is in the ledger.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent
DS = ROOT / "data/2026-07-16-fedorov"
AUDIT = DS / "audit/2026-09-03"
BASE = AUDIT / "baseline"
CACHE = ROOT / "scratch/audit_2026-09-03"
TRACKING = {"fbclid", "gclid", "yclid"}
CITY_UA = dict(zip(
    "Kyiv|Kharkiv|Dnipro|Lviv|Odesa|Ivano-Frankivsk|Ternopil|Khmelnytskyi|Lutsk|Cherkasy|Vinnytsia|Poltava|Zaporizhzhia|Kropyvnytskyi|Uzhhorod|Rivne|Mykolaiv|Chernivtsi|Zhytomyr|Sumy|Kolomyia|Chernihiv|Kryvyi Rih|Kremenchuk|Kherson|Mukachevo|Kamianske|Uman|Izmail|Kalush|Sheptytskyi|Oleksandriia|Kamianets-Podilskyi".split("|"),
    "Київ|Харків|Дніпро|Львів|Одеса|Івано-Франківськ|Тернопіль|Хмельницький|Луцьк|Черкаси|Вінниця|Полтава|Запоріжжя|Кропивницький|Ужгород|Рівне|Миколаїв|Чернівці|Житомир|Суми|Коломия|Чернігів|Кривий Ріг|Кременчук|Херсон|Мукачево|Кам'янське|Умань|Ізмаїл|Калуш|Шептицький|Олександрія|Кам'янець-Подільський".split("|")))
COUNT_RE = re.compile(r"(?:\d[\d\s.,–−-]{0,12}|сот\w*|тисяч\w*|десятк\w*|двадцят\w*|тридцят\w*|сорок\w*|п.?ятдесят\w*|шістдесят\w*|сімдесят\w*|вісімдесят\w*|дев.?яност\w*|пів\s*сот\w*|ста|сто|двохсот|кількасот).{0,90}(?:люд\w*|учасник\w*|містян\w*|активіст\w*|протестуваль\w*|мітингуваль\w*|осіб|осо\w*|жител\w*|мешкан\w*|львів.?ян\w*|киян\w*|житомирян\w*)", re.I)
COUNT_RE = re.compile(r"(?<!\w)" + COUNT_RE.pattern, re.I)
PEOPLE = r"(?:люд\w*|учасник\w*|містян\w*|громадян\w*|активіст\w*|протестуваль\w*|мітингуваль\w*|осіб|особ\w*|жител\w*|мешкан\w*|дніпрян\w*|чернівчан\w*|тернополян\w*|рівнян\w*|полтавц\w*|харків.?ян\w*|львів.?ян\w*|киян\w*|житомирян\w*)"
NUMERAL = r"(?:\d[\d\s.,–−-]{0,12}|сот\w*|тисяч\w*|десятк\w*|десять|десяти|одинадцят\w*|дванадцят\w*|тринадцят\w*|чотирнадцят\w*|п.?ятнадцят\w*|шістнадцят\w*|сімнадцят\w*|вісімнадцят\w*|дев.?ятнадцят\w*|двадцят\w*|тридцят\w*|сорок\w*|п.?ятдесят\w*|шістдесят\w*|сімдесят\w*|вісімдесят\w*|дев.?яност\w*|ста|сто|двохсот|кількасот|одиночн\w*)"
SMALL_NUMERAL = r"(?:один|одна|одну|одного|двоє|двох|дві|два|троє|трьох|три|четверо|чотири|чотирьох|п.?ятеро|п.?ять|шестеро|шість|семеро|сім|восьмеро|вісім|дев.?ятеро|дев.?ять)"
SMALL_COUNT_RE = re.compile(r"(?<!\w)" + SMALL_NUMERAL + r"(?!\w)(?:\s+(?!з\b|із\b)\w+){0,1}\s+" + PEOPLE, re.I)
EXTRA_COUNT_RE = re.compile(r"(?<!\w)(?:" + NUMERAL + r").{0,90}" + PEOPLE + r"|" + PEOPLE + r".{0,45}(?<!\w)" + NUMERAL, re.I)
EVENT_RE = re.compile(r"Федоров|протест|мітинг|акці|картон|пікет|ход[аіу]", re.I)

def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def flat(text):
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()

def norm_url(value):
    p = urlsplit(html.unescape(value.strip()))
    host = p.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+", "/", p.path).rstrip("/")
    if host == "suspilne.media":
        path = re.sub(r"^/amp/", "/", path)
    path = re.sub(r"/amp$", "", path)
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
         if not k.lower().startswith("utm_") and k.lower() not in TRACKING
         and not (k.lower() == "amp" and v.lower() in {"", "1", "true"})
         and not (k.lower() == "output" and v.lower() == "amp")]
    return urlunsplit(("https", host, path, urlencode(sorted(q)), ""))

def event_date(row):
    value = row.get("published", "")
    if re.search(r"подія\s+не датована", value, re.I):
        return None
    m = re.search(r"подія\s+(\d{1,2})\.(\d{1,2})", value, re.I)
    if not m:
        m = re.match(r"\s*(\d{1,2})\.(\d{1,2})", value)
    if not m:
        return None
    try:
        year = re.search(r"\b(20\d\d)\b", value)
        return date(int(year.group(1)) if year else 2026, int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None

def source_id(url):
    return hashlib.sha256(norm_url(url).encode()).hexdigest()[:20]

def init():
    AUDIT.mkdir(parents=True, exist_ok=True)
    BASE.mkdir(exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    files = {name: DS / name for name in ("publications.csv", "cities.csv", "by_day.csv", "meta.json", "prose.md")}
    files.update({"README.md": ROOT / "README.md", "prompt.md": ROOT / "prompt.md"})
    for name, src in files.items():
        target = BASE / name
        if not target.exists():
            shutil.copy2(src, target)
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.iterdir() if p.is_file()}
    prior = AUDIT / "baseline_manifest.json"
    if prior.exists():
        assert json.loads(prior.read_text(encoding="utf-8")) == manifest, "Baseline was modified"
    else:
        dump(prior, manifest)
    print("Baseline preserved:", len(manifest), "files")

def source_urls():
    grouped = defaultdict(list)
    for row in read_csv(BASE / "publications.csv") + read_csv(BASE / "cities.csv"):
        url = row["link"]
        if url not in grouped[norm_url(url)]:
            grouped[norm_url(url)].append(url)
    return grouped

def extract(raw, url, encoding):
    from bs4 import BeautifulSoup
    import trafilatura
    soup = BeautifulSoup(raw.decode(encoding or "utf-8", errors="replace"), "html.parser")
    headline = flat((soup.find("h1") or soup.find("title")).get_text(" ")) if (soup.find("h1") or soup.find("title")) else ""
    canon = soup.find("link", rel="canonical")
    dates = [x.get("content") for x in soup.find_all("meta")
             if x.get("property", x.get("name", "")) in {"article:published_time", "date", "datePublished", "pubdate"}]
    dates += re.findall(r'"datePublished"\s*:\s*"([^"\\]+)"', str(soup))
    dates = list(dict.fromkeys(dates))
    main = trafilatura.extract(raw, url=url, output_format="txt", include_comments=False,
                              include_tables=True, favor_precision=True) or ""
    if not main:
        node = soup.select_one('[itemprop="articleBody"],article,main')
        if node:
            for item in node.select("script,style,nav,aside,footer"):
                item.decompose()
            main = node.get_text("\n", strip=True)
    return {"headline": headline, "canonical": canon.get("href", "") if canon else "",
            "published_metadata": dates, "body": main}


def enrich():
    """Read saved raw captures only; do not refetch or alter historical bodies."""
    sources = json.loads((AUDIT/"sources.json").read_text(encoding="utf-8"))
    for s in sources:
        if s.get("body_path") and (ROOT/s["body_path"]).is_file():
            s["body_hash_encoding"] = "UTF-8 text; universal newline normalization"
            s["body_file_sha256"] = hashlib.sha256((ROOT/s["body_path"]).read_bytes()).hexdigest()
        if s.get("raw_path") and s.get("http_status") == 200:
            raw = (ROOT/s["raw_path"]).read_text(encoding="utf-8", errors="replace")
            extra = re.findall(r'"datePublished"\s*:\s*"([^"\\]+)"', raw)
            s["published_metadata"] = list(dict.fromkeys(s.get("published_metadata", []) + extra))
            s["modified_metadata"] = list(dict.fromkeys(re.findall(r'"dateModified"\s*:\s*"([^"\\]+)"', raw)))
    dump(AUDIT/"sources.json", sources)

def fetch_one(url):
    import requests
    key = source_id(url)
    meta_path = CACHE / f"{key}.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    result = {"source_id": key, "requested_url": url,
              "retrieved_at": datetime.now(timezone.utc).isoformat(), "http_status": None,
              "error": "", "final_url": "", "body_path": "", "body_sha256": ""}
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.5"},
                         timeout=(10, 25), allow_redirects=True)
        result.update(http_status=r.status_code, final_url=r.url)
        raw_path = CACHE / f"{key}.html"
        raw_path.write_bytes(r.content)
        result["raw_path"] = str(raw_path.relative_to(ROOT))
        result["raw_sha256"] = hashlib.sha256(r.content).hexdigest()
        if r.status_code == 200:
            enc = r.encoding
            if not enc or enc.lower() in {"iso-8859-1", "ascii"}:
                enc = r.apparent_encoding
            got = extract(r.content, r.url, enc)
            body = got.pop("body")
            result.update(got)
            body_path = CACHE / f"{key}.txt"
            body_path.write_text(body, encoding="utf-8")
            result.update(body_path=str(body_path.relative_to(ROOT)), body_sha256=hashlib.sha256(body.encode()).hexdigest(), body_chars=len(body))
    except Exception as exc:
        result["error"] = str(exc)
    dump(meta_path, result)
    return result

def fetch_all():
    grouped = source_urls()
    urls = [sorted(v, key=lambda x: ("/amp" in x, len(x)))[0] for v in grouped.values()]
    manifest = AUDIT / "sources.json"
    preserved = {s["source_id"]: s for s in json.loads(manifest.read_text(encoding="utf-8"))} if manifest.exists() else {}
    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = [pool.submit(fetch_one, u) for u in urls]
        for job in as_completed(jobs):
            result = job.result()
            # A rerun must not discard recovered bodies or targeted additions.
            result.update(preserved.get(result["source_id"], {}))
            results.append(result)
            if len(results) % 40 == 0:
                print("Retrieved", len(results), "/", len(urls), flush=True)
    preserved.update({s["source_id"]: s for s in results})
    dump(manifest, sorted(preserved.values(), key=lambda r: r["source_id"]))
    print("HTTP outcomes", Counter(r["http_status"] for r in results))


def add_sources(urls):
    """Targeted recovery sources; keep them separate from original coverage."""
    sources = {s["source_id"]: s for s in json.loads((AUDIT / "sources.json").read_text(encoding="utf-8"))}
    for url in urls:
        sid = source_id(url)
        if sid not in sources:
            s = fetch_one(url)
            s.update(evidence_method="direct_http", discovery="targeted_audit_gap", audit_date="2026-09-03")
            sources[sid] = s
        print(sid, sources[sid].get("http_status"), url)
    dump(AUDIT / "sources.json", sorted(sources.values(), key=lambda s: s["source_id"]))

def body_for(source):
    p = ROOT / source.get("body_path", "")
    value = p.read_text(encoding="utf-8") if p.is_file() else ""
    return "" if re.search(r"^URL .*?(?:not safe to open|cannot be opened)|^iframe$", value.strip()) else value

def recover():
    sources = json.loads((AUDIT / "sources.json").read_text(encoding="utf-8"))
    historical = {}
    old = ROOT / "scratch/update_2026-09-01"
    for name in ("candidates.csv", "review.csv"):
        if not (old / name).exists():
            continue
        for row in read_csv(old / name):
            url = row.get("final_url") or row.get("url")
            path = row.get("text_path", "")
            if url and path and (ROOT / path).is_file():
                historical[norm_url(url)] = path
    for s in sources:
        s.setdefault("evidence_method", "direct_http")
        if body_for(s):
            continue
        path = CACHE / ("web-" + s["source_id"] + ".txt")
        raw = path.read_text(encoding="utf-8") if path.exists() else ""
        lines = re.findall(r"L\d+: ?(.*?)(?=L\d+:|$)", raw, re.S)
        if lines and not re.search(r"is not safe to open|cannot be opened", raw) and not (len(lines) == 1 and flat(lines[0]) == "iframe"):
            clean = []
            for line in lines:
                line = re.sub(r"cite[^†\n]+†([^†]+)(?:†[^]+)?", r"\1", line)
                line = re.sub(r"[^]*", "", line)
                line = flat(line)
                if line:
                    clean.append(line)
            start = next((i for i, p in enumerate(clean) if p.startswith("# ")), 0)
            clean = clean[start:]
            body = "\n".join(clean)
            target = CACHE / ("recovered-" + s["source_id"] + ".txt")
            target.write_text(body, encoding="utf-8")
            s.update(body_path=str(target.relative_to(ROOT)), body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                     body_chars=len(body), evidence_method="web_open", recovery_raw_path=str(path.relative_to(ROOT)),
                     recovery_retrieved_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat())
            if clean and clean[0].startswith("# "):
                s["headline"] = clean[0][2:]
        elif norm_url(s["requested_url"]) in historical:
            prior = ROOT / historical[norm_url(s["requested_url"]) ]
            body = prior.read_text(encoding="utf-8")
            s.update(body_path=str(prior.relative_to(ROOT)), body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                     body_chars=len(body), evidence_method="historical_cache", historical_file_mtime=datetime.fromtimestamp(prior.stat().st_mtime, timezone.utc).isoformat())
        else:
            s["evidence_method"] = "unavailable"
            s["body_path"] = ""
            s["body_chars"] = 0
            s["body_sha256"] = ""
    dump(AUDIT / "sources.json", sources)
    print("Evidence methods", Counter(s["evidence_method"] for s in sources))

def city_patterns():
    gaz = {r["city"]: r for r in read_csv(ROOT / "gazetteer.csv")}
    patterns = {}
    for c in read_csv(BASE / "cities.csv"):
        g = gaz.get(CITY_UA[c["city"]], {})
        pattern = (g.get("regex") or g.get("stems") or CITY_UA[c["city"]]) + "|" + re.escape(c["city"])
        patterns[c["city"]] = re.compile(pattern, re.I)
    return patterns

def candidate_passages(body, include_small=True):
    paras = [flat(x) for x in body.splitlines() if flat(x)]
    out = []
    for i, p in enumerate(paras):
        probe = re.sub(r"\b\d{1,3}[- ]річн\w*|\b\d+[- ]?[йя]?(?: день| дня)", "", p, flags=re.I)
        probe = re.sub(r"\b\d{1,2}\s+(?:липня|серпня|вересня|січня|лютого|березня|квітня|травня|червня)|\b\d{1,2}:\d{2}\b|\b20\d\d\s+рок\w*", "", probe, flags=re.I)
        if COUNT_RE.search(probe) or EXTRA_COUNT_RE.search(probe) or (include_small and SMALL_COUNT_RE.search(probe)):
            out.append({"paragraph": i, "text": p,
                        "context": "\n".join(paras[max(0, i-1):i+2])})
    return out

def screen():
    sources = {s["source_id"]: s for s in json.loads((AUDIT / "sources.json").read_text(encoding="utf-8"))}
    rows = read_csv(BASE / "publications.csv")
    patterns = city_patterns()
    body_cache = {k: body_for(s) for k, s in sources.items()}
    passage_cache = {k: candidate_passages(b) for k, b in body_cache.items()}
    seen = {}
    screens = []
    for i, row in enumerate(rows, 1):
        sid = source_id(row["link"])
        body = body_cache.get(sid, "")
        text = flat(body)
        q = flat(row["quote_uk"])
        key = (row["city"], norm_url(row["link"]), row["run"])
        duplicate_of = seen.get(key)
        seen.setdefault(key, i)
        match = "not_applicable" if q.lower() in {"невідомо", "unknown", "цифри немає", ""} else ("exact" if q in text else "mismatch")
        if match == "mismatch" and q.strip('«»"') in text:
            match = "outer_quote_marks"
        passages = [p for p in passage_cache.get(sid, []) if patterns[row["city"]].search(p["context"])]
        screens.append({"row_id": i, "city": row["city"], "event_date": event_date(row), "source_id": sid,
                        "run": row["run"], "category": row["category"], "quote_match": match,
                        "city_mentioned": bool(patterns[row["city"]].search(body)),
                        "event_words": bool(EVENT_RE.search(body)), "body_available": bool(body),
                        "duplicate_of": duplicate_of, "candidate_passages": passages,
                        "unassigned_count_candidates": len(passage_cache.get(sid, [])) - len(passages),
                        "screening_outcome": "duplicate_candidate" if duplicate_of else
                        "unavailable" if not body else "manual_review" if passage_cache.get(sid) or match == "mismatch" else "no_count_candidate"})
    dump(AUDIT / "publication_screen.json", screens)
    by_cd = defaultdict(list)
    for s in screens:
        if s["event_date"]:
            by_cd[(s["city"], s["event_date"])].append(s)
    cells = []
    for row in read_csv(BASE / "by_day.csv"):
        for day, value in row.items():
            if day == "city" or not value:
                continue
            candidates = by_cd[(row["city"], "2026-" + day)]
            cells.append({"city": row["city"], "date": "2026-"+day, "original": int(value),
                          "rows": [s["row_id"] for s in candidates],
                          "sources": sorted(set(s["source_id"] for s in candidates))})
    dump(AUDIT / "daily_candidates.json", cells)
    dump(CACHE / "passages.json", passage_cache)
    print("Publication outcomes", Counter(s["screening_outcome"] for s in screens))
    print("Quote matches", Counter(s["quote_match"] for s in screens))
    print("Daily cells", len(cells))
    print("Unique count-bearing sources", sum(bool(p) for p in passage_cache.values()))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["init", "fetch", "screen", "recover", "add", "enrich"])
    parser.add_argument("urls", nargs="*")
    args = parser.parse_args()
    if args.action == "add":
        add_sources(args.urls)
    else:
        {"init": init, "fetch": fetch_all, "screen": screen, "recover": recover, "enrich": enrich}[args.action]()

if __name__ == "__main__":
    main()
