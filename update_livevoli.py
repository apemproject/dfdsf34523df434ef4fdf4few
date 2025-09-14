import requests, re, json
from datetime import datetime, timezone, timedelta

URL = "https://halu.serv00.net/poli2.php"
OUTPUT = "LiveVoli.json"

def fetch_live_data():
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print("⚠️ Gagal mengambil data:", e)
        return

    # 🔹 Regex fleksibel untuk tangkap semua jadwal, termasuk yang sedang live
    # Format: tanggal opsional, waktu wajib, WIB, link, judul
    pattern = r'(\d{2}-\d{2}-\d{4})?\s*(\d{2}:\d{2})\s*WIB\s*<a href=[\'"]?([^\'"\s>]+)[\'"]?.*?>([^<]+)</a>'
    matches = re.findall(pattern, html)

    data = []
    seen = set()  # track jadwal unik

    for date_str, time_str, src, title in matches:
        try:
            # jika tanggal kosong, gunakan tanggal hari ini
            if not date_str:
                dt = datetime.now(timezone(timedelta(hours=7)))
                dt = dt.replace(hour=int(time_str[:2]), minute=int(time_str[3:5]))
            else:
                dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
                dt = dt.replace(tzinfo=timezone(timedelta(hours=7)))

            start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S%z")

            # hanya tampilkan satu entri untuk duplikat
            key = (title.strip(), start_iso, src.strip())
            if key in seen:
                continue
            seen.add(key)

            # ambil poster JWPlayer jika ada
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

    # Hapus jadwal yang sudah lewat
    now = datetime.now(timezone(timedelta(hours=7)))
    data = [item for item in data if datetime.fromisoformat(item["start"]) > now]

    # Simpan JSON
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Data berhasil disimpan ({len(data)} pertandingan).")

if __name__ == "__main__":
    fetch_live_data()
