import requests
import re
import json
import time
from datetime import datetime, timedelta, timezone

# =================== CONFIG ===================
MAIN_URL = "https://agratv.vercel.app/jadwal.php"  # Halaman jadwal pertandingan
BASE_URL = "https://agratv.vercel.app/"            # Base URL untuk membentuk link lengkap
OUTPUT_FILE = "VLeagueKorea.json"
INTERVAL = 120  # Cek tiap 2 menit
LOCAL_TZ = timezone(timedelta(hours=7))  # WIB
CHECK_WINDOW = timedelta(minutes=60)      # ±60 menit untuk cek src HLS
# ==============================================

def fetch_html(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text

def parse_main(html):
    """Parse semua <a href='?id=...'> di div.main"""
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
    """Cek halaman target untuk HLS .m3u8 atau iframe src"""
    try:
        start_dt = datetime.fromisoformat(match["start"])
        now = datetime.now(LOCAL_TZ)
        if abs(start_dt - now) <= CHECK_WINDOW or match.get("src") == "":
            url = BASE_URL + match["href"]
            r = requests.get(url)
            r.raise_for_status()
            html = r.text

            # Cek HLS .m3u8
            m3u8 = re.search(r"(https?://.*?\.m3u8)", html)
            if m3u8:
                match["src"] = m3u8.group(1)
            else:
                # fallback ke iframe src
                iframe = re.search(r"<iframe.*?src=['\"](.*?)['\"]", html)
                match["src"] = iframe.group(1) if iframe else ""
    except:
        match["src"] = ""

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
    for m in new_matches:
        fetch_hls_src(m)  # realtime update src jika perlu
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
