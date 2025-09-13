import requests, re, json
from datetime import datetime

URL = "https://halu.serv00.net/poli2.php"
OUTPUT = "LiveVoli.json"

html = requests.get(URL).text

# Format contoh baris:
# 14-09-2025 09:30 WIB  
pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+WIB\s+【\d+†([^†]+)†([^】]+)】'
matches = re.findall(pattern, html)

data = []
for date_str, time_str, title, src in matches:
    dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
    start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"

    # cari ID untuk poster
    m = re.search(r'/media/([^/]+)/', src)
    poster = f"https://cdn.jwplayer.com/v2/media/{m.group(1)}/poster.jpg?width=1920" if m else ""

    data.append({
        "title": title.strip(),
        "start": start_iso,
        "src": src.strip(),
        "poster": poster
    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Updated {OUTPUT} with {len(data)} items")
