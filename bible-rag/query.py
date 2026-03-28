"""
BibleRAG Query
==============
Shared query function for retrieving commentary chunks from ChromaDB.
Used by both BibleDeepDive (web app) and bible-mcp (Claude Desktop).

Usage:
    from query import search_commentaries
    chunks = search_commentaries("Psalm 23", book="Psalms", chapter=23)

Author: Segun Omojola
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional

# ── Database Setup ─────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
_collection = None

def get_collection():
    """Get the Chroma collection — cached after first call."""
    global _collection
    if _collection is not None:
        return _collection
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    _collection = client.get_or_create_collection(
        name="bible_commentaries",
        embedding_function=ef,
    )
    return _collection


# ── Query Function ─────────────────────────────────────────────────────────────

def search_commentaries(
    reference: str,
    book: Optional[str] = None,
    chapter: Optional[int] = None,
    top_k: int = 5,
) -> List[Dict]:
    """
    Search the commentary database for chunks relevant to a Bible reference.

    Args:
        reference: Bible reference string e.g. "Psalm 23", "Romans 8"
        book: Optional book filter e.g. "Psalms", "Romans"
        chapter: Optional chapter filter e.g. 23, 8
        top_k: Number of chunks to return (default 5)

    Returns:
        List of dicts with keys: text, commentator, work, reference, score
        Empty list if database has no relevant content.
    """
    try:
        collection = get_collection()

        if collection.count() == 0:
            return []

        # Build filter if book and chapter are provided
        where = None
        if book and chapter:
            where = {
                "$and": [
                    {"book": {"$eq": book}},
                    {"chapter": {"$eq": chapter}},
                ]
            }
        elif book:
            where = {"book": {"$eq": book}}

        # Query Chroma
        results = collection.query(
            query_texts=[reference],
            n_results=min(top_k, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"][0]:
            return []

        # Format results
        chunks = []
        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({
                "text": doc,
                "commentator": meta.get("commentator", "Unknown"),
                "work": meta.get("work", ""),
                "reference": meta.get("reference", ""),
                "book": meta.get("book", ""),
                "chapter": meta.get("chapter", 0),
                "score": round(1 - distance, 3),  # convert distance to similarity score
            })

        return chunks

    except Exception as e:
        # Graceful fallback — if RAG fails, app continues without it
        print(f"RAG query failed (non-fatal): {e}")
        return []


def format_for_prompt(chunks: List[Dict]) -> str:
    """
    Format retrieved chunks into a string for injection into Claude prompts.
    Returns empty string if no chunks.
    """
    if not chunks:
        return ""

    lines = ["\n\nCOMMENTARY SOURCES — cite these specifically in Layer 7:"]
    lines.append("=" * 60)

    for i, chunk in enumerate(chunks, 1):
        lines.append(f"\n[{i}] {chunk['commentator']} — {chunk['work']}")
        lines.append(f"Reference: {chunk['reference']}")
        lines.append(f"Relevance: {chunk['score']}")
        lines.append("-" * 40)
        lines.append(chunk["text"][:800])  # cap at 800 chars per chunk in prompt
        lines.append("")

    lines.append("=" * 60)
    lines.append("Use the above as your primary sources for Layer 7.")
    lines.append("Quote directly and attribute precisely.")

    return "\n".join(lines)


# ── Test ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing query on Psalm 23...\n")

    chunks = search_commentaries("Psalm 23", book="Psalms", chapter=23)

    if chunks:
        print(f"✓ Found {len(chunks)} chunk(s)\n")
        for i, chunk in enumerate(chunks, 1):
            print(f"[{i}] {chunk['commentator']} — {chunk['reference']} (score: {chunk['score']})")
            print(f"    {chunk['text'][:150]}...")
            print()

        print("\n--- Formatted for prompt ---")
        print(format_for_prompt(chunks[:2]))
    else:
        print("No results — ensure index.py has been run first")
