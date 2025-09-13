import requests
import json
from datetime import datetime, timezone, timedelta

URL = "https://api-gw.sports.naver.com/schedule/v1/leagues/volleyball"
output_file = "VLeagueKorea.json"
LOCAL_TZ = timezone(timedelta(hours=8))  # UTC+8

def fetch_matches():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    }
    try:
        r = requests.get(URL, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("matches", [])
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        return []

def filter_today(matches):
    today = datetime.now(LOCAL_TZ).date()
    filtered = []

    print(f"📅 Today (UTC+8): {today}")
    for i, match in enumerate(matches, 1):
        start_time_str = match.get("startDate")
        if not start_time_str:
            print(f"⚠️ Match {i}: No startDate")
            continue
        try:
            start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
            print(f"🔹 Match {i}: {match.get('homeTeamName', '?')} vs {match.get('awayTeamName', '?')}")
            print(f"   Raw startDate: {start_time_str}, Converted: {start_dt}")
        except Exception as e:
            print(f"❌ Match {i}: Failed to parse startDate: {e}")
            continue

        if start_dt.date() == today:
            status = match.get("status", "").lower()
            filtered.append({
                "title": f"{match.get('homeTeamName', '')} vs {match.get('awayTeamName', '')} | {match.get('tournamentName', '')}",
                "start": start_dt.isoformat(),
                "src": match.get("streamUrl", "") if status=="live" else "",
                "poster": match.get("posterUrl", "")
            })
            print(f"✅ Added to today's schedule")
        else:
            print(f"ℹ️ Skipped, not today")

    print(f"📊 Total matches for today: {len(filtered)}")
    return filtered

def save_json(matches):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {output_file} with {len(matches)} matches")

def main():
    matches = fetch_matches()
    if not matches:
        print("❌ No matches fetched")
        return
    today_matches = filter_today(matches)
    save_json(today_matches)

if __name__ == "__main__":
    main()
