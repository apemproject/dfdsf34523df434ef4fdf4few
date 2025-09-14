import requests
import json
from datetime import datetime, timedelta, timezone

API_BASE = "https://api-gw.sports.naver.com"
TAB_URL = f"{API_BASE}/cms/templates/volleyball_schedule_league_tab"
OUTPUT_FILE = "VLeagueKorea.json"
DEBUG_FILE = "debug_raw.json"

KST = timezone(timedelta(hours=9))

def fetch_leagues():
    """Ambil daftar liga (kovo, wkovo, dll)"""
    r = requests.get(TAB_URL, timeout=10)
    r.raise_for_status()
    data = r.json()
    leagues = []
    try:
        leagues = data["result"]["templates"][0]["json"]["dataList"]
    except Exception as e:
        print("❌ Gagal ambil data liga:", e)
    return leagues

def fetch_schedule(categoryId, date_str):
    """Ambil jadwal dari 1 kategori dan tanggal tertentu"""
    url = f"{API_BASE}/schedule/games/{categoryId}?date={date_str}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def parse_matches(raw, categoryId):
    """Parse data jadwal jadi list dict sederhana"""
    matches = []
    try:
        games = raw.get("result", {}).get("games", [])
        for g in games:
            matches.append({
                "category": categoryId,
                "date": g.get("gameDate"),
                "time": g.get("gameTime"),
                "home": g.get("homeTeamName"),
                "away": g.get("awayTeamName"),
                "homeScore": g.get("homeTeamScore"),
                "awayScore": g.get("awayTeamScore"),
                "status": g.get("statusName")
            })
    except Exception as e:
        print(f"⚠️ Gagal parse {categoryId}: {e}")
    return matches

def main():
    today = datetime.now(KST).strftime("%Y-%m-%d")
    leagues = fetch_leagues()
    all_matches = []
    raw_dump = {}

    for league in leagues:
        categoryId = league.get("categoryId")
        if not categoryId:
            continue
        print(f"📡 Fetching {categoryId} for {today}")
        raw = fetch_schedule(categoryId, today)
        raw_dump[categoryId] = raw
        matches = parse_matches(raw, categoryId)
        all_matches.extend(matches)

    # simpan hasil akhir
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(all_matches)} matches to {OUTPUT_FILE}")

    # simpan raw untuk debug
    with open(DEBUG_FILE, "w", encoding="utf-8") as f:
        json.dump(raw_dump, f, ensure_ascii=False, indent=2)
    print(f"📝 Raw data saved to {DEBUG_FILE}")

if __name__ == "__main__":
    main()
