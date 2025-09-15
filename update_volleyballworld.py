import requests, re, json
from datetime import datetime, timezone, timedelta

URL = "https://halu.serv00.net/poli2.php"
OUTPUT = "volleyballworld.json"
MATCH_DURATION_HOURS = 3  # asumsi durasi pertandingan 2 jam

def fetch_live_data():
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print("⚠️ Error fetching HTML:", e)
        return

    # 🔹 Ambil semua jadwal (Live + Upcoming)
    pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+WIB\s+<a href=[\'"]?([^\'"\s>]+)[\'"]?.*?>([^<]+)</a>'
    matches = re.findall(pattern, html)

    data = []
    seen = set()  # untuk duplikat

    for date_str, time_str, src, title in matches:
        title = title.strip()
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
            start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"

            # cek duplikat berdasarkan judul + waktu + src
            key = (title, start_iso, src.strip())
            if key in seen:
                continue
            seen.add(key)

            # ambil poster dari URL JWPlayer
            m = re.search(r'/media/([^/]+)/', src)
            poster = f"https://cdn.jwplayer.com/v2/media/{m.group(1)}/poster.jpg?width=1920" if m else ""

            data.append({
                "title": title,
                "start": start_iso,
                "src": src.strip(),
                "poster": poster
            })
        except Exception as e:
            print("⚠️ Error parsing:", date_str, time_str, title, e)

    # 🔹 Filter pertandingan yang sudah selesai (tapi biarkan yang sedang live)
    now = datetime.now(timezone(timedelta(hours=7)))
    filtered = []
    for item in data:
        start_dt = datetime.fromisoformat(item["start"])
        end_dt = start_dt + timedelta(hours=MATCH_DURATION_HOURS)
        if end_dt > now:
            filtered.append(item)

    # 🔹 Simpan JSON
    try:
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        print(f"💾 Data berhasil disimpan ({len(filtered)} pertandingan).")
    except Exception as e:
        print("⚠️ Error saving JSON:", e)

if __name__ == "__main__":
    fetch_live_data()
