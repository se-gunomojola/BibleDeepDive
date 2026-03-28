"""
Spurgeon Extractor
==================
Fetches and parses Charles Spurgeon's Treasury of David
from archive.spurgeon.org

Structure confirmed:
- Exposition section: between <a name="expo"> and <a name="expl">
- One page per Psalm at /treasury/psNNN.php

Author: Segun Omojola
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from typing import List, Dict

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_URL = "https://archive.spurgeon.org/treasury/ps{:03d}.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
REQUEST_DELAY = 1.5


# ── Fetcher ────────────────────────────────────────────────────────────────────

def fetch_psalm_page(psalm_number: int) -> str | None:
    url = BASE_URL.format(psalm_number)
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.text
        print(f"  Warning: Psalm {psalm_number} returned status {response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"  Error fetching Psalm {psalm_number}: {e}")
        return None


# ── Parser ─────────────────────────────────────────────────────────────────────

def extract_exposition(html: str, psalm_number: int) -> str:
    """
    Extract exposition section using raw string positions.
    Confirmed structure: <a name="expo">...</a name="expl">
    """
    # Find start position — just after the expo anchor
    expo_match = re.search(r'<a\s+name=["\']?expo["\']?>', html, re.IGNORECASE)
    if not expo_match:
        print(f"  Warning: No expo anchor found for Psalm {psalm_number}")
        return ""

    # Find end position — at the expl anchor
    expl_match = re.search(r'<a\s+name=["\']?expl["\']?>', html, re.IGNORECASE)
    if not expl_match:
        # Fall back to hint anchor
        expl_match = re.search(r'<a\s+name=["\']?hint["\']?>', html, re.IGNORECASE)

    start = expo_match.end()
    end = expl_match.start() if expl_match else start + 50000

    # Extract the HTML slice between the two anchors
    section_html = html[start:end]

    # Parse with BeautifulSoup to strip remaining tags
    soup = BeautifulSoup(section_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    return clean_text(text)


def clean_text(text: str) -> str:
    """Clean extracted text — normalise whitespace and fix HTML entities."""
    replacements = {
        '&#151;': '—', '&#8212;': '—',
        '&#8220;': '"', '&#8221;': '"',
        '&#8216;': "'", '&#8217;': "'",
        '&amp;': '&', '&nbsp;': ' ',
        '&#39;': "'",
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ── Chunker ────────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping word-count chunks."""
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start:start + chunk_size])
        if len(chunk.strip()) > 100:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ── Main Extractor ─────────────────────────────────────────────────────────────

def extract_spurgeon(psalm_start: int = 1, psalm_end: int = 150, delay: float = REQUEST_DELAY) -> List[Dict]:
    """
    Extract Spurgeon commentary for a range of Psalms.
    Returns list of chunk dicts ready for Chroma indexing.
    """
    all_chunks = []
    print(f"Extracting Spurgeon — Psalms {psalm_start} to {psalm_end}")

    for psalm_num in range(psalm_start, psalm_end + 1):
        print(f"  Psalm {psalm_num}/{psalm_end}...", end=" ", flush=True)

        html = fetch_psalm_page(psalm_num)
        if not html:
            print("skipped")
            continue

        text = extract_exposition(html, psalm_num)
        if not text or len(text) < 100:
            print(f"too short ({len(text)} chars), skipped")
            continue

        chunks = chunk_text(text)
        print(f"{len(chunks)} chunks ({len(text)} chars)")

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "commentator": "Spurgeon",
                "work": "Treasury of David",
                "book": "Psalms",
                "chapter": psalm_num,
                "chunk_index": i,
                "reference": f"Psalm {psalm_num}",
                "testament": "OT"
            })

        time.sleep(delay)

    print(f"\nDone — {len(all_chunks)} total chunks")
    return all_chunks


# ── Test ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing Spurgeon extractor on Psalm 23...\n")
    chunks = extract_spurgeon(psalm_start=23, psalm_end=23, delay=0)
    if chunks:
        print(f"\n✓ Extracted {len(chunks)} chunk(s)")
        print(f"\nFirst chunk preview (500 chars):")
        print("-" * 60)
        print(chunks[0]["text"][:500])
        print("-" * 60)
        print(f"\nMetadata: { {k: v for k, v in chunks[0].items() if k != 'text'} }")
    else:
        print("No chunks extracted — check the extractor")
