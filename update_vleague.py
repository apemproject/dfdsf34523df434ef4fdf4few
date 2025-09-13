import requests
import re
import json
import time
from datetime import datetime, timezone, timedelta

URL = "https://sports.news.naver.com/volleyball/schedule/index.nhn"
output_file = "VLeagueKorea.json"
LOCAL_TZ = timezone(timedelta(hours=8))
CHECK_INTERVAL = 300  # 5 menit

def fetch_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    }
    try:
        r = requests.get(URL, headers=headers, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print("❌ Failed to fetch HTML:", e)
        return ""

def parse_schedule(html):
    matches = []

    # Coba ambil JSON dari window.__INITIAL_STATE__
    match_json = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*\});', html)
    if match_json:
        try:
            data = json.loads(match_json.group(1))
            sched = data.get("schedule", {}).get("matches", [])
            for m in sched:
                matches.append({
                    "title": f"{m.get('homeTeamName','')} vs {m.get('awayTeamName','')} | {m.get('tournamentName','')}",
                    "start": m.get("startDate", ""),
                    "src": m.get("streamUrl", ""),
                    "poster": m.get("posterUrl", "")
                })
            print(f"✅ Found {len(matches)} matches from JSON")
            return matches
        except:
            pass

    # Fallback: ambil dari HTML (DOM statis)
    rows = re.findall(r'<li class=".*?">.*?</li>', html, re.S)
    for row in rows:
        try:
            home = re.search(r'class="home_team".*?>(.*?)<', row, re.S).group(1).strip()
            away = re.search(r'class="away_team".*?>(.*?)<', row, re.S).group(1).strip()
            title = f"{home} vs {away}"

            time_str = re.search(r'class="time".*?>(.*?)<', row, re.S).group(1).strip()
            today = datetime.now(LOCAL_TZ).date()
            start_dt = datetime.combine(today, datetime.strptime(time_str, "%H:%M").time()).astimezone(LOCAL_TZ)

            poster_match = re.search(r'<img .*?src="(.*?)"', row)
            poster = poster_match.group(1) if poster_match else ""

            live_match = re.search(r'class="status_live"', row)
            src_match = re.search(r'<a class="live_link".*?href="(.*?)"', row)
            src = src_match.group(1) if live_match and src_match else ""

            matches.append({
                "title": title,
                "start": start_dt.isoformat(),
                "src": src,
                "poster": poster
            })
        except:
            continue

    print(f"✅ Found {len(matches)} matches from HTML fallback")
    return matches

def filter_today(matches):
    today = datetime.now(LOCAL_TZ).date()
    filtered = []
    for m in matches:
        try:
            dt = datetime.fromisoformat(m["start"])
            if dt.date() == today:
                filtered.append(m)
        except:
            continue
    return filtered

def save_json(matches):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Updated {output_file} with {len(matches)} matches")

def main():
    while True:
        html = fetch_html()
        matches = parse_schedule(html)
        today_matches = filter_today(matches)
        save_json(today_matches)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
