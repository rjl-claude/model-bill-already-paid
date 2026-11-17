"""Version 1.2.0 (Report No. 2's plan step 19, aios-harness#235): the figures the approved outline asks of the bill
already paid (outline-beats.md, "Missing figures", M1 to M9 but M11), in the paper's figures file.

Expected values come from 1.1.0's own keys and the outline's rulings (ADR 0007, 0025, 0027, 0232, 0233, 0234), or
from the publishers' files read here by hand, never from the keys' code."""
import math
import re

import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT

YEARS = range(2002, 2025)
MEASURED = ("cfd_renewable", "constraints", "ro", "fit", "ccl")


@pytest.fixture(scope="module")
def figs():
    return figures.build(figures.frozen_results(ROOT), bridge.no1_release(ROOT))


def _close(a, b, rel=1e-12):
    return math.isclose(a, b, rel_tol=rel, abs_tol=1e-3)


def test_m1_the_headline_in_its_measured_modelled_and_estimated_parts(figs):
    for m in ("real", "cash"):
        parts = [figs[f"all.headline.{b}.{m}"] for b in ("measured", "modelled", "estimated")]
        assert _close(sum(parts), figs[f"all.headline.{m}"])
        # measured: the direct lines and the Climate Change Levy, every year (the outline's §1.1 beat)
        assert _close(parts[0], figs[f"direct.headline.{m}"] + figs[f"ccl.headline.{m}"])
        # estimated: turn-up, and carbon in 2005-2012 (labelled estimated inside a modelled line)
        carbon_est = sum(figs[f"carbon.{y}.{m}"] for y in range(2005, 2013))
        assert _close(parts[2], figs[f"constraint_turnup.headline.{m}"] + carbon_est)
    assert round(figs["all.headline.measured.real"] / 1e9, 1) == 144.5


def test_m2_the_headline_range_from_the_three_estimated_lines_each_changed_on_its_own(figs):
    """ADR 0234, choice 2: carbon's early prices, the turn-up order and the Capacity Market's low share, each
    changed alone; the whole Capacity Market levy is a counting option, not the top of the range. The outline
    questions gave about £247.7bn to £257.8bn, early carbon prices setting both ends. From 1.4.0 (rulings 13b and
    14c) turn-up is out and the carbon pass-through sets both ends (tests/test_version_1_4_0.py); the carbon
    price bracket alone still gives 1.3.1's ends."""
    for m in ("real", "cash"):
        lo = figs[f"all.headline.{m}"] + figs[f"carbon.range.low.headline.{m}"] - figs[f"carbon.headline.{m}"]
        hi = figs[f"all.headline.{m}"] + figs[f"carbon.range.high.headline.{m}"] - figs[f"carbon.headline.{m}"]
        if m == "real":
            assert round(lo / 1e9, 1) == 247.7 and round(hi / 1e9, 1) == 257.8
        # the Capacity Market's low share, changed alone, moves the headline less than early carbon prices
        assert figs[f"capacity_market.range.low.headline.{m}"] - figs[f"capacity_market.headline.{m}"] > (
            lo - figs[f"all.headline.{m}"])
    assert hi < figs["all.headline.real"] + (
        figs["capacity_market.raw.headline.real"] - figs["capacity_market.headline.real"])


# ONS, Families and households in the UK: 2025 (published 17 Apr 2026), Table 5, "All households" (thousands),
# read by hand from the saved workbook, 11 Nov 2026
ONS_HOUSEHOLDS_K = {2002: 24792, 2010: 26240, 2015: 27046, 2020: 27893, 2024: 28609, 2025: 29003}
# Great Britain, ONS Labour Force Survey (April-June), England + Wales + Scotland, read by hand: 2015 on from
# "Households by household size, regions of England and GB constituent countries" 2025; before 2015 from ONS ad hoc
# 005374 (to the nearest hundred)
GB_HOUSEHOLDS = {2005: 21_036_500 + 1_234_300 + 2_271_100, 2015: (22587 + 1326 + 2376) * 1000,
                 2024: (23957 + 1342 + 2568) * 1000, 2025: (24329 + 1404 + 2520) * 1000}
UK_WIDE = ("ro", "ccl")    # ADR 0232: the RO and the CCL run across the UK; every other line in Great Britain


def test_m3_households_each_year_in_both_areas(figs):
    """ADR 0027 (year-matched, ONS) and Richard's ruling of 11 Nov 2026 (report-series ADR 0242): both series as
    keys; `households.<year>` is Great Britain's."""
    for y, k in ONS_HOUSEHOLDS_K.items():
        assert figs[f"households.uk.{y}"] == k * 1000
    for y, v in GB_HOUSEHOLDS.items():
        assert figs[f"households.gb.{y}"] == v
        assert figs[f"households.{y}"] == v
    assert all(f"households.gb.{y}" in figs and f"households.uk.{y}" in figs for y in range(2002, 2026))
    assert all(0.96 < figs[f"households.gb.{y}"] / figs[f"households.uk.{y}"] < 0.985 for y in range(2002, 2026))


def _vat_on(figs, y, v):
    return 0.05 * figs[f"vat.domestic_share.{y}"] * v


def test_m3_money_paid_per_household_each_line_over_its_own_area(figs):
    """ADR 0242: each line over the households of its own area, its VAT with it, then added up: what a household
    in Great Britain paid."""
    for y in (2005, 2016, 2024, 2025):
        lines = [k.split(".")[0] for k in figs if re.fullmatch(rf"[a-z_]+\.{y}\.real", k)
                 and k.split(".")[0] in LINES]
        gb = sum(figs[f"{l}.{y}.real"] for l in lines if l not in UK_WIDE + ("vat",))
        uk = sum(figs.get(f"{l}.{y}.real", 0.0) for l in UK_WIDE)
        vat_uk = _vat_on(figs, y, figs[f"ro.{y}.real"])
        vat_gb = figs[f"vat.{y}.real"] - vat_uk
        expect = (gb + vat_gb) / figs[f"households.gb.{y}"] + (uk + vat_uk) / figs[f"households.uk.{y}"]
        assert _close(figs[f"per_household.{y}.real"], expect, rel=1e-9), y
        # it sits between the whole over UK households and the whole over GB households
        assert figs[f"all.{y}.real"] / figs[f"households.uk.{y}"] < figs[f"per_household.{y}.real"] \
            < figs[f"all.{y}.real"] / figs[f"households.gb.{y}"]
    assert _close(figs["per_household.year_by_year.headline.real"],
                  sum(figs[f"per_household.{y}.real"] for y in YEARS))
    # 1.1.0's figure over today's UK households (29 million) stays as it was, beside it
    assert figs["per_household.headline"] == figs["all.headline.real"] / 29_000_000


def test_m4_what_an_average_household_paid_on_its_own_bills(figs):
    """ADR 0025 with ADR 0242: households' share of every line but the CCL, plus the VAT on it, each over its own
    area's households. In cash, VAT is 5% of households' share, so each area's part is 21 times its VAT (1 + 1/0.05);
    in 2024 prices the two differ by under 0.5% (the RO and FiT are priced by obligation year)."""
    for y in (2010, 2024, 2025):
        vat_uk = _vat_on(figs, y, figs[f"ro.{y}.real"])
        approx = 21 * ((figs[f"vat.{y}.real"] - vat_uk) / figs[f"households.gb.{y}"]
                       + vat_uk / figs[f"households.uk.{y}"])
        assert _close(figs[f"own_bills.per_household.{y}.real"], approx, rel=5e-3), y
    assert _close(figs["own_bills.per_household.headline.real"],
                  sum(figs[f"own_bills.per_household.{y}.real"] for y in YEARS))
    assert figs["own_bills.per_household.headline.real"] < figs["per_household.year_by_year.headline.real"] / 2


LINES = ("cfd_renewable", "constraints", "ro", "fit", "capacity_market", "carbon", "ccl", "tnuos", "bsuos",
         "constraint_turnup", "vat", "sizewell_c")


def test_m5_the_whole_2025_bill_and_the_share_of_it(figs):
    # DUKES 2026, Table 1.3.A, "of which electricity", 2025: £65,071m (reference/electricity_bill.yaml)
    assert figs["bill.2025.cash"] == 65_071_000_000
    assert figs["bill.2025.real"] < figs["bill.2025.cash"]          # 2025 money, priced back to 2024
    assert _close(figs["share_of_bill.2025"], figs["all.2025.real"] / figs["bill.2025.real"])


# HMRC, Climate Change Levy historical rates, Table 1, electricity main rate from 1 April of the year, £/kWh,
# read by hand from the saved page (reference/sources/hmrc-envtax-historical-rates.html)
CCL_RATE = {2001: 0.0043, 2007: 0.00441, 2008: 0.00456, 2009: 0.00470, 2011: 0.00485, 2012: 0.00509,
            2013: 0.00524, 2014: 0.00541, 2015: 0.00554, 2016: 0.00559, 2017: 0.00568, 2018: 0.00583,
            2019: 0.00847, 2020: 0.00811, 2021: 0.00775}


def _rate(y):
    return CCL_RATE[max(k for k in CCL_RATE if k <= y)]


def test_m6_the_headline_under_each_counting_option(figs):
    head = figs["all.headline.real"]
    vat_share = lambda y: 0.05 * figs[f"vat.domestic_share.{y}"]
    # carbon: tax collected only, and none; VAT goes with the carbon not counted
    rest = sum(figs[f"carbon.rest_in_price.{y}.real"] * (1 + vat_share(y)) for y in YEARS)
    assert _close(figs["option.carbon_tax_only.headline.real"], head - rest)
    whole = sum(figs[f"carbon.{y}.real"] * (1 + vat_share(y)) for y in YEARS)
    assert _close(figs["option.no_carbon.headline.real"], head - whole)
    # the CCL: none, and only what is above its 2001 rate (no VAT is counted on the CCL)
    assert _close(figs["option.no_ccl.headline.real"], head - figs["ccl.headline.real"])
    at_2001 = sum(figs[f"ccl.{y}.real"] * 0.0043 / (0.25 * _rate(y - 1) + 0.75 * _rate(y)) for y in YEARS)
    assert _close(figs["option.ccl_above_2001.headline.real"], head - at_2001)
    assert figs["option.ccl_above_2001.headline.real"] - figs["option.no_ccl.headline.real"] < figs["ccl.headline.real"]
    # grid and balancing whole: the charges as paid, not above the gas-led alternative's
    extra = sum((figs[f"tnuos.alternative.{y}.real"] + figs[f"bsuos.alternative.{y}.real"]) * (1 + vat_share(y))
                for y in YEARS)
    assert _close(figs["option.grid_whole.headline.real"], head + extra)
    # the whole Capacity Market levy in place of the part net zero caused
    cm = sum((figs.get(f"capacity_market.raw.{y}.real", 0.0) - figs.get(f"capacity_market.{y}.real", 0.0))
             * (1 + vat_share(y)) for y in YEARS)
    assert _close(figs["option.cm_whole_levy.headline.real"], head + cm)
    # above the top of 1.3.1's range (early carbon prices; from 1.4.0 the pass-through sets a higher top)
    assert figs["option.cm_whole_levy.headline.real"] > (
        head + figs["carbon.range.high.headline.real"] - figs["carbon.headline.real"] - 1e9)


def test_m6f_suppliers_energy_saving_schemes_beside_the_figure(figs):
    """ADR 0233: left out, their size shown. The size is the schemes' cost on electricity bills as Report No. 1's
    pinned release holds it (EEC to GBIS, the lower end of each range), gross: No. 1's own line nets off the 2001
    scheme's level, which a gross count does not. Households pay them all, so VAT is on the whole."""
    import json
    run = json.loads((ROOT / "reference/engine/v4-s43-run.json").read_text())
    gross = {}
    for y in YEARS:
        nz10 = next(r for r in run["bills"][str(y)]["netzero"] if r["id"] == "NZ10")["national_gbp_m_nominal"]
        gross[y] = (nz10 + run["on_the_road"]["years"][str(y)]["nz10_on_the_road_gbp_m"]) * 1e6
    assert _close(figs["energy_saving_schemes.headline.cash"], sum(gross.values()))
    assert round(figs["energy_saving_schemes.2002.cash"] / 1e6) == 43        # No. 1: "EEC 43"
    assert round(figs["energy_saving_schemes.2024.cash"] / 1e6) == 762       # "ECO 566, GBIS 195"
    assert figs["energy_saving_schemes.basis"] == "estimated"
    assert _close(figs["option.energy_saving_schemes.headline.real"],
                  figs["all.headline.real"] + 1.05 * figs["energy_saving_schemes.headline.real"])


CFD_TECHS = ("offshore_wind", "biomass_conversion", "dedicated_biomass", "onshore_wind",
             "advanced_conversion_technology", "energy_from_waste", "solar_pv")


def test_m8_cfd_by_technology_2016_to_2024_in_2024_prices(figs):
    """LCCC's payments contract by contract, from the snapshot the frozen file was built from, by technology
    and calendar year: the technologies add up to the CfD line, which 1.0.0 takes from the same payments."""
    for m in ("real", "cash"):
        techs = sum(figs[f"cfd_renewable.by_technology.{t}.headline.{m}"] for t in CFD_TECHS)
        assert abs(techs - figs[f"cfd_renewable.headline.{m}"]) < 10.0, m
        assert _close(figs[f"cfd_renewable.by_technology.all.headline.{m}"], techs)
    share = figs["cfd_renewable.by_technology.offshore_wind.headline.real"] / figs["cfd_renewable.headline.real"]
    assert 0.6 < share < 0.9


def test_m6f_the_energy_saving_schemes_line_has_its_range(figs):
    """ADR 0007: an estimate carries its range. Report No. 1's lower and upper ends of each scheme, as the pinned
    shared cost register holds them (ENERGY_SAVING, low_gbp_m and high_gbp_m; the central is the lower end): 2002
    £42.5m to £70.5m and 2024 £761.6m both ends (read by hand from the register)."""
    k = "energy_saving_schemes.range"
    assert abs(figs[f"{k}.low.2002.cash"] / 1e6 - 42.544) < 0.001
    assert abs(figs[f"{k}.high.2002.cash"] / 1e6 - 70.491) < 0.001
    assert abs(figs[f"{k}.high.2024.cash"] / 1e6 - 761.646) < 0.001
    for y in YEARS:
        assert figs[f"{k}.low.{y}.cash"] == pytest.approx(figs[f"energy_saving_schemes.{y}.cash"], rel=1e-12)
        assert figs[f"{k}.low.{y}.cash"] <= figs[f"{k}.high.{y}.cash"]
    for m in ("real", "cash"):
        assert _close(figs[f"{k}.high.headline.{m}"], sum(figs[f"{k}.high.{y}.{m}"] for y in YEARS))
        assert figs[f"{k}.low.headline.{m}"] < figs[f"{k}.high.headline.{m}"]


def test_only_the_ruled_values_move_from_1_2_0(figs):
    """1.3.0 moves only what ADR 0242 (households) and the like-for-like OBR check change; every 1.2.0 key is kept."""
    import json
    import subprocess
    old = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.2.0:results/figures.json"],
                                    capture_output=True, check=True).stdout)["figures"]
    assert set(old) <= set(figs)
    ruled = re.compile(r"households\.\d{4}|(own_bills\.)?per_household\.(\d{4}\.real|year_by_year\.headline\.real|"
                       r"headline\.real)|check\.obr\.levies\..*"
                       r"|range\.(low|high)\.headline\.(real|cash|line)")   # and 1.4.0's rulings 13b, 14c
    moved = [k for k in old if old[k] != figs[k] and not (isinstance(old[k], float)
                                                           and math.isclose(old[k], figs[k], rel_tol=1e-13))]
    assert moved and all(ruled.fullmatch(k) for k in moved), [k for k in moved if not ruled.fullmatch(k)]
