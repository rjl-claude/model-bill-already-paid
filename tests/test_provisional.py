"""2025, the provisional year (version 1.1.0, part 3, aios-harness#224; ADR 0226): every line's 2025 figure in
the paper's figures file, the five lines 1.0.0 holds no 2025 for filled from their published 2025 figures, the
Sizewell C levy from 1 Dec 2025 on its own line, and the 2025 total with its parts.

Expected values come from the sources themselves (the frozen file, the shared cost register's rows, No. 1's run
file, Ofgem's and LCCC's published figures), never from the code under test."""
import math

import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT


@pytest.fixture(scope="module")
def frozen():
    return figures.frozen_results(ROOT)


@pytest.fixture(scope="module")
def figs(frozen):
    return figures.build(frozen, bridge.no1_release(ROOT))


def _schemes(doc):
    return {s["scheme_id"]: s for s in doc["model"]["schemes"]}


def _row(doc, line, year):
    return next(r for r in _schemes(doc)[line]["annual"]["rows"] if r["year"] == year)


# 1.0.0 holds the whole of 2025 for these lines (their data run into 2026)
WHOLE_2025 = ("cfd_renewable", "constraints", "capacity_market", "constraint_turnup", "bsuos")


def test_lines_1_0_0_holds_for_all_of_2025_carry_their_1_0_0_value(frozen, figs):
    for line in WHOLE_2025:
        r = _row(frozen, line, 2025)
        assert figs[f"{line}.2025.real"] == r["cost_gbp_2024"], line
        assert figs[f"{line}.2025.cash"] == r["cost_gbp"], line


CPIH = {2024: 132.9, 2025: 138.0, 2026: 141.83333333333334}   # the frozen file's deflators (ONS L522)


def _real_calendar(cash):
    return cash * CPIH[2024] / CPIH[2025]


def _real_obligation_year(cash):
    # an April-March year: three quarters at 2025's index, one at 2026's (1.0.0's rule, aios-harness#57)
    return cash * CPIH[2024] * (0.75 / CPIH[2025] + 0.25 / CPIH[2026])


def test_ccl_and_fit_2025_are_the_shared_cost_registers_published_figures(figs):
    # register v4-s43 rows: CCL_ELEC 2025 (HMRC Environmental Taxes Bulletin, 31 Mar 2026, Table 1b, provisional)
    # and FIT 2025 (Ofgem FiT quarterly reports 61-64, the four levelisations of 2025-26)
    assert math.isclose(figs["ccl.2025.cash"], 796.21998385e6, rel_tol=1e-12)
    assert math.isclose(figs["fit.2025.cash"], 1877.58410655e6, rel_tol=1e-12)
    assert math.isclose(figs["ccl.2025.real"], _real_calendar(796.21998385e6), rel_tol=1e-12)
    assert math.isclose(figs["fit.2025.real"], _real_obligation_year(1877.58410655e6), rel_tol=1e-12)


def test_the_register_reading_gives_1_0_0s_figure_in_every_closed_year(frozen):
    from billpaid import provisional
    for line in ("ro", "fit", "ccl"):
        read = provisional.register_line(ROOT, line)
        for r in _schemes(frozen)[line]["annual"]["rows"]:
            if r["year"] <= 2024:
                assert math.isclose(read[r["year"]], r["cost_gbp"], rel_tol=1e-12, abs_tol=1e-3), (line, r["year"])


def test_ro_2025_is_ofgems_published_outturn_for_2025_26(figs):
    # Ofgem, "Renewables Obligation Certificates presented and Redistribution of Buy-Out Funds 2025 to 2026"
    # (2 Nov 2026), UK total: 109,924,800 ROCs presented, buy-out price £67.06, £574,621,217 redistributed.
    # Ofgem's scheme value is ROCs presented x (buy-out price + recycle value): 7,371,557,088 + 574,621,217.
    assert figs["ro.2025.cash"] == 7_946_178_305
    assert math.isclose(figs["ro.2025.real"], _real_obligation_year(7_946_178_305), rel_tol=1e-12)


def test_the_ro_reading_on_2024_25_gives_ofgems_stated_scheme_value(frozen):
    # the same page for 2024-25 (12 Nov 2025): 105,852,239 x £64.73 + £844,086,312 = £7,695,901,742.47, against
    # 1.0.0's 2024, Ofgem's own SY23 scheme value to the pound (£7,706,343,000, the register's RO row): £10.4m
    # (0.14%) apart, £7.4m of it the late-payment fund (redistributed 9 Dec 2025), which for 2025-26 is not yet
    # paid out, so the 2025 reading runs low by about that much
    from billpaid import provisional
    assert math.isclose(provisional.ro_outturn(ROOT, "2024-25"), 7_695_901_742.47, rel_tol=1e-12)
    assert abs(7_695_901_742.47 / _row(frozen, "ro", 2024)["cost_gbp"] - 1) < 0.002


def test_a_saved_source_whose_fingerprint_differs_is_refused(tmp_path):
    from billpaid import provisional
    (tmp_path / "reference" / "sources").mkdir(parents=True)
    (tmp_path / "reference" / "provisional_2025.yaml").write_bytes(
        (ROOT / "reference" / "provisional_2025.yaml").read_bytes())
    page = (ROOT / "reference" / "sources" / "ofgem-ro-rocs-presented-buy-out-2025-26.html").read_bytes()
    (tmp_path / "reference" / "sources" / "ofgem-ro-rocs-presented-buy-out-2025-26.html").write_bytes(
        page.replace(b"109,924,800", b"119,924,800"))
    with pytest.raises(ValueError, match="sha256"):
        provisional.ro_outturn(tmp_path, "2025-26")


def test_carbon_2025_is_no1s_provisional_2025_from_its_pinned_release(figs):
    # the v4-s43 run file, carbon_crosscheck 2025 (= bills 2025 NZ1c, GB): carbon in the wholesale price
    # £6,860.6m, of which £1,328.0m collected as tax on power (CPS about £428m, decision 0054; UK ETS auctions
    # on power from ICE report 278, 0079), both provisional in No. 1's release
    assert math.isclose(figs["carbon.2025.cash"], 6860.596264116731e6, rel_tol=1e-12)
    assert math.isclose(figs["carbon.2025.real"], _real_calendar(6860.596264116731e6), rel_tol=1e-12)
    assert math.isclose(figs["carbon.tax_collected.2025.cash"], 1328.028364803115e6, rel_tol=1e-12)
    assert math.isclose(figs["carbon.tax_collected.2025.cash"] + figs["carbon.rest_in_price.2025.cash"],
                        figs["carbon.2025.cash"], rel_tol=1e-12)
    assert math.isclose(figs["carbon.tax_collected.2025.real"] + figs["carbon.rest_in_price.2025.real"],
                        figs["carbon.2025.real"], rel_tol=1e-12)


def test_tnuos_2025_is_the_published_charge_above_no1s_gas_led_alternative(figs):
    # register v4-s43, TNUOS 2025 (NESO final TNUoS reports 2024-25 and 2025-26, calendarised) £4,862.375m, less
    # the generators' share (rb.TNUOS.generators_share_out 2025, -£1,111.503m, 0024); the alternative is the run
    # file's 2025 GO5, generators' share removed, £1,878.839m
    raw, alt = (4862.375 - 1111.5026648984158) * 1e6, 1878.8393989736628e6
    assert math.isclose(figs["tnuos.raw.2025.cash"], raw, rel_tol=1e-12)
    assert math.isclose(figs["tnuos.alternative.2025.cash"], alt, rel_tol=1e-12)
    assert math.isclose(figs["tnuos.2025.cash"], raw - alt, rel_tol=1e-12)
    assert math.isclose(figs["tnuos.2025.real"], _real_calendar(raw - alt), rel_tol=1e-12)
    assert figs["tnuos.alternative.2025.basis"] == "modelled"


def test_the_tnuos_reading_gives_1_0_0s_charge_and_alternative_in_every_closed_year(frozen):
    from billpaid import provisional
    t = _schemes(frozen)["tnuos"]["extras"]
    raw, alt = provisional.tnuos_parts(ROOT)
    for r in t["raw_annual"]:
        assert math.isclose(raw[r["year"]], r["cost"], rel_tol=1e-12, abs_tol=1e-3), r["year"]
    for r in t["road_annual"]:
        assert math.isclose(alt[r["year"]], r["cost"], rel_tol=1e-12, abs_tol=1e-3), r["year"]


def test_sizewell_c_2025_is_what_suppliers_paid_lccc_for_december_2025(figs):
    # LCCC data portal, Actual Nuclear RAB ILR/TRA, Month 2025-12-01: Actual_Supplier_Payments_GBP 85,356,015.37
    # (the levy began on 1 Dec 2025; interim levy rate £3.494/MWh on 24,429,311.73 MWh of eligible demand)
    assert figs["sizewell_c.2025.cash"] == 85_356_015.37
    assert math.isclose(figs["sizewell_c.2025.real"], _real_calendar(85_356_015.37), rel_tol=1e-12)
    assert figs["sizewell_c.layer"] == "direct"
    assert figs["sizewell_c.basis"] == "measured"
    assert "sizewell_c.headline.real" not in figs   # no levy before 1 Dec 2025: not in the 2002-2024 headline


FILLED = ("ro", "fit", "carbon", "tnuos", "sizewell_c")   # the base lines 1.0.0's VAT 2025 had no figure for


def test_vat_2025_adds_vat_on_the_filled_lines_to_1_0_0s_vat_on_the_rest(frozen, figs):
    # 1.0.0's VAT 2025 is 5% of households' share (the engine's 2025 share, 0.36546) of the lines it had a 2025
    # figure for; the filled lines (CCL apart, which households do not pay) add their own 5% of that share
    share = 0.3654581713770123
    base = _row(frozen, "vat", 2025)["cost_gbp"]
    # 1.6.0: and the generators' share of grid and balancing charges (ADR 0264), a new line with 2025 in it
    added = 0.05 * share * sum(figs[f"{line}.2025.cash"] for line in (*FILLED, "generators_share"))
    assert math.isclose(figs["vat.2025.cash"], base + added, rel_tol=1e-12)
    assert math.isclose(figs["vat.2025.real"], _real_calendar(base + added), rel_tol=1e-12)
    assert figs["vat.domestic_share.2025"] == share


def test_the_vat_rule_gives_1_0_0s_vat_in_every_closed_year(frozen, figs):
    from billpaid import provisional
    base = _schemes(frozen)["vat"]["extras"]["base_lines"]
    for y in range(2002, 2025):
        lines = {line: figs[f"{line}.{y}.cash"] for line in base if f"{line}.{y}.cash" in figs}
        assert math.isclose(provisional.vat(lines, figs[f"vat.domestic_share.{y}"]), _row(frozen, "vat", y)["cost_gbp"],
                            rel_tol=1e-9, abs_tol=1e-3), y


DIRECT = ("cfd_renewable", "constraints", "ro", "fit", "sizewell_c")
INDIRECT = ("ccl", "capacity_market", "carbon", "tnuos", "bsuos", "constraint_turnup", "vat",
            "generators_share")   # generators_share: 1.6.0


def test_the_2025_total_and_its_measured_modelled_and_estimated_parts(frozen, figs):
    for m in ("real", "cash"):
        direct = sum(figs[f"{line}.2025.{m}"] for line in DIRECT)
        indirect = sum(figs[f"{line}.2025.{m}"] for line in INDIRECT)
        assert math.isclose(figs[f"direct.2025.{m}"], direct, rel_tol=1e-12)
        assert math.isclose(figs[f"indirect.2025.{m}"], indirect, rel_tol=1e-12)
        assert math.isclose(figs[f"all.2025.{m}"], direct + indirect, rel_tol=1e-12)
        parts = {p: figs[f"all.2025.{p}.{m}"] for p in ("measured", "modelled", "estimated")}
        assert math.isclose(sum(parts.values()), figs[f"all.2025.{m}"], rel_tol=1e-12)
        # measured: payments as recorded; modelled: a share or alternative from No. 1's gas model; estimated:
        # constraint turn-up, the one line 1.0.0 itself calls an estimate. No line is carried forward.
        assert math.isclose(parts["measured"], sum(figs[f"{line}.2025.{m}"] for line in (*DIRECT, "ccl")),
                            rel_tol=1e-12)
        # 1.6.0: and the generators' share, estimated (ADR 0264)
        assert math.isclose(parts["estimated"], _row(frozen, "constraint_turnup", 2025)[
            "cost_gbp_2024" if m == "real" else "cost_gbp"] + figs[f"generators_share.2025.{m}"], rel_tol=1e-12)
    # 2025 stays out of the headline (ADR 0035, 0226): the 2002-2024 sum (1.6.1: £258.6bn with the generators' share)
    assert round(figs["all.headline.real"] / 1e9, 1) == 258.6


def test_each_2025_line_names_its_source(figs):
    for line in (*DIRECT, *INDIRECT):
        assert figs[f"{line}.2025.source"], line
    assert "Ofgem" in figs["ro.2025.source"] and "LCCC" in figs["sizewell_c.2025.source"]
    assert "provisional" in figs["carbon.2025.source"]
    assert figs["carbon.2025.basis"] == "modelled"


def test_the_figures_file_names_the_saved_sources_2025_reads(tmp_path):
    import json
    from billpaid.__main__ import main
    out = tmp_path / "figures.json"
    assert main(["figures", "--out", str(out)]) == 0
    meta = json.loads(out.read_text())["meta"]["provisional_2025"]
    assert meta["ofgem-ro-2025-26"]["sha256"] == "5f5c64da0dbca59e4bad6574b8aa6afbb9faa1e1c9c7a7f80022356f9faf9bf5"
    assert meta["lccc-nuclear-rab-actual"]["sha256"] == "022b6598b11dad66c5441aee9a4646bd936fe2226733fa9f0c5bc36e70a1ba82"
    assert meta["ofgem-ro-2025-26"]["url"].startswith("https://www.ofgem.gov.uk/")
