import requests
import json
import os
from datetime import datetime, timezone, timedelta

# Endpoint Naver API (schedule V-League)
URL = "https://api-gw.sports.naver.com/schedule/v1/leagues/volleyball"

# Folder output
os.makedirs("data", exist_ok=True)
output_file = "data/VLeagueKorea_today.json"

# Atur zona waktu lokal (WIB: UTC+7)
LOCAL_TZ = timezone(timedelta(hours=7))

def main():
    print(f"🌐 Fetching data from {URL} ...")
    try:
        r = requests.get(URL, timeout=20)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        return

    # Ambil tanggal hari ini di WIB
    today = datetime.now(LOCAL_TZ).date()

    # Filter pertandingan yang tayang hari ini
    matches_today = []
    for match in data.get("matches", []):
        start_time_str = match.get("startDate")  # pastikan key ini sesuai API
        if not start_time_str:
            continue
        try:
            # Ubah string ke datetime (ISO format)
            start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
        except ValueError:
            continue

        if start_dt.date() == today:
            matches_today.append(match)

    # Simpan ke file JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matches_today, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {output_file} with {len(matches_today)} matches today ({today})")

if __name__ == "__main__":
    main()
