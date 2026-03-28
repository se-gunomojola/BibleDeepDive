"""
Gill HTML Inspector
Inspect the HTML structure of sacred-texts.com Gill commentary
"""
import requests

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# Fetch Psalm 23
url = "https://sacred-texts.com/bib/cmt/gill/psa023.htm"
response = requests.get(url, headers=headers, timeout=15)
html = response.text

print(f"Status: {response.status_code}")
print(f"Length: {len(html)} chars")
print("\n--- FIRST 2000 CHARS ---")
print(html[:2000])
print("\n--- MIDDLE 2000 CHARS (from position 2000) ---")
print(html[2000:4000])
