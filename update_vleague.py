import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta, timezone

MAIN_URL = "https://example.com/jadwal.php"
BASE_URL = "https://example.com/"
OUTPUT_FILE = "VLeagueKorea.json"
INTERVAL = 300  # 5 menit
LOCAL_TZ = timezone(timedelta(hours=7))  # WIB

def fetch_html(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text

def parse_main(html):
    soup = BeautifulSoup(html, "html.parser")
    main_div = soup.find("div", class_="main")
    links = main_div.find_all("a")
    matches = []

    for a in links:
        href = a.get("href")
        text = a.get_text(strip=True)
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

def update_src(match):
    try:
        url = BASE_URL + match["href"]
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        iframe = soup.find("iframe")
        if iframe:
            match["src"] = iframe.get("src", "")
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
        if m["id"] not in updated or updated[m["id"]].get("src") != m.get("src"):
            update_src(m)
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
