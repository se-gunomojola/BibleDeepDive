#!/bin/bash
pip install -r requirements.txt
pip install -r bible-rag/requirements-rag.txt
cd bible-rag
python3 index.py --source spurgeon
python3 index.py --source gill
python3 index.py --source clarke --books "Psalms" "Romans" "Genesis" "Isaiah" "John" "Hebrews"
python3 index.py --source barnes --books "Psalms" "Romans" "Genesis" "Isaiah" "John" "Hebrews"
cd ..
