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


def test_the_levies_against_the_obrs_outturn_like_for_like(figs):
    """OBR's public finances databank (October 2026 EFO), "Environmental levies", 2002-03 to 2024-25, read by hand:
    £95.478bn. ONS's own series of its parts (public sector finances, EDP dataset, 21 Sep 2026) add up to it every
    year: ROCs (EP89), CfDs (CW5G), the Warm Home Discount (JNJF) and the CRC Energy Efficiency Scheme (L8UA,
    2012-13 to 2019-20). Not in it: the Capacity Market (the OBR's own note: ONS has yet to include it), FiT and the
    green gas levy (nil to 2024-25). So the reference is the OBR's figure less the two schemes the model does not
    count (WHD £5.025bn, CRC £3.881bn, by hand), and what is left is the RO and CfD, ONS's against the model's."""
    model, ref, gap, ratio = _check(figs, "obr.levies")
    k = "check.obr.levies"
    assert abs(figs[f"{k}.reference_whole"] / 1e9 - 95.478) < 1e-6
    assert abs(figs[f"{k}.not_counted.whd"] / 1e9 - 5.025) < 0.001
    assert abs(figs[f"{k}.not_counted.crc"] / 1e9 - 3.881) < 0.001
    assert abs(ref - (figs[f"{k}.reference_whole"] - figs[f"{k}.not_counted.whd"] - figs[f"{k}.not_counted.crc"])) < 1
    # ONS's parts add up to the OBR's figure: nothing in the reference is unaccounted for
    assert abs(figs[f"{k}.ons_parts_less_obr"]) < 1e7
    # the gap is the RO and CfD, each the model's less ONS's, named
    assert abs(gap - (figs[f"{k}.gap.ro"] + figs[f"{k}.gap.cfd"]) - figs[f"{k}.ons_parts_less_obr"]) < 1
    assert abs(ratio - 1) < 0.03
    assert figs[f"{k}.years"] == "2002-03 to 2024-25"


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


def test_the_ro_and_fit_against_ofgems_price_cap_policy_costs(figs):
    """ADR 0241: 2019-20 to 2025-26, only the schemes both Ofgem's policy-cost allowance and the model count (the RO
    and FiT), per typical household, at Ofgem's typical consumption (3.1 MWh, single-rate, April 2018 to December
    2025). Ofgem's side, read by hand from its Annex 4 v1.25 (tab 1a, single-rate, £/MWh supplied; summer and winter
    weighted 0.4324 / 0.5676 as its tab 3a): 2019-20 RO 23.645 / 23.610, FiT 5.884 / 6.113, so £91.88. The model's
    side: its RO and FiT lines over the volume they are charged on, from Ofgem's total obligation notices (2019-20:
    130,183,968 ROCs obligated, 128,722,805 of them in Great Britain at 0.484 per MWh)."""
    k = "check.ofgem.price_cap_policy_costs"
    assert abs(figs[f"{k}.2019.reference"] - 3.1 * (0.4324 * (23.645 + 5.884) + 0.5676 * (23.61 + 6.113))) < 0.01
    ro_mwh = figs["ro.2019.cash"] / 130_183_968 * 0.484
    fit_mwh = figs["fit.2019.cash"] / ((116_940_506 + 11_782_299) / 0.484)
    assert abs(figs[f"{k}.2019.model"] - 3.1 * (ro_mwh + fit_mwh)) < 0.01
    model, ref, gap, ratio = _check(figs, "ofgem.price_cap_policy_costs")
    assert abs(model - sum(figs[f"{k}.{y}.model"] for y in range(2019, 2026))) < 1e-6
    assert abs(ref - sum(figs[f"{k}.{y}.reference"] for y in range(2019, 2026))) < 1e-6
    assert figs[f"{k}.years"] == "2019-20 to 2025-26"
    assert figs[f"{k}.schemes"] == "ro,fit"
    assert figs[f"{k}.typical_consumption_mwh"] == 3.1
    assert 0.8 < ratio < 1.2


def test_the_price_cap_basis_says_when_ofgem_moved_cfds(figs):
    """1.3.1: Ofgem's Annex 4 counted CfD costs as policy costs until its v1.11 (15 May 2022), whose change log
    reads "Removed CfD costs from the annex (moved to annex 2 - wholesale costs)" (the saved workbook's front
    sheet). The check leaves CfD out on both sides in every year."""
    from billpaid import outline_sources as src
    front = " ".join(str(c) for r in src._sheet(ROOT, "ofgem-cap-annex-4", "Front sheet").iter_rows() for c in r if c)
    assert "Removed CfD costs from the annex (moved to annex 2 - wholesale costs)" in front
    basis = figs["check.ofgem.price_cap_policy_costs.basis"]
    assert "v1.11" in basis and "15 May 2022" in basis and "left out on both sides" in basis
    assert "obligation level" in basis and "forward allowance" in basis
    note = figs["check.ofgem.price_cap_policy_costs.2021.note"]
    assert "FiT" in note and "export" in note


def test_1_3_1_moves_no_number_from_1_3_0(figs):
    import json
    import subprocess
    old = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.3.0:results/figures.json"],
                                    capture_output=True, check=True).stdout)["figures"]
    from tests.v1_5_0 import kept
    all_old = set(old)
    old = kept(old)    # less what 1.5.0 drops or moves (tests/test_national_grid_constraints.py)
    assert set(old) <= set(figs)
    import math
    # floats to a part in a million million: 1.5.0's re-split leaves sums of the three balancing lines a
    # fraction of a penny away
    moved = [k for k in old if old[k] != figs[k] and not (isinstance(old[k], float) and math.isclose(
        old[k], figs[k], rel_tol=1e-12, abs_tol=1e-3))]
    # and the headline's range, which 1.4.0's rulings 13b and 14c move (tests/test_version_1_4_0.py)
    # (1.6.0 moves the ends' values again, left out by kept(); the lines that set them are still 1.4.0's)
    ranged = [f"range.{b}.headline.line" for b in ("low", "high")]
    assert sorted(moved) == sorted(["check.ofgem.price_cap_policy_costs.basis", *ranged]), moved
    new_in_1_4_0 = ("option.no_grid_balancing.", "bsuos.turnup_range.", "carbon.pass_through.", "range.lines",
                    # and in 1.6.0 (tests/test_version_1_6_0.py)
                    "generators_share.", "bridge.generators_share.", "option.no_generators_share.",
                    # and in 1.6.3 (tests/test_version_1_6_3.py)
                    "who_paid.")
    assert all(isinstance(figs[k], str) for k in set(figs) - all_old if not k.startswith(new_in_1_4_0))
