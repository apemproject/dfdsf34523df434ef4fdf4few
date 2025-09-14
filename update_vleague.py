import requests
import json
from datetime import datetime, timedelta, timezone

API_CALENDAR_URL = "https://api-gw.sports.naver.com/schedule/calendar"
OUTPUT_FILE = "VLeagueKorea.json"
DEBUG_FILE = "debug_raw.json"

KST = timezone(timedelta(hours=9))
LOCAL_TZ = timezone(timedelta(hours=8))

# kategori yang dipilih
CATEGORY_IDS = ",kovo,wkovo,uvolleyball,volleyballetc"

def fetch_calendar(date_str):
    params = {
        "superCategoryId": "volleyball",
        "categoryIds": CATEGORY_IDS,
        "date": date_str
    }
    r = requests.get(API_CALENDAR_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def parse_matches(raw):
    matches = []
    # Dump raw untuk debug
    # Perlu tahu struktur dari raw
    # Biasanya mungkin ada raw["result"]["schedule"]["gameList"] atau semacamnya
    # Kita coba beberapa kemungkinan

    # Contoh pase:
    # raw -> result -> calendarList -> games, dsb.

    # Fallback: cari semua objek dengan field yang sesuai
    try:
        # contohnya:
        calendar = raw.get("result", {}).get("calendar", {})
        # atau:
        data_list = raw.get("result", {}).get("data", {}).get("games", [])
    except Exception:
        calendar = {}
        data_list = []

    # Versi fallback: cari game list di dalam nested keys
    if not data_list:
        # coba cari dalam raw["result"]["calendar"]["games"]
        data_list = raw.get("result", {}).get("calendar", {}).get("games", [])

    # Parsing
    for game in data_list:
        try:
            home = game.get("homeTeamName") or game.get("homeName") or ""
            away = game.get("awayTeamName") or game.get("awayName") or ""
            start_time = game.get("gameDateTime") or game.get("startTime") or game.get("gameDate") + "T" + game.get("gameTime")

            # konversi ke objek datetime
            if start_time:
                # jika ada format timezone di string
                dt = datetime.fromisoformat(start_time if "+" in start_time or "Z" in start_time else start_time + "+09:00")
                dt_local = dt.astimezone(LOCAL_TZ)
                start_iso = dt_local.isoformat()
            else:
                continue

            # src: link detail kalau ada
            match_id = game.get("gameId") or game.get("id")
            src = f"https://m.sports.naver.com/game/{match_id}" if match_id else ""

            # poster: bisa ambil logo tim home dulu jika ada
            poster = game.get("homeTeamEmblem") or game.get("homeLogo") or ""

            matches.append({
                "title": f"{home} vs {away}",
                "start": start_iso,
                "src": src,
                "poster": poster
            })
        except Exception as e:
            print("Skip game parsing:", e)
    return matches

def clean_expired(matches):
    now = datetime.now(LOCAL_TZ)
    return [m for m in matches if datetime.fromisoformat(m["start"]) > now]

def main():
    today = datetime.now(KST).strftime("%Y-%m-%d")
    raw = fetch_calendar(today)

    with open(DEBUG_FILE, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    matches = parse_matches(raw)
    print("Parsed matches:", len(matches))
    for m in matches:
        print(m["title"], m["start"])

    matches = clean_expired(matches)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(matches)} matches to {OUTPUT_FILE}")
    print(f"📝 Raw data saved to {DEBUG_FILE}")

if __name__ == "__main__":
    main()
