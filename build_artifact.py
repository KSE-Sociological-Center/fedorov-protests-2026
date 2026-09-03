# -*- coding: utf-8 -*-
"""data/<event>/cities.csv + geo.py -> data/<event>/map.html (black-and-white interactive page)"""
import csv, io, json, os, datetime
from geo import COUNTRY, REGIONS

HERE = os.path.dirname(os.path.abspath(__file__))
import json, sys

# Dataset path as an argument, otherwise data/<event>/ buys nothing: the next
# event would still require code edits.
DS = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "data/2026-07-16-fedorov"
ds = lambda n: os.path.join(HERE, DS, n)
META = json.load(io.open(ds("meta.json"), encoding="utf-8"))

SNAPSHOT = META["snapshot"]
SNAPSHOT_ISO = datetime.datetime.strptime(SNAPSHOT, "%d %B %Y").date().isoformat()
AUDIT_ISO = META.get("audit_date", SNAPSHOT_ISO)
AUTHOR = META["author_en"]

cities = list(csv.DictReader(io.open(ds("cities.csv"), encoding="utf-8")))
# counted only for the schema.org/Dataset block at the foot of this file
pubs = list(csv.DictReader(io.open(ds("publications.csv"), encoding="utf-8")))
with io.open(ds("by_day.csv"), encoding="utf-8") as _f:
    NDAYS = len([c for c in csv.DictReader(_f).fieldnames if c and c != "city"])
ORDER = {"5000+": 0, "1000–4999": 1, "100–999": 2, "<100": 3, "unknown": 4, "online": 5}
cities.sort(key=lambda c: (ORDER.get(c["category"], 9), c["city"]))
live = [c["city"] for c in cities if c["status"].startswith("ongoing")]

def pretty_date(value):
    d = datetime.date.fromisoformat(value)
    return "%d %s" % (d.day, d.strftime("%B %Y"))

last_day = max((c.get("last_day", "") for c in cities), default=META["last_action"])
last_cities = [c["city"] for c in cities if c.get("last_day") == last_day]
TITLE = "Protest locations and peak turnout"
SUBTITLE = META["subtitle_en"].replace(" — ", "–")
COORD_END = pretty_date(META["coordinated_end"])
LAST_ACTION = pretty_date(last_day)
STATUS_LINE = ("Publication coverage ends %s; data audited %s. Ukrainian outlets last reported coordinated "
               "actions on %s and one later local action in %s on %s. Kherson joined online." %
               (SNAPSHOT, AUDIT_ISO, COORD_END, ", ".join(last_cities), LAST_ACTION))

LABEL_DIR = {
    "Kyiv": "up", "Kharkiv": "right", "Dnipro": "right", "Lviv": "left", "Odesa": "down",
    "Ivano-Frankivsk": "left", "Ternopil": "up", "Khmelnytskyi": "down", "Lutsk": "left",
    "Cherkasy": "down", "Poltava": "up", "Zaporizhzhia": "right", "Kropyvnytskyi": "down",
    "Uzhhorod": "right", "Rivne": "right", "Mykolaiv": "left", "Chernivtsi": "down",
    "Zhytomyr": "up", "Sumy": "right", "Kolomyia": "down", "Vinnytsia": "right",
    "Chernihiv": "up", "Kryvyi Rih": "down", "Kremenchuk": "left", "Kherson": "down",
    "Mukachevo": "down", "Kamianske": "right", "Uman": "down",
    "Izmail": "left", "Kalush": "up", "Sheptytskyi": "left",
    "Oleksandriia": "left", "Kamianets-Podilskyi": "down",
}

# The CSV keeps full audit notes. The public map shows only facts that help a reader
# interpret an unusual estimate or endpoint.
WEB_NOTES = {
    "Kyiv": ("Police counted about 6,000 people at the 31 July march. Published estimates ranged "
             "from about 1,000 to an organiser claim of 15,000, so we mark Kyiv as contested. "
             "A repeat march on 16 August drew about 1,000–1,500 people; the last Kyiv action was 19 August."),
    "Kharkiv": ("MediaPort watched the crowd grow from about 100 to about 300 within half an hour. "
                "Suspilne's national roundup also reported at least 300. Later reports put the city peak "
                "at about 450 on 19 July."),
    "Dnipro": ("Dnipro had 34 documented action days. About 15 people attended a local action on "
               "29 August; we found no later event."),
    "Odesa": ("One report put the 19 July crowd at about 1,000. The estimate sits on the category "
              "boundary and lacks a second source, so we mark Odesa as contested."),
    "Chernivtsi": ("The audited peak is about 150 on 19 July. A separate 100-person estimate for "
                   "20 July and materially different reports make the city peak contested."),
    "Uzhhorod": ("A headline reported 200 people, but the article body gave no count. We use the "
                 "police estimate of about 50 from 16 July."),
    "Sumy": ("Residents used small pickets and left cardboard signs around the city because of the "
             "security situation."),
    "Kherson": ("Kherson residents joined online because a street gathering was unsafe. We found no "
                "street action during the collection period."),
    "Kamianets-Podilskyi": ("Two reports confirm local actions, but neither gives a crowd count. We "
                            "could not retrieve the original ZHAR.INFO article."),
}
unknown_web_notes = sorted(set(WEB_NOTES) - {c["city"] for c in cities})
if unknown_web_notes:
    raise SystemExit("web notes refer to unknown cities: " + ", ".join(unknown_web_notes))
contested_without_note = sorted(c["city"] for c in cities
                                if c["contested"] == "yes" and c["city"] not in WEB_NOTES)
if contested_without_note:
    raise SystemExit("contested cities need a short web note: " + ", ".join(contested_without_note))

DATA = [dict(n=c["city"], ob=c["oblast"], lat=float(c["lat"]), lon=float(c["lon"]),
             cat=c["category"], q=c["quote_uk"], qen=c["quote_en"], t=c["time"], src=c["source"],
             url=c["link"], contested=c["contested"] == "yes", status=c["status"],
             days=c.get("days_active", ""), first=c.get("first_day", ""),
             last=c.get("last_day", ""), peak=c.get("peak_day", ""),
             note=WEB_NOTES.get(c["city"], ""), dir=LABEL_DIR.get(c["city"], "down")) for c in cities]

HTML = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ | map</title>
<style>
  :root {
    --paper:#fff; --ink:#111; --ink-2:#555; --ink-3:#8a8a8a;
    --land:#fff; --oblast:#c4c4c4; --border:#222; --rule:#e2e2e2; --panel:#fafafa;
    --dot:#0e3667; --blue-4:#0d366b; --blue-3:#2a78d6; --blue-2:#5698e7;
    --blue-1:#86b6ef; --online-fill:#e0ebf6; --contested:#e25c2d;
    --f: "Segoe UI","Noto Sans",system-ui,-apple-system,sans-serif;
  }
  @media (prefers-color-scheme: dark) {
    :root { --paper:#0e0e0f; --ink:#ededed; --ink-2:#a6a6a6; --ink-3:#6f6f6f;
            --land:#181818; --oblast:#3a3a3a; --border:#c8c8c8; --rule:#2b2b2b; --panel:#151515;
            --dot:#b9d7ff; --blue-4:#4d8bd7; --blue-3:#5d9ce7; --blue-2:#79afea;
            --blue-1:#9bc5f1; --online-fill:#25364a; --contested:#ff8a5b; }
  }
  :root[data-theme="dark"] { --paper:#0e0e0f; --ink:#ededed; --ink-2:#a6a6a6; --ink-3:#6f6f6f;
    --land:#181818; --oblast:#3a3a3a; --border:#c8c8c8; --rule:#2b2b2b; --panel:#151515;
    --dot:#b9d7ff; --blue-4:#4d8bd7; --blue-3:#5d9ce7; --blue-2:#79afea;
    --blue-1:#9bc5f1; --online-fill:#25364a; --contested:#ff8a5b; }
  :root[data-theme="light"] { --paper:#fff; --ink:#111; --ink-2:#555; --ink-3:#8a8a8a;
    --land:#fff; --oblast:#c4c4c4; --border:#222; --rule:#e2e2e2; --panel:#fafafa;
    --dot:#0e3667; --blue-4:#0d366b; --blue-3:#2a78d6; --blue-2:#5698e7;
    --blue-1:#86b6ef; --online-fill:#e0ebf6; --contested:#e25c2d; }
  * { box-sizing:border-box; }
  body { background:var(--paper); color:var(--ink); font-family:var(--f); line-height:1.5;
         margin:0; padding:28px 20px 44px; -webkit-font-smoothing:antialiased; }
  .wrap { max-width:1180px; margin:0 auto; display:flex; flex-direction:column; gap:22px; }
  h1 { font-size:clamp(22px,3.2vw,32px); font-weight:700; margin:0; letter-spacing:-.01em; text-wrap:balance; }
  .sub { color:var(--ink-2); margin:0; font-size:15px; }
  .live { font-weight:600; margin:0; font-size:14px; }
  .rule { height:1px; background:var(--ink); }
  .field { display:grid; grid-template-columns:1fr 288px; gap:20px; align-items:start; }
  @media (max-width:880px){ .field { grid-template-columns:1fr; } }
  .mapbox { border:1px solid var(--rule); overflow-x:auto; padding:6px; }
  svg { display:block; width:100%; height:auto; }
  .maphint { display:none; margin:2px 6px 7px; color:var(--ink-3); font-size:11px; }
  @media (max-width:600px){
    #map { width:760px; max-width:none; }
    .maphint { display:block; }
  }
  .land { fill:var(--land); stroke:var(--oblast); stroke-width:.9; }
  .country { fill:none; stroke:var(--border); stroke-width:1.9; stroke-linejoin:round; }
  .dot { cursor:pointer; }
  .dot circle.body { stroke:var(--dot); stroke-width:1.5; }
  .dot.c5000 circle.body { fill:var(--blue-4); }
  .dot.c1000 circle.body { fill:var(--blue-3); }
  .dot.c100  circle.body { fill:var(--blue-2); }
  .dot.csmall circle.body { fill:var(--blue-1); }
  .dot:hover circle.body, .dot:focus-visible circle.body { filter:brightness(.78); }
  .dot:focus-visible { outline:none; }
  .dot.unknown circle.body { fill:none; stroke-dasharray:3 3; }
  .dot.online  circle.body { fill:var(--online-fill); stroke:var(--ink-3); stroke-dasharray:1.5 3; }
  .dot circle.ring { fill:none; stroke:var(--contested); stroke-width:1.3; stroke-dasharray:2.5 3; }
  .dot circle.hit { fill:transparent; }
  .dot text { font-size:12px; font-weight:600; fill:var(--ink); paint-order:stroke;
              stroke:var(--paper); stroke-width:3.5px; stroke-linejoin:round; pointer-events:none; }
  .dot text.num { font-size:10.5px; font-weight:400; fill:var(--ink-2); }
  .dot.is-dim text { fill:var(--ink-3); }
  .panel { border:1px solid var(--rule); background:var(--panel); padding:14px 16px; }
  .panel h2 { font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:var(--ink-3);
              margin:0 0 10px; font-weight:600; }
  #detail { min-height:190px; }
  #detail .city { font-size:19px; font-weight:700; margin:0 0 2px; }
  #detail .ob { font-size:12px; color:var(--ink-3); margin:0 0 10px; }
  #detail blockquote { margin:0 0 10px; font-size:15px; font-style:italic; }
  #detail .meta { font-size:11.5px; color:var(--ink-2); display:flex; flex-direction:column; gap:2px; }
  #detail a { color:var(--ink); }
  #detail .note { font-size:12px; color:var(--ink-2); margin:10px 0 0; }
  .gloss { font-size:12px; color:var(--ink-3); font-style:normal; margin:0 0 10px; }
  #detail .idle { color:var(--ink-3); font-size:13px; margin:0; }
  .chip { display:inline-block; font-size:9.5px; letter-spacing:.06em; text-transform:uppercase;
          border:1px solid var(--ink); padding:1px 5px; margin-left:4px; }
  ul.leg { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:7px; font-size:13px; }
  ul.leg li { display:flex; align-items:center; gap:10px; }
  ul.leg .sw { flex:0 0 46px; display:grid; place-items:center; }
  .tablewrap { overflow-x:auto; border:1px solid var(--rule); }
  table { border-collapse:collapse; width:100%; font-size:13px; }
  caption { text-align:left; padding:10px 14px; color:var(--ink-3); font-size:12px; border-bottom:1px solid var(--rule); }
  th,td { text-align:left; padding:7px 11px; border-bottom:1px solid var(--rule); vertical-align:top; }
  th { font-size:10px; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-3); white-space:nowrap; }
  td.c { white-space:nowrap; font-variant-numeric:tabular-nums; }
  td.q { color:var(--ink-2); font-style:italic; }
  tbody tr:last-child td { border-bottom:none; }
  footer { border-top:1px solid var(--rule); padding-top:14px; color:var(--ink-3); font-size:12px;
           display:flex; flex-direction:column; gap:5px; }
  @media (prefers-reduced-motion: reduce){ *{transition:none!important} }
</style>
<div class="wrap">
  <header style="display:flex;flex-direction:column;gap:8px">
    <h1>__TITLE__</h1>
    <p class="sub">__SUBTITLE__. We plot the highest estimate we could verify for each of __N__ locations.</p>
    <p class="live">__STATUS__</p>
  </header>
  <div class="rule"></div>
  <div class="field">
    <div class="mapbox">
      <p class="maphint">Swipe sideways to see the full map. Tap a city for its source.</p>
      <svg id="map" viewBox="0 0 1000 690" role="img" aria-label="Map of __N__ protest locations and their peak turnout bands">
        <g id="land"></g><g id="dots"></g>
      </svg>
    </div>
    <div style="display:flex;flex-direction:column;gap:20px">
      <div class="panel" id="detail" aria-live="polite">
        <p class="idle">Select a city to see the published quote, date and source.</p>
      </div>
      <div class="panel">
        <h2>Legend</h2>
        <ul class="leg">
          <li><span class="sw"><svg width="40" height="46" viewBox="0 0 40 46"><circle cx="20" cy="23" r="21" fill="var(--blue-4)" stroke="var(--dot)" stroke-width="1.5"/></svg></span><span>5000+ participants</span></li>
          <li><span class="sw"><svg width="40" height="38" viewBox="0 0 40 38"><circle cx="20" cy="19" r="17" fill="var(--blue-3)" stroke="var(--dot)" stroke-width="1.5"/></svg></span><span>1000–4999 participants</span></li>
          <li><span class="sw"><svg width="40" height="30" viewBox="0 0 40 30"><circle cx="20" cy="15" r="12" fill="var(--blue-2)" stroke="var(--dot)" stroke-width="1.5"/></svg></span><span>100–999 participants</span></li>
          <li><span class="sw"><svg width="40" height="20" viewBox="0 0 40 20"><circle cx="20" cy="10" r="6.5" fill="var(--blue-1)" stroke="var(--dot)" stroke-width="1.5"/></svg></span><span>fewer than 100</span></li>
          <li><span class="sw"><svg width="40" height="20" viewBox="0 0 40 20"><circle cx="20" cy="10" r="6.5" fill="none" stroke="var(--dot)" stroke-width="1.5" stroke-dasharray="3 3"/></svg></span><span>no city count published</span></li>
          <li><span class="sw"><svg width="40" height="20" viewBox="0 0 40 20"><circle cx="20" cy="10" r="6.5" fill="var(--online-fill)" stroke="var(--ink-3)" stroke-width="1.5" stroke-dasharray="1.5 3"/></svg></span><span>online action (Kherson)</span></li>
          <li><span class="sw"><svg width="40" height="36" viewBox="0 0 40 36"><circle cx="20" cy="18" r="12" fill="var(--blue-2)" stroke="var(--dot)" stroke-width="1.5"/><circle cx="20" cy="18" r="16" fill="none" stroke="var(--contested)" stroke-width="1.3" stroke-dasharray="2.5 3"/></svg></span><span>sources disagree</span></li>
        </ul>
      </div>
    </div>
  </div>
  <div class="tablewrap">
    <table>
      <caption>Peak bands, published quotes and sources by city.</caption>
      <thead><tr><th>City</th><th>Peak band</th><th>Published quote</th><th>Estimate time</th><th>Documented days</th><th>Status</th><th>Source</th></tr></thead>
      <tbody id="tb"></tbody>
    </table>
  </div>
  <footer>
    <p style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">
      <span>Counts are approximate. We checked Ukrainian media through __SNAP__.</span>
      <span style="font-weight:600;color:var(--ink);white-space:nowrap">Map and data: Valentyn Hatsko, TG: @gorbach_squad.</span>
    </p>
    <p>For each city, we use the highest estimate we could verify in article text. When reports differ,
       we compare timestamps and independent sources. We add a dashed ring where the figures still
       disagree. Quotes reproduce the Ukrainian wording in article bodies; we excluded headlines and
       search snippets.</p>
    <p>Borders and oblasts: Natural Earth 10m.</p>
    <p>Source: Ukrainian media, retrieved September 2026. <a href="https://github.com/KSE-Sociological-Center/fedorov-protests-2026">Repository and data</a>.</p>
  </footer>
</div>
<script>
const CITIES = __DATA__, LAND = __LAND__, COUNTRY = __COUNTRY__;
(function(){
 "use strict";
 const K=Math.cos(48.4*Math.PI/180), LON0=21.7, LON1=40.35, LAT0=52.45, LAT1=44.3;
 const W=1000,H=690,PAD=14;
 const sc=Math.min((W-2*PAD)/((LON1-LON0)*K),(H-2*PAD)/(LAT0-LAT1));
 const ox=PAD+((W-2*PAD)-(LON1-LON0)*K*sc)/2, oy=PAD+((H-2*PAD)-(LAT0-LAT1)*sc)/2;
 const px=l=>ox+(l-LON0)*K*sc, py=l=>oy+(LAT0-l)*sc;
 const NS="http://www.w3.org/2000/svg";
 const el=(n,a)=>{const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);return e;};
 const d=r=>r.map((p,i)=>(i?"L":"M")+px(p[0]).toFixed(1)+" "+py(p[1]).toFixed(1)).join(" ")+" Z";
 const land=document.getElementById("land");
 LAND.forEach(r=>land.appendChild(el("path",{d:d(r),class:"land"})));
 COUNTRY.forEach(r=>land.appendChild(el("path",{d:d(r),class:"country"})));

 const R={"5000+":24,"1000–4999":17,"100–999":12.5,"<100":6.5,"unknown":6.5,"online":6.5};
 const CCLASS={"5000+":"c5000","1000–4999":"c1000","100–999":"c100","<100":"csmall",
               "unknown":"unknown is-dim","online":"online is-dim"};
 const place=(cx,cy,r,dir)=>{const G=6,L=11;
   if(dir==="up")   return {x:cx,a:"middle",y1:cy-r-G-L,y2:cy-r-G};
   if(dir==="down") return {x:cx,a:"middle",y1:cy+r+G+L,y2:cy+r+G+L*2};
   if(dir==="left") return {x:cx-r-G,a:"end",y1:cy+1,y2:cy+1+L};
   return {x:cx+r+G,a:"start",y1:cy+1,y2:cy+1+L};};

 const dots=document.getElementById("dots"), det=document.getElementById("detail");
 const MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
 const fmt=v=>{if(!v)return "";const p=v.split("-");return Number(p[2])+" "+MON[Number(p[1])-1];};
 function render(c){
   const dur=c.days?(c.days+" documented "+(c.days==="1"?"day":"days")+" · "
     +fmt(c.first)+"–"+fmt(c.last)):"";
   det.innerHTML='<p class="city">'+c.n+(c.contested?'<span class="chip">sources differ</span>':'')+'</p>'
    +'<p class="ob">'+c.ob+' · '+c.cat+' · '+c.status+'</p>'
    +(dur?'<p class="ob">'+dur+(c.peak?' · peak '+fmt(c.peak):'')+'</p>':'')
    +'<blockquote>«'+c.q+'»</blockquote>'
    +(c.qen?'<p class="gloss">'+c.qen+'</p>':'')
    +'<div class="meta"><span>Estimate: '+c.t+'</span>'
    +'<span><a href="'+c.url+'" target="_blank" rel="noopener noreferrer">'+c.src+'</a></span></div>'
    +(c.note?'<p class="note">'+c.note+'</p>':'');
 }
 CITIES.slice().sort((a,b)=>R[b.cat]-R[a.cat]).forEach(c=>{
   const r=R[c.cat], cx=px(c.lon), cy=py(c.lat);
   let cls="dot "+CCLASS[c.cat];
   const g=el("g",{class:cls,tabindex:"0",role:"button","aria-label":c.n+", "+c.cat+", "+c.q});
   const ti=el("title",{}); ti.textContent=c.n+": "+c.cat+", «"+c.q+"» ("+c.src+", "+c.t+")"; g.appendChild(ti);
   if(c.contested) g.appendChild(el("circle",{cx:cx,cy:cy,r:r+4,class:"ring"}));
   g.appendChild(el("circle",{cx:cx,cy:cy,r:r,class:"body"}));
   g.appendChild(el("circle",{cx:cx,cy:cy,r:Math.max(r+6,13),class:"hit"}));
   const p=place(cx,cy,c.contested?r+4:r,c.dir);
   const t1=el("text",{x:p.x,y:p.y1,"text-anchor":p.a}); t1.textContent=c.n; g.appendChild(t1);
   if(c.cat!=="unknown"&&c.cat!=="online"){
     const t2=el("text",{x:p.x,y:p.y2,"text-anchor":p.a,class:"num"}); t2.textContent=c.cat; g.appendChild(t2);
   }
   const show=()=>render(c);
   g.addEventListener("mouseenter",show); g.addEventListener("focus",show); g.addEventListener("click",show);
   dots.appendChild(g);
 });
 const tb=document.getElementById("tb");
 CITIES.forEach(c=>{
   const tr=document.createElement("tr");
   tr.innerHTML='<td class="c"><b>'+c.n+'</b>'+(c.contested?'<span class="chip">sources differ</span>':'')+'</td>'
    +'<td class="c">'+c.cat+'</td><td class="q">«'+c.q+'»</td><td class="c">'+c.t+'</td>'
    +'<td class="c">'+(c.days||'')+'</td>'
    +'<td class="c">'+c.status+'</td>'
    +'<td><a href="'+c.url+'" target="_blank" rel="noopener noreferrer">'+c.src+'</a></td>';
   tr.addEventListener("mouseenter",()=>render(c));
   tb.appendChild(tr);
 });
})();
</script>
"""

j = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
out = (HTML.replace("__DATA__", j(DATA))
           .replace("__LAND__", j([r for _, rings in REGIONS for r in rings]))
           .replace("__COUNTRY__", j(COUNTRY))
           .replace("__N__", str(len(cities)))
           .replace("__DAYS__", str(NDAYS))
           .replace("__LIVE__", str(len(live)))
           .replace("__SNAP__", SNAPSHOT)
           .replace("__STATUS__", STATUS_LINE)
           .replace("__AUTHOR__", AUTHOR)
           .replace("__TITLE__", TITLE)
           .replace("__SUBTITLE__", SUBTITLE))

# ---- schema.org/Dataset ---------------------------------------------------------
# Google Dataset Search reads JSON-LD, not prose: without this block the dataset is
# invisible to it no matter how the README is written. Repo-level URLs, so they live
# here rather than in the dataset's meta.json.
REPO = "https://github.com/KSE-Sociological-Center/fedorov-protests-2026"
SITE = "https://kse-sociological-center.github.io/fedorov-protests-2026/"
RAW = REPO.replace("github.com", "raw.githubusercontent.com") + "/main/" + DS.replace("\\", "/")

first = min((c["first_day"] for c in cities if c.get("first_day")), default="")
last = max((c["last_day"] for c in cities if c.get("last_day")), default="")
LD = {
    "@context": "https://schema.org/",
    "@type": "Dataset",
    "name": "%s / %s" % (META["title"], META["title_en"]),
    "alternateName": [META["subtitle"], META["subtitle_en"], "Картонкові протести",
                      "Cardboard protests"],
    "description": (
        "Датасет публікацій українських ЗМІ про «картонкові протести» проти звільнення "
        "Михайла Федорова з посади міністра оборони України, %s. %d публікацій, %d міст, "
        "%d днів: місто, оцінка кількості учасників, дослівна цитата джерела, посилання. "
        "Дані зібрані з національних, регіональних і місцевих медіа. — A dataset of Ukrainian "
        "media publications on the «cardboard protests» over Mykhailo Fedorov's departure from "
        "the Defence Ministry: %d publications, %d cities, city-level crowd-size estimates with "
        "verbatim source quotes and links."
    ) % (META["subtitle"], len(pubs), len(cities), NDAYS, len(pubs), len(cities)),
    "url": SITE,
    "sameAs": REPO,
    "inLanguage": ["uk", "en"],
    "isAccessibleForFree": True,
    "license": "https://creativecommons.org/licenses/by/4.0/",
    "keywords": [
        "картонкові протести", "протести Федоров", "Михайло Федоров", "Міноборони",
        "протести в Україні 2026", "мапа протестів", "кількість учасників протестів",
        "моніторинг ЗМІ", "Україна", "cardboard protests", "Ukraine protests",
        "Mykhailo Fedorov", "protest dataset", "media monitoring", "protest map",
    ],
    "temporalCoverage": "%s/%s" % (first or META["date"], last or META["date"]),
    "spatialCoverage": {"@type": "Place", "name": "Ukraine",
                        "geo": {"@type": "GeoShape", "box": "44.3 21.7 52.45 40.35"}},
    "datePublished": META["date"],
    "dateModified": AUDIT_ISO,
    "creator": {
        "@type": "Person", "name": META["author_en"].split(",")[0].strip(),
        "affiliation": {"@type": "Organization",
                        "name": "Center for Sociological Research, KSE University",
                        "url": "https://kse.ua/"},
    },
    "publisher": {"@type": "Organization", "name": "KSE University", "url": "https://kse.ua/"},
    "distribution": [
        {"@type": "DataDownload", "name": "cities.csv — one row per location",
         "encodingFormat": "text/csv", "contentUrl": RAW + "/cities.csv"},
        {"@type": "DataDownload", "name": "publications.csv — one row per publication x city",
         "encodingFormat": "text/csv", "contentUrl": RAW + "/publications.csv"},
        {"@type": "DataDownload", "name": "by_day.csv — approximate turnout per city per day",
         "encodingFormat": "text/csv", "contentUrl": RAW + "/by_day.csv"},
    ],
    "variableMeasured": [
        {"@type": "PropertyValue", "name": "category",
         "description": "banded crowd-size estimate: 5000+, 1000-4999, 100-999, <100, unknown, online"},
        {"@type": "PropertyValue", "name": "days_active",
         "description": "distinct days on which a protest in that city is documented"},
        {"@type": "PropertyValue", "name": "quote_uk",
         "description": "verbatim crowd-size quote, in the original Ukrainian"},
    ],
}
LDTAG = '<script type="application/ld+json">%s</script>\n' % json.dumps(
    LD, ensure_ascii=False, indent=1)
out = LDTAG + out
slop_markers = ("1 SEP UPDATE", "REVISED UPWARD", "NEW in the 6 Aug run",
                "Settled to took place", "The only city where")
leaked = [marker for marker in slop_markers if marker in out]
if leaked:
    raise SystemExit("internal audit prose leaked into map: " + ", ".join(leaked))
io.open(ds("map.html"), "w", encoding="utf-8").write(out)
print("cities: %d | active at close: %d | size: %d KB" % (len(cities), len(live), len(out.encode("utf-8")) // 1024))

# ---- optional: the same page as the repo's GitHub Pages site --------------------
if "--site" in sys.argv:
    site = out.replace("<title>", '<link rel="canonical" href="%s">\n<meta name="description" '
                       'content="%s">\n<meta property="og:image" content="%smap.png">\n<title>'
                       % (SITE, LD["description"][:300].replace('"', "&quot;"), SITE), 1)
    os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
    io.open(os.path.join(HERE, "docs", "index.html"), "w", encoding="utf-8").write(site)
    for f in ("map.png", "chart_by_day.png"):
        src, dst = ds(f), os.path.join(HERE, "docs", f)
        if os.path.exists(src):
            io.open(dst, "wb").write(io.open(src, "rb").read())
    io.open(os.path.join(HERE, "docs", ".nojekyll"), "w", encoding="utf-8").write("")
    print("site: docs/index.html (+ map.png, chart_by_day.png)")
