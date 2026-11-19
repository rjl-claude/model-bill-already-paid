"""Version 1.5.0 (aios-harness#266; Richard's rulings of 19 Nov 2026, "2 then 1" and "completely sever"): wind
switch-off (constraint) payments 2010-2015 from National Grid's own record, the Monthly Balancing Services Summary
(reference/mbss_wind_payments.yaml), and no input or cross-check from the earlier third-party database anywhere in
the model.

Expected values are worked here by hand from the printed figures, never taken from the model's code:
2014 and 2015 are the sums of their printed months; April-December 2013 likewise; the three April-March totals
before that (£0.2m, £34.1m, £7.6m) are spread a quarter to the calendar year they end in and three quarters to the
one they start in (the model's rule for April-March years, billpaid.calendar_years.fy_to_cy)."""
import json
import math
import re
import subprocess

import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT
from billpaid.reference import load_annual_costs

# £m cash
NATIONAL_GRID = {2010: 0.75 * 0.2,                       # 0.15
                 2011: 0.25 * 0.2 + 0.75 * 34.1,         # 25.625
                 2012: 0.25 * 34.1 + 0.75 * 7.6,         # 14.225
                 2013: 0.25 * 7.6 + 33.7,                # 35.6: January-March spread, April-December from months
                 2014: 57.0, 2015: 96.9}
BALANCING = ("constraints", "constraint_turnup", "bsuos")
OLD_NAME = re.compile(r"\bREF\b|Renewable Energy Foundation|(?i:ref\.org)")


@pytest.fixture(scope="module")
def frozen():
    return figures.frozen_results(ROOT)


@pytest.fixture(scope="module")
def figs(frozen):
    return figures.build(frozen, bridge.no1_release(ROOT))


@pytest.fixture(scope="module")
def old():
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.4.0:results/figures.json"],
                                     capture_output=True, check=True).stdout)["figures"]


def _row(doc, line, y):
    s = next(s for s in doc["model"]["schemes"] if s["scheme_id"] == line)
    return next((r for r in s["annual"]["rows"] if r["year"] == y), None)


def test_2010_to_2015_are_national_grids_record(figs):
    for y, v in NATIONAL_GRID.items():
        assert math.isclose(figs[f"constraints.{y}.cash"] / 1e6, v, abs_tol=1e-9), y
    assert math.isclose(sum(figs[f"constraints.{y}.cash"] for y in NATIONAL_GRID) / 1e6, 229.5, abs_tol=1e-9)


def test_the_years_and_the_spread_years_are_named(figs):
    assert figs["constraints.national_grid_years"] == "2010,2011,2012,2013,2014,2015"
    assert figs["constraints.spread_years"] == "2010,2011,2012,2013"
    assert figs["constraints.basis"] == "measured"
    # the four years' total is what National Grid printed; its split between them is estimated
    assert [figs.get(f"constraints.{y}.basis") for y in range(2010, 2017)] == ["estimated"] * 4 + [None] * 3


def test_the_reference_file_holds_primary_records_for_every_year_before_the_pin(frozen):
    """2010-2015 National Grid's record as billpaid.mbss makes it; 2016-2023 Elexon's own yearly sums from the
    store as the frozen file saw it. The pin, the first year of the daily Elexon feed, stays 2024."""
    from billpaid import elexon_record, mbss
    hist = load_annual_costs(ROOT / "reference/annual_scheme_costs.yaml")["constraints_history"]
    assert hist.bottom_up_from == 2024
    held = dict(zip(hist.annual["year"].to_list(), hist.annual["cost_gbp"].to_list()))
    assert sorted(held) == list(range(2010, 2024))
    for y, v in NATIONAL_GRID.items():
        assert math.isclose(held[y] / 1e6, v, abs_tol=1e-9), y
    assert {y: round(v) for y, v in mbss.calendar_years(ROOT).items()} == {y: round(held[y]) for y in NATIONAL_GRID}
    elexon = elexon_record.elexon_by_year(frozen, ROOT)
    for y in range(2016, 2024):
        assert held[y] == elexon[y][0], y


def test_the_three_balancing_lines_still_add_to_the_same_total_each_year(frozen, figs):
    for y in range(2010, 2025):
        for m, col in (("cash", "cost_gbp"), ("real", "cost_gbp_2024")):
            before = sum((_row(frozen, line, y) or {col: 0.0})[col] for line in BALANCING)
            after = sum(figs.get(f"{line}.{y}.{m}", 0.0) for line in BALANCING)
            assert math.isclose(before, after, rel_tol=1e-12, abs_tol=1e-3), (y, m)


def _gs(figs, m):
    """What 1.6.0's new line adds to the headline and the indirect layer: the generators' share and its VAT."""
    return figs[f"all.headline.{m}"] - figs[f"option.no_generators_share.headline.{m}"]


def test_the_headline_does_not_move(figs, old):
    """(1.6.0's new line apart, which adds to the indirect layer: tests/test_version_1_6_0.py)"""
    for m in ("cash", "real"):
        assert math.isclose(figs[f"all.headline.{m}"] - _gs(figs, m), old[f"all.headline.{m}"], rel_tol=1e-13)
        moved = figs[f"direct.headline.{m}"] - old[f"direct.headline.{m}"]
        assert math.isclose(moved, old[f"indirect.headline.{m}"] - figs[f"indirect.headline.{m}"] + _gs(figs, m),
                            rel_tol=1e-9)
    # £229.5m in place of the £195.63m 1.4.0 held for the six years
    assert abs((figs["direct.headline.cash"] - old["direct.headline.cash"]) / 1e6 - (229.5 - 195.631658)) < 1e-6


def test_2015_turn_up_stays_capped(figs, old):
    """2015: turn-up is capped at the balancing uplift (BSUoS nil), so the higher constraint figure comes out of
    turn-up, as in 2018 at 1.2.0."""
    assert figs["bsuos.2015.cash"] == 0.0
    assert math.isclose(figs["constraint_turnup.2015.cash"] + figs["constraints.2015.cash"],
                        old["constraint_turnup.2015.cash"] + old["constraints.2015.cash"], rel_tol=1e-12)


def test_no_other_1_4_0_value_moves_and_only_the_old_keys_go(figs, old):
    gone = set(old) - set(figs)
    assert gone == {"constraints.ref_years"} | {k for k in old if k.startswith("check.ref.")}
    years = range(2010, 2016)
    allowed = {f"{line}.{y}.{m}" for line in BALANCING for y in years for m in ("cash", "real")}
    allowed |= {f"{t}.{y}.{m}" for t in ("direct", "indirect") for y in years for m in ("cash", "real")}
    allowed |= {f"{line}.headline.{m}" for line in BALANCING + ("direct", "indirect") for m in ("cash", "real")}
    allowed |= {f"all.headline.{b}.{m}" for b in ("measured", "modelled", "estimated") for m in ("cash", "real")}
    allowed |= {k for k in old if k.startswith("constraint_turnup.range.") and (".2015." in k or ".headline." in k)}
    allowed |= {k for k in old if k.startswith("constraint_turnup.cross_check.estimate")}
    # the same money seen through 1.4.0's options: balancing with turn-up at its range, and the case without grid
    # and balancing
    allowed |= {k for k in old if k.startswith("bsuos.turnup_range.") and ".headline." in k}
    allowed |= {k for k in old if k.startswith("option.no_grid_balancing.")}
    from tests import v1_6_0
    allowed |= {k for k in old if v1_6_0.moved(k)}   # what 1.6.0's new line moves (tests/test_version_1_6_0.py)
    moved = {k for k in old if k in figs and old[k] != figs[k] and not (isinstance(old[k], float) and math.isclose(
        old[k], figs[k], rel_tol=1e-12, abs_tol=1e-3))}   # a thousandth of a pound: float dust around zero
    assert moved <= allowed, sorted(moved - allowed)


def test_no_key_and_no_working_file_names_the_old_database(figs):
    assert not [k for k in figs if k.startswith("check.ref") or "ref_years" in k]
    assert not [k for k, v in figs.items() if isinstance(v, str) and OLD_NAME.search(v)]
    for gone in ("reference/ref_totals.yaml", "reference/ref_crosscheck.yaml"):
        assert not (ROOT / gone).exists(), gone
    assert not list((ROOT / "reference/sources").glob("ref-*"))
    # clock_findings.yaml is a record of what the live Clock's old histories were: it stays as written
    files = [*(ROOT / "src/billpaid").rglob("*.py"),
             *(p for p in (ROOT / "reference").glob("*.yaml") if p.name != "clock_findings.yaml"),
             ROOT / "README.md", ROOT / "GLOSSARY.md", ROOT / "docs/figures.md"]
    named = [str(p.relative_to(ROOT)) for p in files if OLD_NAME.search(p.read_text())]
    assert named == []
