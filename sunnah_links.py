# sunnah_links.py — build sunnah.com URLs for "Go to site" links.
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SUNNAH_SLUGS = {
    "bukhari": "bukhari", "muslim": "muslim", "abu-dawud": "abudawud",
    "tirmidhi": "tirmidhi", "nasai": "nasai", "ibn-majah": "ibnmajah",
}

def collection_url(site_slug: str) -> str:
    return f"https://sunnah.com/{SUNNAH_SLUGS[site_slug]}"

def hadith_url(site_slug: str, id_in_book: int) -> str:
    return f"https://sunnah.com/{SUNNAH_SLUGS[site_slug]}:{id_in_book}"
