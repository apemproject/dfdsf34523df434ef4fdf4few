import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone

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

    kst = timezone(timedelta(hours=9))   # Korea Standard Time
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
        match_link = base_url + link_tag["href"] if link_tag else ""

        # poster (thumbnail)
        img_tag = cols[1].find("img") or cols[3].find("img")
        poster = img_tag["src"] if img_tag else "/assets/default.jpg"

        # gabungkan tanggal + waktu
        try:
            match_time = datetime.strptime(
                f"{date_obj.strftime('%Y-%m-%d')} {time_txt}", "%Y-%m-%d %H:%M"
            ).replace(tzinfo=kst)
        except ValueError:
            # kalau waktu kosong (misalnya "취소" atau "연기")
            continue

        # skip kalau sudah lewat
        if match_time < now_kst:
            continue

        # ubah ke format ISO +08:00
        iso_time = match_time.astimezone(
            timezone(timedelta(hours=8))
        ).strftime("%Y-%m-%dT%H:%M:%S+08:00")

        events.append({
            "title": f"{team1} vs {team2}",
            "start": iso_time,
            "src": match_link,
            "poster": poster
        })

    # simpan ke file
    with open("VLeagueKorea.json", "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

    print("✅ VLeagueKorea.json berhasil diperbarui")

if __name__ == "__main__":
    scrape_schedule()
