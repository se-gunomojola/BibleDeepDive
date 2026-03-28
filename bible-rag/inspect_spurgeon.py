"""
Spurgeon HTML Inspector
Run this once to see the raw HTML structure of the Spurgeon Archive.
Paste the output back so we can write the parser correctly.
"""

import requests

url = "https://archive.spurgeon.org/treasury/ps023.php"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers, timeout=15)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)} chars")
print("\n--- FIRST 3000 CHARACTERS ---")
print(response.text[:3000])
