"""1.7.0: the Clock's results file counts the bill already paid as Report No. 2 does (Richard, 22 Nov 2026: "publish
the report and ensure the clock is consistent"). One seam: billpaid.account.apply, which both the paper's figures
file and the Clock's results file go through."""
import pytest

from billpaid import account, figures
from billpaid.__main__ import ROOT


@pytest.fixture(scope="module")
def counted():
    return account.apply(figures.frozen_results(ROOT), ROOT)


def _to_2024(rows):
    return sum(r["cost_gbp_2024"] for r in rows if r["year"] <= 2024)


def test_the_frozen_file_counted_by_the_account_gives_the_paper_s_headline(counted):
    total = sum(_to_2024(s["annual"]["rows"]) for s in counted["model"]["schemes"])
    assert round(total / 1e9, 1) == 258.6        # the paper's all.headline.real (Report No. 2, v1.0.0)


def test_the_clock_s_own_totals_carry_the_new_line(counted):
    """The Clock shows its totals blocks, not the lines: the indirect block and the direct perspective must add up
    to the same bill, years 2002 to 2024, and to each line's total for the whole file."""
    m = counted["model"]
    indirect = _to_2024(m["indirect"]["annual"]["rows"])
    direct = _to_2024(m["perspectives"]["renewables"]["annual"]["rows"])
    assert round((direct + indirect) / 1e9, 1) == 258.6
    assert round(direct / 1e9, 1) == 125.9 and round(indirect / 1e9, 1) == 132.8   # the paper's two layers
    for name, block, members in (("indirect", m["indirect"], [s for s in m["schemes"] if s["layer"] == "indirect"]),
                                 ("renewables", m["perspectives"]["renewables"],
                                  [s for s in m["schemes"] if "renewables" in s["perspectives"]])):
        assert block["cumulative_gbp"] == pytest.approx(sum(s["cumulative_gbp"] for s in members)), name
        assert block["runrate_gbp_per_year"] == pytest.approx(sum(s["runrate_gbp_per_year"] for s in members)), name
    assert "generators_share" in {s["scheme_id"] for s in m["schemes"] if s["layer"] == "indirect"}
