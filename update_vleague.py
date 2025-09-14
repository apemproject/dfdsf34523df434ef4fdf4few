import requests
import json
from datetime import datetime, timedelta, timezone

API_URL = "https://api-gw.sports.naver.com/cms/templates/volleyball_new_home_feed"
OUTPUT_FILE = "VLeagueKorea.json"
DEBUG_FILE = "debug_raw.json"

KST = timezone(timedelta(hours=9))
LOCAL_TZ = timezone(timedelta(hours=8))

def fetch_data():
    """Ambil data mentah dari API Naver Sport"""
    r = requests.get(API_URL, timeout=10)
    r.raise_for_status()
    return r.json()

def parse_schedule(raw):
    """Parse jadwal ke format JSON sederhana"""
    matches = []

    try:
        contents = raw.get("result", {}).get("content", [])
    except Exception:
        return matches

    for block in contents:
        items = block.get("items", [])
        for g in items:
            if g.get("type") != "game":
                continue

            home = g.get("homeTeamName", "")
            away = g.get("awayTeamName", "")
            title = f"{home} vs {away}"

            start_time = g.get("gameDateTime")
            if start_time:
                try:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+09:00"))
                    dt_local = dt.astimezone(LOCAL_TZ)
                    start_str = dt_local.isoformat()
                except Exception:
                    start_str = ""
            else:
                start_str = ""

            matches.append({
                "title": title,
                "start": start_str,
                "src": "",
                "poster": ""
            })

    return matches

def clean_expired(matches):
    now = datetime.now(LOCAL_TZ)
    cleaned = []
    for m in matches:
        try:
            dt = datetime.fromisoformat(m["start"])
            if dt + timedelta(hours=3) > now:
                cleaned.append(m)
        except Exception:
            continue
    return cleaned

def main():
    raw = fetch_data()

    # Simpan debug file
    with open(DEBUG_FILE, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    matches = parse_schedule(raw)
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
