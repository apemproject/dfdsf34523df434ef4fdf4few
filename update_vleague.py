import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone
import os


def scrape_schedule():
    base_url = "https://sports.news.naver.com"
    schedule_url = f"{base_url}/volleyball/schedule/index"

    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(schedule_url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    events = []

    # ambil tanggal di header
    date_str = soup.select_one(".schedule_calendar strong").get_text(strip=True)
    date_obj = datetime.strptime(date_str.split()[0], "%Y.%m.%d")

    kst = timezone(timedelta(hours=9))  # Korea Standard Time
    now_kst = datetime.now(kst)

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

        # waktu pertandingan (gabung tanggal + jam)
        if ":" in time_txt:
            hour, minute = map(int, time_txt.split(":"))
            start_dt = datetime(
                date_obj.year, date_obj.month, date_obj.day, hour, minute, tzinfo=kst
            )
        else:
            continue  # skip kalau tidak ada jam

        # skip kalau sudah lewat
        if start_dt + timedelta(hours=2) < now_kst:
            continue

        event = {
            "title": f"{team1} vs {team2}",
            "start": start_dt.astimezone(timezone(timedelta(hours=8))).isoformat(),  # konversi ke GMT+8
            "src": link,
            "poster": ""  # bisa diisi thumbnail kalau ada
        }
        events.append(event)

    return events


if __name__ == "__main__":
    data = scrape_schedule()

    out_file = "VLeagueKorea.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Updated {out_file} with {len(data)} events")
