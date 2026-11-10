"""aios-harness#142 (1): the closed years recorded under register.checks come out in year order whatever
order the feed's rows arrive in, so two builds of the same code write byte-identical results."""
from __future__ import annotations

import random
from datetime import date

import polars as pl

from billpaid import register as R


def _feed(years: list[int], seed: int) -> pl.DataFrame:
    rows = [(date(y, m, 15), 1000.0 * m) for y in years for m in range(1, 13)]
    random.Random(seed).shuffle(rows)
    return pl.DataFrame({"date": [r[0] for r in rows], "cost_gbp": [r[1] for r in rows]})


def test_register_checks_years_in_order_whatever_the_row_order():
    years = list(range(2010, 2026))
    values = {y: 0.5 for y in years}  # GBP 0.5m against a feed of GBP 0.078m: every year is moved and recorded
    for seed in range(6):
        checks: dict = {}
        R.rescale_closed_years(_feed(years, seed), values, closed=2025, checks=checks, line="L")
        assert list(checks["L"]) == [str(y) for y in years], seed
