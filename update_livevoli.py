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

    # 🔹 Ambil semua link .m3u8
    pattern = r'<a href=[\'"]?([^\'"\s>]+\.m3u8)[\'"]?.*?>([^<]+)</a>'
    matches = re.findall(pattern, html)

    data = []
    seen = set()

    for src, title in matches:
        try:
            # cari tanggal dan waktu di sebelah link (format: DD-MM-YYYY HH:MM WIB)
            dt_match = re.search(r'(\d{2}-\d{2}-\d{4})?\s*(\d{2}:\d{2})\s*WIB', html[:html.find(src)])
            if dt_match:
                date_str, time_str = dt_match.groups()
                if not date_str:
                    dt = datetime.now(timezone(timedelta(hours=7)))
                    dt = dt.replace(hour=int(time_str[:2]), minute=int(time_str[3:5]))
                else:
                    dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
                    dt = dt.replace(tzinfo=timezone(timedelta(hours=7)))
            else:
                # jika tidak ditemukan, pakai waktu sekarang
                dt = datetime.now(timezone(timedelta(hours=7)))

            start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S%z")

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
            print("⚠️ Error parsing:", title, e)

    # hapus jadwal yang sudah lewat
    now = datetime.now(timezone(timedelta(hours=7)))
    data = [item for item in data if datetime.fromisoformat(item["start"]) > now]

    # simpan JSON
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Data berhasil disimpan ({len(data)} pertandingan).")

if __name__ == "__main__":
    fetch_live_data()
