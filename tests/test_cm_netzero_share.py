"""Capacity Market: only the part net zero caused is counted (change of
13 October 2026). Pins the per-year share and the carry-forward of the last
modelled year. (What the site publishes from it, and the change-log entry, are
tested in web-subsidy-clock.)"""
from datetime import date
from pathlib import Path

import polars as pl
import pytest

from billpaid import reference
from billpaid.schemes import capacity_market

REF = Path("reference/capacity_market_netzero_share.yaml")


def deflators():
    return pl.DataFrame({"year": [2002, 2003, 2004, 2005, 2023, 2024, 2025],
                         "index": [70.0, 71.0, 72.0, 73.0, 128.0, 132.0, 136.0]},
                        schema={"year": pl.Int64, "index": pl.Float64})


def _share_table(rows: dict[int, tuple[float, float, float, float]], carry: int) -> dict:
    """rows: year -> (cm_paid, netzero, low, high)."""
    years = {}
    for y, (paid, nz, lo, hi) in rows.items():
        years[y] = {"cm_paid_gbp": paid, "netzero_gbp": nz,
                    "netzero_low_gbp": lo, "netzero_high_gbp": hi,
                    "share": nz / paid, "share_low": lo / paid, "share_high": hi / paid}
    return {"years": years, "carry_forward_from": carry, "provenance": {}}


def _build_cm(tmp_path, payments: dict[date, float], cm_share):
    from billpaid.store import SnapshotStore
    store = SnapshotStore(tmp_path)
    cm = pl.DataFrame({"date": list(payments), "auction": ["T-4"] * len(payments),
                       "payment_gbp": list(payments.values())},
                      schema={"date": pl.Date, "auction": pl.String, "payment_gbp": pl.Float64})
    store.write("capacity_market", "payments", cm, source_url="u", date_col="date")
    return None, capacity_market.result(store, cm_share, deflators())[0]


def test_per_year_share_applied_to_each_month(tmp_path):
    share = _share_table({2024: (300.0, 75.0, 30.0, 300.0),     # 25%
                          2025: (200.0, 100.0, 20.0, 200.0)},   # 50%
                         carry=2025)
    _, cm = _build_cm(tmp_path, {date(2024, 1, 1): 100.0, date(2024, 6, 1): 200.0,
                                 date(2025, 3, 1): 120.0, date(2025, 9, 1): 80.0}, share)
    annual = {r["year"]: r["cost_gbp"] for r in cm.annual.to_dicts()}
    assert annual == pytest.approx({2024: 75.0, 2025: 100.0})
    assert cm.cumulative_gbp == pytest.approx(175.0)
    assert cm.attribution_pct == pytest.approx(175.0 / 500.0)
    # the raw levy is still published beside the counted part
    assert {r["year"]: r["cost"] for r in cm.extras["raw_annual"]} == {2024: 300.0, 2025: 200.0}
    # the range: low and high are the same rule with the low/high shares
    assert cm.extras["range"]["low"]["cumulative"] == pytest.approx(30.0 + 20.0)
    assert cm.extras["range"]["high"]["cumulative"] == pytest.approx(500.0)
    # run-rate is the 12 months to the latest month (Oct 2024-Sep 2025) of
    # the COUNTED series: only the two 2025 months, at the 2025 share
    assert cm.runrate_gbp_per_year == pytest.approx(0.5 * (120.0 + 80.0))


def test_years_after_the_model_carry_the_last_share_forward(tmp_path):
    share = _share_table({2025: (200.0, 50.0, 10.0, 200.0)}, carry=2025)    # 25%
    _, cm = _build_cm(tmp_path, {date(2025, 1, 1): 200.0, date(2026, 1, 1): 40.0,
                                 date(2027, 1, 1): 60.0}, share)
    annual = {r["year"]: r["cost_gbp"] for r in cm.annual.to_dicts()}
    assert annual[2026] == pytest.approx(10.0)
    assert annual[2027] == pytest.approx(15.0)
    basis = {r["year"]: r["basis"] for r in cm.extras["netzero_share"]}
    assert basis == {2025: "modelled", 2026: "carried forward from 2025",
                     2027: "carried forward from 2025"}


def test_a_stale_share_fails_the_build(tmp_path):
    """The share was computed against the engine's CM total; if LCCC restates
    the year by more than 2% the share no longer applies."""
    share = _share_table({2025: (200.0, 50.0, 10.0, 200.0)}, carry=2025)
    with pytest.raises(ValueError, match="rerun the gas-counterfactual engine"):
        _build_cm(tmp_path, {date(2025, 1, 1): 210.0}, share)


def test_a_year_before_the_model_is_an_error_not_full_levy(tmp_path):
    share = _share_table({2025: (200.0, 50.0, 10.0, 200.0)}, carry=2025)
    with pytest.raises(ValueError, match="no net-zero share"):
        _build_cm(tmp_path, {date(2024, 1, 1): 10.0, date(2025, 1, 1): 200.0}, share)


def test_cm_data_without_a_share_table_fails_rather_than_counting_in_full(tmp_path):
    with pytest.raises(ValueError, match="net-zero share"):
        _build_cm(tmp_path, {date(2025, 1, 1): 200.0}, None)


# ---- the committed reference file and the published data ----

def test_reference_file_shares_match_the_engine_and_2025_carries():
    # aios-harness#42 (decision 0168): the s32 hand copy (reference/capacity_market_netzero_share.yaml) is
    # retired; the shares are the pinned engine release's netzero_gbp over the register's CM paid
    from billpaid import register as R
    root = Path(".").resolve()
    assert not (root / "reference/capacity_market_netzero_share.yaml").exists()
    cm = R.cm_share_from_engine(root, R.load_pinned(root))
    assert sorted(cm["years"]) == list(range(2016, 2026))
    assert cm["carry_forward_from"] == 2025
    y25 = cm["years"][2025]
    # v4-s43 Clock export: netzero 209,095,098.25 over CM paid 1,431,463,285.03 (register CM_PAID 2025)
    assert y25["share"] == pytest.approx(209.09509825 / 1431.46328503, rel=1e-6)
    assert cm["provenance"]["engine"] == "gas-counterfactual v4-s43"
    for y, r in cm["years"].items():
        assert 0.0 <= r["share_low"] <= r["share"] <= r["share_high"] == pytest.approx(1.0), y
    assert all(cm["years"][y]["share"] < 0.5 for y in range(2017, 2026))


def test_reference_file_rejects_an_impossible_share(tmp_path):
    p = tmp_path / "cm.yaml"
    p.write_text("carry_forward_from: 2025\nyears:\n  2025: {cm_paid_gbp: 100, netzero_gbp: 120, "
                 "netzero_low_gbp: 10, netzero_high_gbp: 100}\n")
    with pytest.raises(ValueError, match="shares must satisfy"):
        reference.load_cm_netzero_share(p)
