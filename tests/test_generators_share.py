"""Version 1.6.0 (report-series ADR 0264; Richard, 19 Nov 2026): the part of the generators' share of grid (TNUoS) and
balancing (BSUoS) charges not paid out of subsidy, above the gas-led alternative, labelled estimated.

Expected values come from outside this model's code: Report No. 1's own figure for the net-zero part of the
generators' share (its pinned run file, `fleet.<year>.gen_nz_charge`), the publishers' printed figures (DUKES 6.2,
Ofgem's FIT reports, read by hand on 19 Nov 2026), and 1.5.0's frozen figures file."""
import math

import pytest

from billpaid import bridge, figures, generators_share as gs
from billpaid.__main__ import ROOT

YEARS = range(2002, 2026)


@pytest.fixture(scope="module")
def no1():
    return bridge.no1_release(ROOT).run


@pytest.fixture(scope="module")
def charges():
    doc, _, _ = figures.elexon_record.apply(figures.frozen_results(ROOT), ROOT, figures.LAST_CLOSED_YEAR)
    return gs.charges(doc, ROOT)


def test_the_grid_share_above_the_alternative_is_report_no_1s_own_figure(charges, no1):
    """(whole TNUoS - the alternative with the share in) - (TNUoS less the share - the alternative without it): the
    same, every year 2002-2025, as No. 1's net-zero part of the generators' TNUoS (£m), to a pound."""
    for y in YEARS:
        assert math.isclose(charges[y]["tnuos"], no1["fleet"][str(y)]["gen_nz_charge"]["tnuos_gbp_m"] * 1e6,
                            abs_tol=1.0), y


def test_the_balancing_share_is_the_whole_charges_share_above_the_alternative(charges, no1):
    """1.6.1 (the coordinator's ruling of 19 Nov 2026 on 1.6.0's judgement 6, under ADR 0264): the generators' share
    of the whole BSUoS charge above the alternative, switch-off payments and turn-up included, since the model's
    balancing lines take that share off and count it nowhere else. It is No. 1's figure, to a pound, every year.
    The share is nil from April 2023 (CMP308), so 2024 and 2025 are nil."""
    for y in YEARS:
        assert math.isclose(charges[y]["bsuos"], no1["fleet"][str(y)]["gen_nz_charge"]["bsuos_gbp_m"] * 1e6,
                            abs_tol=1.0), y
    assert abs(charges[2024]["bsuos"]) < 1.0 and abs(charges[2025]["bsuos"]) < 1.0   # nil, to float noise


def test_balancing_is_now_counted_whole_less_only_the_subsidised_stations_part(figs, no1):
    """The three balancing lines (switch-off, turn-up, BSUoS) plus the new line's balancing part equal the whole BSUoS
    charge above the alternative with the generators' share in, less the subsidised stations' part of that share,
    every year 2002-2024. Whole charge: the register's BSUOS series; the alternative: No. 1's Clock export; the
    share: No. 1's own figure."""
    from billpaid import register as R
    whole = R.load_pinned(ROOT)["register"].series("BSUOS")
    ex, _ = R.engine_export(ROOT)
    for y in range(2002, 2025):
        share = no1["fleet"][str(y)]["gen_nz_charge"]["bsuos_gbp_m"] * 1e6
        u = figs[f"generators_share.unsubsidised_share.{y}.central"]
        three = sum(figs.get(f"{line}.{y}.cash", 0.0) for line in ("constraints", "constraint_turnup", "bsuos"))
        expect = whole[y] * 1e6 - ex["balancing"]["years"][str(y)]["central_gbp"] - (1 - u) * share
        assert math.isclose(three + u * figs[f"generators_share.bsuos.{y}.cash"], expect, abs_tol=1.0), y


def test_the_grid_part_is_1_6_0s(figs, v160):
    for y in YEARS:
        for m in ("cash", "real"):
            assert figs[f"generators_share.tnuos.{y}.{m}"] == v160[f"generators_share.tnuos.{y}.{m}"], (y, m)


@pytest.fixture(scope="module")
def output():
    return gs.generation(figures.frozen_results(ROOT), ROOT)


def test_the_output_series_are_the_publishers_printed_figures(output):
    """DUKES 2026 Table 6.2 (GWh, UK), as printed: RO-eligible 2024 72,260.35, all renewables 144,484.73, all
    sources 286,027.5332; 2002 5,755.11, 11,126.81 and 387,245. FIT by calendar year: a quarter of the FIT year
    ending in it and three quarters of the one starting in it (2024: 8,340 and 7,970 GWh, Ofgem SY14 and SY15).
    CfD: LCCC's daily generation, 31.14 TWh in 2024, none before 2016."""
    g = output
    assert g[2024]["ro"] == 72260.35 and g[2024]["renewables"] == pytest.approx(144484.73)
    assert g[2024]["total"] == 286027.5332
    assert (g[2002]["ro"], g[2002]["total"]) == (5755.11, 387245)
    assert g[2002]["renewables"] == pytest.approx(11126.81)
    assert g[2024]["fit"] == pytest.approx(0.25 * 8340 + 0.75 * 7970)
    assert g[2010]["fit"] == pytest.approx(0.75 * 68.5594) and g[2009]["fit"] == 0.0
    assert g[2025]["fit"] == pytest.approx(7970)   # FIT year 2025-26 not yet reported: SY15 carried forward
    assert round(g[2024]["cfd"] / 1e3, 2) == 31.14 and g[2015]["cfd"] == 0.0


def test_each_fit_figure_is_in_its_saved_report():
    import re
    for y, row in gs.fit_generation(ROOT).items():
        text = re.sub(r"\s+", " ", gs.pdf_text(ROOT, row["source"]))
        assert row["quote"] in text, (y, row["source"])


def test_the_unsubsidised_share_of_output(output):
    """1 - (RO-eligible + CfD + FIT) / all output (central); every renewable station subsidised (low); FIT left out
    (high). 2024 by hand: 1 - (72,260.35 + 31,136 + 8,062.5) / 286,027.5 = 0.610; low 1 - 144,484.7 / 286,027.5 =
    0.495; high 1 - (72,260.35 + 31,136) / 286,027.5 = 0.639. 2002: 1 - 5,755 / 387,245 = 0.985."""
    u = gs.unsubsidised_share(output)
    assert round(u[2024]["central"], 3) == 0.610
    assert round(u[2024]["low"], 3) == 0.495 and round(u[2024]["high"], 3) == 0.639
    assert round(u[2002]["central"], 3) == 0.985
    for y in YEARS:
        assert 0 < u[y]["low"] <= u[y]["central"] <= u[y]["high"] < 1, y


@pytest.fixture(scope="module")
def figs():
    return figures.build(figures.frozen_results(ROOT), bridge.no1_release(ROOT))


@pytest.fixture(scope="module")
def old():
    """1.5.0's frozen figures file, as tagged."""
    import json
    import subprocess
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.5.0:results/figures.json"],
                                     capture_output=True, check=True).stdout)["figures"]


@pytest.fixture(scope="module")
def v160():
    """1.6.0's figures file, as tagged (never pinned)."""
    import json
    import subprocess
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.6.0:results/figures.json"],
                                     capture_output=True, check=True).stdout)["figures"]


def test_the_line_is_the_share_above_the_alternative_times_the_unsubsidised_share(figs, no1):
    """2024 by hand: No. 1's generators' TNUoS £456.41m (BSUoS nil since CMP308) times 1 - (72,260.35 + 31,136.45 +
    8,062.5) / 286,027.5332, about £278.6m cash. An indirect line, labelled estimated, low confidence."""
    u = 1 - (72260.35 + 31136.45 + 8062.5) / 286027.5332
    assert figs["generators_share.2024.cash"] == pytest.approx(
        no1["fleet"]["2024"]["gen_nz_charge"]["tnuos_gbp_m"] * 1e6 * u, rel=1e-5)
    assert (figs["generators_share.basis"], figs["generators_share.layer"],
            figs["generators_share.confidence"]) == ("estimated", "indirect", "low")
    for y in YEARS:
        assert f"generators_share.{y}.real" in figs and f"generators_share.{y}.cash" in figs
    assert figs["generators_share.2025.source"]


def test_vat_is_charged_on_households_share_of_the_new_line(figs, old):
    """VAT moves by exactly 5% of households' share of the line each year (decision 0027), 2025 included."""
    for y in range(2002, 2026):
        for m in ("cash", "real"):
            added = 0.05 * figs[f"vat.domestic_share.{y}"] * figs[f"generators_share.{y}.{m}"]
            assert figs[f"vat.{y}.{m}"] == pytest.approx(old[f"vat.{y}.{m}"] + added, rel=1e-12, abs=1e-3), (y, m)


def test_the_headline_without_the_line_is_1_5_0s(figs, old):
    """The counting option without the new line and its VAT gives 1.5.0's headline, so the paper can print the old
    basis; the headline is higher by the line and its VAT."""
    for m in ("cash", "real"):
        assert figs[f"option.no_generators_share.headline.{m}"] == pytest.approx(old[f"all.headline.{m}"], rel=1e-13)
        assert figs[f"all.headline.{m}"] > old[f"all.headline.{m}"] + figs[f"generators_share.headline.{m}"] - 1
        assert figs[f"all.2025.{m}"] > old[f"all.2025.{m}"]


def test_the_line_has_its_range_and_its_parts(figs, no1):
    """Each year at the low and high unsubsidised share, the headline at each end, and the parts: the generators'
    share above the alternative by charge (TNUoS is No. 1's own figure), the unsubsidised share, the output (GWh).
    2024 by hand: low 0.495 and high 0.639 of £456.41m."""
    tn = no1["fleet"]["2024"]["gen_nz_charge"]["tnuos_gbp_m"] * 1e6
    assert figs["generators_share.tnuos.2024.cash"] == pytest.approx(tn, abs=1.0)
    assert figs["generators_share.range.low.2024.cash"] == pytest.approx(tn * (1 - 144484.73 / 286027.5332), rel=1e-6)
    assert figs["generators_share.range.high.2024.cash"] == pytest.approx(
        tn * (1 - (72260.35 + 31136.45) / 286027.5332), rel=1e-5)
    assert figs["generators_share.unsubsidised_share.2024.central"] == pytest.approx(
        1 - (72260.35 + 31136.45 + 8062.5) / 286027.5332, rel=1e-6)
    assert figs["generators_share.generation.ro.2024"] == 72260.35
    assert figs["generators_share.range.years"] == ",".join(str(y) for y in YEARS)
    assert "subsidised" in figs["generators_share.range.method"]
    for m in ("cash", "real"):
        assert (figs[f"generators_share.range.low.headline.{m}"] < figs[f"generators_share.headline.{m}"]
                < figs[f"generators_share.range.high.headline.{m}"])
        assert figs[f"generators_share.tnuos.headline.{m}"] + figs[f"generators_share.bsuos.headline.{m}"] > \
            figs[f"generators_share.headline.{m}"]
    assert "generators_share" in figs["range.lines"].split(",")
    # the headline's estimated part holds the line
    assert figs["all.headline.estimated.cash"] > figs["generators_share.headline.cash"]


def test_every_key_matches_one_template(figs):
    import re
    pats = [re.compile(figures.template_regex(t)) for t in figures.KEYS]
    for k in figs:
        assert sum(bool(p.fullmatch(k)) for p in pats) == 1, k
