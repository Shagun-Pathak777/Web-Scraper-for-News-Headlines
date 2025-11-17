
import sys
import time
import requests
from bs4 import BeautifulSoup

# ---------- USER SETTINGS ----------
# Default URL (change to the news page you want)
URL = "https://www.bbc.com/news"
OUTPUT_FILE = "headlines.txt"
MAX_HEADLINES = 50
REQUEST_TIMEOUT = 10
SLEEP_BEFORE_REQUEST = 1  # polite delay
# -----------------------------------

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NewsScraper/1.0; +https://example.com/bot)"
}

def fetch_html(url):
    """Fetch page HTML with basic error handling."""
    try:
        time.sleep(SLEEP_BEFORE_REQUEST)
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        raise RuntimeError(f"Error fetching {url}: {e}") from e

def extract_headlines_generic(html, max_items=MAX_HEADLINES):
    """Generic extraction: title + h1/h2/h3 tags."""
    soup = BeautifulSoup(html, "html.parser")
    candidates = []

    # title tag
    if soup.title and soup.title.string:
        candidates.append(soup.title.string)

    # heading tags
    for tag in ("h1", "h2", "h3"):
        for el in soup.find_all(tag):
            txt = el.get_text(separator=" ", strip=True)
            if txt:
                candidates.append(txt)

    return _clean_and_dedupe(candidates, max_items)

def extract_headlines_bbc(html, max_items=MAX_HEADLINES):
    """
    Site-specific extractor for BBC. Adjust or add more site-specific functions
    for other sites after inspecting page structure via browser dev tools.
    """
    soup = BeautifulSoup(html, "html.parser")
    candidates = []

    # BBC often uses these selectors for promo headings
    selectors = [
        "h1",
        "h2",
        "h3.gs-c-promo-heading__title",  # specific class
        "a.gs-c-promo-heading"           # links that contain headlines
    ]
    for sel in selectors:
        for el in soup.select(sel):
            txt = el.get_text(separator=" ", strip=True)
            if txt:
                candidates.append(txt)

    return _clean_and_dedupe(candidates, max_items)

def _clean_and_dedupe(items, max_items):
    """Normalize whitespace, dedupe (case-insensitive), preserve order."""
    seen = set()
    cleaned = []
    for raw in items:
        s = " ".join(raw.split())  # collapse whitespace
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(s)
        if len(cleaned) >= max_items:
            break
    return cleaned

def save_headlines(headlines, filename=OUTPUT_FILE):
    """Save headlines, one per line."""
    with open(filename, "w", encoding="utf-8") as f:
        for h in headlines:
            f.write(h + "\n")

def choose_extractor_for_url(url):
    """Pick a site-specific extractor when available, else generic."""
    host = url.lower()
    if "bbc." in host:
        return extract_headlines_bbc
    # Add more site-specific rules here:
    # if "cnn." in host: return extract_headlines_cnn
    return extract_headlines_generic

def main():
    url = URL
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()

    print(f"Fetching: {url}")
    try:
        html = fetch_html(url)
    except RuntimeError as e:
        print(e)
        return

    extractor = choose_extractor_for_url(url)
    headlines = extractor(html)

    if not headlines:
        print("No headlines found — try changing the URL or add a site-specific selector.")
        return

    print(f"Found {len(headlines)} headlines (showing up to {MAX_HEADLINES}):\n")
    for i, h in enumerate(headlines, 1):
        print(f"{i}. {h}")

    save_headlines(headlines)
    print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
