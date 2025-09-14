import requests
import json
from datetime import datetime, timedelta, timezone
import os

API_URL = "https://api-gw.sports.naver.com/schedule/games/vleague"
OUTPUT_FILE = "VLeagueKorea.json"
DEBUG_FILE = "debug_raw.json"

# Zona waktu Korea (UTC+9)
KST = timezone(timedelta(hours=9))
# Konversi ke UTC+8 sesuai permintaan
LOCAL_TZ = timezone(timedelta(hours=8))


def fetch_data():
    """Ambil data mentah dari API Naver Sport"""
    params = {
        "date": datetime.now(KST).strftime("%Y%m%d"),
        "category": "volleyball",
    }
    r = requests.get(API_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def parse_schedule(raw):
    """Parse jadwal ke format JSON yang diinginkan"""
    matches = []

    try:
        game_list = raw.get("result", {}).get("gameList", [])
    except Exception:
        return matches

    for g in game_list:
        title = f"{g.get('homeTeamName','')} vs {g.get('awayTeamName','')}"
        start_time = g.get("gameDateTime")

        # convert start_time (KST) ke UTC+8
        if start_time:
            dt = datetime.fromisoformat(start_time.replace("Z", "+09:00"))
            dt_local = dt.astimezone(LOCAL_TZ)
            start_str = dt_local.isoformat()
        else:
            start_str = ""

        matches.append({
            "title": title,
            "start": start_str,
            "src": "",    # bisa diisi otomatis jika ada link streaming
            "poster": ""  # bisa diisi thumbnail jika ada
        })

    return matches


def clean_expired(matches):
    """Hapus jadwal yang sudah lewat 3 jam dari sekarang"""
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

    # simpan debug file
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
