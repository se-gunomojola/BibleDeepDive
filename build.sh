#!/bin/bash
set -e
echo "Installing dependencies..."
pip install -r requirements.txt
pip install chromadb==1.5.5 requests beautifulsoup4

echo "Building RAG commentary database..."
cd bible-rag
python3 index.py --source spurgeon
python3 index.py --source gill
python3 index.py --source clarke --books "Psalms" "Romans" "Genesis" "Isaiah" "John" "Hebrews"
python3 index.py --source barnes --books "Psalms" "Romans" "Genesis" "Isaiah" "John" "Hebrews"
cd ..
echo "RAG database built successfully"
