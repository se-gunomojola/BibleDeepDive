"""
Sacred Texts Extractor
======================
Fetches and parses commentaries from sacred-texts.com.
Handles three commentators with identical URL structure:
    - John Gill (gill)
    - Adam Clarke (clarke)
    - Albert Barnes (barnes)

URL pattern: sacred-texts.com/bib/cmt/{commentator}/{book_abbr}{chapter:03d}.htm
Example: sacred-texts.com/bib/cmt/gill/rom008.htm

Author: Segun Omojola
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_URL = "https://sacred-texts.com/bib/cmt/{commentator}/{book}{chapter:03d}.htm"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
REQUEST_DELAY = 1.5

# ── Commentator config ─────────────────────────────────────────────────────────
COMMENTATORS = {
    "gill": {
        "name": "John Gill",
        "work": "Exposition of the Old and New Testament",
        "slug": "gill",
    },
    "clarke": {
        "name": "Adam Clarke",
        "work": "Commentary on the Bible",
        "slug": "clarke",
    },
    "barnes": {
        "name": "Albert Barnes",
        "work": "Notes on the Bible",
        "slug": "barnes",
    },
}

# ── Bible book map ─────────────────────────────────────────────────────────────
# Format: book_name -> (url_abbreviation, chapters, testament)
BIBLE_BOOKS = {
    # Old Testament
    "Genesis":        ("gen", 50, "OT"),
    "Exodus":         ("exo", 40, "OT"),
    "Leviticus":      ("lev", 27, "OT"),
    "Numbers":        ("num", 36, "OT"),
    "Deuteronomy":    ("deu", 34, "OT"),
    "Joshua":         ("jos", 24, "OT"),
    "Judges":         ("jdg", 21, "OT"),
    "Ruth":           ("rut",  4, "OT"),
    "1 Samuel":       ("sa1", 31, "OT"),
    "2 Samuel":       ("sa2", 24, "OT"),
    "1 Kings":        ("kg1", 22, "OT"),
    "2 Kings":        ("kg2", 25, "OT"),
    "1 Chronicles":   ("ch1", 29, "OT"),
    "2 Chronicles":   ("ch2", 36, "OT"),
    "Ezra":           ("ezr", 10, "OT"),
    "Nehemiah":       ("neh", 13, "OT"),
    "Esther":         ("est", 10, "OT"),
    "Job":            ("job", 42, "OT"),
    "Psalms":         ("psa",150, "OT"),
    "Proverbs":       ("pro", 31, "OT"),
    "Ecclesiastes":   ("ecc", 12, "OT"),
    "Song of Solomon":("sol",  8, "OT"),
    "Isaiah":         ("isa", 66, "OT"),
    "Jeremiah":       ("jer", 52, "OT"),
    "Lamentations":   ("lam",  5, "OT"),
    "Ezekiel":        ("eze", 48, "OT"),
    "Daniel":         ("dan", 12, "OT"),
    "Hosea":          ("hos", 14, "OT"),
    "Joel":           ("joe",  3, "OT"),
    "Amos":           ("amo",  9, "OT"),
    "Obadiah":        ("oba",  1, "OT"),
    "Jonah":          ("jon",  4, "OT"),
    "Micah":          ("mic",  7, "OT"),
    "Nahum":          ("nah",  3, "OT"),
    "Habakkuk":       ("hab",  3, "OT"),
    "Zephaniah":      ("zep",  3, "OT"),
    "Haggai":         ("hag",  2, "OT"),
    "Zechariah":      ("zac", 14, "OT"),
    "Malachi":        ("mal",  4, "OT"),
    # New Testament
    "Matthew":        ("mat", 28, "NT"),
    "Mark":           ("mar", 16, "NT"),
    "Luke":           ("luk", 24, "NT"),
    "John":           ("joh", 21, "NT"),
    "Acts":           ("act", 28, "NT"),
    "Romans":         ("rom", 16, "NT"),
    "1 Corinthians":  ("co1", 16, "NT"),
    "2 Corinthians":  ("co2", 13, "NT"),
    "Galatians":      ("gal",  6, "NT"),
    "Ephesians":      ("eph",  6, "NT"),
    "Philippians":    ("phi",  4, "NT"),
    "Colossians":     ("col",  4, "NT"),
    "1 Thessalonians":("th1",  5, "NT"),
    "2 Thessalonians":("th2",  3, "NT"),
    "1 Timothy":      ("ti1",  6, "NT"),
    "2 Timothy":      ("ti2",  4, "NT"),
    "Titus":          ("tit",  3, "NT"),
    "Philemon":       ("plm",  1, "NT"),
    "Hebrews":        ("heb", 13, "NT"),
    "James":          ("jam",  5, "NT"),
    "1 Peter":        ("pe1",  5, "NT"),
    "2 Peter":        ("pe2",  3, "NT"),
    "1 John":         ("jo1",  5, "NT"),
    "2 John":         ("jo2",  1, "NT"),
    "3 John":         ("jo3",  1, "NT"),
    "Jude":           ("jde",  1, "NT"),
    "Revelation":     ("rev", 22, "NT"),
}


# ── Fetcher ────────────────────────────────────────────────────────────────────

def fetch_page(commentator_slug: str, book_abbr: str, chapter: int) -> Optional[str]:
    url = BASE_URL.format(
        commentator=commentator_slug,
        book=book_abbr,
        chapter=chapter
    )
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.text
        if response.status_code == 404:
            return None  # Chapter doesn't exist — skip silently
        print(f"    Warning: {url} returned {response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"    Error fetching {url}: {e}")
        return None


# ── Parser ─────────────────────────────────────────────────────────────────────

def extract_commentary_text(html: str) -> str:
    """
    Extract main commentary text from sacred-texts.com page.
    Content is in <p> tags after the second <HR> element.
    Navigation, headers and metadata appear before content.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove navigation elements
    for tag in soup.find_all(["script", "style", "img", "a"]):
        tag.decompose()

    # Find all <hr> tags — content starts after the second one
    hrs = soup.find_all("hr")
    if len(hrs) >= 2:
        # Get everything after the second HR
        second_hr = hrs[1]
        content_parts = []
        for sibling in second_hr.find_next_siblings():
            text = sibling.get_text(separator=" ", strip=True)
            if text and len(text) > 20:
                content_parts.append(text)
        text = " ".join(content_parts)
    else:
        # Fallback — get all body text
        text = soup.get_text(separator=" ", strip=True)

    return clean_text(text)


def clean_text(text: str) -> str:
    """Normalise whitespace and fix common HTML entities."""
    replacements = {
        '&#151;': '—', '&#8212;': '—',
        '&#8220;': '"', '&#8221;': '"',
        '&#8216;': "'", '&#8217;': "'",
        '&amp;': '&', '&nbsp;': ' ',
        '&#39;': "'", '\xa0': ' ',
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ── Chunker ────────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
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

def extract_commentator(
    commentator_key: str,
    books: Optional[List[str]] = None,
    delay: float = REQUEST_DELAY
) -> List[Dict]:
    """
    Extract commentary for a commentator across specified books.

    Args:
        commentator_key: "gill", "clarke", or "barnes"
        books: list of book names to extract. None = all 66 books.
        delay: seconds between requests

    Returns:
        List of chunk dicts ready for Chroma indexing.
    """
    if commentator_key not in COMMENTATORS:
        raise ValueError(f"Unknown commentator: {commentator_key}. Choose from: {list(COMMENTATORS.keys())}")

    config = COMMENTATORS[commentator_key]
    books_to_process = books if books else list(BIBLE_BOOKS.keys())
    all_chunks = []

    print(f"Extracting {config['name']} — {len(books_to_process)} book(s)")

    for book_name in books_to_process:
        if book_name not in BIBLE_BOOKS:
            print(f"  Unknown book: {book_name} — skipping")
            continue

        book_abbr, num_chapters, testament = BIBLE_BOOKS[book_name]
        book_chunks = 0

        for chapter in range(1, num_chapters + 1):
            html = fetch_page(config["slug"], book_abbr, chapter)
            if not html:
                continue

            text = extract_commentary_text(html)
            if not text or len(text) < 100:
                continue

            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": chunk,
                    "commentator": config["name"],
                    "work": config["work"],
                    "book": book_name,
                    "chapter": chapter,
                    "chunk_index": i,
                    "reference": f"{book_name} {chapter}",
                    "testament": testament,
                })
            book_chunks += len(chunks)
            time.sleep(delay)

        print(f"  {book_name}: {book_chunks} chunks")

    print(f"\nDone — {len(all_chunks)} total chunks from {config['name']}")
    return all_chunks


# ── Test ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    commentator = sys.argv[1] if len(sys.argv) > 1 else "gill"
    print(f"Testing {commentator} extractor on Psalm 23 and Romans 8...\n")

    chunks = extract_commentator(
        commentator_key=commentator,
        books=["Psalms", "Romans"],
        delay=0.5
    )

    if chunks:
        print(f"\n✓ Extracted {len(chunks)} total chunk(s)")
        print(f"\nSample chunk:")
        print("-" * 60)
        print(chunks[0]["text"][:400])
        print("-" * 60)
        print(f"Metadata: { {k: v for k, v in chunks[0].items() if k != 'text'} }")
    else:
        print("No chunks extracted")
