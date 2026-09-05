#!/usr/bin/env python3
"""Build index.html for the Project Outbreak site from the published Workshop listing data.

Sources (all published, nothing in progress):
  assets/data/workshop-po.json      the Project Outbreak Zombies listing (versions, changelog, images)
  assets/data/workshop-family.json  the other published add-ons by the same author
  assets/shots/, assets/family/, assets/cards/   images downloaded from the listings and the shipped card art
Live numbers (servers, players, rank) are fetched by the page at view time from the sibling
stats site at /outbreak-stats/latest.json (same origin on GitHub Pages).
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PO = json.loads((ROOT / "assets/data/workshop-po.json").read_text(encoding="utf-8"))
FAMILY = json.loads((ROOT / "assets/data/workshop-family.json").read_text(encoding="utf-8"))

DISCORD = "https://discord.gg/JumfhFujRF"
STATS_SITE = "https://outbreakarma.github.io/outbreak-stats/"
STATS_JSON = "https://outbreakarma.github.io/outbreak-stats/latest.json"
GITHUB = "https://github.com/outbreakarma"

E = html.escape


def mb(n: int | None) -> str:
    return f"{n / 1048576:.0f} MB" if n else "?"


def date(iso: str | None) -> str:
    return iso[:10] if iso else "?"


def bullets(changelog: str | None) -> list[str]:
    out = []
    for line in (changelog or "").splitlines():
        line = line.strip()
        if line.startswith("-"):
            out.append(line[1:].strip())
    return out


ROLES = [
    {"name": "Shambler", "pace": "Slow", "img": "assets/cards/PO_Card_Shambler_Military.png", "img2": "assets/cards/PO_Card_Shambler_Civilian.png",
     "blurb": "The slow archetype. Numbers over speed: the wall that keeps coming while you reload."},
    {"name": "Sprinter", "pace": "Fast", "img": "assets/cards/PO_Card_Sprinter_Military.png", "img2": "assets/cards/PO_Card_Sprinter_Civilian.png",
     "blurb": "The fast archetype. Closes distance in seconds and tackles what it catches."},
    {"name": "Feral", "pace": "Crawling", "img": "assets/cards/PO_Card_Feral_Military.png", "img2": "assets/cards/PO_Card_Feral_Civilian.png",
     "blurb": "The crawling archetype. Low, quick and hard to spot in cover and crops."},
]

SHOTS = [
    {"full": "assets/shots/po_07.jpg", "mid": "assets/shots/po_08.jpg", "small": "assets/shots/po_09.jpg", "alt": "A horde pours through a fence line toward a sandbagged position between two bunkers"},
    {"full": "assets/shots/po_10.jpg", "mid": "assets/shots/po_11.jpg", "small": "assets/shots/po_12.jpg", "alt": "Night rain at a checkpoint: soldiers behind sandbags and a turret gunner fire into an advancing crowd"},
    {"full": "assets/shots/po_13.jpg", "mid": "assets/shots/po_14.jpg", "small": "assets/shots/po_15.jpg", "alt": "A dozen infected in torn civilian and military clothes walk through a wheat field"},
]

FAMILY_ORDER = ["7B763100BAFA1F9A", "6209E38AB237098E", "6B9BD0DA529C0D1E", "4FD4A1BD550793F4", "40B5686CC205703A"]
FAMILY_ROLE = {
    "7B763100BAFA1F9A": "Optional module",
    "6209E38AB237098E": "Optional module",
    "6B9BD0DA529C0D1E": "Optional module",
    "4FD4A1BD550793F4": "Required by Project Outbreak",
    "40B5686CC205703A": "Same author, standalone",
}


def role_cards() -> str:
    return "".join(
        f'<article class="role"><div class="role-art"><img src="{r["img"]}" alt="{E(r["name"])} card art" loading="lazy" width="512" height="384"><img class="alt" src="{r["img2"]}" alt="" loading="lazy" width="512" height="384"></div>'
        f'<div class="role-body"><div class="pace">{E(r["pace"])}</div><h3>{E(r["name"])}</h3><p>{E(r["blurb"])}</p></div></article>'
        for r in ROLES
    )


def shot_figures() -> str:
    return "".join(
        f'<figure class="shot"><a href="{s["full"]}" target="_blank" rel="noopener"><img src="{s["mid"]}" srcset="{s["small"]} 776w, {s["mid"]} 1480w, {s["full"]} 1920w" sizes="(max-width: 700px) 100vw, 60vw" alt="{E(s["alt"])}" loading="lazy" width="1480" height="832"></a><figcaption>{E(s["alt"])}</figcaption></figure>'
        for s in SHOTS
    )


def family_cards() -> str:
    by_id = {f["id"]: f for f in FAMILY}
    out = []
    for mod_id in FAMILY_ORDER:
        f = by_id.get(mod_id)
        if not f:
            continue
        img = f.get("previewFile", "")
        out.append(
            f'<article class="fam" data-mod="{mod_id}">'
            f'<a class="fam-art" href="{E(f["workshopUrl"])}" target="_blank" rel="noopener"><img src="{img}" alt="{E(f["name"])} Workshop preview" loading="lazy"></a>'
            f'<div class="fam-body"><div class="pace">{E(FAMILY_ROLE.get(mod_id, ""))}</div><h3>{E(f["name"])}</h3><p>{E(f.get("summary") or "")}</p>'
            f'<div class="facts"><span>v{E(f["version"])}</span><span>{E(str(f["downloads"] or 0))} downloads</span><span>{int(round((f["rating"] or 0) * 100))}% rating</span><span class="live" data-live="{mod_id}">live: …</span></div>'
            f'<div class="links"><a class="btn small" href="{E(f["workshopUrl"])}" target="_blank" rel="noopener">Workshop</a></div></div></article>'
        )
    return "".join(out)


def version_rows() -> str:
    return "".join(
        f'<tr><td class="mono">{E(v["version"])}</td><td class="mono">{E(date(v["createdAt"]))}</td><td class="mono">{E(v.get("gameVersion") or "")}</td><td class="mono num">{mb(v.get("size"))}</td></tr>'
        for v in PO["versions"]
    )


def changelog_list() -> str:
    return "".join(f"<li>{E(b)}</li>" for b in bullets(PO.get("changelog")))


def family_changelogs() -> str:
    by_id = {f["id"]: f for f in FAMILY}
    out = []
    for mod_id in FAMILY_ORDER:
        f = by_id.get(mod_id)
        if not f or not bullets(f.get("changelog")):
            continue
        head = (f.get("changelog") or "").strip().splitlines()[0]
        out.append(f'<details><summary>{E(f["name"])} <span class="mono">{E(head)}</span></summary><ul>' + "".join(f"<li>{E(b)}</li>" for b in bullets(f.get("changelog"))) + "</ul></details>")
    return "".join(out)


page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project Outbreak</title>
<meta name="description" content="{E(PO["summary"])} A zombie sandbox add-on for Arma Reforger, on the Workshop.">
<meta property="og:title" content="Project Outbreak">
<meta property="og:description" content="{E(PO["summary"])}">
<meta property="og:image" content="https://outbreakarma.github.io/assets/shots/po_00.jpg">
<meta property="og:type" content="website">
<link rel="icon" href="assets/cards/Outbreak_FactionIcon_ui.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{
  --ground:#0c0a08; --ground-2:#14110d; --panel:#181410; --panel-2:#1f1a14; --line:#2c251d; --line-2:#3a3126;
  --bone:#efe7d6; --bone-2:#cfc4b0; --muted:#9d9283; --ember:#e8931f; --ember-2:#f5b34a; --ember-soft:#2e1d08; --rust:#b8461f; --ok:#7fbf7a;
  --display:'Anton','Impact','Arial Narrow',sans-serif; --body:'Public Sans','Segoe UI',system-ui,sans-serif; --mono:'IBM Plex Mono',ui-monospace,Consolas,monospace;
  color-scheme:dark;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth;background:var(--ground)}}
body{{margin:0;background:var(--ground);color:var(--bone);font-family:var(--body);font-size:17px;line-height:1.55}}
body::before{{content:"";position:fixed;inset:0;pointer-events:none;opacity:.055;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");z-index:0}}
a{{color:var(--ember-2)}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 22px;position:relative;z-index:1}}
nav.top{{position:sticky;top:0;z-index:5;background:rgba(12,10,8,.82);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}}
nav.top .wrap{{display:flex;align-items:center;justify-content:space-between;gap:16px;height:58px}}
nav.top .logo{{display:flex;align-items:center;gap:10px;font-family:var(--display);font-size:22px;letter-spacing:.06em;text-transform:uppercase;color:var(--bone);text-decoration:none}}
nav.top .logo img{{width:30px;height:30px}}
nav.top ul{{display:flex;gap:18px;list-style:none;margin:0;padding:0;font-size:14px;font-weight:600;letter-spacing:.04em;text-transform:uppercase}}
nav.top ul a{{color:var(--bone-2);text-decoration:none}}
nav.top ul a:hover{{color:var(--ember-2)}}
@media (max-width:820px){{nav.top ul{{display:none}}}}
.hero{{position:relative;min-height:600px;display:flex;align-items:flex-end;overflow:hidden;background:#000}}
.hero img.bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 30%;opacity:.92}}
.hero::after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(12,10,8,.15) 0%,rgba(12,10,8,.35) 45%,rgba(12,10,8,.96) 100%)}}
.hero .wrap{{position:relative;z-index:2;padding-bottom:44px;padding-top:120px;width:100%}}
.eyebrow{{font-family:var(--mono);font-size:12.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--ember-2)}}
.hero h1{{font-family:var(--display);font-size:clamp(56px,10vw,132px);line-height:.88;margin:10px 0 14px;letter-spacing:.02em;text-transform:uppercase;color:#fff;text-shadow:0 6px 40px rgba(0,0,0,.7)}}
.hero h1 span{{color:var(--ember)}}
.hero p.lead{{font-size:clamp(18px,2.2vw,24px);max-width:56ch;margin:0 0 22px;color:var(--bone);text-shadow:0 2px 12px rgba(0,0,0,.8)}}
.cta{{display:flex;flex-wrap:wrap;gap:12px;align-items:center}}
.btn{{display:inline-flex;align-items:center;gap:8px;padding:13px 20px;border-radius:3px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:14px;text-decoration:none;border:1px solid var(--ember);color:#1a1005;background:linear-gradient(180deg,var(--ember-2),var(--ember));box-shadow:0 8px 24px rgba(232,147,31,.25)}}
.btn.ghost{{background:rgba(12,10,8,.55);color:var(--bone);border-color:var(--line-2)}}
.btn.small{{padding:8px 12px;font-size:12px}}
.factstrip{{display:flex;flex-wrap:wrap;gap:10px 26px;margin-top:26px;font-family:var(--mono);font-size:13px;color:var(--bone-2)}}
.factstrip b{{color:#fff;font-weight:500}}
.credit{{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-top:14px}}
section{{padding:64px 0 10px}}
h2{{font-family:var(--display);font-size:clamp(34px,5vw,56px);letter-spacing:.03em;text-transform:uppercase;margin:0 0 8px;line-height:1;color:#fff}}
h2 em{{font-style:normal;color:var(--ember)}}
.sub{{color:var(--muted);max-width:70ch;margin:0 0 26px;font-size:17px}}
.live-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}
.tile{{background:linear-gradient(180deg,var(--panel-2),var(--panel));border:1px solid var(--line-2);border-radius:4px;padding:16px 18px;position:relative}}
.tile::before{{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--ember)}}
.tile .k{{font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}}
.tile .v{{font-family:var(--display);font-size:52px;line-height:1;margin-top:6px;color:#fff;font-variant-numeric:tabular-nums}}
.tile .d{{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:6px}}
.roles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}
.role{{background:var(--panel);border:1px solid var(--line-2);border-radius:4px;overflow:hidden;display:flex;flex-direction:column}}
.role-art{{position:relative;aspect-ratio:4/3;background:#000}}
.role-art img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:opacity .35s}}
.role-art img.alt{{opacity:0}}
.role:hover .role-art img.alt{{opacity:1}}
.role-body{{padding:16px 18px 18px}}
.pace{{font-family:var(--mono);font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--ember-2)}}
.role h3,.fam h3{{font-family:var(--display);font-size:30px;letter-spacing:.03em;margin:4px 0 6px;color:#fff;text-transform:uppercase}}
.role p,.fam p{{margin:0;color:var(--bone-2)}}
.gm{{display:grid;grid-template-columns:1.1fr .9fr;gap:22px;align-items:center}}
@media (max-width:820px){{.gm{{grid-template-columns:1fr}}}}
.gm ul{{margin:0;padding-left:0;list-style:none;display:grid;gap:12px}}
.gm li{{background:var(--panel);border:1px solid var(--line-2);border-left:3px solid var(--ember);padding:12px 14px;border-radius:3px}}
.gm li b{{display:block;font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ember-2);margin-bottom:4px}}
.gm img{{width:100%;border-radius:4px;border:1px solid var(--line-2);display:block}}
.shots{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}}
.shot{{margin:0}}
.shot img{{width:100%;height:auto;display:block;border-radius:4px;border:1px solid var(--line-2)}}
.shot figcaption{{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:8px}}
.fams{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
.fam{{background:var(--panel);border:1px solid var(--line-2);border-radius:4px;overflow:hidden;display:flex;flex-direction:column}}
.fam-art{{display:block;aspect-ratio:16/9;background:#000}}
.fam-art img{{width:100%;height:100%;object-fit:cover;display:block}}
.fam-body{{padding:14px 16px 16px;display:flex;flex-direction:column;gap:8px;flex:1}}
.facts{{display:flex;flex-wrap:wrap;gap:6px 12px;font-family:var(--mono);font-size:12px;color:var(--muted)}}
.facts .live{{color:var(--ok)}}
.links{{margin-top:auto;padding-top:6px}}
.two{{display:grid;grid-template-columns:1.2fr .8fr;gap:24px}}
@media (max-width:820px){{.two{{grid-template-columns:1fr}}}}
.changelog{{background:var(--panel);border:1px solid var(--line-2);border-radius:4px;padding:18px 22px}}
.changelog h3{{font-family:var(--mono);font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:var(--ember-2);margin:0 0 10px}}
.changelog ul{{margin:0;padding-left:20px;color:var(--bone-2)}}
.changelog li{{margin:6px 0}}
details{{border-top:1px solid var(--line);padding:10px 0}}
summary{{cursor:pointer;font-weight:600;color:var(--bone)}}
summary .mono{{color:var(--muted);font-weight:400;margin-left:8px}}
details ul{{margin:8px 0 0;padding-left:20px;color:var(--bone-2)}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}}
th{{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:400}}
.mono{{font-family:var(--mono)}}
.num{{text-align:right}}
.tablewrap{{overflow-x:auto;background:var(--panel);border:1px solid var(--line-2);border-radius:4px}}
.credits{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
.credits div{{background:var(--panel);border:1px solid var(--line-2);border-radius:4px;padding:14px 16px;font-size:15px;color:var(--bone-2)}}
.credits b{{display:block;font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ember-2);margin-bottom:6px}}
footer{{margin-top:60px;border-top:1px solid var(--line-2);padding:26px 0 40px;color:var(--muted);font-size:14px}}
footer .wrap{{display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px 24px}}
footer a{{color:var(--bone-2)}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important;scroll-behavior:auto}}}}
</style>
</head>
<body>
<nav class="top"><div class="wrap">
  <a class="logo" href="#top"><img src="assets/cards/Outbreak_FactionIcon_ui.png" alt="">Project Outbreak</a>
  <ul><li><a href="#live">Live</a></li><li><a href="#infected">The infected</a></li><li><a href="#gm">Game Master</a></li><li><a href="#shots">Screenshots</a></li><li><a href="#family">Add-ons</a></li><li><a href="#changes">Changes</a></li><li><a href="{E(PO["workshopUrl"])}" target="_blank" rel="noopener">Workshop</a></li></ul>
</div></nav>

<header class="hero" id="top">
  <img class="bg" src="assets/shots/po_00.jpg" alt="" fetchpriority="high">
  <div class="wrap">
    <div class="eyebrow">Arma Reforger · Workshop add-on · version {E(PO["version"])}</div>
    <h1>Project <span>Outbreak</span></h1>
    <p class="lead">{E(PO["summary"])} Place them through Game Master, or let ambient populations and directed waves shape an entire scenario.</p>
    <div class="cta">
      <a class="btn" href="{E(PO["workshopUrl"])}" target="_blank" rel="noopener">Get it on the Workshop</a>
      <a class="btn ghost" href="{DISCORD}" target="_blank" rel="noopener">Join the Discord</a>
      <a class="btn ghost" href="{STATS_SITE}" target="_blank" rel="noopener">Live server stats</a>
    </div>
    <div class="factstrip">
      <span>Downloads <b>{PO["downloads"]:,}</b></span>
      <span>Rating <b>{int(round((PO["rating"] or 0) * 100))}%</b> from {PO["ratingCount"]} ratings</span>
      <span>Game <b>{E(PO["gameVersion"])}</b></span>
      <span>Size <b>{mb(PO["sizeBytes"])}</b></span>
      <span>Licence <b>{E(PO["license"])}</b></span>
      <span>Updated <b>{E(date(PO["updatedAt"]))}</b></span>
    </div>
    <div class="credit">Title art by redeye.vol2, as credited on the Workshop listing.</div>
  </div>
</header>

<section id="live"><div class="wrap">
  <h2>On servers <em>right now</em></h2>
  <p class="sub">Counted hourly from the public Arma Reforger server list by our <a href="{STATS_SITE}" target="_blank" rel="noopener">server watch</a> (data from ArmaHQ). Players are the people on servers running the add-on, not subscribers.</p>
  <div class="live-grid" id="live-grid">
    <div class="tile"><div class="k">Servers running it</div><div class="v" data-k="servers">…</div><div class="d" data-k="servers-d"></div></div>
    <div class="tile"><div class="k">Players on them</div><div class="v" data-k="players">…</div><div class="d" data-k="players-d"></div></div>
    <div class="tile"><div class="k">Rank among zombie mods</div><div class="v" data-k="rank">…</div><div class="d" data-k="rank-d"></div></div>
    <div class="tile"><div class="k">Versions in use</div><div class="v" data-k="versions">…</div><div class="d" data-k="versions-d"></div></div>
  </div>
</div></section>

<section id="infected"><div class="wrap">
  <h2>The <em>infected</em></h2>
  <p class="sub">Three archetypes ship in the core add-on, each with its own animations and behaviour, in civilian and military dress. Health and damage are yours to tune.</p>
  <div class="roles">{role_cards()}</div>
</div></section>

<section id="gm"><div class="wrap">
  <h2>Built for <em>Game Master</em></h2>
  <p class="sub">Everything is placeable and configurable from the Game Master interface, on your own scenarios and servers.</p>
  <div class="gm">
    <ul>
      <li><b>Place them directly</b>Single creatures and groups of four, eight or sixteen, plus a mixed horde card, straight from the Outbreak faction in Game Master.</li>
      <li><b>Ambient populations and directed waves</b>Let the sandbox populate itself, or author waves and routes to drive a whole scenario.</li>
      <li><b>Zombie Permanent Kills</b>A global setting. In the headshots, explosives and fire mode, ordinary body damage only knocks zombies down; a headshot, an explosion or fire finishes them. Works with ACE Medical hit-zone mods since {E(PO["version"])}.</li>
      <li><b>Placing ignores AI limit</b>Off by default. Turn it on to keep placing creatures by hand after the active-AI budget is full; ambience, directed spawning and reanimation keep their own budgets.</li>
      <li><b>Downed is not safe</b>Zombies feed on knocked-out survivors, more than one at a time, and finish them unless someone drives them off or revives them.</li>
    </ul>
    <img src="assets/cards/PO_Card_Director.png" alt="The Outbreak Director card art" loading="lazy" width="512" height="384">
  </div>
</div></section>

<section id="shots"><div class="wrap">
  <h2>From the <em>field</em></h2>
  <p class="sub">Screenshots from the Workshop listing.</p>
  <div class="shots">{shot_figures()}</div>
</div></section>

<section id="family"><div class="wrap">
  <h2>The Outbreak <em>family</em></h2>
  <p class="sub">Optional modules extend the core add-on; Creature Melee AI is the foundation it runs on. Live server counts come from the server watch.</p>
  <div class="fams">{family_cards()}</div>
</div></section>

<section id="changes"><div class="wrap">
  <h2>What <em>changed</em></h2>
  <p class="sub">Published change notes, straight from the Workshop.</p>
  <div class="two">
    <div>
      <div class="changelog"><h3>Project Outbreak Zombies {E(PO["version"])}</h3><ul>{changelog_list()}</ul></div>
      <div style="margin-top:14px">{family_changelogs()}</div>
    </div>
    <div class="tablewrap"><table><thead><tr><th>Version</th><th>Published</th><th>Game</th><th class="num">Size</th></tr></thead><tbody>{version_rows()}</tbody></table></div>
  </div>
</div></section>

<section id="credits"><div class="wrap">
  <h2>Credits and <em>licence</em></h2>
  <div class="credits">
    <div><b>Licence</b>Original Project Outbreak content is released under the Arma Public License (APL). Incorporated assets remain under the Fab Standard License.</div>
    <div><b>Animation and sound</b>Several attack and tackling animations and sounds come from Yummy Games. Feral movement uses Crawling Ghoul Anims by RamsterZ. The Gadgets spear movement is adapted from work by Bacengdu.</div>
    <div><b>Dependency</b>Requires Creature Melee AI by the same author. Arma Reforger, Enfusion and Workbench are by Bohemia Interactive.</div>
    <div><b>Not affiliated</b>Project Outbreak is an unofficial community project and is not endorsed by Bohemia Interactive. Server data on this site comes from ArmaHQ.</div>
  </div>
</div></section>

<footer><div class="wrap">
  <span>Project Outbreak · <a href="{E(PO["workshopUrl"])}" target="_blank" rel="noopener">Workshop</a> · <a href="{DISCORD}" target="_blank" rel="noopener">Discord</a> · <a href="{STATS_SITE}" target="_blank" rel="noopener">Server watch</a> · <a href="{GITHUB}" target="_blank" rel="noopener">GitHub</a></span>
  <span class="mono">Built from the published listing, {E(date(PO["updatedAt"]))} · listing id {E(PO["id"])}</span>
</div></footer>

<script>
(function(){{
  const fmt = n => (n==null?'–':Number(n).toLocaleString('en-US'));
  const set = (k,v) => {{ const el=document.querySelector('[data-k="'+k+'"]'); if(el) el.textContent=v; }};
  fetch('{STATS_JSON}', {{cache:'no-store'}}).then(r=>r.ok?r.json():Promise.reject(r.status)).then(L=>{{
    const t = L.tracked && L.tracked['{PO["id"]}'];
    const kw = L.keyword || {{}};
    if (t && t.seen){{
      set('servers', fmt(t.servers)); set('servers-d', fmt(t.serversWithPlayers)+' with players');
      set('players', fmt(t.players)); set('players-d', fmt(t.capacity)+' slots available');
      set('rank', t.keywordRank ? '#'+t.keywordRank : '–'); set('rank-d', 'of '+fmt(kw.modCount)+' zombie mods · #'+fmt(t.globalRank)+' of all mods');
      const vs = Object.entries(t.versions||{{}});
      set('versions', vs.length); set('versions-d', vs.slice(0,3).map(([v,c])=>v+' ×'+c).join(' · '));
    }} else {{ set('servers','0'); set('servers-d','not seen in the last snapshot'); }}
    document.querySelectorAll('[data-live]').forEach(el=>{{
      const m = L.tracked && L.tracked[el.getAttribute('data-live')];
      el.textContent = (m && m.seen) ? 'live: '+fmt(m.servers)+' servers · '+fmt(m.players)+' players' : 'live: not on servers';
    }});
    const when = new Date(L.generatedUtc);
    const sub = document.querySelector('#live .sub'); if (sub) sub.insertAdjacentHTML('beforeend', ' Snapshot '+when.toISOString().replace('T',' ').slice(0,16)+' UTC.');
  }}).catch(()=>{{ ['servers','players','rank','versions'].forEach(k=>set(k,'–')); set('servers-d','live numbers unavailable right now'); document.querySelectorAll('[data-live]').forEach(el=>el.textContent=''); }});
}})();
</script>
</body>
</html>
"""

(ROOT / "index.html").write_text(page, encoding="utf-8")
(ROOT / ".nojekyll").touch()
print(f"wrote index.html ({len(page):,} chars) for {PO['name']} {PO['version']}, {len(FAMILY)} family add-ons")
