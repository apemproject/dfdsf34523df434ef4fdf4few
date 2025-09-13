import requests, re, json
from datetime import datetime

URL = "https://halu.serv00.net/poli2.php"
OUTPUT = "LiveVoli.json"

print(f"🌐 Fetching data from {URL} ...")
r = requests.get(URL, timeout=15)
r.raise_for_status()
html = r.text
print("✅ Request success")
print(f"🔎 HTML length: {len(html)}")
print("🔎 HTML preview:\n", html[:500])

# Regex fleksibel: href=... sampai spasi sebelum target=
pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+WIB\s*<a href=([^\s]+)\s+target=_blank>([^<]+)</a>'
matches = re.findall(pattern, html)

print(f"📊 Jumlah match ditemukan: {len(matches)}")
for m in matches:
    print("➡️", m)  # debug biar kelihatan di log

data = []
for date_str, time_str, src, title in matches:
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
        start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"

        # cari poster dari ID media
        m = re.search(r'/media/([^/]+)/', src)
        poster = f"https://cdn.jwplayer.com/v2/media/{m.group(1)}/poster.jpg?width=1920" if m else ""

        data.append({
            "title": title.strip(),
            "start": start_iso,
            "src": src.strip(),
            "poster": poster
        })
    except Exception as e:
        print("⚠️ Error parsing:", date_str, time_str, title, e)

if data:
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Data berhasil disimpan ke {OUTPUT} ({len(data)} pertandingan).")
else:
    print("ℹ️ Tidak ada jadwal ditemukan. File lama tidak diubah.")
