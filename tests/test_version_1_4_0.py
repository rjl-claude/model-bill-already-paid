"""Version 1.4.0 (aios-harness#243, Report No. 2, Richard's rulings of 16 Nov 2026, points 12, 14 and 21).

Expected values come from 1.3.1's own keys, read from its frozen figures file by hand (17 Nov 2026), or from the
rulings sheet (report-series/price-of-the-climate-bill/rulings-sheet.md), never from the new keys' code."""
import hashlib
import json
import math
import subprocess

import pytest

from billpaid import bridge, figures, results
from billpaid.__main__ import ROOT

YEARS = range(2002, 2025)


@pytest.fixture(scope="module")
def figs():
    return figures.build(figures.frozen_results(ROOT), bridge.no1_release(ROOT))


def _close(a, b, rel=1e-12):
    return math.isclose(a, b, rel_tol=rel, abs_tol=1e-3)


def test_12e_the_headline_without_grid_and_balancing_and_their_vat(figs):
    """Ruling 12e: the headline with none of the grid and balancing cost above the gas-led alternative counted
    (the TNUoS and BSUoS lines, £14.6bn and £2.0bn in the ruling), and the VAT on them taken out with them.
    By hand from 1.3.1's keys: £16.52bn of lines and £0.31bn of VAT, so £235.6bn in 2024 prices, £16.8bn less;
    in cash £13.68bn and £0.25bn, so £190.9bn, £13.9bn less."""
    assert round(figs["option.no_grid_balancing.headline.real"] / 1e9, 1) == 235.6
    # 1.6.1: the generators' share of grid and balancing charges (£6.10bn) and its VAT go too, so £23.0bn less; the
    # case itself does not move
    assert round(figs["option.no_grid_balancing.less_than_headline.real"] / 1e9, 1) == 23.0
    # cash: £190.94bn at 1.4.0; 1.5.0 moves £28m from balancing to constraint payments, so £190.97bn, printing £191.0bn
    assert round(figs["option.no_grid_balancing.headline.cash"] / 1e9, 1) == 191.0
    assert round(figs["option.no_grid_balancing.less_than_headline.cash"] / 1e9, 1) == 19.0   # 1.6.1: was 13.9
    for m in ("real", "cash"):
        assert _close(figs[f"option.no_grid_balancing.headline.{m}"]
                      + figs[f"option.no_grid_balancing.less_than_headline.{m}"], figs[f"all.headline.{m}"])
        taken = sum((figs.get(f"tnuos.{y}.{m}", 0.0) + figs.get(f"bsuos.{y}.{m}", 0.0)
                     + figs[f"generators_share.{y}.{m}"])   # 1.6.0
                    * (1 + 0.05 * figs[f"vat.domestic_share.{y}"]) for y in YEARS)
        assert _close(figs[f"option.no_grid_balancing.less_than_headline.{m}"], taken)


def test_12e_has_short_plain_words_to_print_beside_the_headline(figs):
    words = figs["option.no_grid_balancing.words"]
    assert words == ("The headline with none of the grid and balancing cost above the gas-led alternative "
                     "counted, and none of the VAT on it")
    assert not any(c in words for c in ";–—")


def test_14c_turn_up_range_moves_only_the_split_with_balancing(figs):
    """Ruling 14c: switch-off payments, turn-up and balancing are one recorded total split three ways (paper §8.1),
    so turn-up at its low or high takes the change off the BSUoS line and the total does not move."""
    years = [int(y) for y in figs["constraint_turnup.range.years"].split(",")]
    assert years[0] == 2015
    for bound in ("low", "high"):
        for m in ("real", "cash"):
            for y in years:
                assert _close(figs[f"bsuos.turnup_range.{bound}.{y}.{m}"]
                              + figs[f"constraint_turnup.range.{bound}.{y}.{m}"],
                              figs[f"bsuos.{y}.{m}"] + figs[f"constraint_turnup.{y}.{m}"])
                assert figs[f"bsuos.turnup_range.{bound}.{y}.{m}"] >= -1e-3   # nil where the cap binds, to float rounding
            assert _close(figs[f"bsuos.turnup_range.{bound}.headline.{m}"]
                          + figs[f"constraint_turnup.range.{bound}.headline.{m}"],
                          figs[f"bsuos.headline.{m}"] + figs[f"constraint_turnup.headline.{m}"])
    # 1.3.1's turn-up range keys are kept as they were (by hand from 1.3.1: £3.23bn to £3.63bn)
    assert round(figs["constraint_turnup.range.low.headline.real"] / 1e9, 2) == 3.23
    # high: £3.625bn at 1.3.1 and 1.4.0; 1.5.0 takes £8m off 2015's capped turn-up, so £3.617bn
    assert round(figs["constraint_turnup.range.high.headline.real"] / 1e9, 2) == 3.62


def test_14c_turn_up_no_longer_sets_the_headline_range(figs):
    assert "constraint_turnup" not in figs["range.lines"].split(",")
    assert figs["range.low.headline.line"] != "constraint_turnup"
    assert figs["range.high.headline.line"] != "constraint_turnup"


def test_21a_the_readme_describes_carbon_as_the_model_computes_it():
    """Ruling 21a: the README's table said "power-sector share of auction revenue", the retired emissions-trading
    line. The carbon line (billpaid.schemes.carbon, paper §7.5) is the carbon price times the carbon intensity of
    the plant that set the price times the power made, and it holds the Carbon Price Support, so the levy's row
    holds the levy alone (billpaid.register)."""
    rows = {r.split("|")[1].strip(): r for r in (ROOT / "README.md").read_text().splitlines() if r.startswith("| ")}
    carbon = rows["Carbon in the electricity price"]
    assert "auction revenue" not in carbon
    for words in ("carbon price", "price-setting plant", "power made"):
        assert words in carbon, words
    assert "Emissions trading (UK/EU ETS)" not in rows and "CCL & Carbon Price Support" not in rows
    assert "carbon line" in rows["Climate Change Levy"]


SETTINGS = {"2005_2012": (0.60, 1.0, 1.10), "2013_2020": (0.75, 1.0, 1.20), "2021_on": (0.75, 1.0, 1.20)}
PERIODS = {"2005_2012": range(2005, 2013), "2013_2020": range(2013, 2021), "2021_on": range(2021, 2026)}


def test_13b_the_pass_through_settings_by_period(figs):
    """Ruling 13b, the coordinator's settings of 17 Nov 2026 (handover/research-13b-pass-through.md): 2005-2012 60% to
    110%, 2013-2020 75% to 120%, 2021 on (2025 provisional with it) 75% to 120% carried forward; central 100%."""
    for p, (lo, c, hi) in SETTINGS.items():
        assert (figs[f"carbon.pass_through.{p}.low"], figs[f"carbon.pass_through.{p}.central"],
                figs[f"carbon.pass_through.{p}.high"]) == (lo, c, hi)
    assert figs["carbon.pass_through.2005_2012.years"] == "2005-2012"
    assert figs["carbon.pass_through.2013_2020.years"] == "2013-2020"
    assert figs["carbon.pass_through.2021_on.years"] == "2021-2025"


def test_13b_the_carbon_line_at_each_end_of_the_pass_through_bracket(figs):
    """By hand from 1.3.1's carbon keys: the line at the low settings £59.09bn, at the high £97.40bn (2024 prices,
    2002-2024), against £82.86bn; in cash £47.99bn and £78.66bn. 2025 (provisional) £4.96bn and £7.93bn."""
    assert round(figs["carbon.pass_through.range.low.headline.real"] / 1e9, 2) == 59.09
    assert round(figs["carbon.pass_through.range.high.headline.real"] / 1e9, 2) == 97.40
    assert round(figs["carbon.pass_through.range.low.headline.cash"] / 1e9, 2) == 47.99
    assert round(figs["carbon.pass_through.range.high.headline.cash"] / 1e9, 2) == 78.66
    assert round(figs["carbon.pass_through.range.low.2025.real"] / 1e9, 2) == 4.96
    assert round(figs["carbon.pass_through.range.high.2025.real"] / 1e9, 2) == 7.93
    for p, years in PERIODS.items():
        for y in years:
            for i, bound in ((0, "low"), (2, "high")):
                for m in ("real", "cash"):
                    assert _close(figs[f"carbon.pass_through.range.{bound}.{y}.{m}"],
                                  figs[f"carbon.{y}.{m}"] * SETTINGS[p][i])


def test_13b_the_headline_at_the_bracket_carries_vat_with_carbon(figs):
    """The headline with the pass-through at all its low settings together, or all its high, everything else
    central; the VAT on the carbon moves with it, as in the carbon counting options. By hand from 1.3.1: swing
    -£24.21bn and +£14.81bn, headline £228.19bn to £267.21bn (2024 prices); cash -£19.01bn and +£12.22bn."""
    assert round(figs["carbon.pass_through.swing.low.real"] / 1e9, 2) == -24.21
    assert round(figs["carbon.pass_through.swing.high.real"] / 1e9, 2) == 14.81
    assert round(figs["carbon.pass_through.swing.low.cash"] / 1e9, 2) == -19.01
    assert round(figs["carbon.pass_through.swing.high.cash"] / 1e9, 2) == 12.22
    for bound in ("low", "high"):
        for m in ("real", "cash"):
            assert _close(figs[f"carbon.pass_through.headline.{bound}.{m}"],
                          figs[f"all.headline.{m}"] + figs[f"carbon.pass_through.swing.{bound}.{m}"])
    # 1.6.1: the headline is £6.22bn higher (the generators' share and its VAT): £234.41bn to £273.43bn
    assert round(figs["carbon.pass_through.headline.low.real"] / 1e9, 2) == 234.41
    assert round(figs["carbon.pass_through.headline.high.real"] / 1e9, 2) == 273.43


def test_13b_pass_through_joins_the_headline_range_and_sets_both_ends(figs):
    # 1.6.0: the generators' share joins the lines whose ranges set the headline's (it sets neither end)
    assert figs["range.lines"] == "carbon,capacity_market,carbon_pass_through,generators_share"
    assert figs["range.low.headline.line"] == figs["range.high.headline.line"] == "carbon_pass_through"
    for bound in ("low", "high"):
        for m in ("real", "cash"):
            assert _close(figs[f"range.{bound}.headline.{m}"], figs[f"carbon.pass_through.headline.{bound}.{m}"])
    assert round(figs["range.low.headline.real"] / 1e9, 1) == 234.4    # 1.6.1: was 228.2
    assert round(figs["range.high.headline.real"] / 1e9, 1) == 273.4   # 1.6.1: was 267.2


def test_13b_words_name_the_sources_and_the_judgement(figs):
    sources = figs["carbon.pass_through.sources"]
    for name in ("Guo and Castagneto Gissey 2019", "Guo and Newbery 2020", "Sijm, Neuhoff and Chen 2006",
                 "Castagneto-Gissey 2014"):
        assert name in sources, name
    basis = figs["carbon.pass_through.2021_on.basis"]
    assert "judgement" in basis and "no published estimate" in basis
    for k in ("carbon.pass_through.sources", "carbon.pass_through.2021_on.basis", "carbon.pass_through.method",
              "carbon.pass_through.vat", "carbon.pass_through.2005_2012.basis", "carbon.pass_through.2013_2020.basis"):
        assert not any(c in figs[k] for c in ";–—"), k


# 1.3.1's figures file as frozen at its tag (the paper's pin before 1.4.0)
V131_SHA256 = "98ce486f49b7264f89250da99b82ff3d813afb12c726642ee271ceb128b55253"
# (the ends' values move again at 1.6.0 and are left out by tests.v1_5_0.kept; the lines that set them do not)
MOVED = {f"range.{b}.headline.line": None for b in ("low", "high")}


def _v131() -> dict:
    data = subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.3.1:results/figures.json"],
                          capture_output=True, check=True).stdout
    assert hashlib.sha256(data).hexdigest() == V131_SHA256
    return json.loads(data)["figures"]


def test_no_1_3_1_key_moves_but_the_headline_range_and_none_is_dropped(figs):
    """Every 1.3.1 key is kept with its value, except the headline's range, which rulings 13b and 14c move: its ends
    from £247.7bn and £257.8bn (early carbon prices) to £228.2bn and £267.2bn (carbon pass-through)."""
    from tests.v1_5_0 import kept
    old = kept(_v131())    # less what 1.5.0 drops or moves (tests/test_national_grid_constraints.py)
    assert set(old) <= set(figs)
    # floats to a part in a million million: 1.5.0's re-split leaves sums of the three balancing lines a
    # fraction of a penny away
    moved = sorted(k for k in old if old[k] != figs[k] and not (isinstance(old[k], float) and math.isclose(
        old[k], figs[k], rel_tol=1e-12, abs_tol=1e-3)))
    assert moved == sorted(MOVED), moved
    assert (old["range.low.headline.line"], old["range.high.headline.line"]) == ("carbon", "carbon")
    whole = _v131()
    assert round(whole["range.low.headline.real"] / 1e9, 1) == 247.7
    assert round(whole["range.high.headline.real"] / 1e9, 1) == 257.8


def test_the_model_is_version_1_6_2_and_its_figures_file_says_so():
    assert results.model_version() == "1.6.2"
    doc = figures.document(figures.frozen_results(ROOT), bridge.no1_release(ROOT))
    assert doc["meta"]["version"] == "1.6.2"
    assert doc["meta"]["built_from"]["version"] == "1.0.0"


def test_the_committed_figures_file_is_the_one_the_model_builds(tmp_path):
    """The file the paper pins is reproducible: a fresh build is byte for byte the committed file, and the
    fingerprint beside it is that file's."""
    out = tmp_path / "figures.json"
    fp = results.write(figures.document(figures.frozen_results(ROOT), bridge.no1_release(ROOT)), out)
    committed = ROOT / "results" / "figures.json"
    assert committed.read_bytes() == out.read_bytes()
    assert (ROOT / "results" / "figures.json.sha256").read_text() == f"{fp}  figures.json\n"
    assert json.loads(committed.read_text())["meta"]["version"] == "1.6.2"
