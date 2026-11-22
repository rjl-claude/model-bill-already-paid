"""The bill already paid, counted as Report No. 2 counts it (version 1.7.0; Richard, 22 Nov 2026: "publish the report
and ensure the clock is consistent").

One account for both readers: the paper's figures file (billpaid.figures, from the frozen results file) and the
Clock's results file (billpaid.results, from each morning's run) go through `counted`, so the Clock shows the same
lines, counted the same way, as the paper:

1. wind constraint payments from a primary record in every closed year (Elexon where the store holds the whole year,
   National Grid before: billpaid.elexon_record, 1.2.0 and 1.5.0), with the split of balancing re-applied;
2. the generators' share of grid and balancing charges not paid out of subsidy, and the VAT on it
   (billpaid.generators_share, 1.6.0, ADR 0264);
3. each changed line's own total and run rate, and the Clock's totals blocks (the direct perspectives and the
   indirect layer), made again from the lines, so every figure the Clock shows carries the same account.
"""
from __future__ import annotations

import math
from pathlib import Path

import polars as pl

from billpaid import elexon_record, generators_share
from billpaid.money import PERSPECTIVES, latest_real_factor, rate_per_second
from billpaid.schemes import vat as vat_mod

LAST_CLOSED_YEAR = 2024          # the last whole year a primary record replaces (the paper's headline runs 2002-2024)
ANNUAL_SCHEMA = {"year": "Int64", "cost_gbp": "Float64", "cost_gbp_2024": "Float64"}


def apply(doc: dict, root: Path) -> dict:
    """A copy of a results file, counted as the paper counts the bill already paid."""
    return counted(doc, root)[0]


def counted(doc: dict, root: Path) -> tuple[dict, list[int], dict]:
    """(doc, the years of wind constraint payments from National Grid's record, the generators' share table)."""
    doc, _, national_grid = elexon_record.apply(doc, root, LAST_CLOSED_YEAR)
    vat_before = _rows_total(_line(doc, "vat"))
    doc, table = generators_share.apply(doc, root)
    _settle(doc, vat_before)
    _totals(doc)
    return doc, national_grid, table


def _line(doc: dict, line: str) -> dict:
    return next(s for s in doc["model"]["schemes"] if s["scheme_id"] == line)


def _rows_total(s: dict) -> float:
    return math.fsum(r["cost_gbp"] for r in s["annual"]["rows"])


def _settle(doc: dict, vat_before: float) -> None:
    """The new line as a whole line of the file (every field a line carries, its run rate the last year's cost), and
    the VAT line's total and run rate moved by the VAT on it, by the VAT line's own rule."""
    gs, vat = _line(doc, generators_share.LINE), _line(doc, "vat")
    rows = gs["annual"]["rows"]
    last = max(rows, key=lambda r: r["year"])
    gs.update({
        "annual": {"schema": ANNUAL_SCHEMA, "rows": rows},
        "runrate_gbp_per_year": last["cost_gbp"],
        "data_to": f"{last['year']}-12-31",
        "attribution_pct": 1.0,
        "attribution_note": ("The generators' share of grid (TNUoS) and balancing (BSUoS) charges above the gas-led "
                             "alternative, times the share of the year's power made by stations with no subsidy."),
        "carry_with": None,
    })
    order = ["scheme_id", "label", "perspectives", "cadence", "annual", "cumulative_gbp", "runrate_gbp_per_year",
             "data_to", "layer", "attribution_pct", "attribution_note", "attribution_confidence", "extras", "carry_with"]
    for k in [k for k in gs if k not in order]:
        order.append(k)
    reordered = {k: gs[k] for k in order}
    gs.clear()
    gs.update(reordered)
    vat["cumulative_gbp"] += _rows_total(vat) - vat_before
    share = max(vat["extras"]["domestic_share"], key=lambda r: r["year"])["share"]
    factor = vat_mod.RATE * share
    vat["runrate_gbp_per_year"] += factor * gs["runrate_gbp_per_year"]
    if vat.get("carry_with") is not None:
        vat["carry_with"][generators_share.LINE] = factor


def _block(members: list[dict], factor: float) -> dict:
    """A totals block made from its lines, as billpaid.money._aggregate makes it."""
    by_year: dict[int, list[float]] = {}
    real = all(all("cost_gbp_2024" in r for r in s["annual"]["rows"]) for s in members)
    for s in members:
        for r in s["annual"]["rows"]:
            y = by_year.setdefault(r["year"], [0.0, 0.0])
            y[0] += r["cost_gbp"]
            y[1] += r.get("cost_gbp_2024", 0.0)
    years = sorted(by_year)
    schema = dict(ANNUAL_SCHEMA) if real else {"year": "Int64", "cost_gbp": "Float64"}
    rows = [{"year": y, "cost_gbp": by_year[y][0], **({"cost_gbp_2024": by_year[y][1]} if real else {})} for y in years]
    runrate = sum(s["runrate_gbp_per_year"] for s in members)
    out = {"cumulative_gbp": sum(s["cumulative_gbp"] for s in members),
           "runrate_gbp_per_year": runrate,
           "rate_gbp_per_sec": rate_per_second(runrate),
           "annual": {"schema": schema, "rows": rows},
           "since_year": years[0] if years else None}
    if real:
        out["cumulative_gbp_2024"] = math.fsum(r["cost_gbp_2024"] for r in rows)
    out["runrate_gbp_per_year_2024"] = runrate * factor
    out["rate_gbp_per_sec_2024"] = out["rate_gbp_per_sec"] * factor
    return out


def _totals(doc: dict) -> None:
    m = doc["model"]
    deflators = pl.DataFrame(doc["deflators"]["rows"],
                             schema={k: getattr(pl, v) for k, v in doc["deflators"]["schema"].items()}, orient="row")
    factor = latest_real_factor(deflators)
    direct = [s for s in m["schemes"] if s["layer"] == "direct"]
    m["perspectives"] = {p: _block([s for s in direct if p in s["perspectives"]], factor) for p in PERSPECTIVES}
    m["indirect"] = _block([s for s in m["schemes"] if s["layer"] == "indirect"], factor)
