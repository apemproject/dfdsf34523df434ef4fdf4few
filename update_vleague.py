import requests
import json

# Endpoint Naver API (schedule V-League)
URL = "https://api-gw.sports.naver.com/schedule/v1/leagues/volleyball"

def main():
    print(f"🌐 Fetching data from {URL} ...")
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    data = r.json()

    # Simpan langsung ke root repo
    output_file = "VLeagueKorea.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {output_file} with {len(json.dumps(data))} characters")

if __name__ == "__main__":
    main()
