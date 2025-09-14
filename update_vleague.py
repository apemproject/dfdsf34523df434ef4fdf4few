import requests
import json
from datetime import datetime

def fetch_data():
    url = "https://api-gw.sports.naver.com/cms/templates/volleyball_schedule_league_tab"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()

    # simpan raw biar bisa dicek strukturnya
    with open("debug_raw.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data

def parse_matches(data):
    matches = []
    try:
        game_list = data["result"]["gameList"]
    except KeyError:
        print("⚠️ Tidak ada gameList di response.")
        return matches

    for item in game_list:
        matches.append({
            "date": item.get("gameDate"),
            "time": item.get("gameTime"),
            "home": item.get("homeTeamName"),
            "away": item.get("awayTeamName"),
            "homeScore": item.get("homeScore"),
            "awayScore": item.get("awayScore"),
            "status": item.get("status")
        })
    return matches

def main():
    raw = fetch_data()
    matches = parse_matches(raw)

    print(f"Parsed matches: {len(matches)}")

    with open("VLeagueKorea.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(matches)} matches to VLeagueKorea.json")
    print("📝 Raw data saved to debug_raw.json")

if __name__ == "__main__":
    main()
