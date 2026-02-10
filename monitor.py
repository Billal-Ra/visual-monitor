on:
  schedule:
    - cron: "*/5 * * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install --upgrade pip
      - run: pip install playwright opencv-python scikit-image pyyaml requests
      - run: playwright install chromium

      - run: python monitor.py
        env:
          DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}

      - name: Deploy dashboard to GitHub Pages (gh-pages)
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
          force_orphan: true

