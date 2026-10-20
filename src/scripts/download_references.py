#!/usr/bin/env python3
"""Download architectural reference images for the Brihadisvara Temple model.

The script queries the Wikimedia Commons API for freely licensed photographs of
the Brihadisvara Temple (Peruvudaiyar Kovil), Thanjavur, downloads the actual
image files into ``src/references/images`` and records full attribution
metadata in ``src/references/image_manifest.json``.

Design rules
------------
* Only public, unauthenticated HTTP endpoints are used.
* No authentication, CAPTCHA or access control is bypassed.
* Only files whose real byte signature matches a known image format are kept;
  HTML error pages saved as ``.jpg`` are rejected.
* Every download is verified by decoding the image.
* Existing files are never overwritten; the download is skipped and recorded.
* The run is resumable: a partially written file is removed and retried.
* Metadata is written from the API response only -- nothing is invented.

Usage
-----
    python3 src/scripts/download_references.py [--limit N] [--dry-run] [--force]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:  # Pillow is optional but strongly recommended for decode verification
    from PIL import Image

    HAVE_PIL = True
except Exception:  # pragma: no cover - depends on host
    HAVE_PIL = False

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
REF_DIR = PROJECT_ROOT / "src" / "references"
IMAGE_DIR = REF_DIR / "images"
MANIFEST_PATH = REF_DIR / "image_manifest.json"
SOURCES_PATH = REF_DIR / "sources.md"

API_ENDPOINT = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "BrihadisvaraTemple3D/1.0 (educational architectural study; "
    "contact: local repository owner) python-urllib"
)
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0
THUMB_WIDTH = 1600

# Categories on Commons that reliably contain the required views.
CATEGORIES = [
    "Category:Brihadisvara Temple",
    "Category:Brihadeeswarar Temple",
]

# Human readable role of each reference view, mapped by keyword matching on the
# Commons file title.  The role is a *documentation* label for the analyst; it is
# never presented as a historical fact.
ROLE_KEYWORDS = [
    ("vimana", ("vimana", "shikhara", "tower", "superstructure")),
    ("gopuram", ("gopuram", "gopura", "gateway", "tiruvasal", "gateway")),
    ("nandi", ("nandi", "bull")),
    ("mandapa", ("mandapa", "mandapam", "hall", "pillared", "column")),
    ("courtyard", ("courtyard", "quadrangle", "prakara", "compound", "wall", "complex")),
    ("plinth", ("plinth", "base", "moulding", "molding", "adhishthanam", "upapitham")),
    ("interior", ("interior", "sanctum", "garbhagriha", "linga", "chola", "fresco", "mural", "ceiling")),
    ("sculpture", ("sculpt", "carving", "nandi", "relief", "dvarapala", "yali")),
    ("aerial", ("aerial", "bird", "panorama", "view", "overall", "complex")),
]

IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"GIF87a": ("gif", "image/gif"),
    b"GIF89a": ("gif", "image/gif"),
    b"BM": ("bmp", "image/bmp"),
}


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def _opener() -> urllib.request.OpenerDirector:
    context = ssl.create_default_context()
    handler = urllib.request.HTTPSHandler(context=context)
    opener = urllib.request.build_opener(handler)
    opener.addheaders = [("User-Agent", USER_AGENT), ("Accept-Encoding", "identity")]
    return opener


def http_get(url: str, retries: int = MAX_RETRIES) -> bytes:
    """GET a URL with bounded retries; returns the raw body."""
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with _opener().open(url, timeout=REQUEST_TIMEOUT) as response:
                if response.status != 200:
                    raise urllib.error.HTTPError(url, response.status, "bad status", response.headers, None)
                return response.read()
        except Exception as exc:  # noqa: BLE001 - network errors are all retryable
            last_error = exc
            if attempt < retries:
                time.sleep(RETRY_BACKOFF * attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {url} ({last_error})")


def api_query(params: dict[str, Any]) -> dict[str, Any]:
    url = API_ENDPOINT + "?" + urllib.parse.urlencode(params)
    payload = http_get(url)
    return json.loads(payload.decode("utf-8"))


# --------------------------------------------------------------------------- #
# Manifest handling
# --------------------------------------------------------------------------- #
@dataclass
class ReferenceEntry:
    filename: str
    title: str
    page_url: str
    image_url: str
    author: str
    source_organisation: str
    licence: str
    attribution: str
    downloaded_at: str
    width_px: int
    height_px: int
    bytes: int
    sha256: str
    status: str
    view_role: str = "general"
    source_category: str = ""
    notes: str = ""


def load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"project": "Brihadisvara Temple architectural reference set", "images": []}


def save_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Naming helpers
# --------------------------------------------------------------------------- #
def slugify(text: str) -> str:
    # Commons titles frequently carry their own file extension.
    text = re.sub(r"\.(jpe?g|png|gif|tiff?|webp)$", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"[_\s]+", "-", text.strip())
    text = re.sub(r"[^A-Za-z0-9\-()]+", "", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text.lower()[:70] or "image"


def classify(title: str) -> str:
    low = title.lower()
    for role, keywords in ROLE_KEYWORDS:
        if any(keyword in low for keyword in keywords):
            return role
    return "general"


def detect_format(blob: bytes) -> tuple[str, str] | None:
    for signature, (ext, mime) in IMAGE_SIGNATURES.items():
        if blob.startswith(signature):
            return ext, mime
    if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return "webp", "image/webp"
    return None


def verify_image(path: Path) -> tuple[int, int] | None:
    """Decode the file; return (width, height) or None if it is not a valid image."""
    if HAVE_PIL:
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                return int(image.width), int(image.height)
        except Exception:
            return None
    # Fallback: signature-only validation when Pillow is unavailable.
    try:
        blob = path.read_bytes()[:16]
    except OSError:
        return None
    return None if detect_format(blob) is None else (0, 0)


# --------------------------------------------------------------------------- #
# Commons search
# --------------------------------------------------------------------------- #
def fetch_candidates(limit: int) -> list[dict[str, Any]]:
    """Query Commons for image files in the temple categories."""
    candidates: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for category in CATEGORIES:
        try:
            data = api_query(
                {
                    "action": "query",
                    "format": "json",
                    "generator": "categorymembers",
                    "gcmtitle": category,
                    "gcmtype": "file",
                    "gcmlimit": str(limit),
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime|extmetadata",
                    "iiurlwidth": str(THUMB_WIDTH),
                }
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  ! category query failed for {category}: {exc}", file=sys.stderr)
            continue

        pages = (data.get("query") or {}).get("pages") or {}
        for page in pages.values():
            title = page.get("title", "")
            if not title or title in seen_titles:
                continue
            info_list = page.get("imageinfo") or []
            if not info_list:
                continue
            info = info_list[0]
            if not info.get("mime", "").startswith("image/"):
                continue
            seen_titles.add(title)
            candidates.append(
                {
                    "title": title,
                    "page_url": info.get("descriptionurl", ""),
                    "image_url": info.get("thumburl") or info.get("url", ""),
                    "full_url": info.get("url", ""),
                    "width": int(info.get("thumbwidth") or info.get("width") or 0),
                    "height": int(info.get("thumbheight") or info.get("height") or 0),
                    "extmetadata": info.get("extmetadata", {}),
                    "category": category,
                }
            )
    return candidates


def extract_metadata(candidate: dict[str, Any]) -> dict[str, str]:
    meta = candidate.get("extmetadata") or {}

    def value(key: str) -> str:
        entry = meta.get(key) or {}
        if isinstance(entry, dict):
            return re.sub(r"<[^>]+>", "", str(entry.get("value", ""))).strip()
        return str(entry).strip()

    author = value("Artist") or "Unknown (not stated on Commons)"
    licence = value("LicenseShortName") or value("UsageTerms") or "See Commons file page"
    credit = value("Credit") or ""
    organisation = "Wikimedia Commons"
    if author and author.lower() not in {"unknown", "unknown (not stated on commons)"}:
        organisation = "Wikimedia Commons"
    return {
        "author": author,
        "licence": licence,
        "attribution": credit or f"{author} — {licence} — via Wikimedia Commons",
        "source_organisation": organisation,
    }


# --------------------------------------------------------------------------- #
# Download
# --------------------------------------------------------------------------- #
def unique_path(base: Path) -> Path:
    if not base.exists():
        return base
    stem, suffix = base.stem, base.suffix
    index = 2
    while True:
        candidate = base.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def download_candidate(candidate: dict[str, Any], dry_run: bool, force: bool) -> ReferenceEntry:
    title = candidate["title"]
    role = classify(title)
    metadata = extract_metadata(candidate)
    base_name = f"{role}_{slugify(re.sub(r'^File:', '', title))}"
    target = IMAGE_DIR / f"{base_name}.jpg"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    entry = ReferenceEntry(
        filename=target.name,
        title=re.sub(r"^File:", "", title),
        page_url=candidate["page_url"],
        image_url=candidate["image_url"],
        author=metadata["author"],
        source_organisation=metadata["source_organisation"],
        licence=metadata["licence"],
        attribution=metadata["attribution"],
        downloaded_at=now,
        width_px=candidate["width"],
        height_px=candidate["height"],
        bytes=0,
        sha256="",
        status="pending",
        view_role=role,
        source_category=candidate["category"],
    )

    if target.exists() and not force:
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        size = target.stat().st_size
        dimensions = verify_image(target)
        if dimensions is None:
            entry.status = "existing-file-invalid"
            entry.sha256 = digest
            entry.bytes = size
            return entry
        entry.width_px, entry.height_px = dimensions
        entry.bytes = size
        entry.sha256 = digest
        entry.status = "skipped-existing"
        return entry

    if dry_run:
        entry.status = "dry-run"
        return entry

    try:
        blob = http_get(candidate["image_url"])
    except Exception as exc:  # noqa: BLE001
        entry.status = f"download-failed: {exc}"
        return entry

    detected = detect_format(blob)
    if detected is None:
        entry.status = "rejected-not-an-image"
        return entry
    extension, _mime = detected
    if extension != "jpg":
        target = target.with_suffix(f".{extension}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target = unique_path(target)
    tmp_path = target.with_suffix(target.suffix + ".part")
    try:
        tmp_path.write_bytes(blob)
        dimensions = verify_image(tmp_path)
        if dimensions is None:
            tmp_path.unlink(missing_ok=True)
            entry.status = "rejected-decode-failed"
            return entry
        tmp_path.replace(target)
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        entry.status = f"write-failed: {exc}"
        return entry

    entry.filename = target.name
    entry.width_px, entry.height_px = dimensions
    entry.bytes = target.stat().st_size
    entry.sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
    entry.status = "downloaded"
    return entry


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def write_sources_md(entries: Iterable[ReferenceEntry]) -> None:
    entries = list(entries)
    lines = [
        "# Reference Image Sources & Attribution",
        "",
        "All images in `src/references/images/` were obtained from Wikimedia Commons",
        "through its public MediaWiki API (no authentication, no scraping of",
        "restricted pages). Licences and authors are reproduced verbatim from the",
        "`extmetadata` block returned by the API for each file.",
        "",
        f"Last generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "| File | View role | Author | Licence | Source organisation | Page |",
        "|---|---|---|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            f"| `{entry.filename}` | {entry.view_role} | {entry.author} | {entry.licence} "
            f"| {entry.source_organisation} | [Commons page]({entry.page_url}) |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "* Images are used strictly as visual evidence of proportion, silhouette and",
        "  detail. They are not dimensioned drawings and no measurement in this",
        "  project is derived from pixel measurement of a photograph.",
        "* Every image remains the property of its author and is redistributed here",
        "  under the licence stated in the table above.",
        "* Machine readable metadata (including SHA-256 checksums and byte sizes) is",
        "  in `image_manifest.json`.",
        "",
    ]
    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_PATH.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=40, help="max files per Commons category")
    parser.add_argument("--dry-run", action="store_true", help="query only, do not download")
    parser.add_argument("--force", action="store_true", help="re-download even if the file exists")
    args = parser.parse_args(argv)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    known = {entry.get("filename"): entry for entry in manifest.get("images", [])}

    print(f"Querying Wikimedia Commons for Brihadisvara Temple references ...")
    candidates = fetch_candidates(args.limit)
    print(f"  {len(candidates)} candidate file(s) found.")

    entries: list[ReferenceEntry] = []
    for candidate in candidates:
        entry = download_candidate(candidate, args.dry_run, args.force)
        entries.append(entry)
        status = entry.status
        print(f"  [{status:>18}] {entry.filename}  ({entry.width_px}x{entry.height_px})")
        if entry.filename in known and status == "skipped-existing":
            # preserve the original download timestamp of an already known file
            previous = known[entry.filename]
            entry.downloaded_at = previous.get("downloaded_at", entry.downloaded_at)
            entry.sha256 = previous.get("sha256", entry.sha256) or entry.sha256
            entry.status = "skipped-existing"
        known[entry.filename] = asdict(entry)

    manifest["images"] = [known[key] for key in sorted(known)]
    manifest["last_run"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest["source_api"] = API_ENDPOINT
    manifest["categories"] = CATEGORIES
    manifest["downloaded_by"] = "src/scripts/download_references.py"
    if not args.dry_run:
        save_manifest(manifest)
        write_sources_md([ReferenceEntry(**record) for record in manifest["images"]])

    downloaded = sum(1 for e in entries if e.status == "downloaded")
    skipped = sum(1 for e in entries if e.status == "skipped-existing")
    failed = sum(1 for e in entries if e.status.startswith(("download-failed", "rejected", "write-failed")))
    print(f"\ndownloaded={downloaded} skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
