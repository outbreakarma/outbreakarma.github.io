#!/usr/bin/env python3
"""Build index.html for the Project Outbreak site from the published Workshop listing data.

Sources (all published, nothing in progress):
  assets/data/workshop-po.json      the Project Outbreak Zombies listing (versions, changelog, images)
  assets/data/workshop-family.json  every other public Workshop item by the same author
  assets/shots/, assets/family/, assets/cards/   images downloaded from the listings and the shipped card art
Live numbers (servers, players, rank, download history) are fetched by the page at view time from the
sibling stats site, /outbreak-stats/trend.json and /outbreak-stats/latest.json (same origin on GitHub Pages).
The page renders completely without them; the live parts then say that the numbers are unavailable.
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
GITHUB = "https://github.com/outbreakarma"
SITE_REPO = "https://github.com/outbreakarma/outbreakarma.github.io"
STATS_REPO = "https://github.com/outbreakarma/outbreak-stats"
RM_MOD = "https://reforgermods.net/mods/{id}/"
AHQ_MOD = "https://www.armahq.com/mods/{id}"
APL = "https://www.bohemia.net/en/community/licenses/arma-public-license"


def clean(text: str | None) -> str:
    """Listing text as shown on the page: no em or en dashes used as punctuation."""
    t = (text or "").replace(" — ", ", ").replace("—", ", ").replace(" – ", " to ").replace("–", "-")
    return t


def E(text) -> str:
    return html.escape(clean(str(text)))


def mb(n: int | None) -> str:
    return f"{n / 1048576:.0f} MB" if n else "?"


def date(iso: str | None) -> str:
    return iso[:10] if iso else "?"


def ws(mod_id: str) -> str:
    return f"https://reforger.armaplatform.com/workshop/{mod_id}"


def ext(href: str, text: str, cls: str = "") -> str:
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{html.escape(href, quote=True)}" target="_blank" rel="noopener">{text}</a>'


def bullets(changelog: str | None) -> list[str]:
    out = []
    for line in (changelog or "").splitlines():
        line = line.strip()
        if line.startswith("-"):
            out.append(line[1:].strip())
    return out


def changelog_html(changelog: str | None, version: str | None) -> str:
    """Bullets as a list, other lines as short paragraphs; a leading version line is dropped."""
    parts, items = [], []
    for raw in (changelog or "").splitlines():
        line = raw.strip()
        if not line or line == (version or ""):
            continue
        if line.startswith("-"):
            items.append(f"<li>{E(line[1:].strip())}</li>")
            continue
        if items:
            parts.append("<ul>" + "".join(items) + "</ul>")
            items = []
        parts.append(f"<p>{E(line)}</p>")
    if items:
        parts.append("<ul>" + "".join(items) + "</ul>")
    return "".join(parts)


ROLES = [
    {"name": "Shambler", "pace": "Slow", "img": "assets/cards/PO_Card_Shambler_Military.png", "img2": "assets/cards/PO_Card_Shambler_Civilian.png",
     "blurb": "The slow archetype. Numbers over speed: the wall that keeps coming while you reload."},
    {"name": "Sprinter", "pace": "Fast", "img": "assets/cards/PO_Card_Sprinter_Military.png", "img2": "assets/cards/PO_Card_Sprinter_Civilian.png",
     "blurb": "The fast archetype. Closes distance in seconds and tackles what it catches."},
    {"name": "Feral", "pace": "Crawling", "img": "assets/cards/PO_Card_Feral_Military.png", "img2": "assets/cards/PO_Card_Feral_Civilian.png",
     "blurb": "The crawling archetype. Low, quick and hard to spot in cover and crops."},
]

IMAGES = json.loads((ROOT / "assets/data/images.json").read_text(encoding="utf-8")) if (ROOT / "assets/data/images.json").exists() else {}
CAPS = json.loads((ROOT / "assets/data/captions.json").read_text(encoding="utf-8")) if (ROOT / "assets/data/captions.json").exists() else {"hero": None, "captions": {}}


def local(url: str | None) -> str:
    return IMAGES.get(url or "", "")


def shots() -> list[dict]:
    """Gallery entries from the listing: the title art first, then every screenshot."""
    items = []
    if PO.get("preview"):
        items.append({"url": PO["preview"], "thumbs": PO.get("previewThumbs", [])})
    for sshot in PO.get("screenshots", []):
        if isinstance(sshot, dict):
            items.append({"url": sshot["url"], "thumbs": sshot.get("thumbs", [])})
        else:
            items.append({"url": sshot, "thumbs": []})
    out = []
    for i, it in enumerate(items):
        full = local(it["url"])
        if not full:
            continue
        thumbs = [local(t) for t in it["thumbs"] if local(t)]
        mid = thumbs[0] if thumbs else full
        small = thumbs[1] if len(thumbs) > 1 else mid
        caption = CAPS["captions"].get(it["url"]) or (f"Screenshot {i} from the Workshop listing" if i else "Workshop title art from the listing")
        out.append({"full": full, "mid": mid, "small": small, "alt": caption})
    return out


def hero() -> tuple[str, str]:
    """The configured hero if the listing still carries it, else the first screenshot, else the title art."""
    all_shots = shots()
    want = local(CAPS.get("hero"))
    for cand in all_shots:
        if want and cand["full"] == want:
            return cand["full"], cand["mid"]
    pick_from = all_shots[1:] or all_shots
    return (pick_from[0]["full"], pick_from[0]["mid"]) if pick_from else ("", "")


SHOTS = shots()
HERO_FULL, HERO_MID = hero()
# The gallery leads with gameplay that is not the hero; the title art also heads the core add-on card.
GALLERY = [s for s in SHOTS[1:] if s["full"] != HERO_FULL] + [s for s in SHOTS[1:] if s["full"] == HERO_FULL] + SHOTS[:1]

PO_ID = PO["id"]
CMAI_ID = "4FD4A1BD550793F4"
# Every public item by the author, in display groups. Ids missing from the listing data are skipped.
GROUPS = [
    {"id": "outbreak", "label": "Project Outbreak", "blurb": "The zombie sandbox and its optional modules. Start with the core add-on, then add what your scenario needs.",
     "items": [PO_ID, "7B763100BAFA1F9A", "6209E38AB237098E", "6B9BD0DA529C0D1E", "384E32C2A832444E", "297640FBAC0C46C3"]},
    {"id": "scenarios", "label": "Scenarios", "blurb": "Ready-to-host multiplayer scenarios that run Project Outbreak for you.",
     "items": ["0B4FB11C20129700", "0B4FB11C20129701"]},
    {"id": "creatures", "label": "Creatures", "blurb": "Stand-alone creature add-ons, each built on Creature Melee AI.",
     "items": ["475357F020261002", "9C6F9425B58142E7", "E1DCD3CAF138441C", "135E4CF7BBB94766"]},
    {"id": "tools", "label": "Foundation and tools", "blurb": "The melee AI framework under every creature here, plus AI support and weapons.",
     "items": [CMAI_ID, "40B5686CC205703A", "3CBDFAB9713149BE", "9E4B2C7A1D5F8036"]},
]
ROLE = {
    PO_ID: "Core add-on",
    "7B763100BAFA1F9A": "Optional module", "6209E38AB237098E": "Optional module", "6B9BD0DA529C0D1E": "Optional module",
    "384E32C2A832444E": "Optional module", "297640FBAC0C46C3": "Optional module, creatures",
    "0B4FB11C20129700": "Scenario", "0B4FB11C20129701": "Scenario, lighter",
    "475357F020261002": "Creature", "9C6F9425B58142E7": "Creatures", "E1DCD3CAF138441C": "Creature", "135E4CF7BBB94766": "Creature",
    CMAI_ID: "Foundation, required", "40B5686CC205703A": "Standalone", "3CBDFAB9713149BE": "Weapon", "9E4B2C7A1D5F8036": "Weapon, work in progress",
}
PO_ENTRY = dict(PO, previewFile=local(PO.get("preview")))
ITEMS = {f["id"]: f for f in FAMILY} | {PO_ID: PO_ENTRY}
FIRST_PARTY = set(ITEMS)
ALL_IDS = [i for g in GROUPS for i in g["items"] if i in ITEMS] + [i for i in ITEMS if i not in {x for g in GROUPS for x in g["items"]}]
TOTAL_DOWNLOADS = sum(int(ITEMS[i].get("downloads") or 0) for i in ALL_IDS)


def plural(n: int, word: str) -> str:
    return word if n == 1 else word + "s"


def rating_text(f: dict) -> str:
    n = int(f.get("ratingCount") or 0)
    if n == 0:
        return "no ratings yet"
    if n < 3:
        return f"{n} rating{'s' if n > 1 else ''}"
    return f"{int(round((f.get('rating') or 0) * 100))}% of {n:,} ratings"


def needs_html(f: dict) -> str:
    deps = f.get("dependencies") or []
    if not deps:
        return ""
    own = [d for d in deps if d["id"] in FIRST_PARTY]
    other = [d for d in deps if d["id"] not in FIRST_PARTY]
    if len(deps) <= 3:
        shown, rest = deps, 0
    else:
        shown, rest = (own or deps[:2]), len(deps) - len(own or deps[:2])
    links = ", ".join(ext(ws(d["id"]), E(d["name"])) for d in shown)
    more = f', and {ext(ws(f["id"]), f"{rest} more")}' if rest else ""
    return f'<div class="needs">Needs {links}{more}</div>' if other or own else ""


def card(mod_id: str, featured: bool = False) -> str:
    f = ITEMS[mod_id]
    img = f.get("previewFile", "")
    cls = "fam reveal" + (" featured" if featured else "")
    cta = ""
    if featured:
        cta = (f'<div class="cta small-cta">{ext(ws(mod_id), "Subscribe on the Workshop", "btn small")}'
               f'{ext(STATS_SITE, "Live server stats", "btn small ghost")}</div>')
    return (
        f'<article class="{cls}" data-mod="{mod_id}">'
        f'<a class="fam-art" href="{ws(mod_id)}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true"><img src="{img}" alt="" loading="lazy"></a>'
        f'<div class="fam-body"><div class="pace">{E(ROLE.get(mod_id, "By the same author"))}</div>'
        f'<h3>{ext(ws(mod_id), E(f["name"]))}</h3><p>{E(f.get("summary") or "")}</p>'
        f'<div class="facts"><span class="ver">v{E(f["version"])}</span><span><b data-dl="{mod_id}" data-build="{int(f.get("downloads") or 0)}">{int(f.get("downloads") or 0):,}</b> {plural(int(f.get("downloads") or 0), "download")}</span><span>{E(rating_text(f))}</span></div>'
        f'<div class="live" data-live="{mod_id}"><i></i><span>checking servers</span></div>'
        f'{needs_html(f)}{cta}'
        f'<div class="links">{ext(ws(mod_id), "Workshop")}{ext(RM_MOD.format(id=mod_id), "Server stats")}{ext(AHQ_MOD.format(id=mod_id), "ArmaHQ")}</div>'
        f'</div></article>'
    )


def groups_html() -> str:
    out = []
    for g in GROUPS:
        ids = [i for i in g["items"] if i in ITEMS]
        if not ids:
            continue
        dl = sum(int(ITEMS[i].get("downloads") or 0) for i in ids)
        cards = "".join(card(i, featured=(i == PO_ID)) for i in ids)
        out.append(
            f'<div class="group g-{g["id"]}" id="group-{g["id"]}"><div class="group-head"><h3>{E(g["label"])}</h3>'
            f'<p>{E(g["blurb"])}</p><span class="count">{len(ids)} item{"s" if len(ids) > 1 else ""} · {dl:,} downloads</span></div>'
            f'<div class="fams n{len(ids)}">{cards}</div></div>'
        )
    return "".join(out)


def role_cards() -> str:
    return "".join(
        f'<article class="role reveal"><div class="role-art"><img src="{r["img"]}" alt="{E(r["name"])} card art" loading="lazy" width="512" height="384"><img class="alt" src="{r["img2"]}" alt="" loading="lazy" width="512" height="384"></div>'
        f'<div class="role-body"><div class="pace">{E(r["pace"])}</div><h3>{E(r["name"])}</h3><p>{E(r["blurb"])}</p></div></article>'
        for r in ROLES
    )


def shot_figures() -> str:
    """The first image spans the full width; the rest fill rows of three without a gap."""
    rest = len(GALLERY) - 1
    out = []
    for i, s in enumerate(GALLERY):
        span = ""
        if i == 0:
            span = " wide"
        elif rest % 3 == 1 and i == len(GALLERY) - 1:
            span = " wide"
        elif rest % 3 == 2 and i >= len(GALLERY) - 2:
            span = " half"
        sizes = "(max-width: 700px) 100vw, 1180px" if span == " wide" else "(max-width: 700px) 100vw, 400px"
        out.append(
            f'<figure class="shot reveal{span}"><a href="{s["full"]}" data-i="{i}" target="_blank" rel="noopener"><img src="{s["mid"]}" srcset="{s["small"]} 776w, {s["mid"]} 1480w, {s["full"]} 1920w" sizes="{sizes}" alt="{E(s["alt"])}" loading="lazy" width="1480" height="832"></a><figcaption>{E(s["alt"])}</figcaption></figure>'
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
    """Every other item's latest change notes, most recently updated first."""
    items = [ITEMS[i] for i in ALL_IDS if i != PO_ID and (ITEMS[i].get("changelog") or "").strip()]
    items.sort(key=lambda f: f.get("updatedAt") or "", reverse=True)
    return "".join(
        f'<details><summary>{E(f["name"])} <span class="mono">v{E(f["version"])} · {E(date(f.get("updatedAt")))}</span></summary>'
        f'<div class="cl">{changelog_html(f.get("changelog"), f.get("version"))}<p class="mono small">{ext(ws(f["id"]) + "/changelog", "Full history on the Workshop")}</p></div></details>'
        for f in items
    )


def link_list(rows: list[tuple[str, str, str]]) -> str:
    return "<ul>" + "".join(f"<li>{ext(href, E(text))}<small>{E(note)}</small></li>" for href, text, note in rows) + "</ul>"


def links_html() -> str:
    every = [(ws(i), ITEMS[i]["name"], f'v{ITEMS[i]["version"]} · {int(ITEMS[i].get("downloads") or 0):,} {plural(int(ITEMS[i].get("downloads") or 0), "download")}') for i in ALL_IDS]
    blocks = [
        ("Community", [
            (DISCORD, "Discord", "Questions, bug reports, server owners and previews"),
            (ws(PO_ID), "Project Outbreak Zombies on the Workshop", "Subscribe, rate and read the full description"),
            (GITHUB, "GitHub", "Both sites are open source"),
        ]),
        ("Live numbers", [
            (STATS_SITE, "Outbreak Server Watch", "Hourly servers, players, downloads and rankings"),
            (RM_MOD.format(id=PO_ID), "Project Outbreak Zombies on ReforgerMods.net", "30-day server and player history"),
            (AHQ_MOD.format(id=PO_ID), "Project Outbreak Zombies on ArmaHQ", "Every server running it right now"),
            (STATS_SITE + "trend.json", "trend.json", "The live numbers on this page, as JSON"),
        ]),
        ("Sources and licences", [
            (APL, "Arma Public License (APL)", "The licence of the original Project Outbreak content"),
            ("https://reforger.armaplatform.com/workshop?search=zombie", "Zombie mods on the Workshop", "Everything else in the genre"),
            (SITE_REPO, "This site's source", "Rebuilt every hour from the public listings"),
            (STATS_REPO, "Server watch source", "Collector, backfill and raw data"),
        ]),
    ]
    out = [f'<div class="lpanel reveal"><h3>{E(t)}</h3>{link_list(rows)}</div>' for t, rows in blocks]
    out.append(f'<div class="lpanel reveal wide-l"><h3>Every add-on</h3>{link_list(every)}</div>')
    return "".join(out)


CSS = r"""
:root{
  --ground:#0c0a08; --ground-2:#14110d; --panel:#181410; --panel-2:#1f1a14; --line:#2c251d; --line-2:#3a3126;
  --bone:#efe7d6; --bone-2:#cfc4b0; --muted:#9d9283; --ember:#e8931f; --ember-2:#f5b34a; --ember-soft:#2e1d08; --rust:#b8461f; --ok:#7fbf7a;
  --display:'Anton','Impact','Arial Narrow',sans-serif; --body:'Public Sans','Segoe UI',system-ui,sans-serif; --mono:'IBM Plex Mono',ui-monospace,Consolas,monospace;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:70px;background:var(--ground)}
body{margin:0;background:var(--ground);color:var(--bone);font-family:var(--body);font-size:17px;line-height:1.55;overflow-x:hidden}
body::before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.055;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");z-index:0}
a{color:var(--ember-2);text-underline-offset:3px;text-decoration-color:rgba(245,179,74,.4)}
a:hover{color:#ffd28a;text-decoration-color:currentColor}
:focus-visible{outline:2px solid var(--ember-2);outline-offset:2px}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px;position:relative;z-index:1}
nav.top{position:sticky;top:0;z-index:20;background:rgba(12,10,8,.82);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
nav.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;height:58px}
nav.top .logo{display:flex;align-items:center;gap:10px;font-family:var(--display);font-size:22px;letter-spacing:.06em;text-transform:uppercase;color:var(--bone);text-decoration:none;flex:none}
nav.top .logo img{width:30px;height:30px}
nav.top ul{display:flex;gap:18px;list-style:none;margin:0;padding:0;font-size:13.5px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;overflow-x:auto;scrollbar-width:none;white-space:nowrap}
nav.top ul::-webkit-scrollbar{display:none}
nav.top ul a{color:var(--bone-2);text-decoration:none;padding:4px 0;border-bottom:2px solid transparent}
nav.top ul a:hover,nav.top ul a.on{color:var(--ember-2);border-color:var(--ember)}
nav.top .navcta{flex:none}
@media (max-width:980px){nav.top .navcta{display:none}}
@media (max-width:700px){nav.top .logo span{display:none}nav.top ul{gap:14px;font-size:12.5px;mask-image:linear-gradient(90deg,#000 85%,transparent)}}
.hero{position:relative;min-height:min(92vh,760px);display:flex;align-items:flex-end;overflow:hidden;background:#000}
.hero img.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 30%;opacity:.92;transform-origin:60% 40%;animation:drift 26s ease-out both}
@keyframes drift{from{transform:scale(1.09)}to{transform:scale(1)}}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(12,10,8,.25) 0%,rgba(12,10,8,.2) 35%,rgba(12,10,8,.97) 100%),radial-gradient(120% 80% at 0% 100%,rgba(12,10,8,.7),transparent 60%)}
.hero .wrap{position:relative;z-index:2;padding-bottom:46px;padding-top:120px;width:100%}
.eyebrow{font-family:var(--mono);font-size:12.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--ember-2)}
.hero h1{font-family:var(--display);font-size:clamp(60px,11vw,148px);line-height:.86;margin:12px 0 16px;letter-spacing:.02em;text-transform:uppercase;color:#fff;text-shadow:0 6px 40px rgba(0,0,0,.7)}
.hero h1 span{color:var(--ember);display:inline-block}
.hero p.lead{font-size:clamp(18px,2.2vw,23px);max-width:56ch;margin:0 0 24px;color:var(--bone);text-shadow:0 2px 12px rgba(0,0,0,.8)}
.livechip{display:inline-flex;align-items:center;gap:10px;padding:7px 14px 7px 12px;border-radius:99px;background:rgba(12,10,8,.62);border:1px solid rgba(127,191,122,.45);backdrop-filter:blur(6px);font-family:var(--mono);font-size:13px;color:var(--bone);text-decoration:none;margin-bottom:6px}
.livechip:hover{border-color:var(--ok);color:#fff}
.livechip i,.live i{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 0 rgba(127,191,122,.6);animation:ping 2.2s infinite;flex:none}
.livechip b{color:#fff;font-weight:500}
.livechip[hidden]{display:none}
@keyframes ping{0%{box-shadow:0 0 0 0 rgba(127,191,122,.55)}70%{box-shadow:0 0 0 9px rgba(127,191,122,0)}100%{box-shadow:0 0 0 0 rgba(127,191,122,0)}}
.cta{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.btn{display:inline-flex;align-items:center;gap:8px;padding:13px 20px;border-radius:3px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:14px;text-decoration:none;border:1px solid var(--ember);color:#1a1005;background:linear-gradient(180deg,var(--ember-2),var(--ember));box-shadow:0 8px 24px rgba(232,147,31,.25);transition:transform .15s,box-shadow .15s}
.btn:hover{color:#1a1005;transform:translateY(-1px);box-shadow:0 12px 30px rgba(232,147,31,.35)}
.btn.ghost{background:rgba(12,10,8,.55);color:var(--bone);border-color:var(--line-2);box-shadow:none}
.btn.ghost:hover{color:#fff;border-color:var(--ember)}
.btn.small{padding:8px 13px;font-size:12px}
.factstrip{display:flex;flex-wrap:wrap;gap:10px 28px;margin-top:28px;font-family:var(--mono);font-size:13px;color:var(--bone-2)}
.factstrip b{color:#fff;font-weight:500}
.factstrip a{color:#fff;text-decoration:none;border-bottom:1px dotted var(--muted)}
section{padding:72px 0 8px}
h2{font-family:var(--display);font-size:clamp(36px,5vw,58px);letter-spacing:.03em;text-transform:uppercase;margin:0 0 8px;line-height:1;color:#fff}
h2 em{font-style:normal;color:var(--ember)}
.sub{color:var(--muted);max-width:72ch;margin:0 0 28px;font-size:17px}
.sub a{color:var(--bone-2)}
.live-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
@media (max-width:980px){.live-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:520px){.live-grid{grid-template-columns:1fr}}
.tile{background:linear-gradient(180deg,var(--panel-2),var(--panel));border:1px solid var(--line-2);border-radius:4px;padding:16px 18px 14px;position:relative;overflow:hidden;min-width:0}
.tile::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--ember)}
.tile .k{font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.tile .v{font-family:var(--display);font-size:56px;line-height:1;margin-top:6px;color:#fff;font-variant-numeric:tabular-nums}
.tile .d{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:6px;min-height:1.5em}
.tile .d .up{color:var(--ok)}
.tile svg{display:block;width:100%;height:44px;margin-top:10px}
.live-wide{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:12px;margin-top:12px}
@media (max-width:820px){.live-wide{grid-template-columns:1fr}}
.split .bars{display:flex;height:14px;border-radius:2px;overflow:hidden;margin:14px 0 12px;background:#000;border:1px solid var(--line)}
.split .bars span{display:block;height:100%;transform-origin:left;transform:scaleX(0);transition:transform 1.2s cubic-bezier(.2,.8,.2,1)}
.split.go .bars span{transform:scaleX(1)}
.split .bars .a{background:var(--ember)} .split .bars .b{background:repeating-linear-gradient(135deg,#9c6a2a 0 6px,#7d5420 6px 12px)}
.split .lg{display:flex;flex-wrap:wrap;gap:6px 26px;font-family:var(--mono);font-size:12.5px;color:var(--muted)}
.split .lg b{font-family:var(--display);font-weight:400;font-size:30px;color:#fff;margin-right:8px;vertical-align:-4px}
.split .lg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px}
.live-foot{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;justify-content:space-between;margin-top:16px;font-family:var(--mono);font-size:12px;color:var(--muted)}
.roles{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.role{background:var(--panel);border:1px solid var(--line-2);border-radius:4px;overflow:hidden;display:flex;flex-direction:column}
.role-art{position:relative;aspect-ratio:4/3;background:#000;overflow:hidden}
.role-art img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:opacity .35s,transform .6s}
.role-art img.alt{opacity:0}
.role:hover .role-art img.alt{opacity:1}
.role:hover .role-art img{transform:scale(1.03)}
.role-body{padding:16px 18px 18px}
.pace{font-family:var(--mono);font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--ember-2)}
.role h3,.fam h3{font-family:var(--display);font-size:30px;letter-spacing:.03em;margin:4px 0 6px;color:#fff;text-transform:uppercase;line-height:1.05}
.fam h3 a{color:inherit;text-decoration:none}
.fam h3 a:hover{color:var(--ember-2)}
.role p,.fam p{margin:0;color:var(--bone-2)}
.gm{display:grid;grid-template-columns:1.1fr .9fr;gap:24px;align-items:center}
@media (max-width:820px){.gm{grid-template-columns:1fr}}
.gm ul{margin:0;padding-left:0;list-style:none;display:grid;gap:12px}
.gm li{background:var(--panel);border:1px solid var(--line-2);border-left:3px solid var(--ember);padding:12px 14px;border-radius:3px}
.gm li b{display:block;font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ember-2);margin-bottom:4px}
.gm-art{margin:0;background:#16171a;border:1px solid var(--line-2);border-radius:4px;padding:18px;position:relative;box-shadow:0 30px 60px rgba(0,0,0,.45)}
.gm-art::before,.gm-art::after{content:"";position:absolute;width:16px;height:16px;border:2px solid var(--ember);opacity:.8}
.gm-art::before{top:-1px;left:-1px;border-right:0;border-bottom:0}
.gm-art::after{bottom:-1px;right:-1px;border-left:0;border-top:0}
.gm-art img{width:100%;display:block;border-radius:2px}
.gm-art figcaption{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-top:10px;letter-spacing:.06em}
.shots{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:14px}
.shot{margin:0;grid-column:span 2;min-width:0}
.shot.wide{grid-column:1/-1}
.shot.half{grid-column:span 3}
@media (max-width:700px){.shot,.shot.half{grid-column:1/-1}}
.shot a{display:block;overflow:hidden;border-radius:4px;border:1px solid var(--line-2);background:#000;cursor:zoom-in}
.shot img{width:100%;height:auto;display:block;transition:transform .6s cubic-bezier(.2,.8,.2,1)}
.shot:not(.wide) img{aspect-ratio:16/9;object-fit:cover}
.shot.wide img{aspect-ratio:21/9;object-fit:cover}
@media (max-width:700px){.shot.wide img{aspect-ratio:16/9}}
.shot a:hover img{transform:scale(1.025)}
.shot figcaption{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:8px}
dialog.lb{border:0;padding:0;background:transparent;max-width:min(96vw,1700px);max-height:96vh;color:var(--bone)}
dialog.lb::backdrop{background:rgba(6,5,4,.92);backdrop-filter:blur(4px)}
dialog.lb img{display:block;max-width:min(96vw,1700px);max-height:84vh;width:auto;height:auto;border-radius:3px;border:1px solid var(--line-2)}
dialog.lb .bar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:10px;font-family:var(--mono);font-size:12.5px;color:var(--bone-2)}
dialog.lb button{all:unset;cursor:pointer;font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;padding:8px 12px;border:1px solid var(--line-2);border-radius:3px;color:var(--bone);background:rgba(12,10,8,.7)}
dialog.lb button:hover{border-color:var(--ember);color:#fff}
dialog.lb button:focus-visible{outline:2px solid var(--ember-2)}
.mods-head{display:flex;flex-wrap:wrap;gap:10px 30px;align-items:baseline;margin:-10px 0 26px;font-family:var(--mono);font-size:13px;color:var(--muted)}
.mods-head b{font-family:var(--display);font-weight:400;font-size:34px;color:#fff;margin-right:8px;vertical-align:-4px}
.mods-head a{color:var(--bone-2)}
.group{margin-top:34px}
.group:first-of-type{margin-top:0}
.group-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 16px;padding-bottom:10px;margin-bottom:16px;border-bottom:1px solid var(--line-2);position:relative}
.group-head::after{content:"";position:absolute;left:0;bottom:-1px;width:64px;height:2px;background:var(--ember)}
.group-head h3{font-family:var(--display);font-size:28px;letter-spacing:.04em;text-transform:uppercase;margin:0;color:#fff;font-weight:400}
.group-head p{margin:0;color:var(--muted);font-size:15px;flex:1 1 320px}
.group-head .count{font-family:var(--mono);font-size:12px;color:var(--muted);letter-spacing:.06em}
.fams{display:grid;gap:16px;grid-template-columns:repeat(4,minmax(0,1fr))}
.fams.n2{grid-template-columns:repeat(2,minmax(0,1fr))}
.fams.n3{grid-template-columns:repeat(3,minmax(0,1fr))}
.g-outbreak .fams{grid-template-columns:repeat(3,minmax(0,1fr))}
.g-outbreak .fam.featured{grid-column:span 2;grid-row:span 2}
@media (max-width:1000px){.fams,.fams.n3,.g-outbreak .fams{grid-template-columns:repeat(2,minmax(0,1fr))}.g-outbreak .fam.featured{grid-row:auto}.g-outbreak .fam:last-child:nth-child(even){grid-column:span 2}}
@media (max-width:600px){.fams,.fams.n2,.fams.n3,.g-outbreak .fams{grid-template-columns:1fr}.g-outbreak .fam.featured,.g-outbreak .fam:last-child:nth-child(even){grid-column:auto}}
.fam{background:var(--panel);border:1px solid var(--line-2);border-radius:4px;overflow:hidden;display:flex;flex-direction:column;min-width:0;transition:border-color .2s,transform .2s,box-shadow .2s}
.fam:hover{border-color:#5a4a36;transform:translateY(-2px);box-shadow:0 14px 34px rgba(0,0,0,.4)}
.fam-art{display:block;aspect-ratio:16/9;background:#000;overflow:hidden}
.fam-art img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .6s cubic-bezier(.2,.8,.2,1)}
.fam:hover .fam-art img{transform:scale(1.04)}
.fam-body{padding:14px 16px 14px;display:flex;flex-direction:column;gap:9px;flex:1}
.fam p{font-size:15px;line-height:1.45}
.fam.featured{border-color:rgba(232,147,31,.55);background:linear-gradient(180deg,#22190f,var(--panel) 60%)}
.fam.featured .fam-art{aspect-ratio:auto;flex:1 1 auto;min-height:240px}
.fam.featured h3{font-size:44px}
.fam.featured p{font-size:16.5px}
.facts{display:flex;flex-wrap:wrap;gap:4px 14px;font-family:var(--mono);font-size:12px;color:var(--muted)}
.facts b{color:var(--bone);font-weight:500}
.facts .ver{color:var(--ember-2)}
.live{display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:12px;color:var(--muted)}
.live i{width:7px;height:7px;background:#5b5349;animation:none}
.live.on{color:var(--ok)}
.live.on i{background:var(--ok);animation:ping 2.2s infinite}
.needs{font-size:13px;color:var(--muted)}
.needs a{color:var(--bone-2)}
.fam .links{display:flex;flex-wrap:wrap;gap:4px 16px;margin-top:auto;padding-top:10px;border-top:1px solid var(--line);font-family:var(--mono);font-size:11.5px;letter-spacing:.08em;text-transform:uppercase}
.fam .links a{color:var(--muted);text-decoration:none}
.fam .links a:hover{color:var(--ember-2)}
.small-cta{gap:8px;margin-top:2px}
.two{display:grid;grid-template-columns:1.2fr .8fr;gap:24px;align-items:start}
@media (max-width:820px){.two{grid-template-columns:1fr}}
.changelog{background:var(--panel);border:1px solid var(--line-2);border-radius:4px;padding:18px 22px}
.changelog h3{font-family:var(--mono);font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:var(--ember-2);margin:0 0 10px}
.changelog ul{margin:0;padding-left:20px;color:var(--bone-2)}
.changelog li{margin:6px 0}
details{border-top:1px solid var(--line);padding:10px 2px}
details:last-child{border-bottom:1px solid var(--line)}
summary{cursor:pointer;font-weight:600;color:var(--bone);list-style-position:outside}
summary:hover{color:#fff}
summary .mono{color:var(--muted);font-weight:400;margin-left:8px;font-size:13px}
.cl{padding:4px 0 2px 2px;color:var(--bone-2);font-size:15.5px}
.cl ul{margin:8px 0 0;padding-left:20px}
.cl p{margin:8px 0 0}
.small{font-size:12px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}
th{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:400}
tbody tr:first-child td{color:#fff}
.mono{font-family:var(--mono)}
.num{text-align:right}
.tablewrap{overflow-x:auto;background:var(--panel);border:1px solid var(--line-2);border-radius:4px}
.linkgrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
@media (max-width:900px){.linkgrid{grid-template-columns:1fr}}
.lpanel{background:var(--panel);border:1px solid var(--line-2);border-radius:4px;padding:16px 18px}
.lpanel h3{font-family:var(--mono);font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--ember-2);margin:0 0 10px;font-weight:500}
.lpanel ul{list-style:none;margin:0;padding:0;display:grid;gap:9px}
.lpanel li a{color:var(--bone);font-weight:600;text-decoration-color:rgba(239,231,214,.25)}
.lpanel li a:hover{color:var(--ember-2)}
.lpanel li small{display:block;color:var(--muted);font-size:13px;line-height:1.35}
.lpanel.wide-l{grid-column:1/-1}
.lpanel.wide-l ul{grid-template-columns:repeat(4,minmax(0,1fr));gap:10px 18px}
@media (max-width:900px){.lpanel.wide-l ul{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:520px){.lpanel.wide-l ul{grid-template-columns:1fr}}
.credits{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.credits div{background:var(--panel);border:1px solid var(--line-2);border-radius:4px;padding:14px 16px;font-size:15px;color:var(--bone-2)}
.credits b{display:block;font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ember-2);margin-bottom:6px}
footer{margin-top:70px;border-top:1px solid var(--line-2);padding:26px 0 40px;color:var(--muted);font-size:14px}
footer .wrap{display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px 24px}
footer a{color:var(--bone-2)}
.js .reveal{opacity:0;transform:translateY(18px);transition:opacity .7s ease,transform .7s cubic-bezier(.2,.8,.2,1)}
.js .reveal.in{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}.js .reveal{opacity:1;transform:none}.split .bars span{transform:none}}
"""

JS = r"""
(function(){
  'use strict';
  const CFG = JSON.parse(document.getElementById('cfg').textContent);
  const reduce = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  const $ = s => document.querySelector(s), $$ = s => Array.from(document.querySelectorAll(s));
  const fmt = n => (n == null || isNaN(n)) ? '-' : Number(n).toLocaleString('en-US');
  const DAY = 864e5;

  // reveal on scroll
  const rev = $$('.reveal');
  if ('IntersectionObserver' in window && !reduce){
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } }), {rootMargin:'0px 0px -6% 0px'});
    rev.forEach(el => io.observe(el));
  } else rev.forEach(el => el.classList.add('in'));

  // current section in the nav
  const navLinks = $$('nav.top ul a[href^="#"]');
  if ('IntersectionObserver' in window){
    const secIo = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting){ navLinks.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#'+e.target.id)); } }), {rootMargin:'-45% 0px -50% 0px'});
    navLinks.forEach(a => { const s = document.getElementById(a.getAttribute('href').slice(1)); if (s) secIo.observe(s); });
  }

  // count-up
  function countTo(el, target){
    if (target == null || isNaN(target)) return;
    const from = Number((el.textContent || '').replace(/[^0-9]/g, '')) || 0;
    if (reduce || from === target){ el.textContent = fmt(target); return; }
    const t0 = performance.now(), dur = 1100;
    (function step(now){ const k = Math.min(1, (now-t0)/dur), e = 1-Math.pow(1-k, 3); el.textContent = fmt(Math.round(from + (target-from)*e)); if (k < 1) requestAnimationFrame(step); })(t0);
    setTimeout(() => { el.textContent = fmt(target); }, dur + 400);  // a hidden tab pauses animation frames
  }
  // Runs fn once el is on screen; a timer makes sure a number never stays at its start value.
  function whenSeen(el, fn){
    let done = false; const go = () => { if (!done){ done = true; fn(); } };
    if (!('IntersectionObserver' in window)) return go();
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting){ io.disconnect(); go(); } }), {threshold:.3});
    io.observe(el);
    setTimeout(() => { io.disconnect(); go(); }, 4000);
  }

  // sparkline
  function spark(vals, stepped){
    const v = vals.filter(x => x != null); const n = v.length;
    if (n < 2) return '';
    const max = Math.max(1, ...v), min = Math.min(...v), lo = min > max*0.6 ? min*0.97 : 0, rng = (max-lo) || 1;
    const pts = v.map((y,i) => [(i/(n-1))*100, 38-((y-lo)/rng)*34]);
    let d = '';
    pts.forEach((p,i) => { d += i ? (stepped ? 'H'+p[0].toFixed(1)+'V'+p[1].toFixed(1) : 'L'+p[0].toFixed(1)+','+p[1].toFixed(1)) : 'M'+p[0].toFixed(1)+','+p[1].toFixed(1); });
    return '<svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true"><path d="'+d+' L100,40 L0,40 Z" fill="#e8931f" opacity=".16"/><path d="'+d+'" fill="none" stroke="#f5b34a" stroke-width="1.7" vector-effect="non-scaling-stroke"/><circle cx="'+pts[n-1][0].toFixed(1)+'" cy="'+pts[n-1][1].toFixed(1)+'" r="2.4" fill="#f5b34a"/></svg>';
  }

  // lightbox
  const shots = $$('.shot a');
  const lb = $('#lb');
  if (lb && typeof lb.showModal === 'function' && shots.length){
    let cur = 0;
    const show = i => { cur = (i + shots.length) % shots.length; const a = shots[cur], img = a.querySelector('img'); $('#lb-img').src = a.getAttribute('href'); $('#lb-img').alt = img.alt; $('#lb-cap').textContent = img.alt; $('#lb-n').textContent = (cur+1)+' / '+shots.length; };
    shots.forEach((a,i) => a.addEventListener('click', ev => { if (ev.ctrlKey || ev.metaKey || ev.shiftKey) return; ev.preventDefault(); show(i); lb.showModal(); }));
    $('#lb-prev').addEventListener('click', () => show(cur-1));
    $('#lb-next').addEventListener('click', () => show(cur+1));
    $('#lb-close').addEventListener('click', () => lb.close());
    lb.addEventListener('click', ev => { if (ev.target === lb) lb.close(); });
    lb.addEventListener('keydown', ev => { if (ev.key === 'ArrowLeft') show(cur-1); else if (ev.key === 'ArrowRight') show(cur+1); });
  }

  // live numbers from the Outbreak Server Watch
  const get = u => fetch(u, {cache:'no-store'}).then(r => r.ok ? r.json() : null).catch(() => null);
  Promise.all([get(CFG.stats+'trend.json'), get(CFG.stats+'latest.json')]).then(([T, L]) => {
    if (!T && !L){ throw new Error('no data'); }
    const tracked = {};
    Object.entries((L && L.tracked) || {}).forEach(([id, e]) => { const w = e.workshop || {}; tracked[id] = {servers:e.servers, players:e.players, seen:e.seen, keywordRank:e.keywordRank, globalRank:e.globalRank, versions:e.versions, capacity:e.capacity, serversWithPlayers:e.serversWithPlayers, downloads:w.downloads, playerHours7d:w.playerHours7d, rootDeployments:w.rootDeployments, dependencyDeployments:w.dependencyDeployments}; });
    Object.entries((T && T.tracked) || {}).forEach(([id, e]) => { tracked[id] = Object.assign(tracked[id] || {}, Object.fromEntries(Object.entries(e).filter(([k,v]) => v != null))); });
    const kwCount = (T && T.keyword && T.keyword.modCount) || (L && L.keyword && L.keyword.modCount);
    const allMods = (T && T.uniqueMods) || (L && L.totals && L.totals.uniqueMods);
    const gen = new Date((T || L).generatedUtc).getTime();
    const po = tracked[CFG.po] || {};
    const hours = T && T.hours ? T.hours : null;
    const dl = T && T.downloads ? T.downloads : null;
    const DT = dl ? dl.t.map(s => s*1000) : [];
    const series = id => (dl && dl.d[id]) || [];
    function dlGain(id, span){
      if (!dl) return null;
      const a = series(id), from = gen-span; let prev = null;
      for (let i = 0; i < DT.length && DT[i] <= from; i++) if (a[i] != null) prev = a[i];
      if (prev == null) return null;
      let g = 0;
      for (let i = 0; i < DT.length; i++){ if (DT[i] <= from || a[i] == null) continue; if (a[i] > prev) g += a[i]-prev; prev = a[i]; }
      const n = tracked[id] && tracked[id].downloads; if (n != null && n > prev) g += n-prev;
      return g;
    }

    // hero chip
    const chip = $('#livechip');
    if (chip && po.servers != null){ chip.innerHTML = '<i></i><span><b>'+fmt(po.servers)+'</b> servers running it right now · <b>'+fmt(po.players)+'</b> players on them</span>'; chip.hidden = false; }

    // tiles
    const set = (k, html) => { const el = document.querySelector('[data-k="'+k+'"]'); if (el) el.innerHTML = html; };
    const big = (k, n) => { const el = document.querySelector('[data-k="'+k+'"]'); if (!el) return; el.textContent = '0'; whenSeen(el, () => countTo(el, n)); };
    if (po.servers != null){
      big('servers', po.servers); big('players', po.players);
      set('servers-d', fmt(po.serversWithPlayers)+' of them with players');
      if (hours && hours.p[CFG.po]){ let pk = null; hours.p[CFG.po].forEach((v,i) => { if (v != null && (!pk || v > pk.v)) pk = {v:v, t:hours.t[i]*1000}; }); if (pk) set('players-d', 'peak '+fmt(pk.v)+' in the last 14 days, '+new Date(pk.t).toISOString().slice(5,10)); }
      if (hours){ set('servers-s', spark(hours.s[CFG.po] || [])); set('players-s', spark(hours.p[CFG.po] || [])); }
      const rk = $('[data-k="rank"]'); if (rk) rk.textContent = po.keywordRank ? '#'+po.keywordRank : '-';
      set('rank-d', 'of '+fmt(kwCount)+' zombie mods by servers · #'+fmt(po.globalRank)+' of all '+fmt(allMods)+' mods in use');
    } else { set('servers-d', 'not seen on a server in the last snapshot'); }
    const poDl = po.downloads;
    if (poDl != null){
      big('downloads', poDl);
      const g7 = dlGain(CFG.po, 7*DAY);
      set('downloads-d', g7 != null ? '<span class="up">+'+fmt(g7)+'</span> in the last 7 days' : 'Workshop total');
      if (dl){ const a = series(CFG.po), v = []; DT.forEach((t,i) => { if (t >= gen-30*DAY && a[i] != null) v.push(a[i]); }); v.push(poDl); set('downloads-s', spark(v, true)); }
    }
    // how servers get it + player-hours
    const root = po.rootDeployments, viaDep = po.dependencyDeployments;
    const wide = $('#live-wide');
    if (wide){
      const parts = [];
      if (root != null && viaDep != null && root+viaDep > 0){
        const pa = Math.round(100*root/(root+viaDep));
        parts.push('<div class="tile split"><div class="k">How servers get it</div><div class="bars" role="img" aria-label="'+root+' servers load it directly, '+viaDep+' through another mod"><span class="a" style="width:'+pa+'%"></span><span class="b" style="width:'+(100-pa)+'%"></span></div><div class="lg"><span><i style="background:var(--ember)"></i><b>'+fmt(root)+'</b>load it directly</span><span><i style="background:#9c6a2a"></i><b>'+fmt(viaDep)+'</b>get it because another mod needs it</span></div></div>');
      }
      if (po.playerHours7d != null) parts.push('<div class="tile"><div class="k">Player-hours, last 7 days</div><div class="v" data-k="ph">0</div><div class="d">about '+fmt(Math.round(po.playerHours7d/7))+' hours of play a day on servers running it</div></div>');
      wide.innerHTML = parts.join('');
      const sp = wide.querySelector('.split'); if (sp) whenSeen(sp, () => sp.classList.add('go'));
      const ph = wide.querySelector('[data-k="ph"]'); if (ph) whenSeen(ph, () => countTo(ph, po.playerHours7d));
    }
    const stamp = $('#live-stamp'); if (stamp) stamp.textContent = 'Snapshot '+new Date(gen).toISOString().slice(0,16).replace('T',' ')+' UTC';

    // every card: live line and downloads
    $$('[data-live]').forEach(el => {
      const m = tracked[el.getAttribute('data-live')];
      const sp = el.querySelector('span');
      if (!m){ el.remove(); return; }
      if (m.servers){ el.classList.add('on'); sp.textContent = fmt(m.servers)+' server'+(m.servers === 1 ? '' : 's')+' · '+fmt(m.players)+' player'+(m.players === 1 ? '' : 's')+' now'; }
      else sp.textContent = 'Not on a public server right now';
    });
    let total = 0;
    $$('[data-dl]').forEach(el => {
      const id = el.getAttribute('data-dl'), m = tracked[id], b = Number(el.getAttribute('data-build')) || 0;
      const n = (m && m.downloads != null && m.downloads > b) ? m.downloads : b;
      if (!el.closest('.factstrip')) total += n;
      if (n !== b) el.textContent = fmt(n);
    });
    const tot = $('#dl-total'); if (tot && total) countTo(tot, total);
  }).catch(() => {
    $$('[data-k]').forEach(el => { if (el.classList.contains('v')) el.textContent = '-'; });
    const d = document.querySelector('[data-k="servers-d"]'); if (d) d.textContent = 'live numbers are unavailable right now';
    $$('[data-live]').forEach(el => el.remove());
  });
  // the hero total counts up once
  const heroDl = $('.factstrip [data-dl]');
  if (heroDl) countTo(heroDl, Number(heroDl.getAttribute('data-build')));
})();
"""

CFG = json.dumps({"stats": STATS_SITE, "po": PO_ID}).replace("</", "<\\/")
NAV = [("live", "Live"), ("infected", "Infected"), ("gm", "Game Master"), ("shots", "Field"), ("mods", "All mods"), ("changes", "Changes"), ("links", "Links")]

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project Outbreak</title>
<meta name="description" content="{E(PO["summary"])} A zombie sandbox add-on for Arma Reforger, on the Workshop.">
<meta name="theme-color" content="#0c0a08">
<meta property="og:title" content="Project Outbreak">
<meta property="og:description" content="{E(PO["summary"])}">
<meta property="og:image" content="https://outbreakarma.github.io/{SHOTS[0]["full"] if SHOTS else ""}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="assets/cards/Outbreak_FactionIcon_ui.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<script>document.documentElement.classList.add('js')</script>
<style>{CSS}</style>
</head>
<body>
<nav class="top" aria-label="Sections"><div class="wrap">
  <a class="logo" href="#top"><img src="assets/cards/Outbreak_FactionIcon_ui.png" alt=""><span>Project Outbreak</span></a>
  <ul>{"".join(f'<li><a href="#{k}">{v}</a></li>' for k, v in NAV)}</ul>
  {ext(ws(PO_ID), "Workshop", "btn small navcta")}
</div></nav>

<header class="hero" id="top">
  <img class="bg" src="{HERO_FULL}" srcset="{HERO_MID} 1480w, {HERO_FULL} 1920w" sizes="100vw" alt="" fetchpriority="high">
  <div class="wrap">
    <a class="livechip" id="livechip" href="#live" hidden></a>
    <div class="eyebrow">Arma Reforger · Workshop add-on · version {E(PO["version"])}</div>
    <h1>Project <span>Outbreak</span></h1>
    <p class="lead">{E(PO["summary"])} Place them through Game Master, or let ambient populations and directed waves shape an entire scenario.</p>
    <div class="cta">
      {ext(ws(PO_ID), "Get it on the Workshop", "btn")}
      {ext(DISCORD, "Join the Discord", "btn ghost")}
      {ext(STATS_SITE, "Live server stats", "btn ghost")}
    </div>
    <div class="factstrip">
      <span>Downloads <b data-dl="{PO_ID}" data-build="{int(PO["downloads"] or 0)}">{int(PO["downloads"] or 0):,}</b></span>
      <span>Rating <b>{int(round((PO["rating"] or 0) * 100))}%</b> from {PO["ratingCount"]} ratings</span>
      <span>Game <b>{E(PO["gameVersion"])}</b></span>
      <span>Size <b>{mb(PO["sizeBytes"])}</b></span>
      <span>Licence {ext(APL, "APL")}</span>
      <span>Updated <b>{E(date(PO["updatedAt"]))}</b></span>
    </div>
  </div>
</header>

<section id="live"><div class="wrap">
  <h2>On servers <em>right now</em></h2>
  <p class="sub">Counted every hour from the public Arma Reforger server list by the {ext(STATS_SITE, "Outbreak Server Watch")}, with data from {ext("https://reforgermods.net", "ReforgerMods.net")} and {ext("https://www.armahq.com", "ArmaHQ")}. Players are the people on servers running the add-on, not subscribers.</p>
  <div class="live-grid">
    <div class="tile reveal"><div class="k">Servers running it</div><div class="v" data-k="servers">-</div><div class="d" data-k="servers-d"></div><div data-k="servers-s"></div></div>
    <div class="tile reveal"><div class="k">Players on them</div><div class="v" data-k="players">-</div><div class="d" data-k="players-d"></div><div data-k="players-s"></div></div>
    <div class="tile reveal"><div class="k">Workshop downloads</div><div class="v" data-k="downloads">-</div><div class="d" data-k="downloads-d"></div><div data-k="downloads-s"></div></div>
    <div class="tile reveal"><div class="k">Rank among zombie mods</div><div class="v" data-k="rank">-</div><div class="d" data-k="rank-d"></div></div>
  </div>
  <div class="live-wide" id="live-wide"></div>
  <div class="live-foot"><span id="live-stamp"></span>{ext(STATS_SITE, "Open the full server watch", "btn small ghost")}</div>
</div></section>

<section id="infected"><div class="wrap">
  <h2>The <em>infected</em></h2>
  <p class="sub">Three archetypes ship in the core add-on, each with its own animations and behaviour, in civilian and military dress. Health and damage are yours to tune. Hover a card to see the other outfit.</p>
  <div class="roles">{role_cards()}</div>
</div></section>

<section id="gm"><div class="wrap">
  <h2>Built for <em>Game Master</em></h2>
  <p class="sub">Everything is placeable and configurable from the Game Master interface, on your own scenarios and servers.</p>
  <div class="gm">
    <ul>
      <li class="reveal"><b>Place them directly</b>Single creatures and groups of four, eight or sixteen, plus a mixed horde card, straight from the Outbreak faction in Game Master.</li>
      <li class="reveal"><b>Ambient populations and directed waves</b>Let the sandbox populate itself, or author waves and routes to drive a whole scenario.</li>
      <li class="reveal"><b>Zombie Permanent Kills</b>A global setting. In the headshots, explosives and fire mode, ordinary body damage only knocks zombies down; a headshot, an explosion or fire finishes them. Works with ACE Medical hit-zone mods.</li>
      <li class="reveal"><b>Placing ignores AI limit</b>Off by default. Turn it on to keep placing creatures by hand after the active-AI budget is full; ambience, directed spawning and reanimation keep their own budgets.</li>
      <li class="reveal"><b>Downed is not safe</b>Zombies feed on knocked-out survivors, more than one at a time, and finish them unless someone drives them off or revives them.</li>
    </ul>
    <figure class="gm-art reveal"><img src="assets/cards/PO_Card_Director.png" alt="The Outbreak Director card art" loading="lazy" width="512" height="384"><figcaption>The Outbreak Director, as it appears in Game Master</figcaption></figure>
  </div>
</div></section>

<section id="shots"><div class="wrap">
  <h2>From the <em>field</em></h2>
  <p class="sub">Screenshots from the {ext(ws(PO_ID), "Workshop listing")}. Select one to see it full size.</p>
  <div class="shots">{shot_figures()}</div>
</div></section>
<dialog class="lb" id="lb" aria-label="Screenshot viewer"><img id="lb-img" alt=""><div class="bar"><span id="lb-cap"></span><span style="display:flex;gap:8px;align-items:center"><span id="lb-n"></span><button type="button" id="lb-prev" aria-label="Previous screenshot">Prev</button><button type="button" id="lb-next" aria-label="Next screenshot">Next</button><button type="button" id="lb-close">Close</button></span></div></dialog>

<section id="mods"><div class="wrap">
  <h2>Everything by <em>Project Outbreak</em></h2>
  <p class="sub">Every public Workshop item from the same author, from the zombie sandbox to stand-alone creatures. Each card shows its live server count from the {ext(STATS_SITE, "Outbreak Server Watch")}.</p>
  <div class="mods-head"><span><b>{len(ALL_IDS)}</b>Workshop items</span><span><b id="dl-total">{TOTAL_DOWNLOADS:,}</b>downloads between them</span><span>{ext(STATS_SITE + "#addons", "Compare them on the server watch")}</span></div>
  {groups_html()}
</div></section>

<section id="changes"><div class="wrap">
  <h2>What <em>changed</em></h2>
  <p class="sub">Published change notes, straight from the Workshop. Other add-ons are listed by their latest update.</p>
  <div class="two">
    <div>
      <div class="changelog"><h3>Project Outbreak Zombies {E(PO["version"])} · {E(date(PO["updatedAt"]))}</h3><ul>{changelog_list()}</ul></div>
      <div style="margin-top:14px">{family_changelogs()}</div>
    </div>
    <div class="tablewrap"><table><thead><tr><th>Version</th><th>Published</th><th>Game</th><th class="num">Size</th></tr></thead><tbody>{version_rows()}</tbody></table></div>
  </div>
</div></section>

<section id="links"><div class="wrap">
  <h2>Useful <em>links</em></h2>
  <p class="sub">Where to get the add-ons, follow the numbers and talk to the people who make and run them.</p>
  <div class="linkgrid">{links_html()}</div>
</div></section>

<section id="credits"><div class="wrap">
  <h2>Credits and <em>licence</em></h2>
  <p class="sub">Who made what, and the licences that apply.</p>
  <div class="credits">
    <div><b>Licence</b>Original Project Outbreak content is released under the {ext(APL, "Arma Public License (APL)")}. Incorporated assets remain under the Fab Standard License.</div>
    <div><b>Animation and sound</b>Several attack and tackling animations and sounds come from Yummy Games. Feral movement uses Crawling Ghoul Anims by RamsterZ. The Gadgets spear movement is adapted from work by Bacengdu.</div>
    <div><b>Dependency</b>Requires {ext(ws(CMAI_ID), "Creature Melee AI")} by the same author. Arma Reforger, Enfusion and Workbench are by Bohemia Interactive.</div>
    <div><b>Not affiliated</b>Project Outbreak is an unofficial community project and is not endorsed by Bohemia Interactive. Server numbers on this site come from {ext("https://reforgermods.net", "ReforgerMods.net")} and {ext("https://www.armahq.com", "ArmaHQ")}, through the {ext(STATS_SITE, "Outbreak Server Watch")}.</div>
  </div>
</div></section>

<footer><div class="wrap">
  <span>Project Outbreak · {ext(ws(PO_ID), "Workshop")} · {ext(DISCORD, "Discord")} · {ext(STATS_SITE, "Server watch")} · {ext(GITHUB, "GitHub")}</span>
  <span class="mono">Built from the published listings, {E(date(PO["updatedAt"]))} · listing id {E(PO_ID)}</span>
</div></footer>
<script type="application/json" id="cfg">{CFG}</script>
<script>{JS}</script>
</body>
</html>
"""

bad = [ch for ch in ("—", "–") if ch in page]
if bad:
    raise SystemExit(f"refusing to write a page with dashes {bad!r}; clean() missed some text")
(ROOT / "index.html").write_text(page, encoding="utf-8")
(ROOT / ".nojekyll").touch()
print(f"wrote index.html ({len(page):,} chars) for {PO['name']} {PO['version']}, {len(ALL_IDS)} items in {len(GROUPS)} groups")
