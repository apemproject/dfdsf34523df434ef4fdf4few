import requests
import json
from datetime import datetime, timedelta, timezone
import time

OUTPUT_JSON = "today.json"
DEBUG_RAW = "debug_raw_today.json"
DEFAULT_POSTER = "assets/default_poster.png"

TEAM_MAP = {}  # otomatis diisi dari API

def fetch_schedule(date: str):
    url = (
        "https://api-gw.sports.naver.com/schedule/calendar"
        f"?superCategoryId=volleyball"
        f"&categoryIds=%2Ckovo%2Cwkovo%2Cuvolleyball%2Cvolleyballetc"
        f"&date={date}"
    )
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
    r.raise_for_status()
    return r.json()

def fetch_live_url(game_id: str):
    url = f"https://api-gw.sports.naver.com/game/{game_id}/live"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
        r.raise_for_status()
        return r.json().get("liveStreamUrl", "")
    except:
        return ""

def build_team_mapping(raw):
    global TEAM_MAP
    for day in raw.get("result", {}).get("dates", []):
        games = day.get("gameInfos")
        if not isinstance(games, list):
            continue
        for game in games:
            for code in [game.get("homeTeamCode"), game.get("awayTeamCode")]:
                if code and code not in TEAM_MAP:
                    TEAM_MAP[code] = code  # nama tim = kode sementara

def parse_schedule(raw, date: str):
    matches = []
    korea_tz = timezone(timedelta(hours=9))
    now = datetime.now(korea_tz)

    for day in raw.get("result", {}).get("dates", []):
        if day.get("ymd") != date:
            continue
        games = day.get("gameInfos")
        if not isinstance(games, list):
            continue
        for game in games:
            home_code = game.get("homeTeamCode")
            away_code = game.get("awayTeamCode")
            home = TEAM_MAP.get(home_code, home_code or "Unknown")
            away = TEAM_MAP.get(away_code, away_code or "Unknown")

            title = f"{home} vs {away}"
            start_time = game.get("startTime") or f"{date}T18:00:00+09:00"
            start_dt = datetime.fromisoformat(start_time)

            status = "UPCOMING"
            src = ""
            if start_dt <= now and game.get("gameId"):
                src = fetch_live_url(str(game["gameId"]))
                if src:
                    status = "LIVE"
                else:
                    status = "FINISHED"

            # skip pertandingan yang sudah selesai
            if status == "FINISHED":
                continue

            matches.append({
                "title": title,
                "start": start_time,
                "status": status,
                "src": src,
                "poster": DEFAULT_POSTER
            })

    # Hapus duplikat
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

def update_loop():
    korea_tz = timezone(timedelta(hours=9))
    while True:
        today = datetime.now(korea_tz).strftime("%Y-%m-%d")
        try:
            raw = fetch_schedule(today)
            save_json(DEBUG_RAW, raw)
            build_team_mapping(raw)
            matches = parse_schedule(raw, today)
            save_json(OUTPUT_JSON, matches)
            print(f"[{datetime.now(korea_tz).strftime('%H:%M:%S')}] Updated {len(matches)} matches for {today}")
        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(60)

if __name__ == "__main__":
    update_loop()
