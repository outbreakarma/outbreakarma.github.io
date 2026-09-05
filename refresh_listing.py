#!/usr/bin/env python3
"""Refresh the published Workshop listing data and images that build.py renders.

Fetches the public Workshop pages for Project Outbreak and its family, reads the JSON each
page embeds, rewrites assets/data/workshop-po.json and workshop-family.json, and downloads any
image the listings reference that is not already on disk (assets/data/images.json maps URL to
local file, so existing files keep their names). Standard library only. Exit code 1 if the
main listing cannot be read; the previous data stays untouched in that case.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "assets/data"
SHOTS = ROOT / "assets/shots"
FAMILY_DIR = ROOT / "assets/family"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 OutbreakSite/1.0 (+https://github.com/outbreakarma/outbreakarma.github.io)"
PO_ID = "F1D4B9B5245B36ED"
FAMILY_IDS = ["7B763100BAFA1F9A", "6209E38AB237098E", "6B9BD0DA529C0D1E", "4FD4A1BD550793F4", "40B5686CC205703A"]
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def get(url: str, retries: int = 3) -> bytes:
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,image/*,*/*"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            last = exc
            time.sleep(10 * attempt)
    raise RuntimeError(f"could not fetch {url}: {last!r}")


def page_props(mod_id: str) -> dict:
    html = get(f"https://reforger.armaplatform.com/workshop/{mod_id}").decode("utf-8", errors="replace")
    m = NEXT_DATA_RE.search(html)
    if not m:
        raise RuntimeError(f"no embedded data on the listing page for {mod_id}")
    return json.loads(m.group(1))["props"]["pageProps"]


def pick(pp: dict) -> dict:
    a = pp["asset"]
    vd = pp.get("assetVersionDetail") or {}
    thumbs = lambda item: [t.get("url") for t in ((item.get("thumbnails") or {}).get("image/jpeg") or [])]  # noqa: E731
    previews = a.get("previews") or []
    return {
        "id": a["id"], "name": a["name"], "author": a["author"]["username"], "summary": a.get("summary"), "description": a.get("description"),
        "license": a.get("license"), "rating": a.get("averageRating"), "ratingCount": a.get("ratingCount"), "version": a.get("currentVersionNumber"),
        "sizeBytes": a.get("currentVersionSize"), "gameVersion": a.get("gameVersion"), "createdAt": a.get("createdAt"), "updatedAt": a.get("updatedAt"),
        "downloads": (pp.get("getAssetDownloadTotal") or {}).get("total"), "tags": [t["name"] for t in a.get("tags", [])],
        "dependencies": [{"id": d["asset"]["id"], "name": d["asset"]["name"], "version": d.get("version")} for d in a.get("dependencies", [])],
        "versions": [{"version": v["version"], "gameVersion": v.get("gameVersion"), "createdAt": v.get("createdAt"), "size": v.get("totalFileSize")} for v in a.get("versions", [])],
        "changelog": vd.get("changelog"),
        "preview": previews[0].get("url") if previews else None,
        "previewThumbs": thumbs(previews[0]) if previews else [],
        "screenshots": [{"url": s.get("url"), "width": s.get("width"), "height": s.get("height"), "thumbs": thumbs(s)} for s in a.get("screenshots", [])],
        "workshopUrl": f"https://reforger.armaplatform.com/workshop/{a['id']}",
    }


def local_name(url: str, folder: Path, prefix: str) -> Path:
    return folder / f"{prefix}{hashlib.sha1(url.encode()).hexdigest()[:10]}.jpg"


def ensure_image(url: str, images: dict, folder: Path, prefix: str) -> str:
    if url in images and (ROOT / images[url]).exists():
        return images[url]
    path = local_name(url, folder, prefix)
    if not path.exists():
        path.write_bytes(get(url))
        print(f"downloaded {url[-60:]} -> {path.relative_to(ROOT)}")
    images[url] = path.relative_to(ROOT).as_posix()
    return images[url]


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    images_path = DATA / "images.json"
    images = json.loads(images_path.read_text(encoding="utf-8")) if images_path.exists() else {}

    try:
        po = pick(page_props(PO_ID))
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED to read the main listing: {exc!r}; keeping previous data")
        return 1
    if po.get("preview"):
        ensure_image(po["preview"], images, SHOTS, "po_")
        for t in po["previewThumbs"]:
            ensure_image(t, images, SHOTS, "po_")
    for s in po["screenshots"]:
        ensure_image(s["url"], images, SHOTS, "po_")
        for t in s["thumbs"]:
            ensure_image(t, images, SHOTS, "po_")
    (DATA / "workshop-po.json").write_text(json.dumps(po, ensure_ascii=False, indent=1), encoding="utf-8")

    family = []
    for mod_id in FAMILY_IDS:
        try:
            item = pick(page_props(mod_id))
        except Exception as exc:  # noqa: BLE001
            print(f"family listing {mod_id} unreadable: {exc!r}; keeping its previous entry")
            prev = json.loads((DATA / "workshop-family.json").read_text(encoding="utf-8")) if (DATA / "workshop-family.json").exists() else []
            item = next((f for f in prev if f["id"] == mod_id), None)
            if not item:
                continue
        if item.get("preview"):
            item["previewFile"] = ensure_image(item["preview"], images, FAMILY_DIR, f"{mod_id}_")
        family.append(item)
        time.sleep(1)
    (DATA / "workshop-family.json").write_text(json.dumps(family, ensure_ascii=False, indent=1), encoding="utf-8")
    images_path.write_text(json.dumps(images, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"listing refreshed: {po['name']} {po['version']} ({po['downloads']} downloads), {len(family)} family add-ons, {len(images)} images mapped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
