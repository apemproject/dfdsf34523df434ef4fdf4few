import requests, json, os, sys
from datetime import datetime, timezone, timedelta

PLAYLIST_ID = "FljcQiNy"
BASE_URL = f"https://cdn.jwplayer.com/v2/playlists/{PLAYLIST_ID}"
OUTFILE = "volleyballbeach.json"

def fetch_schedule_all(limit=50):
    """Ambil semua jadwal dari JWPlayer dengan pagination"""
    all_entries = []
    offset = 0

    while True:
        url = f"{BASE_URL}?page_limit={limit}&page_offset={offset}"
        print(f"🔎 Fetch {url}")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        entries = data.get("playlist", [])
        if not entries:
            break

        all_entries.extend(entries)
        if len(entries) < limit:
            break

        offset += limit

    return all_entries

def parse_entries(entries):
    result = []
    for e in entries:
        title = e.get("title")

        # ambil poster
        poster = None
        media_group = e.get("media_group", [])
        if media_group:
            imgs = media_group[0].get("media_item", [])
            if imgs:
                poster = imgs[-1]["src"]

        # ambil start time dengan prioritas
        ext = e.get("extensions", {})
        start = (
            e.get("scheduled_start") or
            ext.get("VCH.ScheduledStart") or
            ext.get("match_date")
        )

        # fallback ke actions.startDate (epoch ms)
        if not start and "actions" in ext:
            for act in ext.get("actions", []):
                if act.get("type") == "add_to_calendar":
                    ts = act.get("options", {}).get("startDate")
                    if ts:
                        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                        start = dt.isoformat()
                        break

        # konversi string waktu ke WIB
        if isinstance(start, str):
            try:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                dt = dt.astimezone(timezone(timedelta(hours=7)))
                start = dt.isoformat()
            except Exception:
                pass

        # ambil src HLS
        src = None
        for link in e.get("links", []):
            if link.get("type") == "application/vnd.apple.mpegurl":
                src = link.get("href")
                break

        media_id = e.get("id") or e.get("mediaid")

        result.append({
            "title": title,
            "start": start,
            "src": src or f"https://livecdn.euw1-0005.jwplive.com/live/sites/fM9jRrkn/media/{media_id}/live.isml/.m3u8",
            "poster": poster or f"https://cdn.jwplayer.com/v2/media/{media_id}/poster.jpg?width=1920"
        })
    return result

def main():
    try:
        entries = fetch_schedule_all(limit=50)
    except Exception as e:
        print("❌ Gagal fetch data:", e)
        sys.exit(1)

    new_data = parse_entries(entries)

    if os.path.exists(OUTFILE):
        with open(OUTFILE, "r", encoding="utf-8") as f:
            old_data = json.load(f)
    else:
        old_data = []

    if old_data == new_data:
        print("⚡ Tidak ada update dari web sumber → skip workflow.")
        sys.exit(0)

    with open(OUTFILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"📊 Update tersimpan ({len(new_data)} jadwal).")

if __name__ == "__main__":
    main()
