"""Wind switch-off (constraint) payments from Elexon's own record in place of REF's database (version 1.2.0,
Report No. 2's plan step 19, aios-harness#235; Richard's standing ruling: primary sources, no REF where a primary
record exists).

1.0.0 takes 2010-2023 from REF's database and Elexon's settlement stacks from 2024. The stacks start on 6 Nov 2015
(billpaid.elexon.STACK_FIRST_DAY) and 1.0.0's store already holds every day since. So each calendar year the store
holds whole is taken from Elexon: 2016-2023 replace REF. 2010-2015 have no Elexon record (Elexon's API returns no
settlement stack, acceptance or bid-offer data before November 2015, checked 11 Nov 2026) and stay on REF; they are
named by `constraints.ref_years`.

The store is read as it stood when the frozen results file was written (each day's latest version retrieved at or
before the file's `generated_at`), so the figure does not depend on a later fetch.

The three balancing lines (constraints, constraint turn-up, BSUoS) are one measured total split three ways: the
BSUoS charge above the gas-led alternative's (billpaid.schemes.bsuos). 1.0.0's own split rule is applied again with
the new constraint figure: uplift = that total less constraint payments; turn-up = its measured figure, never more
than the uplift nor below zero; BSUoS = the rest. So all, the bridge and VAT do not move; money moves between the
direct layer (constraints) and the indirect (turn-up, BSUoS).
"""
from __future__ import annotations

import copy
import math
import glob
from datetime import date
from pathlib import Path

import polars as pl

from billpaid.money import add_real
from billpaid.reference import load_annual_costs

TABLE = ("constraints", "daily")


def _cutoff(doc: dict) -> str:
    """The frozen file's `generated_at` as a store version name (20261109T063941.720314)."""
    return doc["meta"]["generated_at"][:26].replace("-", "").replace(":", "")


def elexon_by_year(doc: dict, root: Path) -> dict[int, tuple[float, int]]:
    """{year: (£ cash, days held)}: Elexon's wind bids accepted, as the store held them at the frozen file's
    writing."""
    cut = _cutoff(doc)
    out: dict[int, list] = {}
    for d in sorted(glob.glob(str(root / "data/raw" / TABLE[0] / TABLE[1] / "2*"))):
        versions = [v for v in sorted(glob.glob(d + "/*/data.parquet")) if Path(v).parent.name <= cut]
        if not versions:
            continue
        y = int(Path(d).name[:4])
        t = out.setdefault(y, [0.0, 0])
        t[0] += math.fsum(pl.read_parquet(versions[-1])["cost_gbp"].to_list())   # exact, order-free
        t[1] += 1
    return {y: (v[0], v[1]) for y, v in out.items()}


def _whole_year(y: int, days: int) -> bool:
    return days == (date(y + 1, 1, 1) - date(y, 1, 1)).days


def _scheme(doc: dict, line: str) -> dict:
    return next(s for s in doc["model"]["schemes"] if s["scheme_id"] == line)


def apply(doc: dict, root: Path, last_year: int) -> tuple[dict, list[int], list[int]]:
    """A copy of the frozen results file with each whole Elexon year up to `last_year` in place of REF's, and the
    split re-applied. Returns (doc, years moved to Elexon, years left on REF)."""
    doc = copy.deepcopy(doc)
    con, tu, bs = (_scheme(doc, line) for line in ("constraints", "constraint_turnup", "bsuos"))
    measured = {r["year"]: r["cost"] for r in tu["extras"]["measured_annual"]}
    rows = {line["scheme_id"]: {r["year"]: r for r in line["annual"]["rows"]} for line in (con, tu, bs)}
    elexon = elexon_by_year(doc, root)
    moved, on_ref = [], []
    delta = dict.fromkeys(rows, 0.0)
    deflators = pl.DataFrame(doc["deflators"]["rows"],
                             schema={k: getattr(pl, v) for k, v in doc["deflators"]["schema"].items()}, orient="row")
    # 1.0.0 already takes Elexon from the history's pin year (2024): only the years before it are REF's
    pin = load_annual_costs(root / "reference/annual_scheme_costs.yaml")["constraints_history"].bottom_up_from
    for y in sorted(rows["constraints"]):
        if y > last_year or y >= pin:
            continue
        if y not in elexon or not _whole_year(y, elexon[y][1]):
            on_ref.append(y)
            continue
        new_con = elexon[y][0]
        old = {line: rows[line][y]["cost_gbp"] if y in rows[line] else 0.0 for line in rows}
        uplift = old["bsuos"] + old["constraint_turnup"] + old["constraints"] - new_con
        new_tu = min(measured.get(y, 0.0), max(0.0, uplift))
        cash = {"constraints": new_con, "constraint_turnup": new_tu, "bsuos": uplift - new_tu}
        for line, v in cash.items():
            if line in rows and y in rows[line]:
                r = rows[line][y]
                delta[line] += v - r["cost_gbp"]
                r["cost_gbp"] = v
                r["cost_gbp_2024"] = _real(v, y, deflators)
            elif v:
                raise ValueError(f"{line} has no {y} row to take {v}")
        moved.append(y)
    for s in (con, tu, bs):
        s["cumulative_gbp"] += delta[s["scheme_id"]]   # each line's own total moves by what its years moved
    return doc, moved, on_ref


def _real(cash: float, y: int, deflators: pl.DataFrame) -> float:
    """£ in 2024 prices by the model's own rule for a calendar-year line (billpaid.money.add_real)."""
    t = add_real(pl.DataFrame({"year": [y], "cost_gbp": [float(cash)]},
                              schema={"year": pl.Int64, "cost_gbp": pl.Float64}), deflators)
    return float(t["cost_gbp_2024"][0])

