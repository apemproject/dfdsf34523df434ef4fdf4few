name: Update V-League Korea

on:
  schedule:
    - cron: "0 * * * *"   # tiap 1 jam sekali
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.x"
      - name: Install dependencies
        run: pip install requests
      - name: Run scraper
        run: python update_vleague.py
      - name: Commit & Push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add VLeagueKorea.json
          git commit -m "Auto update V-League schedule"
          git push
