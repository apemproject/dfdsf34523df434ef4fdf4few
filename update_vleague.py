import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone


def scrape_schedule():
    base_url = "https://sports.news.naver.com"
    schedule_url = f"{base_url}/volleyball/schedule/index"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
    }

    res = requests.get(schedule_url, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # cari tanggal di header
    date_tag = soup.select_one(".schedule_calendar strong")
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)

    if date_tag:
        date_str = date_tag.get_text(strip=True)
        try:
            date_obj = datetime.strptime(date_str.split()[0], "%Y.%m.%d")
        except Exception:
            date_obj = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # fallback: hari ini
        date_obj = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print("⚠️ Tidak menemukan '.schedule_calendar strong', dump HTML ke debug.html")

    events = []

    for row in soup.select(".sch_tb tbody tr"):
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        time_txt = cols[0].get_text(strip=True)
        team1 = cols[1].get_text(strip=True)
        team2 = cols[3].get_text(strip=True)

        # link detail pertandingan
        link_tag = cols[1].find("a") or cols[3].find("a")
        link = base_url + link_tag["href"] if link_tag else ""

        # gabungkan tanggal + jam
        if ":" in time_txt:
            hour, minute = map(int, time_txt.split(":"))
            start_dt = datetime(
                date_obj.year, date_obj.month, date_obj.day,
                hour, minute, tzinfo=kst
            )
        else:
            continue

        # skip kalau sudah lewat (anggap durasi 2 jam)
        if start_dt + timedelta(hours=2) < now_kst:
            continue

        # konversi ke GMT+8 (WIB +1)
        start_gmt8 = start_dt.astimezone(timezone(timedelta(hours=8)))

        event = {
            "title": f"{team1} vs {team2}",
            "start": start_gmt8.isoformat(),
            "src": link,
            "poster": ""
        }
        events.append(event)

    return events


if __name__ == "__main__":
    data = scrape_schedule()

    out_file = "VLeagueKorea.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Updated {out_file} with {len(data)} events")
