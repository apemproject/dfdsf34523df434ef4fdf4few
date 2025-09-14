import requests
import json
from datetime import datetime, timedelta, timezone
import time

OUTPUT_JSON = "VLeagueKorea.json"
DEBUG_RAW_DIR = "debug_raw"
DEFAULT_POSTER = "assets/default_poster.png"

# Mapping awal (akan diisi otomatis dari API)
TEAM_MAP = {}

def fetch_schedule(date: str):
    url = (
        "https://api-gw.sports.naver.com/schedule/calendar"
        f"?superCategoryId=volleyball"
        f"&categoryIds=%2Ckovo%2Cwkovo%2Cuvolleyball%2Cvolleyballetc"
        f"&date={date}"
    )
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_live_url(game_id: str):
    url = f"https://api-gw.sports.naver.com/game/{game_id}/live"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("liveStreamUrl", "")
    except:
        return ""

def build_team_mapping(raw_list):
    """
    Ambil semua kode tim dari raw JSON dan buat mapping otomatis
    Jika belum ada di TEAM_MAP, nama tim disamakan dengan kode
    """
    global TEAM_MAP
    for raw in raw_list:
        for day in raw.get("result", {}).get("dates", []):
            for game in day.get("gameInfos", []):
                for code in [game.get("homeTeamCode"), game.get("awayTeamCode")]:
                    if code and code not in TEAM_MAP:
                        TEAM_MAP[code] = code  # sementara nama = kode

def parse_schedule(raw, date: str):
    matches = []
    korea_tz = timezone(timedelta(hours=9))
    now = datetime.now(korea_tz)

    for day in raw.get("result", {}).get("dates", []):
        if day.get("ymd") != date:
            continue
        for game in day.get("gameInfos", []):
            home_code = game.get("homeTeamCode")
            away_code = game.get("awayTeamCode")
            home = TEAM_MAP.get(home_code, home_code or "Unknown")
            away = TEAM_MAP.get(away_code, away_code or "Unknown")

            title = f"{home} vs {away}"
            start_time = game.get("startTime") or f"{date}T18:00:00+09:00"
            start_dt = datetime.fromisoformat(start_time)

            # Tentukan status dan src
            status = "UPCOMING"
            src = ""
            if start_dt <= now and game.get("gameId"):
                src = fetch_live_url(str(game["gameId"]))
                if src:
                    status = "LIVE"
                else:
                    status = "FINISHED"

            # Poster default dari assets
            poster = DEFAULT_POSTER

            matches.append({
                "title": title,
                "start": start_time,
                "status": status,
                "src": src,
                "poster": poster
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
        dates = [
            (datetime.now(korea_tz) + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(2)
        ]
        all_matches = []
        raw_list = []

        # Fetch semua jadwal
        for date in dates:
            try:
                raw = fetch_schedule(date)
                save_json(f"{DEBUG_RAW_DIR}_{date}.json", raw)
                raw_list.append(raw)
            except Exception as e:
                print(f"❌ Error fetching {date}: {e}")

        # Build mapping otomatis dari semua kode tim
        build_team_mapping(raw_list)

        # Parse schedule
        for i, raw in enumerate(raw_list):
            date = dates[i]
            matches = parse_schedule(raw, date)
            all_matches.extend(matches)

        save_json(OUTPUT_JSON, all_matches)
        print(f"[{datetime.now(korea_tz).strftime('%Y-%m-%d %H:%M:%S')}] Updated {len(all_matches)} matches")
        time.sleep(60)

if __name__ == "__main__":
    update_loop()
