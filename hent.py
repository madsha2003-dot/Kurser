"""Henter kurser fra Yahoo Finance via yfinance og skriver docs/data/*.json til GitHub Pages.

kurser.json   seneste kurs, ændring i dag, tidspunkt for seneste handel (opdateres hvert 15. min.)
intradag.json 5-minutters kurser for seneste handelsdag pr. ticker
historik.json daglige lukkekurser, 1 år (opdateres ved første kørsel hver dag)
Kurserne er forsinkede efter børsens regler hos Yahoo (typisk 0–20 min.).
"""
import json, os, sys, datetime as dt
import pandas as pd
import yfinance as yf

OUT = os.path.join(os.path.dirname(__file__), "docs", "data")
os.makedirs(OUT, exist_ok=True)
cfg = json.load(open(os.path.join(os.path.dirname(__file__), "tickere.json"), encoding="utf-8"))
NAVN = {**cfg["watchlist"], **cfg["indeks"]}
GRUPPE = {**{t: "watchlist" for t in cfg["watchlist"]}, **{t: "indeks" for t in cfg["indeks"]}}
T = list(NAVN)
now = dt.datetime.now(dt.timezone.utc)


def col(df, field, t):
    try:
        s = df[field][t] if isinstance(df.columns, pd.MultiIndex) else df[field]
        return s.dropna()
    except KeyError:
        return pd.Series(dtype=float)


def iso(ts):
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    daily = yf.download(T, period="1y", interval="1d", auto_adjust=False, progress=False, group_by="column", threads=True)
    intra = yf.download(T, period="1d", interval="5m", auto_adjust=False, progress=False, group_by="column", threads=True, prepost=False)
    rows, idag, hist = [], {}, {}
    for t in T:
        d = col(daily, "Close", t)
        if len(d) > 10:  # fjern enkeltstående fejlkurser (fx forkert split-justering hos Yahoo)
            med = d.rolling(11, center=True, min_periods=3).median()
            d = d[(d / med).between(0.6, 1.67)]
        i = col(intra, "Close", t)
        if d.empty and i.empty:
            rows.append({"ticker": t, "navn": NAVN[t], "gruppe": GRUPPE[t], "fejl": "ingen data"}); continue
        hist[t] = [[x.strftime("%Y-%m-%d"), round(float(v), 4)] for x, v in d.items()]
        last_t, last = (i.index[-1], float(i.iloc[-1])) if not i.empty else (d.index[-1], float(d.iloc[-1]))
        # forrige lukkekurs = seneste daglige lukkekurs før handelsdagen for seneste kurs
        dag = pd.Timestamp(last_t).date() if not i.empty else d.index[-1].date()
        prev = d[[x.date() < dag for x in d.index]]
        pc = float(prev.iloc[-1]) if len(prev) else None
        if not i.empty:
            idag[t] = [[iso(x), round(float(v), 4)] for x, v in i.items()]
        rows.append({"ticker": t, "navn": NAVN[t], "gruppe": GRUPPE[t], "kurs": round(last, 4), "forrige_luk": pc,
                     "aendring": None if pc is None else round(last / pc - 1, 6),
                     "tid": iso(last_t), "handelsdag": str(dag),
                     "hoej_52u": round(float(d.max()), 4) if len(d) else None, "lav_52u": round(float(d.min()), 4) if len(d) else None,
                     "aar_til_dato": None})
        ytd = d[[x.year == now.year for x in d.index]]
        prev_year = d[[x.year < now.year for x in d.index]]
        if len(prev_year):
            rows[-1]["aar_til_dato"] = round(last / float(prev_year.iloc[-1]) - 1, 6)
    json.dump({"opdateret": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "kilde": "Yahoo Finance via yfinance (forsinket efter børsens regler)", "rows": rows},
              open(os.path.join(OUT, "kurser.json"), "w"), ensure_ascii=False)
    json.dump({"opdateret": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "serier": idag}, open(os.path.join(OUT, "intradag.json"), "w"))
    json.dump({"opdateret": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "serier": hist}, open(os.path.join(OUT, "historik.json"), "w"))
    ok = sum(1 for r in rows if "kurs" in r)
    print(f"{ok}/{len(rows)} tickers", now)
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
