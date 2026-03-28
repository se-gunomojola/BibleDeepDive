"""
Matthew Henry Extractor
=======================
Fetches Matthew Henry's Commentary on the Whole Bible from CCEL.
URL pattern: ccel.org/ccel/henry/mhc{vol}.{book}{chapter}.html

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

# CCEL volume map for Matthew Henry
# Format: book -> (volume, ccel_book_code, chapters, testament)
HENRY_BOOKS = {
    "Genesis":        (1,  "Gen",   50, "OT"),
    "Exodus":         (1,  "Exod",  40, "OT"),
    "Leviticus":      (1,  "Lev",   27, "OT"),
    "Numbers":        (1,  "Num",   36, "OT"),
    "Deuteronomy":    (1,  "Deut",  34, "OT"),
    "Joshua":         (2,  "Josh",  24, "OT"),
    "Judges":         (2,  "Judg",  21, "OT"),
    "Ruth":           (2,  "Ruth",   4, "OT"),
    "1 Samuel":       (2,  "1Sam",  31, "OT"),
    "2 Samuel":       (2,  "2Sam",  24, "OT"),
    "1 Kings":        (2,  "1Kgs",  22, "OT"),
    "2 Kings":        (2,  "2Kgs",  25, "OT"),
    "Psalms":         (3,  "Ps",   150, "OT"),
    "Proverbs":       (3,  "Prov",  31, "OT"),
    "Isaiah":         (4,  "Isa",   66, "OT"),
    "Jeremiah":       (4,  "Jer",   52, "OT"),
    "Ezekiel":        (4,  "Ezek",  48, "OT"),
    "Daniel":         (4,  "Dan",   12, "OT"),
    "Matthew":        (5,  "Matt",  28, "NT"),
    "Mark":           (5,  "Mark",  16, "NT"),
    "Luke":           (5,  "Luke",  24, "NT"),
    "John":           (5,  "John",  21, "NT"),
    "Acts":           (6,  "Acts",  28, "NT"),
    "Romans":         (6,  "Rom",   16, "NT"),
    "1 Corinthians":  (6,  "1Cor",  16, "NT"),
    "2 Corinthians":  (6,  "2Cor",  13, "NT"),
    "Galatians":      (6,  "Gal",    6, "NT"),
    "Ephesians":      (6,  "Eph",    6, "NT"),
    "Philippians":    (6,  "Phil",   4, "NT"),
    "Hebrews":        (6,  "Heb",   13, "NT"),
    "Revelation":     (6,  "Rev",   22, "NT"),
}

def fetch_page(vol: int, book_code: str, chapter: int) -> Optional[str]:
    url = f"https://www.ccel.org/ccel/henry/mhc{vol}.{book_code}.{chapter}.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.text if r.status_code == 200 else None
    except:
        return None

def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove navigation and scripts
    for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    # CCEL content is in div.sectionbody or main content area
    content = soup.find("div", class_="sectionbody")
    if not content:
        content = soup.find("div", id="content")
    if not content:
        content = soup.find("body")
    if not content:
        return ""
    text = content.get_text(separator=" ", strip=True)
    return clean_text(text)

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

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

def extract_henry(books: Optional[List[str]] = None, delay: float = REQUEST_DELAY) -> List[Dict]:
    books_to_process = books if books else list(HENRY_BOOKS.keys())
    all_chunks = []
    print(f"Extracting Matthew Henry — {len(books_to_process)} book(s)")

    for book_name in books_to_process:
        if book_name not in HENRY_BOOKS:
            print(f"  {book_name}: not in Henry map — skipping")
            continue
        vol, book_code, num_chapters, testament = HENRY_BOOKS[book_name]
        book_chunks = 0

        for chapter in range(1, num_chapters + 1):
            html = fetch_page(vol, book_code, chapter)
            if not html:
                continue
            text = extract_text(html)
            if not text or len(text) < 100:
                continue
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": chunk,
                    "commentator": "Matthew Henry",
                    "work": "Commentary on the Whole Bible",
                    "book": book_name,
                    "chapter": chapter,
                    "chunk_index": i,
                    "reference": f"{book_name} {chapter}",
                    "testament": testament,
                })
            book_chunks += len(chunks)
            time.sleep(delay)

        print(f"  {book_name}: {book_chunks} chunks")

    print(f"\nDone — {len(all_chunks)} total chunks from Matthew Henry")
    return all_chunks

if __name__ == "__main__":
    print("Testing Matthew Henry on Psalm 23 and Romans 8...\n")
    chunks = extract_henry(books=["Psalms", "Romans"], delay=0.5)
    if chunks:
        print(f"\n✓ {len(chunks)} chunks extracted")
        print(chunks[0]["text"][:300])
    else:
        print("No chunks — check CCEL URLs")
