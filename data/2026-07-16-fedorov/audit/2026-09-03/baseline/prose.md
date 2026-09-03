# Protests over Mykhailo Fedorov leaving the Defence Ministry — media collection

**Final collection check: 1 September 2026.** The dataset covers documented actions from **16 July through 29 August 2026**, a **{DAYS}-day calendar span**. The last documented coordinated multi-city actions took place on **19 August**, when parliament appointed Yevhen Khmara defence minister and organisers described their recurring actions as final. A separate reformatted action of about 15 people took place in **Dnipro on 29 August**; no later action was found in the systematic 30 August–1 September check.

Each city carries its **best-supported peak over the full wave**, not a count at one arbitrary hour. `first_day`, `last_day`, `days_active` and `peak_day` describe documented action days; they do not imply that every day in between had a count. The 115 publication × city rows added in this update are tagged `run = 1 Sep`; earlier rows keep their historical run labels.

> The tables below are generated from `cities.csv` and `publications.csv` by `build_report.py`. Edit the CSVs, not `report.md`. `check_consistency.py` verifies the shared data model and generated artifacts.

> Quotes stay in the original Ukrainian. `quote_uk` is the outlet's exact wording from the retrieved page body; English glosses belong in `quote_en`.

## Context and finding

The protests began after Fedorov was not returned to the defence portfolio in the new cabinet. They reached **{N} Ukrainian cities**, including an online action in Kherson. The movement did not follow a simple opening-day peak and decline: the largest individual action came on **day 16, 31 July**, when police estimated about 6,000 participants in Kyiv. A second Kyiv march on **16 August** drew roughly 1,000–1,500 people; the last documented coordinated actions were much smaller gatherings on 18–19 August.

The main finding is therefore two-part: **the biggest individual action occurred on day 16, not at the start; the last documented coordinated multi-city actions were on 19 August, while one late local action extended the documented calendar span to 29 August.**

## Timeline and reaction

Events that establish the political or wave-level context are recorded here rather than as city rows unless a publication also documents a concrete local action.

| Date | Event | Evidence |
|---|---|---|
| 14–15 Jul | The previous cabinet resigned; Fedorov confirmed that he was leaving the Defence Ministry. | Context reported across the opening-day national coverage. |
| 16 Jul | Cardboard-sign protests began in Kyiv and regions. Parliament approved the new cabinet without a defence minister. | Opening-day national and regional reports in Table 1. |
| 17 Jul | The Cabinet named **Yevhen Khmara acting defence minister**; protests continued for a second day. | [LB.ua](https://lb.ua/society/2026/07/17/752652_kabmin_zatverdiv_hmaru_tvo.html) |
| 19 Jul | Kyiv exceeded 5,000 participants; actions continued in roughly 15 cities. | [LIGA.net / Interfax-Ukraine](https://news.liga.net/ua/society/news/chetvertyy-den-mitynhiv-u-kyievi-cherez-vidstavku-fedorova-zibrav-ponad-5000-liudey-interfaks-ukraina) |
| 22 Jul | President Zelenskyy formally removed Oleksandr Syrskyi as Commander-in-Chief and appointed Mykhailo Drapatyi. | [Presidential decree №627/2026](https://www.president.gov.ua/documents/6272026-60453), [presidential address](https://www.president.gov.ua/news/rosiya-povinna-vidchuvati-zrostannya-tisku-i-sankcij-ce-i-na-105553) |
| 24 Jul | Organisers declared the Kyiv campaign open-ended after their deadline passed. | [TSN](https://tsn.ua/ukrayina/povernit-fedorova-u-kiyevi-ogolosili-bezstrokovi-protesti-2790456.html) |
| 28 Jul | The Kyiv action was cancelled because of a missile threat and replaced with plans for a march. | [Tvoe Misto](https://tvoemisto.tv/uk/news/veteran-dmytro-kozyatynskyy-zaklykav-ne-vyhodyty-na-protest-u-kyyevi-28-lypnya-cherez-raketnu-zagrozu-7712.html) |
| **31 Jul** | **Day 16 and the largest individual action:** the all-Ukrainian march drew a police estimate of about 6,000 in Kyiv. | [Ukrinform](https://www.ukrinform.ua/rubric-regions/4149949-u-kievi-vidbuvaetsa-protestna-hoda-za-reformi-v-oboronnij-sferi.html) |
| 1–12 Aug | Turnout fell, but recurring actions continued in Kyiv and a smaller group of cities. Dnipro and Uzhhorod supplied the densest city-level daily counts. | Body-level city reports in Table 1. |
| 14 Aug | Kyiv resumed with conflicting body-level estimates from up to 100 to about 500; the daily chart uses about 300, the repeated independent estimate. | [Suspilne](https://suspilne.media/1379402-u-kievi-prohodit-akcia-na-pidtrimku-fedorova-aktivisti-zbiraut-vimogi-do-ofisu-prezidenta), [DW](https://www.dw.com/uk/kartonkovi-protesti-v-kievi-vimogi-povernuti-fedorova-ta-kritika-umerova/a-78377289), [Gazeta.ua](https://gazeta.ua/articles/politics/_u-kiyevi-ta-regionah-lyudi-vijshli-na-akciyi-na-pidtrimku-eksministra-oboroni-fedorova/1256655) |
| **16 Aug** | A repeat protest march in Kyiv drew about 1,000–1,500; parallel actions were reported in Odesa, Zaporizhzhia and other cities. | [Suspilne](https://suspilne.media/1380396-u-kievi-protestna-hoda-cerez-zvilnenna-mihajla-fedorova-z-minoboroni) |
| 18 Aug | Small final coordinated actions continued; Kyiv had no more than about 30 participants. That evening, Fedorov called for a legal and secure mechanism to restore the electoral process during a prolonged war. | [OBOZ.UA / Interfax-Ukraine](https://www.obozrevatel.com/ukr/novosti-obschestvo/ganba-v-mistah-ukraini-34-j-den-pospil-trivayut-mitingi-za-povernennya-fedorova-foto-video.htm), [Hromadske Radio](https://hromadske.radio/news/2026/08/18/fedorov-zaklykav-do-provedennia-vyboriv-pislia-podannia-zelenskoho-na-pryznachennia-khmary-ministrom-oborony) |
| **19 Aug** | Parliament appointed Khmara with **312 votes in favour** (2 against, 0 abstentions, 20 did not vote). About 100 people protested near parliament; organisers and regional groups described these as their final recurring actions. | [Official roll-call vote](https://meeting.rada.gov.ua/work/vote/vot-35385_skl9), [Graty](https://graty.me/trista-golosiv-nardepiv-za-kandidata-vid-prezidenta-ta-sotnya-protestuvalnikiv-pid-radoyu-yakim-buv-ostannij-miting-za-fedorova), [Suspilne Rivne](https://suspilne.media/rivne/1383012-ludi-aki-hodili-na-akcii-na-pidtrimku-mihajla-fedorova-zibralisa-vostanne-u-rivnomu/), [Radio Svoboda](https://www.radiosvoboda.org/a/news-kozyatynskyy-zayava-protesty-fedorov-vybory/33833857.html) |
| **29 Aug** | Dnipro held a separate action under the slogan “Enough ignoring”, attended by about 15 people. This is the latest documented local action. | [Dnipro.media](https://www.dnipro.media/novyny-dnipro/aktsiya-protestu-proty-vidstavky-fedorova-u-dnipri-yak-prohodyt/) |
| 30 Aug–1 Sep | Systematic search found follow-up coverage of the 29 August Dnipro action but no later protest. | Negative search check; absence means “not found”, not proof of no unreported action. |

## Methodological warnings

1. **Page bodies govern.** Search snippets, headlines and summaries are discovery aids only. Every new quote and every numeric estimate was checked against the downloaded body of the specific article.
2. **Publication date is not always event date.** A 20 August Dnipro article explicitly describes the 19 August action; the Graty retrospective published on 21 August also describes 19 August. Event dates are recorded in `published` notes and in `by_day.csv`, not inferred blindly from the page timestamp.
3. **A city peak and a daily aggregate are different quantities.** The map uses each city's peak over the wave. The daily chart sums only usable body-level city estimates for that date, so its aggregate can be higher on a broad multi-city day even when the largest single action occurred on another day.
4. **Blank cells are missing estimates, not zero turnout.** Later coverage often confirmed that an action happened without publishing a count. Such cells remain empty in `by_day.csv`.
5. **Round-ups are not automatically independent confirmation.** National summaries frequently copy regional desks or organisers. `provenance` records own reporting, police estimates, relays and unspecified sourcing.
6. **Headlines can inflate.** Numbers are accepted only when the page body supports them. “Thousands” in a headline does not override a smaller or absent body count.
7. **Day numbering in sources is unreliable.** Dnipro sometimes counted multiple local actions within one calendar day. Calendar dates, not outlet labels such as “day 36”, anchor the series.
8. **The late Dnipro action changes the calendar endpoint, not the last documented coordinated-action date.** The national recurring campaign is last documented on 19 August; the 29 August event is retained because the dataset records all verified in-scope local actions.

## Random sampled-day audit — 1 September

Six dates were drawn reproducibly from the 35 dates with at least one numeric city estimate, using seed `fedorov-protests-audit-2026-09-01`: **18 July, 22 July, 31 July, 4 August, 15 August and 19 August**. All 22 populated city-date cells on those dates were checked against the current article body and fresh news discovery.

- **21 of 22 daily estimates were confirmed without change.** The one correction is Dnipro on 31 July: the Suspilne report initially described about 100 people at the assembly point but its final body says about 500 joined overall. `by_day.csv` and the Dnipro city peak now use 500. [Suspilne Dnipro](https://suspilne.media/dnipro/1368904-16-j-den-mitingiv-na-pidtrimku-fedorova-u-dnipri-dolucilisa-do-vseukrainskoi-protestnoi-hodi/)
- The sampled-day news sweep added **14 publication × city rows**, including additional 18 July reporting, a nine-city 4 August roundup and a separate Kyiv evening action on 19 August. It removed **four invalid or duplicate rows**: two Kyiv rows incorrectly derived from an Uzhhorod-only story and two AMP duplicates.
- Eight existing publication rows were upgraded from `unknown` or an early count to body-supported quotes and categories. Examples include 30 participants in Mykolaiv on 22 July, the Kyiv police estimate of 6,000 on 31 July, and Kyiv's 120-person 4 August action. [Suspilne Mykolaiv](https://suspilne.media/mykolaiv/1361696-mikolaivci-vcergove-vijsli-na-miting-proti-zvilnenna-ministra-oboroni-fedorova-foto/) · [Ukrinform](https://www.ukrinform.ua/rubric-regions/4149949-u-kievi-vidbuvaetsa-protestna-hoda-za-reformi-v-oboronnij-sferi.html) · [Novyny.LIVE](https://news.novyny.live/popri-doshch-ta-trivogi-ukrayintsi-znovu-mitinguvali-proti-vidstavki-fedorova-338557.html)
- Textual quantities remain explicitly normalized: `кілька сотень` is coded as 300 for the daily chart, while `понад` estimates use the stated lower-bound integer. The original wording remains in `publications.csv`, so the numeric convention is auditable.

## Coverage audit for the 1 September run

The update used national and regional outlets, Suspilne regional desks, direct checks of local outlets and a direct sitemap sweep of the 0XX.ua network. Telegram and announced-city lists were treated as leads, not numeric evidence.

- The discovery pass produced **200 candidate publisher URLs**; 197 returned HTTP 200 and 164 yielded usable article bodies.
- A direct 0XX.ua sweep covered 21 city domains and seven protest-related slug hits; it produced **no new confirmed city**.
- The focused 20 August–1 September search found one later in-scope action: **Dnipro, 29 August**. Searches for 30 August–1 September found no later action.
- The update adds **115 rows** with `run = 1 Sep`. Repeat mentions across collection runs are preserved; duplicate publication × city rows inside the new run were removed.
- Seven old homepage links were restored to specific articles. One irrecoverable `18000.com.ua` helper row, which had no specific article, original headline or usable quote, was removed rather than retained as evidence.
- No new city was added without a retrieved city-level publication. “Blank spots” remain a methodological note and are not drawn on the map.
- Access constraints remain source-specific: some pages require browser rendering, some domains are dead, and some legacy pages cannot be recovered. They are not converted into evidence from snippets.

## Table 1 — all publications

One row per publication × city. Historical runs remain unchanged; the new verified slice is tagged `run = 1 Sep`.

<!-- TABLE1:START -->
<!-- TABLE1:END -->

## Table 2 — summary by city

Each figure is the **best-supported city peak over the full {DAYS}-day calendar span (16 July–{LAST})**. `days_active` counts distinct documented action days and is a floor, not a claim that no action occurred on uncounted days.

<!-- TABLE2:START -->
<!-- TABLE2:END -->

## Block 3 — computed coverage aggregates

<!-- BLOCK3:START -->
<!-- BLOCK3:END -->

---

*Protest sizes are approximate. Collection was checked through 1 September 2026; some locations may still be missing.*
