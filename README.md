# Project Outbreak website

The public site for **Project Outbreak**, a zombie sandbox add-on for Arma Reforger:
https://outbreakarma.github.io/

Static, no framework. `build.py` renders `index.html` from the published Workshop listing
data under `assets/data/` (versions, change notes, screenshots, and every other public
Workshop item by the same author). Nothing on the page comes from work in progress: only what
is published on the Workshop. The page groups the items in `GROUPS` in `build.py`.

- `assets/shots/` screenshots and title art from the Workshop listing (title art by redeye.vol2)
- `assets/family/` preview images of the other public Workshop items by the same author
- `assets/cards/` the Game Master card art shipped in the add-on
- `assets/data/workshop-po.json`, `workshop-family.json` the listing data the page is built from

Live numbers (servers, players, rank, downloads, player-hours) are fetched at view time from
the sibling stats site, https://outbreakarma.github.io/outbreak-stats/ (`trend.json` and
`latest.json`), which counts them hourly from ReforgerMods.net and ArmaHQ. The page renders
completely without them.

## Rebuild

```
python build.py
```

Then commit `index.html`. GitHub Pages serves the repository root from `main`.

## Refresh the listing data

```
python refresh_listing.py
python build.py
```

`refresh_listing.py` reads the public Workshop page of Project Outbreak Zombies and of every id
in `FAMILY_IDS`, rewrites the JSON under `assets/data/` and downloads any new preview image.
The workflow `.github/workflows/refresh.yml` runs both every hour and commits the result. To
show a new Workshop item, add its id to `FAMILY_IDS` and to a group in `build.py`.

## Licence and credits

Project Outbreak content is released under the Arma Public License (APL). Incorporated assets
remain under the Fab Standard License and are credited on the page. Not affiliated with
Bohemia Interactive.
