import requests
import json
from datetime import datetime, timezone, timedelta

URL = "https://api-gw.sports.naver.com/schedule/v1/leagues/volleyball"
output_file = "VLeagueKorea.json"
LOCAL_TZ = timezone(timedelta(hours=8))

def fetch_and_save():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    data = r.json().get("matches", [])

    today = datetime.now(LOCAL_TZ).date()
    filtered = []

    for match in data:
        start_time_str = match.get("startDate")
        if not start_time_str:
            continue
        start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
        if start_dt.date() == today:
            status = match.get("status", "").lower()
            filtered.append({
                "title": f"{match.get('homeTeamName', '')} vs {match.get('awayTeamName', '')} | {match.get('tournamentName', '')}",
                "start": start_dt.isoformat(),
                "src": match.get("streamUrl", "") if status=="live" else "",
                "poster": match.get("posterUrl", "")
            })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {output_file} with {len(filtered)} matches today")

if __name__ == "__main__":
    fetch_and_save()
