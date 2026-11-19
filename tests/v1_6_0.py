"""What version 1.6.0 (report-series ADR 0264) moves, for the older versions' "nothing else moves" tests: a new
indirect line, the generators' share of grid and balancing charges not paid out of subsidy, so every total that
holds all lines, the VAT on it, the bridge's two ends and the steps that reconcile it, and the headline's range and
counting options. The moves are tested in tests/test_version_1_6_0.py; the line in tests/test_generators_share.py."""
import re

Y = r"(20(0[2-9]|1\d|2[0-5]))"
MOVED = re.compile(
    rf"(all|indirect|vat)\.({Y}|headline)\.(cash|real)"
    r"|all\.(2025|headline)\.(estimated|modelled)\.(cash|real)"
    rf"|bridge\.(no2_money_paid|power_before_carbon|vat)\.({Y}|headline)\.(cash|real)"
    r"|bridge\.(no2_money_paid|power_before_carbon)\.label|bridge\.steps"
    r"|carbon\.pass_through\.headline\.(low|high)\.(cash|real)"
    r"|option\.(carbon_tax_only|ccl_above_2001|cm_whole_levy|energy_saving_schemes|grid_whole|no_carbon|no_ccl)"
    r"\.headline\.(cash|real)"
    r"|option\.no_grid_balancing\.less_than_headline\.(cash|real)"
    rf"|(own_bills\.)?per_household\.({Y}\.real|year_by_year\.headline\.real|headline\.real)"
    r"|per_household\.(2024|headline)"
    r"|range\.(low|high)\.headline\.(cash|real)|range\.lines"
    rf"|share_of_bill\.({Y}|headline)")
NEW = re.compile(r"(bridge\.)?generators_share\..+|option\.no_generators_share\.headline\.(cash|real)")


def moved(key: str) -> bool:
    return bool(MOVED.fullmatch(key))
