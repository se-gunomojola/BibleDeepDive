"""
BibleRAG Indexer
================
Indexes commentary chunks into ChromaDB.
Supports: spurgeon, gill, clarke, barnes, henry, jfb

Usage:
    python3 index.py --source spurgeon --psalms 1 150
    python3 index.py --source gill
    python3 index.py --source gill --books "Psalms" "Romans"
    python3 index.py --source henry --books "Psalms" "Romans"
    python3 index.py --source jfb --books "Psalms" "Romans"
    python3 index.py --stats

Author: Segun Omojola
"""

import argparse
import os
import sys
import chromadb
from chromadb.utils import embedding_functions

DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name="bible_commentaries",
        embedding_function=ef,
        metadata={"description": "Public domain Bible commentaries — BibleDeepDive RAG"}
    )

def index_chunks(chunks: list, collection, batch_size: int = 50):
    if not chunks:
        print("No chunks to index.")
        return
    print(f"\nIndexing {len(chunks)} chunks into Chroma...")
    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        ids, documents, metadatas = [], [], []
        for chunk in batch:
            chunk_id = (
                f"{chunk['commentator'].lower().replace(' ', '_').replace('-', '_')}_"
                f"{chunk['book'].lower().replace(' ', '_')}_"
                f"ch{chunk['chapter']}_"
                f"chunk{chunk['chunk_index']}"
            )
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append({
                "commentator": chunk["commentator"],
                "work": chunk["work"],
                "book": chunk["book"],
                "chapter": chunk["chapter"],
                "reference": chunk["reference"],
                "testament": chunk["testament"],
                "chunk_index": chunk["chunk_index"],
            })
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        total += len(batch)
        print(f"  {total}/{len(chunks)} chunks indexed...", end="\r")
    print(f"\n✓ Done — {total} chunks stored")

def print_stats(collection):
    count = collection.count()
    print(f"\nDatabase: {DB_PATH}")
    print(f"Total chunks: {count}")
    if count > 0:
        sample = collection.peek(limit=8)
        print("Sample entries:")
        for id_, meta in zip(sample["ids"], sample["metadatas"]):
            print(f"  {meta['commentator']:25} {meta['reference']}")

def main():
    parser = argparse.ArgumentParser(description="BibleRAG Indexer")
    parser.add_argument("--source",
                        choices=["spurgeon", "gill", "clarke", "barnes", "henry", "jfb"],
                        help="Commentator to index")
    parser.add_argument("--psalms", nargs=2, type=int, metavar=("START", "END"))
    parser.add_argument("--books", nargs="+")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    collection = get_collection()

    if args.stats:
        print_stats(collection)
        return

    if not args.source:
        parser.print_help()
        return

    if args.source == "spurgeon":
        from extractors.spurgeon import extract_spurgeon
        start = args.psalms[0] if args.psalms else 1
        end = args.psalms[1] if args.psalms else 150
        chunks = extract_spurgeon(psalm_start=start, psalm_end=end)

    elif args.source in ("gill", "clarke", "barnes"):
        from extractors.sacred_texts import extract_commentator
        chunks = extract_commentator(commentator_key=args.source, books=args.books)

    elif args.source == "henry":
        from extractors.henry import extract_henry
        chunks = extract_henry(books=args.books)

    elif args.source == "jfb":
        from extractors.jfb import extract_jfb
        chunks = extract_jfb(books=args.books)

    else:
        print(f"Unknown source: {args.source}")
        sys.exit(1)

    if not chunks:
        print("No chunks extracted.")
        sys.exit(1)

    index_chunks(chunks, collection)
    print_stats(collection)

if __name__ == "__main__":
    main()
