"""
Jamieson-Fausset-Brown Extractor
=================================
Fetches JFB Commentary from CCEL.
URL pattern: ccel.org/ccel/jamieson/jfb.{Book}.{Book}_C{chapter}.html

Author: Segun Omojola
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
REQUEST_DELAY = 1.5

JFB_BOOKS = {
    "Genesis":       ("Gen",   "Gen",   50, "OT"),
    "Exodus":        ("Exod",  "Exod",  40, "OT"),
    "Psalms":        ("Ps",    "Ps",   150, "OT"),
    "Proverbs":      ("Prov",  "Prov",  31, "OT"),
    "Isaiah":        ("Isa",   "Isa",   66, "OT"),
    "Jeremiah":      ("Jer",   "Jer",   52, "OT"),
    "Ezekiel":       ("Ezek",  "Ezek",  48, "OT"),
    "Daniel":        ("Dan",   "Dan",   12, "OT"),
    "Matthew":       ("Matt",  "Matt",  28, "NT"),
    "Mark":          ("Mark",  "Mark",  16, "NT"),
    "Luke":          ("Luke",  "Luke",  24, "NT"),
    "John":          ("John",  "John",  21, "NT"),
    "Acts":          ("Acts",  "Acts",  28, "NT"),
    "Romans":        ("Rom",   "Rom",   16, "NT"),
    "1 Corinthians": ("1Cor",  "1Cor",  16, "NT"),
    "Galatians":     ("Gal",   "Gal",    6, "NT"),
    "Ephesians":     ("Eph",   "Eph",    6, "NT"),
    "Hebrews":       ("Heb",   "Heb",   13, "NT"),
    "Revelation":    ("Rev",   "Rev",   22, "NT"),
}

def fetch_page(book_section: str, book_chapter: str, chapter: int) -> Optional[str]:
    url = f"https://www.ccel.org/ccel/jamieson/jfb.{book_section}.{book_chapter}_C{chapter}.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.text if r.status_code == 200 else None
    except:
        return None

def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    content = soup.find("div", class_="sectionbody")
    if not content:
        content = soup.find("div", id="content")
    if not content:
        content = soup.find("body")
    if not content:
        return ""
    text = content.get_text(separator=" ", strip=True)
    return re.sub(r'\s+', ' ', text).strip()

def chunk_text(text: str) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start:start + CHUNK_SIZE])
        if len(chunk.strip()) > 100:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def extract_jfb(books: Optional[List[str]] = None, delay: float = REQUEST_DELAY) -> List[Dict]:
    books_to_process = books if books else list(JFB_BOOKS.keys())
    all_chunks = []
    print(f"Extracting Jamieson-Fausset-Brown — {len(books_to_process)} book(s)")

    for book_name in books_to_process:
        if book_name not in JFB_BOOKS:
            print(f"  {book_name}: not in JFB map — skipping")
            continue
        book_sec, book_chap, num_chapters, testament = JFB_BOOKS[book_name]
        book_chunks = 0

        for chapter in range(1, num_chapters + 1):
            html = fetch_page(book_sec, book_chap, chapter)
            if not html:
                continue
            text = extract_text(html)
            if not text or len(text) < 100:
                continue
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": chunk,
                    "commentator": "Jamieson-Fausset-Brown",
                    "work": "Commentary Critical and Explanatory",
                    "book": book_name,
                    "chapter": chapter,
                    "chunk_index": i,
                    "reference": f"{book_name} {chapter}",
                    "testament": testament,
                })
            book_chunks += len(chunks)
            time.sleep(delay)

        print(f"  {book_name}: {book_chunks} chunks")

    print(f"\nDone — {len(all_chunks)} total chunks from JFB")
    return all_chunks

if __name__ == "__main__":
    print("Testing JFB on Psalm 23 and Romans...\n")
    chunks = extract_jfb(books=["Psalms", "Romans"], delay=0.5)
    if chunks:
        print(f"\n✓ {len(chunks)} chunks extracted")
        print(chunks[0]["text"][:300])
    else:
        print("No chunks — check CCEL URLs")
