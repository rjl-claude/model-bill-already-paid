"""Wind switch-off (constraint) payments 2010-2015 from National Grid's own record (version 1.5.0, aios-harness#266;
Richard's ruling of 19 Nov 2026): the Monthly Balancing Services Summary, section "Payments to Wind Powered
Generation", as typed with its saved reports in reference/mbss_wind_payments.yaml.

National Grid prints each month from April 2013 and, before that, one total for each April-March year (2010/11,
2011/12, 2012/13; none before). So:

- a calendar year whose twelve months are printed is their sum (2014, 2015);
- the three April-March totals are spread by the model's rule for April-March years (calendar_years.fy_to_cy):
  a quarter to the calendar year they end in, three quarters to the one they start in (2010, 2011, 2012, and
  January-March 2013, to which April-December 2013's printed months are added).

The six years' total is what National Grid printed, whatever the spread; only its split between 2010, 2011, 2012
and 2013 is estimated (SPREAD_YEARS). The count is every payment to a wind farm, in or out of the Balancing
Mechanism; Elexon's record, which the model takes from 2016, is accepted bids in the Balancing Mechanism.
"""
from __future__ import annotations

import math
from pathlib import Path

import yaml

from billpaid.calendar_years import fy_to_cy

FILE = "reference/mbss_wind_payments.yaml"
YEARS = range(2010, 2016)
SPREAD_YEARS = (2010, 2011, 2012, 2013)   # years holding part of an April-March total with no months printed
FIRST_MONTH = "2013-04"


def calendar_years(root: Path) -> dict[int, float]:
    """{calendar year: £ cash}, 2010-2015."""
    doc = yaml.safe_load((root / FILE).read_text())
    months = {k: float(v) for k, v in doc["monthly_gbp_m"].items()}
    if min(months) != FIRST_MONTH:
        raise ValueError(f"{FILE}: months start at {min(months)}, not {FIRST_MONTH}")
    # April-March totals with no months printed, keyed by start year
    fy = {int(k[:4]): float(v) for k, v in doc["financial_year_gbp_m"].items() if int(k[:4]) < int(FIRST_MONTH[:4])}
    fy[int(FIRST_MONTH[:4])] = 0.0        # 2013/14 is taken from its months, not spread
    spread = fy_to_cy(fy, YEARS[:4])
    out = {}
    for y in YEARS:
        printed = [v for k, v in months.items() if k.startswith(f"{y}-")]
        if y not in SPREAD_YEARS and len(printed) != 12:
            raise ValueError(f"{FILE}: {y} has {len(printed)} months, not 12")
        out[y] = round(spread.get(y, 0.0) + math.fsum(printed), 3) * 1e6   # printed to £0.1m; a quarter is £0.025m
    return out
