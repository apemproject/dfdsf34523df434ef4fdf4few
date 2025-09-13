import requests
import json
import re
import time
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

URL = "https://sports.news.naver.com/volleyball/schedule/index.nhn"
output_file = "VLeagueKorea.json"
LOCAL_TZ = timezone(timedelta(hours=8))
MAX_RETRIES = 3
RETRY_DELAY = 5  # detik

def fetch_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(URL, headers=headers, timeout=10)
            r.raise_for_status()
            return r.text
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                print(f"Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print("❌ Failed to fetch HTML after retries.")
                return None

def parse_schedule(html):
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script")
    data_json = None
    
    # Cari JSON jadwal di <script>
    for script in scripts:
        if "window.__INITIAL_STATE__" in script.text:
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*\});', script.text)
            if match:
                try:
                    data_json = json.loads(match.group(1))
                    print("✅ Found initial state JSON")
                except json.JSONDecodeError:
                    print("❌ Failed to parse JSON")
                break
    
    if not data_json:
        print("❌ Data schedule tidak ditemukan di halaman. Struktur Naver mungkin berubah.")
        return []

    # Fallback path: coba beberapa kemungkinan key
    matches = []
    for key in ["schedule", "matchList", "matches"]:
        matches = data_json.get(key, [])
        if matches:
            print(f"✅ Using key '{key}' for matches")
            break
    if not matches:
        print("⚠️ Tidak ada match ditemukan. Perlu cek struktur terbaru Naver.")
    return matches

def filter_today(matches):
    today = datetime.now(LOCAL_TZ).date()
    filtered = []

    for i, match in enumerate(matches, 1):
        start_time_str = match.get("startDate") or match.get("start_time")
        if not start_time_str:
            continue
        try:
            start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
        except Exception:
            continue

        if start_dt.date() == today:
            filtered.append({
                "title": f"{match.get('homeTeamName', match.get('home_team', ''))} vs "
                         f"{match.get('awayTeamName', match.get('away_team', ''))} | "
                         f"{match.get('tournamentName', match.get('tournament', ''))}",
                "start": start_dt.isoformat(),
                "src": match.get("streamUrl", ""),
                "poster": match.get("posterUrl", "")
            })
    print(f"📊 Total matches today: {len(filtered)}")
    return filtered

def save_json(matches):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {output_file} with {len(matches)} matches")

def main():
    html = fetch_html()
    matches = parse_schedule(html)
    today_matches = filter_today(matches)
    save_json(today_matches)

if __name__ == "__main__":
    main()
