"""A range for each line labelled estimated (version 1.1.0, part 4, aios-harness#225): constraint turn-up's own
range and carbon's estimated years, 2005-2012. The method is written down in docs/figures.md, "The ranges".

Expected values come from worked examples and the sources themselves, never from the code under test."""
import math


# One half-hour's accepted offers, as Elexon's settlement stack gives them (volume MWh, price £/MWh)
STACK = [
    {"volume": 50, "originalPrice": 80.0, "soFlag": False, "sequenceNumber": 1, "cadlFlag": False},
    {"volume": 30, "originalPrice": 150.0, "soFlag": True, "sequenceNumber": 2, "cadlFlag": False},
    {"volume": 40, "originalPrice": 40.0, "soFlag": True, "sequenceNumber": 3, "cadlFlag": False},
    {"volume": 100, "originalPrice": 10.0, "soFlag": False, "sequenceNumber": 4, "cadlFlag": True},  # CADL: out
]


def test_the_turn_up_walk_prices_the_switched_off_wind_on_the_cheapest_and_dearest_accepted_offers():
    from billpaid import ranges
    # 60 MWh of wind switched off. Central (Octopus's walk): unflagged first, then by sequence:
    # 50 at £80 + 10 at £150 = £5,500. Cheapest first: 40 at £40 + 20 at £80 = £3,200.
    # Dearest first: 30 at £150 + 30 at £80 = £6,900. The CADL offer is never used.
    walks = ranges.turnup_walks(STACK, -60.0)
    assert walks["central"] == (60.0, 5500.0)
    assert walks["low"] == (60.0, 3200.0)
    assert walks["high"] == (60.0, 6900.0)


import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT


@pytest.fixture(scope="module")
def figs():
    return figures.build(figures.frozen_results(ROOT), bridge.no1_release(ROOT))


# EEA, "Emissions, allowances, surplus and prices in the EU ETS, 2005-2020", data package, row "EUA price
# (EUR / t CO2-eq)": the price 1.0.0's carbon line rests on in 2005-2012 (the engine's estimated years)
EEA = {2008: 20.018285714285724, 2009: 13.157204724409443, 2010: 14.338503937007872,
       2011: 12.943263598326368, 2012: 7.369725490196074}
EEA.update({2005: 21.824473684210524, 2006: 17.26894117647059, 2007: 0.6535294117647066})
# BlueNext (formerly Powernext Carbon), daily closing price of the Phase I spot EUA (BNS EUA 05-07), 24 Jun 2005
# to 25 Apr 2008: the lowest and highest close each year, EUR/t (2005 from the exchange's opening, 24 Jun)
BLUENEXT = {2005: (18.85, 28.93), 2006: (6.40, 29.75), 2007: (0.02, 5.48)}
# UK Debt Management Office, Phase II auction result notices, 30 auctions 19 Nov 2008 to 25 Oct 2012: the
# lowest and highest clearing price each year, EUR/t (2008: one auction, 19 Nov, EUR 16.15)
DMO = {2008: (16.15, 16.15), 2009: (10.98, 15.05), 2010: (12.15, 15.6), 2011: (9.72, 16.34), 2012: (6.67, 8.55)}


def test_carbon_in_its_estimated_years_ranges_with_the_prices_allowances_traded_or_cleared_at(figs):
    # the line at another allowance price is the line times that price over the EEA's, the engine's merit order
    # held as it is (no Carbon Price Support before April 2013). The range spans the EEA's price and every
    # clearing price of the year's UK auctions: in 2009-2012 the EEA's price lies inside the auctions' own
    # spread; 2008 had one auction, on 19 Nov after the price fell, so its high is the EEA's price itself
    expected = {**BLUENEXT, **DMO, 2008: (16.15, EEA[2008])}
    for y in range(2005, 2013):
        lo, hi = expected[y]
        for m in ("real", "cash"):
            c = figs[f"carbon.{y}.{m}"]
            assert math.isclose(figs[f"carbon.range.low.{y}.{m}"], c * lo / EEA[y], rel_tol=1e-12), (y, m)
            assert math.isclose(figs[f"carbon.range.high.{y}.{m}"], c * hi / EEA[y], rel_tol=1e-12), (y, m)
        assert figs[f"carbon.allowance_price.central.{y}"] == EEA[y]
        assert (figs[f"carbon.allowance_price.low.{y}"], figs[f"carbon.allowance_price.high.{y}"]) == (lo, hi)


def test_the_ranged_headline_moves_only_the_years_with_a_range(figs):
    for line in ("carbon", "constraint_turnup"):
        years = [int(y) for y in figs[f"{line}.range.years"].split(",")]
        for bound in ("low", "high"):
            for m in ("real", "cash"):
                moved = sum(figs[f"{line}.range.{bound}.{y}.{m}"] - figs[f"{line}.{y}.{m}"] for y in years if y <= 2024)
                assert math.isclose(figs[f"{line}.range.{bound}.headline.{m}"], figs[f"{line}.headline.{m}"] + moved,
                                    rel_tol=1e-12)
        assert figs[f"{line}.range.method"]
    assert figs["carbon.range.years"] == "2005,2006,2007,2008,2009,2010,2011,2012"
    lo, mid, hi = (figs[k] for k in ("carbon.range.low.headline.real", "carbon.headline.real",
                                     "carbon.range.high.headline.real"))
    assert lo < mid < hi


def _schemes(doc):
    return {s["scheme_id"]: s for s in doc["model"]["schemes"]}


def _turnup_walks_by_year():
    # the saved re-walk of Elexon's settlement stacks (reference/sources/turnup-range-daily.csv), summed by year
    import csv
    out = {}
    with (ROOT / "reference" / "sources" / "turnup-range-daily.csv").open() as f:
        for r in csv.DictReader(f):
            y = out.setdefault(int(r["date"][:4]), {"central": 0.0, "low": 0.0, "high": 0.0})
            for k in y:
                y[k] += float(r[f"{k}_gbp"])
    return out


def test_the_saved_re_walk_reproduces_1_0_0s_turn_up_every_year():
    # 1.0.0's turn-up as measured (before its cap at the BSUoS uplift), from the frozen file: the re-walk's
    # central, fetched again from Elexon for this part, gives the same figure each year
    measured = {r["year"]: r["cost"] for r in
                _schemes(figures.frozen_results(ROOT))["constraint_turnup"]["extras"]["measured_annual"]}
    walks = _turnup_walks_by_year()
    assert sorted(walks) == list(range(2015, 2026))
    for y, w in walks.items():
        assert math.isclose(w["central"], measured[y], rel_tol=0.005), (y, w["central"], measured[y])
        assert w["low"] <= w["central"] <= w["high"], y


def test_constraint_turn_up_ranges_from_the_cheapest_to_the_dearest_offers_and_never_above_its_cap(figs):
    doc = figures.frozen_results(ROOT)
    measured = {r["year"]: r["cost"] for r in _schemes(doc)["constraint_turnup"]["extras"]["measured_annual"]}
    walks = _turnup_walks_by_year()
    for y in range(2015, 2026):
        central = figs[f"constraint_turnup.{y}.cash"]
        cap = figs[f"bsuos.{y}.cash"] + central     # 1.0.0: turn-up is never more than the BSUoS uplift
        s = measured[y] / walks[y]["central"]       # each year held to 1.0.0's own measured figure
        for bound in ("low", "high"):
            want = min(walks[y][bound] * s, cap)
            assert math.isclose(figs[f"constraint_turnup.range.{bound}.{y}.cash"], want, rel_tol=1e-12), (y, bound)
            assert math.isclose(figs[f"constraint_turnup.range.{bound}.{y}.real"],
                                want * figs[f"constraint_turnup.{y}.real"] / central, rel_tol=1e-12), (y, bound)
        assert (figs[f"constraint_turnup.range.low.{y}.cash"] <= central
                <= figs[f"constraint_turnup.range.high.{y}.cash"]), y
    # 2018: 1.0.0's cap binds (measured £124.8m, the uplift £53.4m), so the high is the line itself
    assert figs["constraint_turnup.range.high.2018.cash"] == figs["constraint_turnup.2018.cash"]
    assert figs["constraint_turnup.range.years"] == ",".join(str(y) for y in range(2015, 2026))


def test_a_saved_range_source_whose_fingerprint_differs_is_refused(tmp_path):
    from billpaid import ranges
    (tmp_path / "reference" / "sources").mkdir(parents=True)
    (tmp_path / "reference" / "ranges.yaml").write_bytes((ROOT / "reference" / "ranges.yaml").read_bytes())
    table = (ROOT / "reference" / "sources" / "dmo-uk-ets-phase2-auctions.csv").read_bytes()
    (tmp_path / "reference" / "sources" / "dmo-uk-ets-phase2-auctions.csv").write_bytes(table.replace(b"10.98", b"1.98"))
    with pytest.raises(ValueError, match="sha256"):
        ranges.dmo_clearing_prices(tmp_path)


def test_the_eea_price_is_the_file_report_no_1s_release_read():
    # the saved EEA package is byte for byte the input the v4-s43 run file records
    import hashlib
    import json
    run = json.loads((ROOT / "reference" / "engine" / "v4-s43-run.json").read_text())
    pinned = run["meta"]["input_checksums"][
        "data/raw/eea/s18a-EUETS_emissions_allowances_surplus_prices_2005-2020_data-package.zip"]
    data = (ROOT / "reference" / "sources" / "eea-euets-emissions-allowances-prices-2005-2020.zip").read_bytes()
    assert hashlib.sha256(data).hexdigest() == pinned
    assert run["ets_auctions"]["files"]["s36/ets/uk-ets-phase2-auctions.csv"] == hashlib.sha256(
        (ROOT / "reference" / "sources" / "dmo-uk-ets-phase2-auctions.csv").read_bytes()).hexdigest()


def test_the_phase_i_spot_record_agrees_with_what_the_exchange_and_the_nao_published():
    # Powernext's annual activity reports: average spot price EUR 22.51 in 2005 (from 24 Jun) and 17.37 in
    # 2006; 2005 high 28.93 on 11 Jul; 2007 high 5.48 on 2 Jan. NAO 2009 review: Phase I peak EUR 29.75, Apr 2006
    from billpaid import ranges
    closes = ranges.bluenext_closes(ROOT)
    assert abs(sum(closes[2005]) / len(closes[2005]) - 22.51) < 0.01
    assert abs(sum(closes[2006]) / len(closes[2006]) - 17.37) < 0.05
    assert max(closes[2005]) == 28.93 and max(closes[2006]) == 29.75 and max(closes[2007]) == 5.48
    assert sorted(closes) == [2005, 2006, 2007]
