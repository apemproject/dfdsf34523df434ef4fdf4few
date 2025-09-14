import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone, timedelta
import time

URL = "https://siegheil.micinproject.my.id/naver"
OUTPUT_JSON = "naver_schedule.json"
DEFAULT_POSTER = "assets/default_poster.png"
UPDATE_INTERVAL = 60  # detik

def fetch_schedule():
    try:
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        r.raise_for_status()
    except Exception as e:
        print("❌ Failed to fetch schedule:", e)
        return []

    soup = BeautifulSoup(r.content, "html.parser")
    matches = []

    # Sesuaikan selector dengan struktur HTML web asli
    for item in soup.select("div.game"):
        # ambil judul
        title_tag = item.select_one("span.title")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        # ambil tanggal dan jam
        date_tag = item.select_one("span.schedule")
        if not date_tag:
            continue
        date_str = date_tag.get_text(strip=True)
        try:
            # contoh format: "14 September 2025 | 18:00 WIB"
            start = datetime.strptime(date_str, "%d %B %Y | %H:%M WIB")
            # gunakan timezone +7 WIB
            start = start.replace(tzinfo=timezone(timedelta(hours=7)))
        except:
            continue
        start_iso = start.isoformat()

        # ambil src streaming jika ada
        a_tag = item.select_one("a.streaming")
        src = a_tag["href"] if a_tag else ""

        # tentukan status
        now = datetime.now(timezone(timedelta(hours=7)))
        if src:
            status = "LIVE"
        elif start > now:
            status = "UPCOMING"
        else:
            status = "FINISHED"

        if status == "FINISHED":
            continue  # skip pertandingan yang sudah selesai

        matches.append({
            "title": title,
            "start": start_iso,
            "status": status,
            "src": src,
            "poster": DEFAULT_POSTER
        })

    # hapus duplikat
    seen = set()
    unique_matches = []
    for m in matches:
        key = (m["title"], m["start"])
        if key not in seen:
            unique_matches.append(m)
            seen.add(key)

    return unique_matches

def save_json(data):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_loop():
    while True:
        matches = fetch_schedule()
        save_json(matches)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Updated {len(matches)} matches")
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    update_loop()
