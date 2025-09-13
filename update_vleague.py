import json
import time
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

URL = "https://sports.news.naver.com/volleyball/schedule/index.nhn"
output_file = "VLeagueKorea.json"
LOCAL_TZ = timezone(timedelta(hours=8))
CHECK_INTERVAL = 300  # detik, 5 menit

def fetch_page(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, wait_until="networkidle")
    return page, browser

def parse_schedule(page):
    # Cek __INITIAL_STATE__ dulu
    try:
        data_json = page.evaluate("() => window.__INITIAL_STATE__ || null")
        if data_json and "schedule" in data_json:
            matches = data_json["schedule"].get("matches", [])
            return matches
    except Exception:
        pass

    # Fallback: ambil dari DOM
    matches = []
    try:
        rows = page.query_selector_all("div.schedule_list > ul > li")
        for row in rows:
            try:
                home = row.query_selector(".home_team").inner_text().strip()
                away = row.query_selector(".away_team").inner_text().strip()
                title = f"{home} vs {away}"

                start_elem = row.query_selector(".time")
                start_str = start_elem.inner_text().strip() if start_elem else ""
                today = datetime.now(LOCAL_TZ).date()
                start_dt = datetime.combine(today, datetime.strptime(start_str, "%H:%M").time()).astimezone(LOCAL_TZ)

                poster_elem = row.query_selector("img.team_logo")
                poster = poster_elem.get_attribute("src") if poster_elem else ""

                live_elem = row.query_selector(".status_live")
                src = row.query_selector("a.live_link").get_attribute("href") if live_elem else ""

                matches.append({
                    "title": title,
                    "start": start_dt.isoformat(),
                    "src": src,
                    "poster": poster
                })
            except Exception:
                continue
    except Exception:
        pass
    return matches

def filter_today(matches):
    today = datetime.now(LOCAL_TZ).date()
    filtered = []
    for match in matches:
        try:
            start_dt = datetime.fromisoformat(match["start"])
            if start_dt.date() == today:
                filtered.append(match)
        except Exception:
            continue
    return filtered

def save_json(matches):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Updated {output_file} dengan {len(matches)} match hari ini")

def main():
    with sync_playwright() as playwright:
        page, browser = fetch_page(playwright)
        try:
            while True:
                matches = parse_schedule(page)
                today_matches = filter_today(matches)
                save_json(today_matches)
                time.sleep(CHECK_INTERVAL)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
