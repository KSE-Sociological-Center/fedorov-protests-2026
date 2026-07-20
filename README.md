# fedorov-protests-2026

A dataset of the protests that followed Mykhailo Fedorov's departure from the post of Minister of Defence of Ukraine, compiled from media reports. Contains the collection prompt, the data, and scripts that generate the map and the report.

Event dates: 16–19 July 2026 (ongoing). The protests are known as «cardboard protests» after the handwritten signs their participants carried.

Everything is in English **except verbatim quotes**, which stay in the original Ukrainian: the `quote_uk` column is defined as the outlet's exact words, and translating a quote turns evidence into paraphrase. English glosses live alongside in `quote_en`. Headlines are likewise kept as published.

## 1. Data source

**Population.** Publications by Ukrainian media (national, regional, local) covering protests connected to Fedorov leaving office. English-language agencies (Interfax-Ukraine, Kyiv Post, AFP, AP) are included to cross-check the Kyiv figure.

**Period.** 15–19 July 2026. Latest run 19 July 2026; the wave is in its fourth day and ongoing.

**Unit of observation.** Publication × city. A publication covering several cities yields several rows.

**Size.** 150 publications, 62 domains, 28 locations.

**Sampling.** Three independent procedures:

1. Parsing national round-ups and live blogs (Suspilne, TSN, NV, Ukrainska Pravda, LB, RBC, Detector Media, Censor.NET, Glavcom, 24 Kanal, ZAXID, ZN.UA, KP.UA), which enumerate cities themselves.
2. Direct retrieval from Suspilne's regional desks (22 sections) and local outlets, for every city found in step 1.
3. A gazetteer sweep: 499 Ukrainian city names from Wikidata queried through Google News, requiring the name in the headline. Validated on Kremenchuk, which the procedure finds independently. Coverage: cities ≥30k. Yield beyond procedures 1–2: Kolomyia (day 1) and Uman (day 4, surfaced by re-running the grep over the day-4 round-ups — see §5).

**Text retrieval.** Raw page (`curl`), tags stripped, quote located by literal string match. Search-engine snippets and summarizer models were not used as a source of figures. See §3.6.

## 2. Variables

### `cities.csv` — unit: location (N = 28)

| Variable | Type | Domain / example |
|---|---|---|
| `city` | text | Kyiv, Kharkiv, … |
| `oblast` | text | Kyiv City, Kharkiv, … |
| `lat`, `lon` | float | coordinates, WGS84 |
| `category` | categorical | `1000+` · `100–999` · `<100` · `unknown` · `online` |
| `quote_uk` | text | verbatim, as published: «близько 300 людей, їхня кількість збільшується» |
| `quote_en` | text | English gloss: "about 300 people, and their number is growing" |
| `time` | time | the moment the figure is valid for |
| `source` | text | outlet plus attribution: Suspilne Kharkiv (police spokesperson Liudmyla Prokopenko) |
| `link` | URL | the specific publication |
| `contested` | binary | `yes` (4) · `no` (24) |
| `status` | categorical | `ended` (16) · `took place` (11) · `online` (1) |
| `note` | text | justification for the assigned category; conflicting versions |

### `publications.csv` — unit: publication × city (N = 150)

| Variable | Type | Domain / example |
|---|---|---|
| `city` | text | key into the location table |
| `outlet` | text | Suspilne Kharkiv, MediaPort, … |
| `headline_uk` | text | headline as published, original language |
| `link` | URL | publication |
| `published` | text | publication time, with update time where given |
| `quote_uk` | text | verbatim quote about the crowd size |
| `category` | categorical | `unknown` (59) · `100–999` (45) · `<100` (36) · `1000+` (10) |
| `status` | categorical | `took place` (146) · `online` (1) · `ongoing` (1) · `refuted` (1) · `announced` (1) |
| `provenance` | categorical | `own correspondent` (86) · `relay` (44) · `not stated` (12) · `police` (4) · `open-source photo` (4) |
| `provenance_detail_uk` | text | raw attribution as published: «речниця поліції Харківщини Людмила Прокопенко» |
| `run` | time | run timestamp: `13:00` · `15:00` · `18 Jul` · `19 Jul` · `19 Jul PM` |

## 3. Value assignment

### 3.1 `category`

The figure must satisfy three conditions at once: it agrees across several independent sources, it is the latest in time, and it is the largest. The target quantity is the **daily maximum**, not the count at the snapshot time.

Each condition alone produces a systematic error:

| Condition alone | Error | Example |
|---|---|---|
| largest | headline inflation | TSN headline «тисячі людей», body text «сотні» |
| latest | post-peak snapshot | Kharkiv: peak ~300 at 10:12, police counted 200 at 12:10 |
| source agreement | reprint mistaken for confirmation | the national round-up copies the regional desk verbatim |

The `<100` / `100–999` boundary falls where the data clusters: the modal phrasing in Ukrainian media is «близько сотні» (about a hundred). Convention: «близько сотні» codes as `100–999`, applied uniformly to all locations.

### 3.2 `time`

The moment the figure is valid for, **not** the page's `dateModified`. Priority of time sources:

1. A marker inside the text: «ОНОВЛЕНО. 13:30», «станом на 9:05».
2. Publication time, if the figure appears in the original version.
3. `dateModified`, as an upper bound only, flagged in `note`.

Rationale: the CMS updates the stamp without changing content. Four such cases occur in the source set; in one, Suspilne's Lutsk article moved from 14:04 to 15:57 while the body stayed byte-identical.

### 3.3 `contested`

`yes` when sources place the figure on opposite sides of a category boundary. Both versions are then kept in `note` with source and time, and the chosen category is justified there.

A discrepancy explained by crowd growth does **not** count as contested:

```
Dnipro         ~100 (09:34) → several hundred (10:53) → ~300 (12:23)
Cherkasy        ~30 (09:44) → ~100 (12:15)
Khmelnytskyi    ~50 (09:05) → ~100 (09:30)
Kharkiv        ~100 → ~300 within half an hour
```

Contested in this snapshot: Kyiv (Suspilne «сотні» against Interfax «близько двох тисяч»; no official estimate exists), Kharkiv («щонайменше 300» unattributed against «близько 200» from the police), Poltava (local newsrooms counted ~70 themselves against Suspilne's «близько сотні»), and Odesa (the day-4 «близько тисячі» is single-source — 24 Kanal citing Suspilne — and sits at the 1000 boundary).

### 3.4 `provenance`

Codes the type of evidence, not the name of the outlet. Priority under mixed attribution: `police` > `own correspondent` > `relay` > `open-source photo` > `not stated`. The official estimate ranks first because it is the only figure produced outside editorial judgement; the dataset contains two (Kharkiv, Ivano-Frankivsk). The raw wording is preserved in `provenance_detail_uk`.

### 3.5 `status`, `unknown` and `online`

`unknown` and `online` are distinct states, not a count of zero.

- `unknown`: the protest is documented, no source gives a number (Chernihiv, Kryvyi Rih, Kremenchuk, and the day-4 additions Mukachevo, Kamianske, Uman).
- `online`: no street protest took place, for a documented reason, and the protest moved to another format. Kherson: «Через безпекову ситуацію жителі Херсона долучаються до акції онлайн».
- Sumy codes as `<100` with the phrasing «до двадцяти людей»: single pickets and cardboard signs left around the city instead of a rally. KP.UA's claim that the action was cancelled is refuted by an on-scene report with photos (Tsukr).

### 3.6 Systematic source distortions

**National round-ups lag their own regional desks.** The round-up copies the regional text verbatim and updates the figure late. Suspilne's round-up at 11:41: Mykolaiv «26» against the regional «45» (−42%), Dnipro «близько 100» against «близько 300» (−66%). The direction is not constant: in Kharkiv the round-up gave more than the regional desk. Rule: retrieve both, decide by time.

**Fabrication in snippets.** The phrases «кілька тисяч людей» (Kyiv), «близько тисячі» (Kharkiv), «близько 400 молодих людей» (Lviv) appear in no page body. False attribution recorded: an AFP quote credited to Reuters.

**Fabrication in summarizer models.** Passing a page through WebFetch returned "Organizers estimated" where the text reads «за попередньою оцінкою», with no source of the estimate given.

**Headline inflation.** Figures are taken from the body text only.

**Aggregate figures.** «Сотні людей» in 056.ua covers Dnipro, Kryvyi Rih and Kyiv together; it is not assigned to any single location.

**Errors in sources are recorded, not corrected.** Censor.NET's Mykolaiv section calls Fedorov the Minister of Digital Transformation, contradicting its own text.

**Technical sources of false zeroes.** `dumskaya.net` and `monitor.cn.ua` serve windows-1251; reading them as UTF-8 destroys the Cyrillic. Ukrainian inflects city names: searching «Кременчук» returns nothing where the text reads «Кременчуці», so search runs on the stem. Telegram serves timestamps in UTC (Kyiv = UTC+3). The 0XX.ua network is not indexed by search engines and is retrieved from its `/news` feed directly.

**A fixed city list yields confirmation, not discovery.** Uzhhorod, Zhytomyr, Kropyvnytskyi and Kryvyi Rih held protests despite being absent from the organisers' announcement; Kremenchuk appears in no national round-up parsed here. Procedures 2 and 3 in §1 do not depend on a predefined list.

## 4. Files

The data exists in one copy. Edit the CSVs only; everything else is generated.

```
prompt.md                       collection prompt, reusable with a different period
build_gazetteer.py              tiered city gazetteer → gazetteer.csv (self-tested)
gazetteer.csv                   generated: cities ≥20k, tiers A/B, declension-safe stems
geo.py                          borders and oblasts, Natural Earth 10m admin_1
build_map.py                    cities.csv        → map.png
build_report.py                 both CSVs + prose → report.md
build_artifact.py               cities.csv        → map.html
build_chart.py                  by_day.csv        → chart_by_day.png
check_consistency.py            verifies the artifacts against each other
data/2026-07-16-fedorov/
    meta.json                   title, date, snapshot time, author
    cities.csv                  canonical: locations
    publications.csv            canonical: publications
    by_day.csv                  canonical: approx turnout per city per day (chart source)
    prose.md                    hand-written part of the report, markers for generated tables
    report.md                   generated
    map.png                     generated
    map.html                    generated
    chart_by_day.png            generated
```

The build scripts live at the root and are dataset-agnostic. Each takes the dataset directory as an argument, defaulting to `data/2026-07-16-fedorov`. A new event is a new folder under `data/`, not a new script. Everything specific to one event (title, snapshot time, author) sits in that folder's `meta.json`.

`check_consistency.py` checks that the sets of cities and categories match across CSV, report and HTML; that the distribution sums to the row count; that no row predates the collection period (the July 2025 protests share the same keywords); and that no link points at a homepage instead of a publication. `build_map.py` additionally reports label collisions and text that overflows the canvas.

```bash
pip install pillow
python build_map.py        data/2026-07-16-fedorov
python build_report.py     data/2026-07-16-fedorov
python build_artifact.py   data/2026-07-16-fedorov
python check_consistency.py data/2026-07-16-fedorov
```

Borders: Natural Earth 10m admin_1, 24 oblasts plus Kyiv, Crimea and Sevastopol, dissolved into a national outline with `shapely`. Natural Earth assigns Crimea and Sevastopol to Russia; this dataset renders them as Ukraine.

![Protest map, 16–19 July 2026](data/2026-07-16-fedorov/map.png)

Approximate aggregate turnout by day (Kyiv shown separately, as it dominates each day; later days undercount non-Kyiv cities, so those totals are lower bounds):

![Approximate turnout by day, 16–19 July 2026](data/2026-07-16-fedorov/chart_by_day.png)

## 5. Limitations

**The snapshot is open-ended.** The protest is in its fourth day (16–19 July) and ongoing at the 19 July snapshot. Each location carries its peak over the four-day wave; where a crowd was still growing when last recorded, the figure is a lower bound. The political trigger is unresolved — the ministry is unfilled, Yevhen Khmara is acting minister, and parliament went into recess to 18 August without appointing one — so further days are likely.

**Kyiv.** Suspilne has no Kyiv desk. The day-1 peak (~2,000) rests on Interfax, LB, Kyiv Post and AFP, against a stale Suspilne round-up line «сотні»; on day 2 LB's own correspondent gave «близько 3 тисяч» for the evening crowd, which exceeded day 1; day 3 was smaller (Suspilne, reporting Kyiv directly this time, «близько 2 тисяч» by 21:45). Neither the police nor the city administration published a figure. Interfax-Ukraine did report «понад 10 тис.» for the day-2 evening (retrieved via Espreso's citation) — a ~3× gap over LB's own-correspondent count — so the conservative figure is kept as the day-2 peak and the discrepancy flagged rather than the higher number used. Day 4 (19 July) was larger still — Interfax-Ukraine reported «понад 5000» on Ivan Franko Square (via LIGA), now the wave peak.

**Single-source locations.** Kolomyia, and the day-4 additions Mukachevo, Kamianske and Uman, rest on one source each; a targeted search produced no second confirmation.

**Incomplete coverage of small towns.** The gazetteer sweep covered cities ≥30k (111 names beyond the initial list). The <30k tier (364 names) was not run: Google News began returning 503 after roughly 475 queries. A Telegram-monitoring map (ПошукAI, 17 July) had flagged four further cities — Irpin, Boryspil, Kalush, Drohobych, all ≥50k. The 19 July run reran the revised v3 discovery (gazetteer-grep over every downloaded round-up, batch tier-A queries, targeted city searches) and found **no independent source** for any of the four: they appear in no round-up body and no city-level report, so they are not on the map. Almost every gazetteer hit over the round-ups was a false positive (the organiser's surname «Козятинський», the President's name «Володимир», war-attack city lists) — but re-running the grep over the **day-4** round-ups surfaced one real omission, **Uman**, which had appeared only inside a broadcaster's per-city subsection, not any comma-list; the same read verified **Odesa**'s day-4 «близько тисячі», previously seen only in a search snippet. The revised discovery procedure is in `prompt.md` §4; the tiered city list with declension-safe stems is `gazetteer.csv`.

**Links.** In the location table, all 28 links resolve to specific articles. In the publication table, 8 rows (day-1 supporting sources) still point at outlet homepages.

**Categorical scale.** The three bands (`<100`, `100–999`, `1000+`) follow the reference map of the protests against law 12414. The boundary at 100 falls where the data clusters, so some locations are coded by the convention in §3.1 rather than by an exact count.

## Authorship

Data and map: Valentyn Hatsko, Center for Sociological Research, KSE University.
Borders: [Natural Earth](https://www.naturalearthdata.com/), public domain.
Quotes belong to the respective outlets; links point to the original publications.

*Protest sizes are approximate. The project is ongoing; some locations may be missing.*
