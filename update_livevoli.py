import requests, re, json
from datetime import datetime, timezone, timedelta

# 🌐 URL sumber jadwal
URL = "https://halu.serv00.net/poli2.php"

# 💾 File JSON output
OUTPUT = "LiveVoli.json"

# ⏱ Waktu timezone WIB
TZ = timezone(timedelta(hours=7))

def fetch_live_data():
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print("⚠️ Gagal ambil data:", e)
        return

    # 🔹 Regex ambil semua jadwal + link
    # Format: 14-09-2025 12:50 WIB <a href=link>Title</a>
    pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+WIB\s+<a href=[\'"]?([^\'"\s>]+)[\'"]?.*?>([^<]+)</a>'
    matches = re.findall(pattern, html)

    data = []
    seen = set()  # deduplikasi

    for date_str, time_str, src, title in matches:
        try:
            # ⏰ Format ISO dengan timezone
            dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
            start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"

            key = (title.strip(), start_iso, src.strip())
            if key in seen:
                continue  # lewati duplikat
            seen.add(key)

            # 🔹 Ambil poster dari JWPlayer
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

    # 🔹 Hapus jadwal yang sudah lewat (opsional, bisa dikomentari kalau mau semua tetap muncul)
    now = datetime.now(TZ)
    data = [item for item in data if datetime.fromisoformat(item["start"]) > now]

    # 🔹 Simpan JSON
    try:
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Data berhasil disimpan ({len(data)} pertandingan).")
    except Exception as e:
        print("⚠️ Gagal simpan JSON:", e)

if __name__ == "__main__":
    fetch_live_data()
