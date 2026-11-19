"""Version 1.2.0 (Report No. 2's plan step 19, aios-harness#235): wind switch-off (constraint) payments from Elexon's
own record wherever it holds the whole year (Richard's standing ruling: primary sources).

Elexon's settlement stacks start on 6 Nov 2015, so 2016-2023 are Elexon's; 2010-2015 are National Grid's record from
1.5.0 and are named by `constraints.national_grid_years`. Expected values are the input audit's own sums of Elexon's record (report-series,
price-of-the-climate-bill/input-audit-bill-already-paid/output/spot_checks.txt, section 3), never the model's code."""
import json
import math
import subprocess

import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT

# £m cash, Elexon's record summed by calendar year (the audit, 11 Nov 2026, two decimals)
ELEXON_AUDIT = {2016: 82.32, 2017: 109.32, 2018: 125.65, 2019: 141.49, 2020: 283.00, 2021: 147.42,
                2022: 235.64, 2023: 318.84}
# £m cash, the figures 1.0.0 holds for those years (the same audit file)
HELD_1_0_0 = {2016: 81.86, 2017: 108.25, 2018: 124.65, 2019: 138.99, 2020: 274.16, 2021: 143.34,
             2022: 227.18, 2023: 310.48}
BALANCING = ("constraints", "constraint_turnup", "bsuos")


@pytest.fixture(scope="module")
def frozen():
    return figures.frozen_results(ROOT)


@pytest.fixture(scope="module")
def figs(frozen):
    return figures.build(frozen, bridge.no1_release(ROOT))


def _row(doc, line, y):
    s = next(s for s in doc["model"]["schemes"] if s["scheme_id"] == line)
    return next((r for r in s["annual"]["rows"] if r["year"] == y), None)


def test_2016_to_2023_are_elexons_record(figs):
    for y, v in ELEXON_AUDIT.items():
        assert abs(figs[f"constraints.{y}.cash"] / 1e6 - v) < 0.005, y


def test_1_0_0_held_lower_figures_for_those_years(frozen):
    for y, v in HELD_1_0_0.items():
        assert abs(_row(frozen, "constraints", y)["cost_gbp"] / 1e6 - v) < 0.005, y


def test_2010_to_2015_are_not_elexons_and_are_named(figs):
    """Elexon holds no whole year before 2016. From 1.5.0 those years are National Grid's record
    (tests/test_national_grid_constraints.py)."""
    assert figs["constraints.national_grid_years"] == "2010,2011,2012,2013,2014,2015"


def test_the_three_balancing_lines_still_add_to_the_same_total_each_year(frozen, figs):
    """The three are one measured total split three ways (the charge above the gas-led alternative's), so a
    higher constraint figure comes out of the other two, as 1.0.0's own split rule takes it."""
    for y in range(2010, 2025):
        for m, col in (("cash", "cost_gbp"), ("real", "cost_gbp_2024")):
            before = sum((_row(frozen, line, y) or {col: 0.0})[col] for line in BALANCING)
            after = sum(figs.get(f"{line}.{y}.{m}", 0.0) for line in BALANCING)
            assert math.isclose(before, after, rel_tol=1e-12, abs_tol=1e-3), (y, m)


def test_turn_up_stays_capped_and_bsuos_takes_the_rest(figs):
    # 2018: turn-up is capped at the uplift in 1.0.0 (BSUoS nil), so the higher constraint figure comes out of
    # turn-up; in the other years the cap does not bind and BSUoS takes it
    assert figs["bsuos.2018.cash"] == 0.0
    assert abs((figs["constraint_turnup.2018.cash"] + figs["constraints.2018.cash"]) / 1e6 - (53.38 + 124.65)) < 0.01
    for y in (2016, 2017, 2019, 2020, 2021, 2022, 2023):
        assert figs[f"constraint_turnup.{y}.cash"] > 0


def test_the_headline_does_not_move_and_money_moves_from_indirect_to_direct(frozen, figs):
    old = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.1.0:results/figures.json"],
                                    capture_output=True, check=True).stdout)["figures"]
    for m in ("cash", "real"):
        assert math.isclose(figs[f"all.headline.{m}"], old[f"all.headline.{m}"], rel_tol=1e-13)
        moved = figs[f"direct.headline.{m}"] - old[f"direct.headline.{m}"]
        assert math.isclose(moved, old[f"indirect.headline.{m}"] - figs[f"indirect.headline.{m}"], rel_tol=1e-9)
    # Elexon's years: £34.8m more than 1.1.0 held for 2016-2023
    assert abs(sum(figs[f"constraints.{y}.cash"] - old[f"constraints.{y}.cash"] for y in ELEXON_AUDIT) / 1e6
               - 34.8) < 0.05


def test_no_other_1_1_0_value_moves(figs):
    """Every 1.1.0 key is kept, and the only values that move are the replaced years and their sums: the
    three balancing lines 2016-2023, their headlines, the direct and indirect totals, turn-up's range where the cap
    at the balancing uplift binds (2018 both ends, 2022 the high) and its headline, and the turn-up cross-check's
    whole-window estimate. The bridge's balancing step stays zero (it moves by under a millionth of a penny)."""
    old = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.1.0:results/figures.json"],
                                    capture_output=True, check=True).stdout)["figures"]
    from tests.v1_5_0 import kept
    old = kept(old)    # less what 1.5.0 drops or moves (tests/test_national_grid_constraints.py)
    assert set(old) <= set(figs)
    allowed = {f"{line}.{y}.{m}" for line in BALANCING for y in range(2016, 2024) for m in ("cash", "real")}
    allowed |= {f"{line}.headline.{m}" for line in BALANCING + ("direct", "indirect") for m in ("cash", "real")}
    allowed |= {f"{t}.{y}.{m}" for t in ("direct", "indirect") for y in range(2016, 2024) for m in ("cash", "real")}
    allowed |= {f"constraint_turnup.range.{b}.{k}.{m}" for b in ("low", "high") for k in ("2018", "headline")
                for m in ("cash", "real")}
    allowed |= {f"constraint_turnup.range.high.2022.{m}" for m in ("cash", "real")}
    allowed |= {"constraint_turnup.cross_check.estimate.cash"}
    moved = {k for k in old if old[k] != figs[k] and not (isinstance(old[k], float) and math.isclose(
        old[k], figs[k], rel_tol=1e-14, abs_tol=1e-3 if k.startswith("bridge.balancing.") else 0.0))}
    assert moved <= allowed, sorted(moved - allowed)
    assert all(math.isclose(old[k], figs[k], rel_tol=1e-13) for k in ("all.headline.real", "all.headline.cash"))


def test_elexons_saved_answers_show_its_record_starts_on_6_november_2015():
    """The API answers saved and pinned (reference/outline_sources.yaml): nothing for 2012, 2014, mid-2015 or the
    last period of 5 Nov 2015, in the settlement stacks, acceptances, bid-offer data or cashflows; accepted bids on
    6 Nov 2015."""
    from billpaid import outline_sources as src
    for name in ("stack-bid-2012-02-01-p36", "stack-bid-2015-11-05-p48", "boalf-2014-06-01",
                 "bod-2014-06-01-1000", "cashflow-bid-2015-06-01"):
        assert json.loads(src.source(ROOT, f"elexon-{name}"))["data"] == [], name
    first = json.loads(src.source(ROOT, "elexon-stack-bid-2015-11-06-p48"))["data"]
    assert first and all(r["settlementDate"] == "2015-11-06" for r in first)
