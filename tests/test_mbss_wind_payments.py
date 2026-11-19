"""National Grid's own record of payments to wind farms, 2010-11 to 2016-17 (aios-harness#266): the Monthly
Balancing Services Summary (MBSS), "Payments to Wind Powered Generation", saved from NESO's website and typed in
reference/mbss_wind_payments.yaml. From 1.5.0 it is the model's source for 2010-2015 (billpaid.mbss).

These tests hold in place the two ways it differs from Elexon's record, which the model takes from 2016: it prints
no month before April 2013, and it counts every payment to a wind farm, in or out of the Balancing Mechanism, where
Elexon's record counts accepted bids in the Balancing Mechanism only."""
import glob
import hashlib
import math
from pathlib import Path

import polars as pl
import pytest
import yaml

from billpaid.__main__ import ROOT

ROUND = 0.05   # each printed figure is rounded to £0.1m


@pytest.fixture(scope="module")
def mbss():
    return yaml.safe_load((ROOT / "reference/mbss_wind_payments.yaml").read_text())


def _months(mbss, first, last):
    return [v for k, v in mbss["monthly_gbp_m"].items() if first <= k <= last]


def test_every_source_report_is_saved_and_is_the_file_read(mbss):
    assert len(mbss["sources"]) == 8
    for s in mbss["sources"].values():
        assert hashlib.sha256((ROOT / s["file"]).read_bytes()).hexdigest() == s["sha256"], s["file"]
        assert s["url"].startswith("https://www.neso.energy/document/")


def test_financial_year_totals_as_national_grid_prints_them(mbss):
    assert mbss["financial_year_gbp_m"] == {"2010-11": 0.2, "2011-12": 34.1, "2012-13": 7.6, "2013-14": 49.7,
                                            "2014-15": 65.3, "2015-16": 96.8, "2016-17": 83.2}


def test_the_mbss_prints_no_month_before_april_2013(mbss):
    """The table first appears in the August 2013 report, with that year's months only: 2010-11, 2011-12 and
    2012-13 are yearly totals, so calendar 2010, 2011, 2012 and January to March 2013 cannot be built."""
    months = sorted(mbss["monthly_gbp_m"])
    assert months[0] == "2013-04" and months[-1] == "2017-03"
    assert len(months) == 48


@pytest.mark.parametrize("fy,first,last", [("2013-14", "2013-04", "2014-03"), ("2014-15", "2014-04", "2015-03"),
                                           ("2015-16", "2015-04", "2016-03"), ("2016-17", "2016-04", "2017-03")])
def test_each_years_months_add_to_its_printed_total_within_rounding(mbss, fy, first, last):
    months = _months(mbss, first, last)
    assert len(months) == 12
    assert abs(math.fsum(months) - mbss["financial_year_gbp_m"][fy]) <= 13 * ROUND


def test_calendar_2014_and_2015_from_months(mbss):
    assert math.isclose(math.fsum(_months(mbss, "2014-01", "2014-12")), 57.0, abs_tol=1e-9)
    assert math.isclose(math.fsum(_months(mbss, "2015-01", "2015-12")), 96.9, abs_tol=1e-9)
    # April to December 2013 only: January to March 2013 lie inside 2012-13's £7.6m
    assert math.isclose(math.fsum(_months(mbss, "2013-04", "2013-12")), 33.7, abs_tol=1e-9)


def _elexon_month(month: str) -> float:
    """£m, Elexon's accepted wind bids that month, each day's latest version in the store."""
    total = 0.0
    days = sorted(glob.glob(str(ROOT / "data/raw/constraints/daily" / f"{month}-*")))
    assert len(days) >= 28, month
    for d in days:
        total += math.fsum(pl.read_parquet(sorted(glob.glob(d + "/*/data.parquet"))[-1])["cost_gbp"].to_list())
    return total / 1e6


def _span(first, last):
    y, m = map(int, first.split("-"))
    out = []
    while f"{y}-{m:02d}" <= last:
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def test_where_they_overlap_the_mbss_matches_elexon_until_july_2016_then_runs_higher(mbss):
    """December 2015 to July 2016: the two agree within rounding, so with no payments outside the Balancing
    Mechanism the MBSS is Elexon's series. August 2016 to March 2017: the MBSS is about £8.6m (14%) higher. So the
    MBSS is the wider count, and calendar 2016 on the MBSS would be about £7m above the model's Elexon figure."""
    early, late = _span("2015-12", "2016-07"), _span("2016-08", "2017-03")
    m = mbss["monthly_gbp_m"]
    gap_early = math.fsum(m[k] for k in early) - math.fsum(_elexon_month(k) for k in early)
    gap_late = math.fsum(m[k] for k in late) - math.fsum(_elexon_month(k) for k in late)
    assert abs(gap_early) <= len(early) * ROUND
    assert 8.0 < gap_late < 9.2
    y2016 = _span("2016-01", "2016-12")
    assert 6.5 < math.fsum(m[k] for k in y2016) - math.fsum(_elexon_month(k) for k in y2016) < 8.0
