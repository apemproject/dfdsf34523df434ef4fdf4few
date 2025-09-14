import requests
import re
import json
import hashlib
from datetime import datetime, timedelta, timezone
import time

URL = "https://siegheil.micinproject.my.id/naver"
OUTPUT_JSON = "naver_schedule.json"
DEFAULT_POSTER = "assets/default_poster.png"
UPDATE_INTERVAL = 60  # detik

last_html_hash = None

def fetch_schedule():
    try:
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print("❌ Failed to fetch schedule:", e)
        return [], None

    # hash HTML untuk deteksi perubahan
    html_hash = hashlib.md5(html.encode("utf-8")).hexdigest()
    return html, html_hash

def parse_schedule(html):
    matches = []

    # ambil setiap div.game
    game_blocks = re.findall(r'<div[^>]*class=["\']game["\'][^>]*>(.*?)</div>', html, re.DOTALL)

    for block in game_blocks:
        # title
        title_match = re.search(r'<span[^>]*class=["\']title["\'][^>]*>(.*?)</span>', block)
        if not title_match:
            continue
        title = title_match.group(1).strip()

        # tanggal & jam
        date_match = re.search(r'<span[^>]*class=["\']schedule["\'][^>]*>(.*?)</span>', block)
        if not date_match:
            continue
        date_str = date_match.group(1).strip()
        try:
            start = datetime.strptime(date_str, "%d %B %Y | %H:%M WIB")
            start = start.replace(tzinfo=timezone(timedelta(hours=7)))  # WIB +7
        except:
            continue
        start_iso = start.isoformat()

        # src streaming jika ada
        src_match = re.search(r'<a[^>]*class=["\']streaming["\'][^>]*href=["\'](.*?)["\']', block)
        src = src_match.group(1).strip() if src_match else ""

        # status
        now = datetime.now(timezone(timedelta(hours=7)))
        if src:
            status = "LIVE"
        elif start > now:
            status = "UPCOMING"
        else:
            status = "FINISHED"

        if status == "FINISHED":
            continue

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
    global last_html_hash
    while True:
        html, html_hash = fetch_schedule()
        if html is None:
            time.sleep(UPDATE_INTERVAL)
            continue

        if html_hash == last_html_hash:
            # tidak ada perubahan, skip parsing
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No changes, skipping update")
        else:
            matches = parse_schedule(html)
            save_json(matches)
            last_html_hash = html_hash
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Updated {len(matches)} matches")

        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    update_loop()
