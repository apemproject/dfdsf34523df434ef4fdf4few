import requests
import re
import json
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

# =================== CONFIG ===================
MAIN_URL = "https://agratv.vercel.app/jadwal.php"
BASE_URL = "https://agratv.vercel.app/"
OUTPUT_FILE = "VLeagueKorea.json"
INTERVAL = 120  # cek tiap 2 menit
LOCAL_TZ = timezone(timedelta(hours=7))  # WIB
CHECK_WINDOW = timedelta(minutes=30)     # hanya cek src ±30 menit dari sekarang
MAX_THREADS = 5                           # parallel fetch max 5
# ==============================================

def fetch_html(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text

def parse_main(html):
    main_div = re.search(r'<div class="main">(.*?)</div>', html, re.S)
    if not main_div:
        return []

    div_content = main_div.group(1)
    links = re.findall(r"<a\s+href=['\"](.*?)['\"].*?>(.*?)</a>", div_content, re.S)
    matches = []

    for href, text in links:
        text = text.strip()
        parts = text.split(" - ")
        if len(parts) >= 3:
            title = parts[0].replace("[UP]", "").strip() + " | " + parts[1].strip()
            time_str = parts[-1].replace("WIB", "").strip()
            today = datetime.now(LOCAL_TZ).date()
            try:
                start_dt = datetime.strptime(time_str, "%H:%M").replace(
                    year=today.year, month=today.month, day=today.day, tzinfo=LOCAL_TZ
                )
                start_iso = start_dt.isoformat()
            except:
                start_iso = ""
            matches.append({
                "id": href,
                "title": title,
                "start": start_iso,
                "href": href,
                "src": "",
                "poster": ""
            })
    return matches

def fetch_hls_src(match):
    """Cek src HLS atau iframe hanya jika pertandingan ±CHECK_WINDOW atau src kosong"""
    try:
        start_dt = datetime.fromisoformat(match["start"])
        now = datetime.now(LOCAL_TZ)
        if abs(start_dt - now) <= CHECK_WINDOW or match.get("src") == "":
            url = BASE_URL + match["href"]
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            html = r.text

            m3u8 = re.search(r"(https?://.*?\.m3u8)", html)
            if m3u8:
                match["src"] = m3u8.group(1)
            else:
                iframe = re.search(r"<iframe.*?src=['\"](.*?)['\"]", html)
                match["src"] = iframe.group(1) if iframe else ""
    except:
        pass
    return match

def load_json():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_json(matches):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

def merge_matches(old_matches, new_matches):
    updated = {m["id"]: m for m in old_matches}

    # Fetch src secara paralel
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        results = list(executor.map(fetch_hls_src, new_matches))

    for m in results:
        updated[m["id"]] = m

    return list(updated.values())

def main_loop():
    while True:
        try:
            html = fetch_html(MAIN_URL)
            new_matches = parse_main(html)
            old_matches = load_json()
            merged = merge_matches(old_matches, new_matches)
            save_json(merged)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Updated {len(merged)} matches")
        except Exception as e:
            print("❌ Error:", e)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main_loop()
