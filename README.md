# Project Outbreak website

The public site for **Project Outbreak**, a zombie sandbox add-on for Arma Reforger:
https://outbreakarma.github.io/

Static, no framework. `build.py` renders `index.html` from the published Workshop listing
data under `assets/data/` (versions, change notes, screenshots, family add-ons). Nothing on
the page comes from work in progress: only what is published on the Workshop.

- `assets/shots/` screenshots and title art from the Workshop listing (title art by redeye.vol2)
- `assets/family/` preview images of the other published add-ons by the same author
- `assets/cards/` the Game Master card art shipped in the add-on
- `assets/data/workshop-po.json`, `workshop-family.json` the listing data the page is built from

Live server numbers (servers, players, rank) are fetched at view time from the sibling stats
site, https://outbreakarma.github.io/outbreak-stats/, which counts them hourly from ArmaHQ.

## Rebuild

```
python build.py
```

Then commit `index.html`. GitHub Pages serves the repository root from `main`.

## Refresh the listing data

Re-download the Workshop pages for the ids in `assets/data/` and re-run the extraction that
produced the JSON files (the listing pages embed their data as JSON), then `python build.py`.

## Licence and credits

Project Outbreak content is released under the Arma Public License (APL). Incorporated assets
remain under the Fab Standard License and are credited on the page. Not affiliated with
Bohemia Interactive.
