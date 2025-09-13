import requests, re, json
from datetime import datetime
import os

URL = "https://halu.serv00.net/poli2.php"
OUTPUT = "LiveVoli.json"

print(f"🔍 Fetching data from {URL} ...")
try:
    r = requests.get(URL, timeout=15)
    r.raise_for_status()
    html = r.text
    print("✅ Request success")
    print("🔎 Raw response preview:\n", html[:500])  # tampilkan 500 karakter pertama
except Exception as e:
    print("❌ Gagal fetch data:", e)
    exit(1)

# Regex sesuai pola view-source
pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+WIB\s+【\d+†([^†]+)†([^】]+)】'
matches = re.findall(pattern, html)

print(f"📊 Jumlah baris cocok: {len(matches)}")

data = []
for idx, (date_str, time_str, title, src) in enumerate(matches, 1):
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
        start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"

        # Cari ID media untuk poster
        m = re.search(r'/media/([^/]+)/', src)
        poster = f"https://cdn.jwplayer.com/v2/media/{m.group(1)}/poster.jpg?width=1920" if m else ""

        item = {
            "title": title.strip(),
            "start": start_iso,
            "src": src.strip(),
            "poster": poster
        }
        data.append(item)

        print(f"   ✔️ Parsed [{idx}] {item['title']} ({item['start']})")
    except Exception as e:
        print(f"   ⚠️ Gagal parsing [{idx}]:", e)

if data:
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Updated {OUTPUT} with {len(data)} items")
else:
    print("ℹ️ Tidak ada jadwal ditemukan. File lama tidak diubah.")
