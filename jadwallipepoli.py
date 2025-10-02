import requests, json, os, sys
from datetime import datetime, timezone, timedelta

SOURCES = [
    {"url": "https://zapp-5434-volleyball-tv.web.app/jw/playlists/cUqft8Cd", "outfile": "jepangsvleague.json"},
    {"url": "https://zapp-5434-volleyball-tv.web.app/jw/playlists/FljcQiNy", "outfile": "liveeventvoli.json"},
    {"url": "https://zapp-5434-volleyball-tv.web.app/jw/playlists/MeMYn3wh", "outfile": "volleyballbeach.json"},
    {"url": "https://zapp-5434-volleyball-tv.web.app/jw/playlists/eMqXVhhW", "outfile": "volleyballworld.json"},
]

def fetch_schedule(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("entry", [])

def parse_entries(entries):
    result = []
    for e in entries:
        title = e.get("title")
        poster = None
        media_group = e.get("media_group", [])
        if media_group:
            imgs = media_group[0].get("media_item", [])
            if imgs:
                poster = imgs[-1]["src"]

        ext = e.get("extensions", {})
        start = e.get("scheduled_start") or ext.get("VCH.ScheduledStart") or ext.get("match_date")

        if not start and "actions" in ext:
            for act in ext.get("actions", []):
                if act.get("type") == "add_to_calendar":
                    ts = act.get("options", {}).get("startDate")
                    if ts:
                        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                        start = dt.isoformat()
                        break

        if isinstance(start, str):
            try:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                dt = dt.astimezone(timezone(timedelta(hours=7)))
                start = dt.isoformat()
            except Exception:
                pass

        src = None
        for link in e.get("links", []):
            if link.get("type") == "application/vnd.apple.mpegurl":
                src = link.get("href")
                break

        media_id = e.get("id")
        result.append({
            "title": title,
            "start": start,
            "src": src or f"https://livecdn.euw1-0005.jwplive.com/live/sites/fM9Rkn/media/{media_id}/live.isml/.m3u8",
            "poster": poster or f"https://cdn.jwplayer.com/v2/media/{media_id}/poster.jpg?width=1920"
        })
    return result

def update_file(outfile, data):
    # Cek apakah ada perubahan
    old_data = []
    if os.path.exists(outfile):
        with open(outfile, "r", encoding="utf-8") as f:
            try:
                old_data = json.load(f)
            except Exception:
                old_data = []

    if old_data != data:
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📊 Update tersimpan di {outfile} ({len(data)} jadwal).")
        return True
    else:
        print(f"⚡ Tidak ada update → skip {outfile}.")
        return False

def main():
    any_update = False
    for src in SOURCES:
        try:
            entries = fetch_schedule(src["url"])
        except Exception as e:
            print(f"❌ Gagal fetch data dari {src['url']}: {e}")
            continue

        parsed = parse_entries(entries)
        updated = update_file(src["outfile"], parsed)
        if updated:
            any_update = True

    if not any_update:
        print("⚡ Tidak ada update di semua sumber → skip commit.")
        sys.exit(0)

if __name__ == "__main__":
    main()
