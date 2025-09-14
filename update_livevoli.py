import requests, re, json
from datetime import datetime, timezone, timedelta

URL = "https://halu.serv00.net/poli2.php"
OUTPUT = "LiveVoli.json"

print(f"🌐 Fetching data from {URL} ...")
r = requests.get(URL, timeout=15)
r.raise_for_status()
html = r.text
print("✅ Request success")

# 🔹 Lewati bagian Watch Live - Schedule Screen
sections = re.split(r'Watch Live - Schedule Screen', html, maxsplit=1)
html_section = sections[1] if len(sections) > 1 else html

# 🔹 Ambil semua link resmi (Live and upcoming, Upcoming VNL, dsb.)
pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+WIB\s+<a href=[\'"]?([^\'"\s>]+)[\'"]?.*?>([^<]+)</a>'
matches = re.findall(pattern, html_section)
print(f"📊 Jumlah jadwal ditemukan: {len(matches)}")

data = []
for date_str, time_str, src, title in matches:
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
        start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"

        # Cari poster dari ID media JWPlayer
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

# 🔹 Hapus duplikat
seen = set()
unique_data = []
for item in data:
    key = (item["title"], item["start"], item["src"])
    if key not in seen:
        seen.add(key)
        unique_data.append(item)

# 🔹 Hapus pertandingan yang sudah lewat (WIB)
now = datetime.now(timezone(timedelta(hours=7)))
data = [item for item in unique_data if datetime.fromisoformat(item["start"]) > now]

# 🔹 Simpan JSON terbaru
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"💾 Data berhasil disimpan ({len(data)} pertandingan).")
