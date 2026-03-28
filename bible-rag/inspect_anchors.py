"""
Find all anchor names on Psalm 23 page
"""
import requests
import re

url = "https://archive.spurgeon.org/treasury/ps023.php"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

response = requests.get(url, headers=headers, timeout=15)
html = response.text

# Find all anchor name attributes
anchors = re.findall(r'<[Aa]\s+[^>]*[Nn][Aa][Mm][Ee]\s*=\s*["\']?([^"\'>\s]+)', html)
print("All anchor names found:")
for a in anchors:
    print(f"  '{a}'")

# Also show 500 chars around each anchor
print("\n--- Context around each anchor ---")
for a in anchors:
    pos = html.lower().find(f'name="{a.lower()}"')
    if pos == -1:
        pos = html.lower().find(f"name={a.lower()}")
    if pos != -1:
        print(f"\n[{a}] at position {pos}:")
        print(html[max(0,pos-100):pos+200])
        print("...")
