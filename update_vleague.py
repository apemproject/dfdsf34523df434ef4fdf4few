import requests
import json
import time
from datetime import datetime, timezone, timedelta

URL = "https://api-gw.sports.naver.com/schedule/v1/leagues/volleyball"
output_file = "VLeagueKorea.json"
LOCAL_TZ = timezone(timedelta(hours=8))
MAX_RETRIES = 5
RETRY_DELAY = 5  # detik, delay antar percobaan

def fetch_matches():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(URL, headers=headers, timeout=10)
            r.raise_for_status()
            return r.json().get("matches", [])
        except requests.exceptions.HTTPError as e:
            if r.status_code == 403:
                print(f"⚠️ Attempt {attempt}: 403 Forbidden. Retrying in {RETRY_DELAY}s...")
            else:
                print(f"❌ HTTP Error: {e}")
                break
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt}: Request failed: {e}. Retrying in {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)
    return []

def filter_today(matches):
    today = datetime.now(LOCAL_TZ).date()
    filtered = []

    for match in matches:
        start_time_str = match.get("startDate")
        if not start_time_str:
            continue
        try:
            start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
        except ValueError:
            continue

        if start_dt.date() == today:
            status = match.get("status", "").lower()
            filtered.append({
                "title": f"{match.get('homeTeamName', '')} vs {match.get('awayTeamName', '')} | {match.get('tournamentName', '')}",
                "start": start_dt.isoformat(),
                "src": match.get("streamUrl", "") if status=="live" else "",
                "poster": match.get("posterUrl", "")
            })

    return filtered

def save_json(matches):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {output_file} with {len(matches)} matches at {datetime.now(LOCAL_TZ).strftime('%H:%M:%S')}")

def main():
    matches = fetch_matches()
    if not matches:
        print("❌ Failed to fetch matches after retries.")
        return
    today_matches = filter_today(matches)
    save_json(today_matches)

if __name__ == "__main__":
    main()
