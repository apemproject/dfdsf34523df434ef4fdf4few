import requests
import json
from datetime import datetime, timedelta, timezone

API_URL = "https://api-gw.sports.naver.com/cms/templates/volleyball_new_home_feed"
OUTPUT_FILE = "VLeagueKorea.json"

HEADERS = {
    "Referer": "https://m.sports.naver.com/volleyball/index",
    "User-Agent": "Mozilla/5.0"
}

def fetch_data():
    r = requests.get(API_URL, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def extract_matches(raw):
    """coba cari list pertandingan di berbagai struktur API"""
    candidates = []

    # 1. feedData -> matchSchedule -> scheduleList
    for item in raw.get("feedData", []):
        if "matchSchedule" in item:
            candidates.extend(item["matchSchedule"].get("scheduleList", []))

    # 2. feedData -> matchList
    for item in raw.get("feedData", []):
        if "matchList" in item:
            candidates.extend(item["matchList"])

    # 3. result -> matchSchedule
    if "result" in raw and "matchSchedule" in raw["result"]:
        candidates.extend(raw["result"]["matchSchedule"].get("scheduleList", []))

    # 4. result -> games
    if "result" in raw and "games" in raw["result"]:
        candidates.extend(raw["result"]["games"])

    return candidates

def parse_schedule(raw):
    matches = []
    for match in extract_matches(raw):
        try:
            home = match.get("homeTeamName") or match.get("homeName") or ""
            away = match.get("awayTeamName") or match.get("awayName") or ""
            start_time = match.get("startTime") or match.get("gameDate")

            if not start_time or not home or not away:
                continue

            # konversi waktu ke +08:00
            dt = datetime.fromisoformat(start_time)
            dt_utc8 = dt.astimezone(timezone(timedelta(hours=8)))

            # link detail pertandingan
            match_id = match.get("gameId") or match.get("id")
            detail_link = f"https://m.sports.naver.com/game/{match_id}" if match_id else ""

            # poster (pakai logo tim kalau ada)
            home_logo = match.get("homeTeamEmblem") or match.get("homeLogo") or ""
            away_logo = match.get("awayTeamEmblem") or match.get("awayLogo") or ""
            poster = home_logo if home_logo else away_logo

            matches.append({
                "title": f"{home} vs {away}",
                "start": dt_utc8.isoformat(),
                "src": detail_link,
                "poster": poster
            })
        except Exception as e:
            print("Skip match:", e)
    return matches

def clean_expired(data):
    """hapus jadwal yang sudah lewat"""
    now = datetime.now(timezone(timedelta(hours=8)))
    return [m for m in data if datetime.fromisoformat(m["start"]) > now]

def main():
    raw = fetch_data()
    matches = parse_schedule(raw)
    matches = clean_expired(matches)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(matches)} matches to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
