import requests, re, json
from datetime import datetime, timezone, timedelta

URL = "https://halu.serv00.net/poli2.php"
OUTPUT = "LiveVoli.json"

def fetch_live_data():
    r = requests.get(URL, timeout=15)
    r.raise_for_status()
    html = r.text

    # 🔹 Ambil seluruh HTML (termasuk Live and upcoming)
    html_section = html

    # 🔹 Regex untuk ambil semua jadwal
    pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+WIB\s+<a href=[\'"]?([^\'"\s>]+)[\'"]?.*?>([^<]+)</a>'
    matches = re.findall(pattern, html_section)

    data = []
    seen_titles = set()  # untuk track duplikat berdasarkan judul

    now = datetime.now(timezone(timedelta(hours=7)))

    for date_str, time_str, src, title in matches:
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
            start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"

            # cek duplikat berdasarkan title saja
            if title.strip() in seen_titles:
                continue  # lewati jika sudah ada
            seen_titles.add(title.strip())

            m = re.search(r'/media/([^/]+)/', src)
            poster = f"https://cdn.jwplayer.com/v2/media/{m.group(1)}/poster.jpg?width=1920" if m else ""

            # 🔹 Simpan semua jadwal, termasuk yang sedang live
            data.append({
                "title": title.strip(),
                "start": start_iso,
                "src": src.strip(),
                "poster": poster
            })
        except Exception as e:
            print("⚠️ Error parsing:", date_str, time_str, title, e)

    # 🔹 Hanya hapus jadwal yang sudah lewat lebih dari 1 jam, biar live masih muncul
    filtered_data = []
    for item in data:
        start_dt = datetime.fromisoformat(item["start"])
        if start_dt + timedelta(hours=1) > now:
            filtered_data.append(item)

    # Simpan JSON
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)

    print(f"💾 Data berhasil disimpan ({len(filtered_data)} pertandingan).")

if __name__ == "__main__":
    fetch_live_data()
