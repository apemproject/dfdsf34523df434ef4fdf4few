import requests
import json
from datetime import datetime, timedelta, timezone
import os

OUTPUT_JSON = "VLeagueKorea.json"
DEBUG_RAW = "debug_raw.json"

# Mapping kode tim ke nama resmi (contoh, bisa ditambahin)
TEAM_MAP = {
    "CS": "Korean Air Jumbos",
    "HN": "Hyundai Capital Skywalkers",
    "MP": "Samsung Bluefangs",
    "HY": "Woori Card",
    # tambahin mapping lain sesuai kebutuhan
}

def fetch_schedule(date: str):
    url = (
        "https://api-gw.sports.naver.com/schedule/calendar"
        f"?superCategoryId=volleyball"
        f"&categoryIds=%2Ckovo%2Cwkovo%2Cuvolleyball%2Cvolleyballetc"
        f"&date={date}"
    )
    print(f"📡 Fetching {url}")
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.json()

def parse_schedule(raw, date: str):
    matches = []
    for day in raw["result"]["dates"]:
        if day["ymd"] != date:
            continue
        if not day.get("gameInfos"):
            continue

        for game in day["gameInfos"]:
            home = TEAM_MAP.get(game["homeTeamCode"], game["homeTeamCode"])
            away = TEAM_MAP.get(game["awayTeamCode"], game["awayTeamCode"])

            title = f"{home} vs {away}"

            # default jam 18:00 KST kalau ga ada di API
            start_time = f"{date}T18:00:00+09:00"

            match = {
                "title": title,
                "start": start_time,
                "src": "",      # nanti bisa diisi dari endpoint detail game
                "poster": ""    # nanti bisa diisi poster tim atau liga
            }
            matches.append(match)

    return matches

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    today = datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=9))
    ).strftime("%Y-%m-%d")  # Korea Time

    raw = fetch_schedule(today)
    save_json(DEBUG_RAW, raw)  # simpan raw data

    matches = parse_schedule(raw, today)
    save_json(OUTPUT_JSON, matches)

    print(f"Parsed matches: {len(matches)}")
    print(f"✅ Saved {len(matches)} matches to {OUTPUT_JSON}")
    print(f"📝 Raw data saved to {DEBUG_RAW}")

if __name__ == "__main__":
    main()
