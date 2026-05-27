"""
fetch_demographics.py
---------------------
Fetches Kolding municipality demographic data from Statistics Denmark's
StatBank API (table FOLK1B: population by region, sex, age, citizenship)
and writes a JSON file consumed by the Kolding Pulse front page.

Output: ../data/kolding_demographics.json (relative to this script)

Run on a schedule (e.g. cron / GitHub Action) to keep data fresh.
StatBank table FOLK1B is updated quarterly.

Requirements:
    pip install requests pandas

Usage:
    python fetch_demographics.py                  # latest available period
    python fetch_demographics.py --period 2025K4  # explicit period
"""
import argparse
import io
import json
import sys
from pathlib import Path

import pandas as pd
import requests

API = "https://api.statbank.dk/v1/data"
TABLEINFO = "https://api.statbank.dk/v1/tableinfo"
TABLE = "folk1b"
REGION = "621"  # Kolding municipality code


def latest_period() -> str:
    """Ask StatBank for the most recent quarter available in FOLK1B."""
    r = requests.post(
        TABLEINFO,
        json={"table": TABLE, "format": "JSON", "lang": "en"},
        timeout=30,
    )
    r.raise_for_status()
    for v in r.json()["variables"]:
        if v["id"] == "Tid":
            return v["values"][-1]["id"]
    raise RuntimeError("Could not locate Tid variable in tableinfo response")


def fetch(variables: list) -> pd.DataFrame:
    """POST a data request and return a parsed DataFrame."""
    payload = {
        "table": TABLE,
        "format": "CSV",
        "lang": "en",
        "delimiter": "Semicolon",
        "variables": variables,
    }
    r = requests.post(API, json=payload, timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text), sep=";", encoding="utf-8-sig")
    df["INDHOLD"] = pd.to_numeric(df["INDHOLD"], errors="coerce").fillna(0).astype(int)
    return df


def build(period: str) -> dict:
    """Pull all three slices we need and assemble the front-end JSON."""
    age_sex = fetch([
        {"code": "OMRÅDE", "values": [REGION]},
        {"code": "KØN", "values": ["TOT", "1", "2"]},
        {"code": "ALDER", "values": ["*"]},
        {"code": "STATSB", "values": ["0000"]},
        {"code": "Tid", "values": [period]},
    ])
    citi = fetch([
        {"code": "OMRÅDE", "values": [REGION]},
        {"code": "KØN", "values": ["TOT", "1", "2"]},
        {"code": "ALDER", "values": ["IALT"]},
        {"code": "STATSB", "values": ["*"]},
        {"code": "Tid", "values": [period]},
    ])
    full = fetch([
        {"code": "OMRÅDE", "values": [REGION]},
        {"code": "KØN", "values": ["TOT"]},
        {"code": "ALDER", "values": ["*"]},
        {"code": "STATSB", "values": ["*"]},
        {"code": "Tid", "values": [period]},
    ])

    # Age × sex (5-year groups)
    age_order = [a for a in age_sex["ALDER"].unique() if a != "Age, total"]
    piv = (
        age_sex[age_sex["ALDER"] != "Age, total"]
        .pivot_table(index="ALDER", columns="KØN", values="INDHOLD", aggfunc="sum")
        .reindex(age_order)
    )
    age_rows = [
        {
            "age": a.replace(" years", ""),
            "men": int(piv.loc[a, "Men"]),
            "women": int(piv.loc[a, "Women"]),
            "total": int(piv.loc[a, "Total"]),
        }
        for a in age_order
    ]

    # Citizenship totals (excluding Danish)
    cit = citi[(citi["STATSB"] != "Total")
               & (citi["STATSB"] != "Denmark")
               & (citi["KØN"] == "Total")].copy()
    cit = cit[cit["INDHOLD"] > 0].sort_values("INDHOLD", ascending=False)
    citizenship = [{"name": r["STATSB"], "count": int(r["INDHOLD"])}
                   for _, r in cit.iterrows()]

    danish = int(citi[(citi["STATSB"] == "Denmark") & (citi["KØN"] == "Total")]["INDHOLD"].iloc[0])
    total = int(citi[(citi["STATSB"] == "Total") & (citi["KØN"] == "Total")]["INDHOLD"].iloc[0])

    # Heatmap: top 12 foreign nationalities × age
    fa = full[(full["ALDER"] != "Age, total")
              & (~full["STATSB"].isin(["Total", "Denmark"]))].copy()
    ct = (
        fa.pivot_table(index="STATSB", columns="ALDER", values="INDHOLD", aggfunc="sum")
        .fillna(0)
        .reindex(columns=age_order)
    )
    ct["__tot"] = ct.sum(axis=1)
    top = ct[ct["__tot"] > 0].sort_values("__tot", ascending=False).head(12)
    heat = {
        "ages": [a.replace(" years", "") for a in age_order],
        "nats": [
            {"name": nat, "vals": [int(row[a]) for a in age_order], "total": int(row["__tot"])}
            for nat, row in top.iterrows()
        ],
    }

    return {
        "meta": {
            "total": total,
            "danish": danish,
            "foreign": total - danish,
            "men": int(piv["Men"].sum()),
            "women": int(piv["Women"].sum()),
            "period": period.replace("K", " Q"),
            "nat_count": len(citizenship),
            "source": "Statistics Denmark, StatBank FOLK1B",
        },
        "age": age_rows,
        "citizenship": citizenship,
        "heat": heat,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--period", help="StatBank period code (e.g. 2026K2). Defaults to latest.")
    ap.add_argument("--out", default=None, help="Output path. Defaults to ../data/kolding_demographics.json")
    args = ap.parse_args()

    period = args.period or latest_period()
    print(f"Fetching FOLK1B for Kolding (region {REGION}), period {period} ...", file=sys.stderr)

    payload = build(period)

    out = Path(args.out) if args.out else Path(__file__).parent.parent / "data" / "kolding_demographics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    m = payload["meta"]
    print(f"Wrote {out}", file=sys.stderr)
    print(f"  Total {m['total']:,} | Danish {m['danish']:,} | Foreign {m['foreign']:,} | "
          f"{m['nat_count']} nationalities | Period {m['period']}", file=sys.stderr)


if __name__ == "__main__":
    main()
