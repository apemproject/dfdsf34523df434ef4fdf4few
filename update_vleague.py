import requests
import json
import time
from datetime import datetime, timezone, timedelta

# Endpoint Naver API
URL = "https://api-gw.sports.naver.com/schedule/v1/leagues/volleyball"

# File JSON output langsung di root
output_file = "VLeagueKorea.json"

# Zona waktu lokal (misal UTC+8 sesuai jadwal)
LOCAL_TZ = timezone(timedelta(hours=8))

# Interval update (detik)
UPDATE_INTERVAL = 300  # tiap 5 menit

def fetch_matches():
    try:
        r = requests.get(URL, timeout=20)
        r.raise_for_status()
        data = r.json()
        return data.get("matches", [])
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
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
            # src hanya jika live
            src = match.get("streamUrl", "") if status == "live" else ""
            # poster selalu dari Naver API
            poster = match.get("posterUrl", "")

            filtered.append({
                "title": f"{match.get('homeTeamName', '')} vs {match.get('awayTeamName', '')} | {match.get('tournamentName', '')}",
                "start": start_dt.isoformat(),
                "src": src,
                "poster": poster
            })

    return filtered

def save_json(matches):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print(f"✅ Updated {output_file} with {len(matches)} matches at {datetime.now(LOCAL_TZ).strftime('%H:%M:%S')}")

def main():
    print("🌐 Scheduler with Naver poster started ...")
    while True:
        matches = fetch_matches()
        today_matches = filter_today(matches)
        save_json(today_matches)
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()
