"""The bridge with Report No. 1 (version 1.1.0, part 2, aios-harness#223; ADR 0222, 0036): the walk from
No. 2's money paid to No. 1's extra cost, every year and the headline, each step named.

Expected values come from the two frozen releases themselves (the 9 Nov results file's 1.0.0 tables; No. 1's
pinned v4-s43 run file and its published figures), never from the bridge's code."""
import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT


@pytest.fixture(scope="module")
def frozen():
    return figures.frozen_results(ROOT)


@pytest.fixture(scope="module")
def figs(frozen):
    return figures.build(frozen, bridge.no1_release(ROOT))


def test_the_walk_starts_at_no2s_money_paid_and_ends_at_no1s_extra_cost(figs):
    assert figs["bridge.no2_money_paid.2024.cash"] == figs["all.2024.cash"]
    assert figs["bridge.no2_money_paid.2024.real"] == figs["all.2024.real"]
    # No. 1's v4-s43 run file, gap.2024.national_gbp_m_nominal: £13,299.169213931149m (2024 is the price base)
    assert figs["bridge.no1_extra_cost.2024.cash"] == pytest.approx(13_299_169_213.931149, abs=1e-3)
    assert figs["bridge.no1_extra_cost.2024.real"] == pytest.approx(13_299_169_213.931149, abs=1e-3)


# The walk, in order: the lines the two reports count alike, the lines they count differently, what only
# No. 1 counts, and what the policies saved or cost in the price of power itself.
STEPS = ["cfd_renewable", "capacity_market", "carbon", "tnuos", "balancing", "ro", "fit", "ccl", "vat",
         "energy_saving_schemes", "power_before_carbon"]
YEARS = range(2002, 2025)
A_TENTH_OF_A_PENNY = 0.001   # £; the figures are sums of up to £22bn held as floats


def _walk(figs, when, m):
    total = figs[f"bridge.no2_money_paid.{when}.{m}"]
    for step in STEPS:          # a fixed order, so the sum does not depend on how a table was sorted
        total += figs[f"bridge.{step}.{when}.{m}"]
    return total


def test_the_steps_add_up_exactly_every_year_and_in_the_headline(figs):
    assert figs["bridge.steps"] == ",".join(["no2_money_paid", *STEPS, "no1_extra_cost"])
    for m in ("cash", "real"):
        for when in [*YEARS, "headline"]:
            assert abs(_walk(figs, when, m) - figs[f"bridge.no1_extra_cost.{when}.{m}"]) < A_TENTH_OF_A_PENNY, (when, m)
    # and no step is left out of the file's list: every bridge money key belongs to a named step
    named = {"no2_money_paid", *STEPS, "no1_extra_cost"}
    assert {k.split(".")[1] for k in figs if k.startswith("bridge.")} - {"steps", "no1"} == named


def test_the_headline_ends_are_the_two_reports_own_headlines(figs):
    for m in ("cash", "real"):
        assert figs[f"bridge.no2_money_paid.headline.{m}"] == pytest.approx(figs[f"all.headline.{m}"], abs=0.001)
    # No. 1 as published (its figures file out/figures/v4-s43.json, key headline_2002_24_gbp_bn:
    # 140.31191674096607, £bn, 2002-24, 2024 prices): "£140.3bn"
    assert figs["bridge.no1_extra_cost.headline.real"] == pytest.approx(140.31191674096607e9, rel=1e-12)
    assert round(figs["bridge.no1_extra_cost.headline.real"] / 1e9, 1) == 140.3
    assert round(figs["bridge.no2_money_paid.headline.real"] / 1e9, 1) == 252.4


def test_the_lines_both_reports_count_alike_are_steps_of_nothing(figs):
    # CfD, the Capacity Market's net-zero part, carbon, grid and balancing: one cost register, one gas model
    for step in ("cfd_renewable", "capacity_market", "carbon", "tnuos", "balancing"):
        for m in ("cash", "real"):
            for y in YEARS:
                assert abs(figs[f"bridge.{step}.{y}.{m}"]) < 0.01, (step, y, m)   # under a penny every year
            assert abs(figs[f"bridge.{step}.headline.{m}"]) < 0.23, (step, m)     # so under 23p in 23 years


def test_the_steps_that_differ_are_no1s_line_less_no2s(figs):
    # No. 1's v4-s43 run file, 2024 (the price base, so cash and 2024 prices are the same), £m
    assert figs["bridge.energy_saving_schemes.2024.cash"] == pytest.approx(717.7765074265375e6, abs=0.001)
    assert figs["bridge.power_before_carbon.2024.real"] == pytest.approx(-7854.72688392154e6, abs=0.001)
    assert figs["bridge.ro.2024.cash"] == pytest.approx(7257.957564933899e6 - figs["ro.2024.cash"], abs=0.001)
    assert figs["bridge.fit.2024.cash"] == pytest.approx(1733.0346759999998e6 - figs["fit.2024.cash"], abs=0.001)
    assert figs["bridge.ccl.2024.cash"] == pytest.approx(9.060479382590984e6 - figs["ccl.2024.cash"], abs=0.001)
    assert figs["bridge.vat.2024.cash"] == pytest.approx(260.8405579408455e6 - figs["vat.2024.cash"], abs=0.001)
    # a year before the price base: No. 1's 2004 RO, £364.47168433531357m cash, priced to 2024 by CPIH (132.9 / 77.8)
    assert figs["bridge.ro.2004.real"] == pytest.approx(364.47168433531357e6 * 132.9 / 77.8 - figs["ro.2004.real"],
                                                         abs=0.001)
    # what the policies saved in the price of power is the largest step, and it is a saving
    saved = figs["bridge.power_before_carbon.headline.real"]
    assert saved < 0 and all(abs(figs[f"bridge.{s}.headline.real"]) <= abs(saved) for s in STEPS)


def test_each_step_has_a_plain_label_and_says_which_report_it_comes_from(figs):
    for step in ["no2_money_paid", *STEPS, "no1_extra_cost"]:
        label = figs[f"bridge.{step}.label"]
        assert isinstance(label, str) and 10 < len(label) <= 120, step
        for word in ("counterfactual", "baseline", "the gap", "NZ", "GO", "Clock"):   # the series glossary; no codes
            assert word not in label, (step, label)
    assert figs["bridge.no2_money_paid.label"].startswith("Money paid")
    assert figs["bridge.no1_extra_cost.label"].startswith("Extra cost")
    for step in ("cfd_renewable", "capacity_market", "carbon", "tnuos", "balancing"):
        assert figs[f"bridge.{step}.kind"] == "same"
    for step in ("ro", "fit", "ccl", "vat"):
        assert figs[f"bridge.{step}.kind"] == "counted_differently"
    for step in ("energy_saving_schemes", "power_before_carbon"):
        assert figs[f"bridge.{step}.kind"] == "no1_only"
    assert figs["bridge.no1.version"] == "v4-s43"
    assert figs["bridge.no1.sha256"] == NO1_RUN_SHA256


NO1_RUN_SHA256 = "dccd97d56efa9b4b26bc68604b8ae7f0204e40a9c1126a653886e268d28b49e4"   # model-register.yaml


def test_no1s_release_is_refused_if_it_is_not_the_pinned_file(tmp_path):
    import hashlib, shutil
    assert hashlib.sha256((ROOT / "reference/engine/v4-s43-run.json").read_bytes()).hexdigest() == NO1_RUN_SHA256
    (tmp_path / "reference/engine").mkdir(parents=True)
    shutil.copy(ROOT / "reference/model_pin.yaml", tmp_path / "reference/model_pin.yaml")
    (tmp_path / "reference/engine/v4-s43-run.json").write_text('{"gap": {}}')
    with pytest.raises(ValueError, match="not the pinned"):
        bridge.no1_release(tmp_path)


def test_the_figures_file_names_the_no1_release_it_read(tmp_path):
    import json
    from billpaid.__main__ import main
    out = tmp_path / "figures.json"
    assert main(["figures", "--out", str(out)]) == 0
    doc = json.loads(out.read_text())
    assert doc["meta"]["no1"] == {"model": "model-gas-counterfactual", "version": "v4-s43",
                                  "file": "reference/engine/v4-s43-run.json", "sha256": NO1_RUN_SHA256}
    assert doc["figures"]["bridge.no1_extra_cost.2024.cash"] == pytest.approx(13_299_169_213.931149, abs=1e-3)
