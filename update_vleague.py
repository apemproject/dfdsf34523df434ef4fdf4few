import requests
import json
from datetime import datetime, timedelta, timezone
import time

OUTPUT_JSON = "VLeagueKorea.json"
DEBUG_RAW_DIR = "debug_raw"

# Mapping kode tim terbaru
TEAM_MAP = {
    "1001": "Hyundai Capital Skywalkers",
    "1002": "Korean Air Jumbos",
    "1004": "Suntory Sunbirds",
    "1009": "Woori Card",
    # Tambahkan semua kode tim lain sesuai API
}

TEAM_POSTER = {
    "1001": "https://example.com/logo_hcsky.png",
    "1002": "https://example.com/logo_kajumbos.png",
    "1004": "https://example.com/logo_suntory.png",
    "1009": "https://example.com/logo_wooricard.png",
}

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
    """
    Ambil live URL dari API detail game jika tersedia.
    """
    url = f"https://api-gw.sports.naver.com/game/{game_id}/live"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("liveStreamUrl", "")
    except:
        return ""

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

            # Tentukan status pertandingan
            status = "UPCOMING"
            src = ""
            if start_dt <= now:
                if game.get("gameId"):
                    src = fetch_live_url(str(game["gameId"]))
                    if src:
                        status = "LIVE"
                    else:
                        status = "FINISHED"

            poster = TEAM_POSTER.get(home_code, "")

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

        for date in dates:
            try:
                raw = fetch_schedule(date)
                save_json(f"{DEBUG_RAW_DIR}_{date}.json", raw)
                matches = parse_schedule(raw, date)
                all_matches.extend(matches)
            except Exception as e:
                print(f"❌ Error fetching/parsing {date}: {e}")

        save_json(OUTPUT_JSON, all_matches)
        print(f"[{datetime.now(korea_tz).strftime('%Y-%m-%d %H:%M:%S')}] Updated {len(all_matches)} matches")
        time.sleep(60)

if __name__ == "__main__":
    update_loop()
