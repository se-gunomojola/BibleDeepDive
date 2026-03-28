"""
Gill Content Inspector - find where commentary text starts
"""
import requests
import re

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
url = "https://sacred-texts.com/bib/cmt/gill/psa023.htm"
response = requests.get(url, headers=headers, timeout=15)
html = response.text

# Show from position 4000 onwards where content likely starts
print("--- CHARS 4000-7000 ---")
print(html[4000:7000])
