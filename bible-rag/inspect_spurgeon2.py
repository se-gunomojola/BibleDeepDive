"""
Spurgeon HTML Inspector - Deep
Shows the exposition section structure
"""

import requests

url = "https://archive.spurgeon.org/treasury/ps023.php"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers, timeout=15)
text = response.text

# Find the exposition anchor and show 3000 chars from there
expo_pos = text.find('name="expo"')
if expo_pos == -1:
    expo_pos = text.find('name=expo')
if expo_pos == -1:
    expo_pos = text.find('EXPO')

print(f"Exposition found at position: {expo_pos}")
print("\n--- 3000 CHARS FROM EXPOSITION ---")
print(text[expo_pos:expo_pos+3000])
