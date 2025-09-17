import requests, re, json
from datetime import datetime, timezone, timedelta

URL = "https://halu.serv00.net/poli2.php"
OUTPUT = "volleyballworld.json"

def fetch_live_data():
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print("⚠️ Error fetching HTML:", e)
        return

    pattern = r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+WIB\s+<a href=[\'"]?([^\'"\s>]+)[\'"]?.*?>([^<]+)</a>'
    matches = re.findall(pattern, html)

    data = []
    seen = set() 

    for date_str, time_str, src, title in matches:
        title = title.strip()
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
            dt = dt.replace(tzinfo=timezone(timedelta(hours=7)))

            dt = dt + timedelta(minutes=10)

            start_iso = dt.isoformat()

            key = (title, start_iso, src.strip())
            if key in seen:
                continue
            seen.add(key)

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

    print(f"📊 Total match diambil dari sumber: {len(data)}")

    try:
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Data berhasil disimpan ke {OUTPUT} ({len(data)} pertandingan).")
    except Exception as e:
        print("⚠️ Error saving JSON:", e)

if __name__ == "__main__":
    fetch_live_data()
