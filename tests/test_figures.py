"""The paper's figures file (version 1.1.0, part 1, aios-harness#222): a flat file read by key, built from
the frozen 9 Nov 2026 results file, that adds keys and moves no 1.0.0 value.

Expected values come from the frozen file's own tables (the 1.0.0 values), never from the keys' code."""
import hashlib
import json
import math
import re

import pytest

from billpaid import bridge, figures
from billpaid import results
from billpaid.__main__ import ROOT, main

PINNED_SHA256 = "738ac005d5fca69015139cbf6857fa1cf87320c6e16a8a234fcdf1557f2f059b"  # model-register.yaml
LINES = ["cfd_renewable", "constraints", "ro", "fit", "capacity_market", "carbon", "ccl", "tnuos",
         "bsuos", "constraint_turnup", "vat"]


@pytest.fixture(scope="module")
def frozen():
    return figures.frozen_results(ROOT)


@pytest.fixture(scope="module")
def figs(frozen):
    return figures.build(frozen, bridge.no1_release(ROOT))


def _close(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-6)


def _schemes(doc):
    return {s["scheme_id"]: s for s in doc["model"]["schemes"]}


# 1.2.0 (aios-harness#235): Elexon's record for wind constraint payments 2016-2023; 1.5.0 (aios-harness#266):
# National Grid's for 2010-2015. The three balancing lines are split again; those cells are tested against the
# sources' own sums in tests/test_elexon_constraints.py and tests/test_national_grid_constraints.py. Every other
# 1.0.0 value stays as it was.
MOVED_LINES, MOVED_YEARS = ("constraints", "constraint_turnup", "bsuos"), range(2010, 2024)


def _moved(line, y):
    return line in MOVED_LINES and y in MOVED_YEARS


def _shift(frozen, figs, y, m):
    """What the constraint line moved in year y (£), which moves from the indirect layer to the direct."""
    if y not in MOVED_YEARS:
        return 0.0
    col = {"real": "cost_gbp_2024", "cash": "cost_gbp"}[m]
    old = next(r for r in _schemes(frozen)["constraints"]["annual"]["rows"] if r["year"] == y)[col]
    return figs[f"constraints.{y}.{m}"] - old


# 1.6.0 (report-series ADR 0264): a new indirect line, the generators' share of grid and balancing charges not paid
# out of subsidy, and 5% VAT on households' share of it. The line is tested in tests/test_generators_share.py; here
# the 1.0.0 totals and the VAT line are expected to move by exactly that much and no more.
def _added(figs, y, m):
    """What 1.6.0 adds to the indirect layer in year y (£): the line and the VAT on it."""
    return figs[f"generators_share.{y}.{m}"] * (1 + 0.05 * figs[f"vat.domestic_share.{y}"])


def _vat_added(figs, y, m):
    return 0.05 * figs[f"vat.domestic_share.{y}"] * figs[f"generators_share.{y}.{m}"]


def test_the_figures_are_built_from_the_file_the_paper_pins():
    data = figures.frozen_bytes(ROOT)
    assert hashlib.sha256(data).hexdigest() == PINNED_SHA256


def test_every_line_every_year_is_its_1_0_0_value_in_2024_prices_and_cash(frozen, figs):
    schemes = _schemes(frozen)
    assert sorted(schemes) == sorted(LINES)
    for line, s in schemes.items():
        for r in s["annual"]["rows"]:
            if r["year"] > figures.LAST_CLOSED_YEAR or _moved(line, r["year"]):
                continue
            if line == "vat":
                for m, col in (("real", "cost_gbp_2024"), ("cash", "cost_gbp")):
                    assert _close(figs[f"vat.{r['year']}.{m}"], r[col] + _vat_added(figs, r["year"], m))
                continue
            assert figs[f"{line}.{r['year']}.real"] == r["cost_gbp_2024"], (line, r["year"])
            assert figs[f"{line}.{r['year']}.cash"] == r["cost_gbp"], (line, r["year"])


def _table(block):
    return {r["year"]: r for r in block["annual"]["rows"] if r["year"] <= figures.LAST_CLOSED_YEAR}


def test_direct_and_indirect_by_year_are_the_1_0_0_totals(frozen, figs):
    direct = _table(frozen["model"]["perspectives"]["renewables"])
    indirect = _table(frozen["model"]["indirect"])
    assert sorted(direct) == sorted(indirect) == list(range(2002, 2025))
    for y in range(2002, 2025):
        for m, col in (("real", "cost_gbp_2024"), ("cash", "cost_gbp")):
            assert _close(figs[f"direct.{y}.{m}"], direct[y][col] + _shift(frozen, figs, y, m)), (y, m)
            assert _close(figs[f"indirect.{y}.{m}"], indirect[y][col] - _shift(frozen, figs, y, m)
                          + _added(figs, y, m)), (y, m)
            assert _close(figs[f"all.{y}.{m}"], direct[y][col] + indirect[y][col] + _added(figs, y, m)), (y, m)


def test_the_headlines_are_2002_to_2024_each_line_and_together(frozen, figs):
    for line, s in _schemes(frozen).items():
        for m, col in (("real", "cost_gbp_2024"), ("cash", "cost_gbp")):
            vat = (lambda y: _vat_added(figs, y, m)) if line == "vat" else (lambda y: 0.0)
            assert _close(figs[f"{line}.headline.{m}"],
                          sum(figs[f"{line}.{y}.{m}"] if _moved(line, y) else r[col] + vat(y)
                              for y, r in _table(s).items()))
    for m, col in (("real", "cost_gbp_2024"), ("cash", "cost_gbp")):
        shift = sum(_shift(frozen, figs, y, m) for y in MOVED_YEARS)
        direct = sum(r[col] for r in _table(frozen["model"]["perspectives"]["renewables"]).values()) + shift
        indirect = (sum(r[col] for r in _table(frozen["model"]["indirect"]).values()) - shift
                    + sum(_added(figs, y, m) for y in range(2002, 2025)))
        assert _close(figs[f"direct.headline.{m}"], direct)
        assert _close(figs[f"indirect.headline.{m}"], indirect)
        assert _close(figs[f"all.headline.{m}"], direct + indirect)


def test_the_2024_price_headline_is_the_worked_figure(figs):
    # summed from the 9 Nov file's two total tables, 2002-2024, 9 Nov 2026: direct £125.8bn + indirect £126.6bn
    # 1.5.0: £46.7m moves from indirect to direct (National Grid's record 2010-2015), so direct, £125.81bn at
    # 1.4.0, is £125.86bn and prints £125.9bn; indirect, £126.60bn, is £126.55bn and still prints £126.6bn
    assert round(figs["direct.headline.real"] / 1e9, 1) == 125.9
    # 1.6.1: the generators' share, £6.10bn, and its VAT, £0.11bn, join the indirect layer: £132.8bn and £258.6bn
    assert round(figs["indirect.headline.real"] / 1e9, 1) == 132.8
    assert round(figs["all.headline.real"] / 1e9, 1) == 258.6


def _cpih(doc):
    return {r["year"]: r["index"] for r in doc["deflators"]["rows"]}


def test_carbon_splits_into_tax_collected_and_the_rest_in_the_price_each_year(frozen, figs):
    carbon = _schemes(frozen)["carbon"]
    cpih, base = _cpih(frozen), _cpih(frozen)[2024]
    parts = {p["year"]: p for p in carbon["extras"]["parts"] if p["year"] <= 2024}
    assert sorted(parts) == list(range(2002, 2025))
    for y, p in parts.items():
        assert figs[f"carbon.tax_collected.{y}.cash"] == p["tax_collected"]
        assert figs[f"carbon.rest_in_price.{y}.cash"] == p["rest_of_carbon_in_price"]
        assert _close(figs[f"carbon.tax_collected.{y}.real"], p["tax_collected"] * base / cpih[y])
        assert _close(figs[f"carbon.tax_collected.{y}.real"] + figs[f"carbon.rest_in_price.{y}.real"],
                      figs[f"carbon.{y}.real"])
        assert figs[f"carbon.{y}.basis"] == p["basis"]
    for m in ("real", "cash"):
        assert _close(figs[f"carbon.tax_collected.headline.{m}"] + figs[f"carbon.rest_in_price.headline.{m}"],
                      figs[f"carbon.headline.{m}"])
    assert figs["carbon.2005.basis"] == "estimated" and figs["carbon.2013.basis"] == "modelled"


def test_grid_and_balancing_raw_and_the_gas_led_alternative_each_year(frozen, figs):
    S = _schemes(frozen)
    cpih, base = _cpih(frozen), _cpih(frozen)[2024]
    for line in ("tnuos", "bsuos"):
        raw = {r["year"]: r["cost"] for r in S[line]["extras"]["raw_annual"]}
        alt = {r["year"]: r["cost"] for r in S[line]["extras"]["road_annual"]}
        for y in range(2002, 2025):
            assert figs[f"{line}.raw.{y}.cash"] == raw[y]
            assert figs[f"{line}.alternative.{y}.cash"] == alt[y]
            assert _close(figs[f"{line}.raw.{y}.real"], raw[y] * base / cpih[y])
            assert _close(figs[f"{line}.alternative.{y}.real"], alt[y] * base / cpih[y])
            assert figs[f"{line}.alternative.{y}.basis"] == "modelled"
        for m in ("real", "cash"):
            assert _close(figs[f"{line}.raw.headline.{m}"] - figs[f"{line}.alternative.headline.{m}"],
                          sum(figs[f"{line}.raw.{y}.{m}"] - figs[f"{line}.alternative.{y}.{m}"]
                              for y in range(2002, 2025)))
    # 1.0.0's rules: TNUoS counts the raw charge above the alternative; BSUoS above the alternative is split
    # into wind constraint payments, constraint turn-up and the BSUoS line
    for y in range(2002, 2025):
        for m in ("real", "cash"):
            above = lambda line: figs[f"{line}.raw.{y}.{m}"] - figs[f"{line}.alternative.{y}.{m}"]
            assert _close(figs[f"tnuos.{y}.{m}"], above("tnuos")), (y, m)
            assert _close(figs[f"bsuos.{y}.{m}"] + figs[f"constraint_turnup.{y}.{m}"]
                          + figs.get(f"constraints.{y}.{m}", 0.0), above("bsuos")), (y, m)


def test_the_capacity_market_netzero_share_and_its_range(frozen, figs):
    cm = _schemes(frozen)["capacity_market"]
    cpih, base = _cpih(frozen), _cpih(frozen)[2024]
    raw = {r["year"]: r["cost"] for r in cm["extras"]["raw_annual"]}
    share = {r["year"]: r for r in cm["extras"]["netzero_share"]}
    # the rule, checked against 1.0.0's own range (every year it holds, to Aug 2026): each year's levy times
    # that year's low or high share, priced to 2024 by CPIH
    for end in ("low", "high"):
        band = {y: raw[y] * share[y][f"share_{end}"] for y in raw}
        assert _close(sum(band.values()), cm["extras"]["range"][end]["cumulative"])
        assert math.isclose(sum(v * base / cpih[y] for y, v in band.items()),
                            cm["extras"]["range"][end]["cumulative_real"], rel_tol=1e-9)
    for y in (y for y in raw if y <= 2024):
        assert figs[f"capacity_market.raw.{y}.cash"] == raw[y]
        assert _close(figs[f"capacity_market.{y}.cash"], raw[y] * share[y]["share"])
        for end, col in (("central", "share"), ("low", "share_low"), ("high", "share_high")):
            assert figs[f"capacity_market.netzero_share.{y}.{end}"] == share[y][col]
        for end in ("low", "high"):
            assert _close(figs[f"capacity_market.range.{end}.{y}.cash"], raw[y] * share[y][f"share_{end}"])
            assert _close(figs[f"capacity_market.range.{end}.{y}.real"],
                          raw[y] * share[y][f"share_{end}"] * base / cpih[y])
    lo, mid, hi = (figs[k] for k in ("capacity_market.range.low.headline.real", "capacity_market.headline.real",
                                     "capacity_market.range.high.headline.real"))
    assert lo <= mid <= hi


def test_vat_household_share_each_year(frozen, figs):
    vat = _schemes(frozen)["vat"]["extras"]
    for r in vat["domestic_share"]:
        if r["year"] <= 2024:
            assert figs[f"vat.domestic_share.{r['year']}"] == r["share"]
    assert figs["vat.rate"] == 0.05


def test_cfd_by_technology_to_the_data_end(frozen, figs):
    cfd = _schemes(frozen)["cfd_renewable"]
    techs = cfd["extras"]["by_technology"]
    assert figs["cfd_renewable.by_technology.offshore_wind.cash"] == techs[0]["cost"]
    assert figs["cfd_renewable.by_technology.offshore_wind.mwh"] == techs[0]["generation_mwh"]
    assert figs["cfd_renewable.by_technology.solar_pv.cash"] < 0
    keys = [k for k in figs if k.startswith("cfd_renewable.by_technology.") and k.endswith(".share")]
    assert len(keys) == len(techs) == 7
    assert _close(sum(figs[k] for k in keys), 1.0)
    # 1.0.0's technologies add up to its CfD total to the data's end (27 Oct 2026), to the penny
    assert abs(figs["cfd_renewable.by_technology.all.cash"] - cfd["cumulative_gbp"]) < 1.0


def test_the_turn_up_cross_check_and_the_cfd_reconciliation(frozen, figs):
    tu = _schemes(frozen)["constraint_turnup"]
    cc = tu["extras"]["cross_check_cumulative"]
    assert figs["constraint_turnup.cross_check.accepted_offers.cash"] == cc["accepted_offers"]
    assert figs["constraint_turnup.cross_check.accepted_offers_wind.cash"] == cc["accepted_offers_wind"]
    old = {r["year"]: r["cost_gbp"] for r in tu["annual"]["rows"]}
    moved = sum(figs[f"constraint_turnup.{y}.cash"] - old[y] for y in MOVED_YEARS)
    assert _close(figs["constraint_turnup.cross_check.estimate.cash"], tu["cumulative_gbp"] + moved)
    rec = frozen["reconciliation"]
    assert figs["cfd_renewable.reconciliation.divergence_pct"] == rec["overall"]["divergence_pct"] == -0.6164
    assert figs["cfd_renewable.reconciliation.bottom_up.cash"] == rec["overall"]["bottom_up"]
    assert figs["cfd_renewable.reconciliation.official.cash"] == rec["overall"]["official"]
    assert figs["cfd_renewable.reconciliation.tolerance_pct"] == rec["tolerance_pct"]
    assert figs["cfd_renewable.reconciliation.matched_days"] == rec["matched_days"]


BASIS = {  # from 1.0.0's own notes on each line: payments as recorded, a share or alternative from the gas model,
           # or the turn-up line, which 1.0.0 calls an estimate
    "cfd_renewable": "measured", "constraints": "measured", "ro": "measured", "fit": "measured",
    "ccl": "measured", "capacity_market": "modelled", "carbon": "modelled", "tnuos": "modelled",
    "bsuos": "modelled", "vat": "modelled", "constraint_turnup": "estimated"}


def test_each_line_carries_its_basis_and_confidence(frozen, figs):
    for line, s in _schemes(frozen).items():
        assert figs[f"{line}.basis"] == BASIS[line], line
        # 1.0.0's confidence where it gives one; the four direct lines, counted in full from payment records,
        # it leaves blank, and they are high
        assert figs[f"{line}.confidence"] == (s["attribution_confidence"] or "high"), line
        assert figs[f"{line}.layer"] == s["layer"]
    assert figs["constraint_turnup.confidence"] == "low" and figs["ro.confidence"] == "high"


def test_the_context_keys(frozen, figs):
    bill = {r["year"]: r for r in frozen["bill"]["rows"]}
    direct = _table(frozen["model"]["perspectives"]["renewables"])
    indirect = _table(frozen["model"]["indirect"])
    cpih = _cpih(frozen)
    for y in range(2002, 2025):
        assert figs[f"bill.{y}.real"] == bill[y]["total_bill_gbp_2024"]
        assert figs[f"bill.{y}.cash"] == bill[y]["total_bill_gbp"]
        assert _close(figs[f"share_of_bill.{y}"],
                      (direct[y]["cost_gbp_2024"] + indirect[y]["cost_gbp_2024"] + _added(figs, y, "real"))
                      / bill[y]["total_bill_gbp_2024"])
        assert figs[f"deflator.{y}.cpih"] == cpih[y]
        assert _close(figs[f"deflator.{y}.to_2024"], cpih[2024] / cpih[y])
    assert figs["bill.2024.cash"] == 66_193_000_000          # DUKES 1.3, as the 9 Nov file holds it
    assert figs["deflator.2024.to_2024"] == 1.0
    assert _close(figs["bill.headline.real"], sum(bill[y]["total_bill_gbp_2024"] for y in range(2002, 2025)))
    assert _close(figs["share_of_bill.headline"], figs["all.headline.real"] / figs["bill.headline.real"])
    assert figs["households"] == frozen["context"]["households"]["value"] == 29_000_000
    assert _close(figs["per_household.headline"], figs["all.headline.real"] / 29_000_000)
    assert _close(figs["per_household.2024"], figs["all.2024.real"] / 29_000_000)


def test_the_figures_command_writes_the_file_with_its_fingerprint_and_source(tmp_path, figs):
    out = tmp_path / "figures.json"
    assert main(["figures", "--out", str(out)]) == 0
    data = out.read_bytes()
    doc = json.loads(data)
    assert list(doc) == ["figures", "meta"]
    assert doc["figures"] == figs
    meta = doc["meta"]
    assert meta["model"] == "model-bill-already-paid" and meta["version"] == results.model_version()
    assert meta["built_from"] == {"file": "results/clock.json", "ref": "2a63b034", "sha256": PINNED_SHA256,
                                  "version": "1.0.0", "generated_at": "2026-11-09T06:39:41.720314+00:00"}
    assert meta["headline_years"] == [2002, 2024]
    fp, name = (tmp_path / "figures.json.sha256").read_text().split()
    assert (fp, name) == (hashlib.sha256(data).hexdigest(), "figures.json")


def test_every_key_has_one_written_meaning_and_the_docs_list_them_all(figs):
    patterns = {t: re.compile(figures.template_regex(t)) for t in figures.KEYS}
    for k in figs:
        hits = [t for t, rx in patterns.items() if rx.fullmatch(k)]
        assert len(hits) == 1, (k, hits)
    used = {t for t, rx in patterns.items() if any(rx.fullmatch(k) for k in figs)}
    assert used == set(figures.KEYS)
    docs = (ROOT / "docs" / "figures.md").read_text()
    for t in figures.KEYS:
        assert f"`{t}`" in docs, t


def test_the_turn_up_window_and_the_cfd_data_end_are_keys(frozen, figs):
    S = _schemes(frozen)
    assert figs["constraint_turnup.cross_check.from"] == S["constraint_turnup"]["extras"]["measured_from"]
    assert figs["constraint_turnup.cross_check.to"] == S["constraint_turnup"]["data_to"] == "2026-10-29"
    assert figs["cfd_renewable.by_technology.to"] == S["cfd_renewable"]["data_to"] == "2026-10-27"
