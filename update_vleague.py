import requests
import json
from datetime import datetime, timedelta, timezone

OUTPUT_JSON = "VLeagueKorea.json"
DEBUG_RAW = "debug_raw.json"

def fetch_schedule(date: str):
    url = (
        "https://api-gw.sports.naver.com/schedule/calendar"
        f"?superCategoryId=volleyball"
        f"&categoryIds=%2Ckovo%2Cwkovo%2Cuvolleyball%2Cvolleyballetc"
        f"&date={date}"
    )
    print(f"📡 Fetching {url}")
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    return r.json()

def parse_schedule(raw, date: str):
    matches = []
    
    for day in raw.get("result", {}).get("dates", []):
        if day.get("ymd") != date:
            continue
        for game in day.get("gameInfos", []):
            # Ambil nama tim langsung dari API, fallback ke kode tim kalau kosong
            home = game.get("homeTeamName") or game.get("homeTeamCode") or "Unknown"
            away = game.get("awayTeamName") or game.get("awayTeamCode") or "Unknown"
            
            title = f"{home} vs {away}"

            # Ambil waktu mulai dari API kalau ada, default jam 18:00 KST
            start_time = game.get("startTime") or f"{date}T18:00:00+09:00"

            match = {
                "title": title,
                "start": start_time,
                "src": "",      # bisa diisi nanti
                "poster": ""    # bisa diisi nanti
            }
            matches.append(match)
    
    # Hapus duplikat berdasarkan title + start
    seen = set()
    unique_matches = []
    for m in matches:
        key = (m['title'], m['start'])
        if key not in seen:
            unique_matches.append(m)
            seen.add(key)
    return unique_matches

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    today = datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=9))
    ).strftime("%Y-%m-%d")  # Korea Time

    raw = fetch_schedule(today)
    save_json(DEBUG_RAW, raw)

    matches = parse_schedule(raw, today)
    save_json(OUTPUT_JSON, matches)

    print(f"Parsed matches: {len(matches)}")
    print(f"✅ Saved {len(matches)} matches to {OUTPUT_JSON}")
    print(f"📝 Raw data saved to {DEBUG_RAW}")

if __name__ == "__main__":
    main()
