"""Constraint turn-up's range (version 1.1.0, part 4, aios-harness#225): every half-hour from the first
settlement stack (Nov 2015) to the end of 2025, the switched-off wind volume priced on that half-hour's accepted
offers three ways (billpaid.ranges.turnup_walks): 1.0.0's own walk, the cheapest offers first, the dearest first.

Reads Elexon Insights settlement stacks (the same public API and the same calls as the turn-up feed,
billpaid.schemes.constraint_turnup) and writes one row a day to reference/sources/turnup-range-daily.csv. The
file is pinned by sha256 in reference/ranges.yaml; the figures build reads only the pinned file, never Elexon.
Run once, on purpose; a rerun is a new source and is never picked up by itself.

    uv run --frozen python tools/turnup_range.py [--start 2015-11-01] [--end 2025-12-31] [--out PATH]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from billpaid import ranges  # noqa: E402
from billpaid.schemes import constraint_turnup as tu  # noqa: E402

FIELDS = ["date", "wind_so_mwh", "central_mwh", "central_gbp", "low_mwh", "low_gbp", "high_mwh", "high_gbp"]


def day_row(d: date, fuel: dict, client: httpx.Client) -> dict:
    periods = range(1, 51)
    with cf.ThreadPoolExecutor(10) as ex:
        bids = list(ex.map(lambda p: tu._stack("bid", d, p, client), periods))
        lost = {p: tu.wind_bids_so(b, fuel)[0] for p, b in zip(periods, bids)}
        # offers only where wind was switched off: elsewhere every walk is zero
        wanted = [p for p in periods if lost[p]]
        offers = dict(zip(wanted, ex.map(lambda p: tu._stack("offer", d, p, client), wanted)))
    row = dict.fromkeys(FIELDS[1:], 0.0)
    for p in wanted:
        wv, o = lost[p], offers[p]
        row["wind_so_mwh"] += wv
        for k, (v, c) in ranges.turnup_walks(o, wv).items():
            row[f"{k}_mwh"] += v
            row[f"{k}_gbp"] += c
    return {"date": d.isoformat(), **row}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2015-11-01")
    p.add_argument("--end", default="2025-12-31")
    p.add_argument("--out", default=str(ROOT / "reference" / "sources" / "turnup-range-daily.csv"))
    a = p.parse_args(argv)
    out = Path(a.out)
    part = out.with_suffix(".partial.csv")
    done = {}
    if part.exists():
        with part.open() as f:
            done = {r["date"]: r for r in csv.DictReader(f)}
    with httpx.Client(timeout=60, limits=httpx.Limits(max_connections=10)) as client:
        fuel = tu.fuel_map(client)
        d, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
        with part.open("a", newline="") as f:
            w = csv.DictWriter(f, FIELDS)
            if not done:
                w.writeheader()
            while d <= end:
                if d.isoformat() not in done:
                    w.writerow(day_row(d, fuel, client))
                    f.flush()
                if d.day == 1:
                    print(f"[turnup-range] {d}", flush=True)
                d += timedelta(days=1)
    with part.open() as f:
        rows = sorted(csv.DictReader(f), key=lambda r: r["date"])
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] if k == "date" else repr(float(r[k])) for k in FIELDS})
    part.unlink()
    print(f"[ok] {len(rows)} days -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
