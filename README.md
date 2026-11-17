# Kurser

Offentlig kursside for watchlisten og udvalgte indeks: **https://madsha2003-dot.github.io/kurser/**

- `hent.py` henter kurser fra Yahoo Finance (yfinance) og skriver `docs/data/*.json`.
- `.github/workflows/kurser.yml` kører hvert 15. minut på hverdage (00–22 UTC).
- `docs/index.html` er siden (GitHub Pages fra `main` / `docs`). Den genindlæser data hvert minut.
- Tickers ændres i `tickere.json`.

Kun kursdata – analyser og modeller ligger i det private repo `markedsdata`.
Kurserne er forsinkede efter børsens regler. Ikke investeringsrådgivning.
