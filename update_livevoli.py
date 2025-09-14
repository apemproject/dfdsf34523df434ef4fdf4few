import requests, re, json, time
from datetime import datetime, timezone, timedelta

URL = "https://halu.serv00.net/poli2.php"
OUTPUT = "LiveVoli.json"
UPDATE_INTERVAL = 60  # detik, 60 detik = 1 menit

def fetch_live_data():
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        html = r.text

        # 🔹 Buang "Watch Live - Schedule Screen"
        sections = re.split(r'Watch Live - Schedule Screen', html, flags=re.IGNORECASE)
        html_section = sections[1] if len(sections) > 1 else html

        # 🔹 Ambil jadwal <a href=...>
        pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+WIB\s+<a href=[\'"]?([^\'"\s>]+)[\'"]?.*?>([^<]+)</a>'
        matches = re.findall(pattern, html_section)

        data = []
        seen_titles = set()

        for date_str, time_str, src, title in matches:
            title_clean = title.strip()
            if title_clean in seen_titles:
                continue
            seen_titles.add(title_clean)

            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
                start_iso = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"

                m = re.search(r'/media/([^/]+)/', src)
                poster = f"https://cdn.jwplayer.com/v2/media/{m.group(1)}/poster.jpg?width=1920" if m else ""

                data.append({
                    "title": title_clean,
                    "start": start_iso,
                    "src": src.strip(),
                    "poster": poster
                })
            except Exception as e:
                print("⚠️ Error parsing:", date_str, time_str, title, e)

        now = datetime.now(timezone(timedelta(hours=7)))
        data = [item for item in data if datetime.fromisoformat(item["start"]) > now]

        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 Data berhasil diperbarui ({len(data)} pertandingan).")
    except Exception as e:
        print("⚠️ Error fetch/update:", e)

if __name__ == "__main__":
    while True:
        fetch_live_data()
        time.sleep(UPDATE_INTERVAL)
