# -*- coding: utf-8 -*-
"""data/<event>/cities.csv + geo.py -> data/<event>/map.html (black-and-white interactive page)"""
import csv, io, json, os
from geo import COUNTRY, REGIONS

HERE = os.path.dirname(os.path.abspath(__file__))
import json, sys

# Dataset path as an argument, otherwise data/<event>/ buys nothing: the next
# event would still require code edits.
DS = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "data/2026-07-16-fedorov"
ds = lambda n: os.path.join(HERE, DS, n)
META = json.load(io.open(ds("meta.json"), encoding="utf-8"))

SNAPSHOT = META["snapshot"]
AUTHOR = META["author_en"]

cities = list(csv.DictReader(io.open(ds("cities.csv"), encoding="utf-8")))
ORDER = {"5000+": 0, "1000–4999": 1, "100–999": 2, "<100": 3, "unknown": 4, "online": 5}
cities.sort(key=lambda c: (ORDER.get(c["category"], 9), c["city"]))
live = [c["city"] for c in cities if c["status"].startswith("ongoing")]

LABEL_DIR = {
    "Kyiv": "up", "Kharkiv": "right", "Dnipro": "right", "Lviv": "left", "Odesa": "down",
    "Ivano-Frankivsk": "left", "Ternopil": "up", "Khmelnytskyi": "down", "Lutsk": "left",
    "Cherkasy": "down", "Poltava": "up", "Zaporizhzhia": "right", "Kropyvnytskyi": "down",
    "Uzhhorod": "right", "Rivne": "right", "Mykolaiv": "left", "Chernivtsi": "down",
    "Zhytomyr": "up", "Sumy": "right", "Kolomyia": "down", "Vinnytsia": "right",
    "Chernihiv": "up", "Kryvyi Rih": "down", "Kremenchuk": "down", "Kherson": "down",
    "Mukachevo": "down", "Kamianske": "up", "Uman": "down",
    "Izmail": "left", "Kalush": "up", "Sheptytskyi": "left",
    "Oleksandriia": "left", "Kamianets-Podilskyi": "down",
}

DATA = [dict(n=c["city"], ob=c["oblast"], lat=float(c["lat"]), lon=float(c["lon"]),
             cat=c["category"], q=c["quote_uk"], qen=c["quote_en"], t=c["time"], src=c["source"],
             url=c["link"], contested=c["contested"] == "yes", status=c["status"],
             days=c.get("days_active", ""), first=c.get("first_day", ""),
             last=c.get("last_day", ""), peak=c.get("peak_day", ""),
             note=c["note"], dir=LABEL_DIR.get(c["city"], "down")) for c in cities]

HTML = """<title>__TITLE__ — map</title>
<style>
  :root {
    --paper:#fff; --ink:#111; --ink-2:#555; --ink-3:#8a8a8a;
    --land:#fff; --oblast:#c4c4c4; --border:#222; --rule:#e2e2e2; --panel:#fafafa;
    --dot:#111; --dot-fill:rgba(0,0,0,.22);
    --f: "Segoe UI","Noto Sans",system-ui,-apple-system,sans-serif;
  }
  @media (prefers-color-scheme: dark) {
    :root { --paper:#0e0e0f; --ink:#ededed; --ink-2:#a6a6a6; --ink-3:#6f6f6f;
            --land:#181818; --oblast:#3a3a3a; --border:#c8c8c8; --rule:#2b2b2b; --panel:#151515;
            --dot:#ededed; --dot-fill:rgba(255,255,255,.26); }
  }
  :root[data-theme="dark"] { --paper:#0e0e0f; --ink:#ededed; --ink-2:#a6a6a6; --ink-3:#6f6f6f;
    --land:#181818; --oblast:#3a3a3a; --border:#c8c8c8; --rule:#2b2b2b; --panel:#151515;
    --dot:#ededed; --dot-fill:rgba(255,255,255,.26); }
  :root[data-theme="light"] { --paper:#fff; --ink:#111; --ink-2:#555; --ink-3:#8a8a8a;
    --land:#fff; --oblast:#c4c4c4; --border:#222; --rule:#e2e2e2; --panel:#fafafa;
    --dot:#111; --dot-fill:rgba(0,0,0,.22); }
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
  .land { fill:var(--land); stroke:var(--oblast); stroke-width:.9; }
  .country { fill:none; stroke:var(--border); stroke-width:1.9; stroke-linejoin:round; }
  .dot { cursor:pointer; }
  .dot circle.body { fill:var(--dot-fill); stroke:var(--dot); stroke-width:1.5; }
  .dot:hover circle.body, .dot:focus-visible circle.body { fill:var(--dot); fill-opacity:.55; }
  .dot:focus-visible { outline:none; }
  .dot.unknown circle.body { fill:none; stroke-dasharray:3 3; }
  .dot.online  circle.body { fill:none; stroke:var(--ink-3); stroke-dasharray:1.5 3; }
  .dot circle.ring { fill:none; stroke:var(--dot); stroke-width:1.3; stroke-dasharray:2.5 3; }
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
    <p class="sub">__SUBTITLE__. Protests in __N__ cities. Figures are each city's peak over the wave.</p>
    <p class="live">Protests are ongoing, figures are preliminary. Snapshot at __SNAP__: in __LIVE__ cities the action was still running. Kherson protested online.</p>
  </header>
  <div class="rule"></div>
  <div class="field">
    <div class="mapbox">
      <svg id="map" viewBox="0 0 1000 690" role="img" aria-label="Map of Ukraine showing cities where protests took place during the wave">
        <g id="land"></g><g id="dots"></g>
      </svg>
    </div>
    <div style="display:flex;flex-direction:column;gap:20px">
      <div class="panel" id="detail" aria-live="polite">
        <p class="idle">Hover a city for the verbatim quote, the time it is valid for, and the source.</p>
      </div>
      <div class="panel">
        <h2>Legend</h2>
        <ul class="leg">
          <li><span class="sw"><svg width="40" height="46" viewBox="0 0 40 46"><circle cx="20" cy="23" r="21" fill="var(--dot-fill)" stroke="var(--dot)" stroke-width="1.5"/></svg></span><span>5000+ participants</span></li>
          <li><span class="sw"><svg width="40" height="38" viewBox="0 0 40 38"><circle cx="20" cy="19" r="17" fill="var(--dot-fill)" stroke="var(--dot)" stroke-width="1.5"/></svg></span><span>1000–4999 participants</span></li>
          <li><span class="sw"><svg width="40" height="30" viewBox="0 0 40 30"><circle cx="20" cy="15" r="12" fill="var(--dot-fill)" stroke="var(--dot)" stroke-width="1.5"/></svg></span><span>100–999 participants</span></li>
          <li><span class="sw"><svg width="40" height="20" viewBox="0 0 40 20"><circle cx="20" cy="10" r="6.5" fill="var(--dot-fill)" stroke="var(--dot)" stroke-width="1.5"/></svg></span><span>fewer than 100</span></li>
          <li><span class="sw"><svg width="40" height="20" viewBox="0 0 40 20"><circle cx="20" cy="10" r="6.5" fill="none" stroke="var(--dot)" stroke-width="1.5" stroke-dasharray="3 3"/></svg></span><span>protest held, no count published</span></li>
          <li><span class="sw"><svg width="40" height="20" viewBox="0 0 40 20"><circle cx="20" cy="10" r="6.5" fill="none" stroke="var(--ink-3)" stroke-width="1.5" stroke-dasharray="1.5 3"/></svg></span><span>online action (Kherson)</span></li>
          <li><span class="sw"><svg width="40" height="36" viewBox="0 0 40 36"><circle cx="20" cy="18" r="12" fill="var(--dot-fill)" stroke="var(--dot)" stroke-width="1.5"/><circle cx="20" cy="18" r="16" fill="none" stroke="var(--dot)" stroke-width="1.3" stroke-dasharray="2.5 3"/></svg></span><span>contested: sources disagree</span></li>
        </ul>
      </div>
    </div>
  </div>
  <div class="tablewrap">
    <table>
      <caption>Summary by city. Each figure is the daily peak: agreed across several independent sources, latest, largest. Quotes are verbatim as published.</caption>
      <thead><tr><th>City</th><th>Category</th><th>Quote (verbatim)</th><th>Peak</th><th>Days</th><th>Status</th><th>Source</th></tr></thead>
      <tbody id="tb"></tbody>
    </table>
  </div>
  <footer>
    <p style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">
      <span>Protest sizes are approximate. The project is ongoing; some locations may be missing.</span>
      <span style="font-weight:600;color:var(--ink);white-space:nowrap">__AUTHOR__</span>
    </p>
    <p>Borders and oblasts: Natural Earth 10m. Selection rule: the figure that agrees across several
       independent sources, is the latest in time and the largest, i.e. the daily peak. «Contested» marks a
       genuine disagreement (Kyiv: «сотні людей» in Suspilne against «близько двох тисяч» in Interfax).
       Quotes are taken from page bodies, never from headlines or search snippets, and are left in the
       original Ukrainian: translating a quote would make it evidence of nothing.</p>
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
 const place=(cx,cy,r,dir)=>{const G=6,L=11;
   if(dir==="up")   return {x:cx,a:"middle",y1:cy-r-G-L,y2:cy-r-G};
   if(dir==="down") return {x:cx,a:"middle",y1:cy+r+G+L,y2:cy+r+G+L*2};
   if(dir==="left") return {x:cx-r-G,a:"end",y1:cy+1,y2:cy+1+L};
   return {x:cx+r+G,a:"start",y1:cy+1,y2:cy+1+L};};

 const dots=document.getElementById("dots"), det=document.getElementById("detail");
 function render(c){
   const dur=c.days?(c.days+(c.days==="1"?" day":" days")+" documented, "
     +(c.first||"?").slice(5)+"–"+(c.last||"?").slice(5)):"";
   det.innerHTML='<p class="city">'+c.n+(c.contested?'<span class="chip">contested</span>':'')+'</p>'
    +'<p class="ob">'+c.ob+' · '+c.cat+' · '+c.status+'</p>'
    +(dur?'<p class="ob">'+dur+(c.peak?' · peak '+c.peak.slice(5):'')+'</p>':'')
    +'<blockquote>«'+c.q+'»</blockquote>'
    +(c.qen?'<p class="gloss">'+c.qen+'</p>':'')
    +'<div class="meta"><span>as of '+c.t+'</span>'
    +'<span><a href="'+c.url+'" target="_blank" rel="noopener noreferrer">'+c.src+'</a></span></div>'
    +(c.note?'<p class="note">'+c.note+'</p>':'');
 }
 CITIES.slice().sort((a,b)=>R[b.cat]-R[a.cat]).forEach(c=>{
   const r=R[c.cat], cx=px(c.lon), cy=py(c.lat);
   let cls="dot"+(c.cat==="unknown"?" unknown is-dim":"")+(c.cat==="online"?" online is-dim":"");
   const g=el("g",{class:cls,tabindex:"0",role:"button","aria-label":c.n+", "+c.cat+", "+c.q});
   const ti=el("title",{}); ti.textContent=c.n+" — "+c.cat+": «"+c.q+"» ("+c.src+", "+c.t+")"; g.appendChild(ti);
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
   tr.innerHTML='<td class="c"><b>'+c.n+'</b>'+(c.contested?'<span class="chip">contested</span>':'')+'</td>'
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
           .replace("__LIVE__", str(len(live)))
           .replace("__SNAP__", SNAPSHOT)
           .replace("__AUTHOR__", AUTHOR)
           .replace("__TITLE__", META["title_en"])
           .replace("__SUBTITLE__", META["subtitle_en"]))
io.open(ds("map.html"), "w", encoding="utf-8").write(out)
print("cities: %d | still ongoing: %d | size: %d KB" % (len(cities), len(live), len(out.encode("utf-8")) // 1024))
