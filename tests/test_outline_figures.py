"""Version 1.2.0 (Report No. 2's plan step 19, aios-harness#235): the figures the approved outline asks of the bill
already paid (outline-beats.md, "Missing figures", M1 to M9 but M11), in the paper's figures file.

Expected values come from 1.1.0's own keys and the outline's rulings (ADR 0007, 0025, 0027, 0232, 0233, 0234), or
from the publishers' files read here by hand, never from the keys' code."""
import math

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
    questions gave about £247.7bn to £257.8bn, early carbon prices setting both ends."""
    assert round(figs["range.low.headline.real"] / 1e9, 1) == 247.7
    assert round(figs["range.high.headline.real"] / 1e9, 1) == 257.8
    assert figs["range.low.headline.line"] == figs["range.high.headline.line"] == "carbon"
    for m in ("real", "cash"):
        assert _close(figs[f"range.low.headline.{m}"], figs[f"all.headline.{m}"]
                      + figs[f"carbon.range.low.headline.{m}"] - figs[f"carbon.headline.{m}"])
        # each of the other two, changed alone, moves the headline less
        for line, lo in (("constraint_turnup", "constraint_turnup.range.low"),
                         ("capacity_market", "capacity_market.range.low")):
            assert figs[f"{lo}.headline.{m}"] - figs[f"{line}.headline.{m}"] > (
                figs[f"range.low.headline.{m}"] - figs[f"all.headline.{m}"])
    assert figs["range.high.headline.real"] < figs["all.headline.real"] + (
        figs["capacity_market.raw.headline.real"] - figs["capacity_market.headline.real"])


# ONS, Families and households in the UK: 2025 (published 17 Apr 2026), Table 5, "All households" (thousands),
# read by hand from the saved workbook, 11 Nov 2026
ONS_HOUSEHOLDS_K = {2002: 24792, 2010: 26240, 2015: 27046, 2020: 27893, 2024: 28609, 2025: 29003}


def test_m3_households_each_year_and_money_paid_per_household_year_by_year(figs):
    """ADR 0027 (year-matched, ONS) with ADR 0232 (each scheme over its own area, as the Clock: UK households)."""
    for y, k in ONS_HOUSEHOLDS_K.items():
        assert figs[f"households.{y}"] == k * 1000
    assert all(f"households.{y}" in figs for y in range(2002, 2026))
    for y in range(2002, 2026):
        assert _close(figs[f"per_household.{y}.real"], figs[f"all.{y}.real"] / figs[f"households.{y}"])
    assert _close(figs["per_household.year_by_year.headline.real"],
                  sum(figs[f"per_household.{y}.real"] for y in YEARS))
    # 1.1.0's figure over today's households stays as it was, beside it
    assert figs["per_household.headline"] == figs["all.headline.real"] / 29_000_000


def test_m4_what_an_average_household_paid_on_its_own_bills(figs):
    """ADR 0025: households' share of each line, the CCL left out (businesses only), plus 5% VAT on that part, over
    that year's households. VAT is itself 5% of households' share of those lines, so the own-bills figure is 21
    times the VAT line (1 + 1/0.05) each year in cash: an independent check on the sum. In 2024 prices it differs by
    under 0.5%, because the RO and FiT lines are priced by obligation year and the VAT line by calendar year."""
    for y in (2010, 2024, 2025):
        assert _close(figs[f"own_bills.per_household.{y}.real"],
                      21 * figs[f"vat.{y}.real"] / figs[f"households.{y}"], rel=5e-3), y
    assert _close(figs["own_bills.per_household.headline.real"],
                  sum(figs[f"own_bills.per_household.{y}.real"] for y in YEARS))
    assert figs["own_bills.per_household.headline.real"] < figs["per_household.year_by_year.headline.real"] / 2


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
    assert figs["option.cm_whole_levy.headline.real"] > figs["range.high.headline.real"] - 1e9


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
