"""Version 1.2.0 (aios-harness#235): the paid side checked against the totals others publish (outline §4.2, §4.3,
Annex B; missing figure M7): model, reference, gap (model less reference) and ratio (model over reference), £ cash,
over the years both cover. Expected values are read by hand from the publishers' saved files, never from the keys'
code."""
import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT


@pytest.fixture(scope="module")
def figs():
    return figures.build(figures.frozen_results(ROOT), bridge.no1_release(ROOT))


def _check(figs, name):
    return [figs[f"check.{name}.headline.{k}"] for k in ("model", "reference", "gap", "ratio")]


def test_the_climate_change_levy_against_hmrcs_receipts(figs):
    model, ref, gap, ratio = _check(figs, "hmrc.ccl")
    assert abs(model - figs["ccl.headline.cash"]) < 0.01
    # HMRC, Environmental Taxes Bulletin (31 Mar 2026), Table 1b, electricity declarations: 2002 £623.0m ... 2024
    # £806.8m; the line is HMRC's own figure, so the check is exact
    assert abs(gap) < 1.0 and abs(ratio - 1) < 1e-9
    assert figs["check.hmrc.ccl.years"] == "2002-2024"


def test_the_levies_against_the_obrs_outturn(figs):
    """OBR's public finances databank (October 2026 EFO), receipts, "Environmental levies (Renewables Obligation
    and Contracts for Difference)", which also holds the Warm Home Discount and the green gas levy: 2002-03 to
    2024-25, read by hand, £95.478bn. The model's side is the RO and CfD lines on the same April-March years."""
    model, ref, gap, ratio = _check(figs, "obr.levies")
    assert abs(ref / 1e9 - 95.478) < 1e-6
    assert figs["check.obr.levies.years"] == "2002-03 to 2024-25"
    ro = sum(figs[f"ro.{y}.cash"] for y in range(2002, 2025))
    assert ro < model < ro + 1.2 * figs["cfd_renewable.headline.cash"]
    assert abs(gap - (model - ref)) < 1e-3 and 0.8 < ratio < 1.0


def test_the_renewables_obligation_against_ofgems_scheme_value(figs):
    """Ofgem's scheme value each obligation year, SY1 (2002-03) to SY23 (2024-25): ROCs presented times what a ROC
    was worth to a supplier, from its annual reports (2005-06 Tables 1-3, 2009-10 Tables 1-3, SY23 Figure A4.1).
    The line adds the mutualisation payments received in 2017-18 to 2021-22, which Ofgem's scheme value leaves
    out: £525.54m (the input audit's sum of Ofgem's tables, 11 Nov 2026)."""
    model, ref, gap, ratio = _check(figs, "ofgem.ro")
    assert abs(model - sum(figs[f"ro.{y}.cash"] for y in range(2002, 2025))) < 0.01
    assert abs(gap / 1e6 - 525.54) < 0.01
    assert figs["check.ofgem.ro.years"] == "2002-03 to 2024-25"


def test_feed_in_tariffs_against_ofgems_levelisation_fund(figs):
    """Ofgem's levelisation fund, FIT years 2010-11 to 2024-25, as printed in its document for each year (e.g.
    2017-18 notice: "The total Levelisation Fund for the year was calculated at £1,375,082,537.07"): the line is
    Ofgem's figure, so the check is exact."""
    model, ref, gap, ratio = _check(figs, "ofgem.fit")
    assert abs(model - sum(figs[f"fit.{y}.cash"] for y in range(2010, 2025))) < 0.01
    assert abs(gap) < 0.01 and abs(ratio - 1) < 1e-12
    assert figs["check.ofgem.fit.years"] == "2010-11 to 2024-25"


def test_the_direct_lines_against_refs_published_series(figs):
    """REF, "UK Renewable Electricity Subsidy Totals 2002 to the Present Day" (April 2025), Table 1, totals row,
    £bn nominal, 2002/03 to 2023/24: RO 67.0, CfD 7.8, FiT 15.3, constraints 1.7 (REGO 1.7 left out: the model
    does not count it), so £91.8bn, read by hand."""
    model, ref, gap, ratio = _check(figs, "ref.direct")
    assert abs(ref / 1e9 - 91.8) < 1e-9
    assert figs["check.ref.direct.years"] == "2002-03 to 2023-24"
    assert abs(gap - (model - ref)) < 1e-3 and 0.95 < ratio < 1.1
