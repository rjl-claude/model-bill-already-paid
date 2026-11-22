"""Version 1.6.3 (Richard, 21 Nov 2026: "Was it not possible to do that for the bill paid to date?"): who paid the
bill already paid, households on their own bills and businesses, as national totals. New keys only: every key of
1.6.2 is exactly as it was. 1.6.2's values come from its own figures file at tag v1.6.2."""
import json
import re
import subprocess
import tomllib

import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT

NEW = re.compile(r"who_paid\.(households|businesses)\.(\d{4}|headline)\.real|who_paid\.households\.headline\.share")
YEARS = range(2002, 2025)


@pytest.fixture(scope="module")
def doc():
    return figures.document(figures.frozen_results(ROOT), bridge.no1_release(ROOT))


@pytest.fixture(scope="module")
def v162():
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.6.2:results/figures.json"],
                                     capture_output=True, check=True).stdout)


def test_the_version_is_1_7_0():
    assert tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"] == "1.7.0"


def test_every_key_of_1_6_2_is_exactly_as_it_was_and_only_who_paid_keys_are_new(doc, v162):
    new, old = doc["figures"], v162["figures"]
    assert all(new[k] == v for k, v in old.items())
    added = set(new) - set(old)
    assert added and all(NEW.fullmatch(k) for k in added), sorted(k for k in added if not NEW.fullmatch(k))


def test_households_and_businesses_add_up_to_the_bill_each_year_and_over_2002_to_2024(doc):
    f = doc["figures"]
    for y in list(YEARS) + [2025]:
        assert f[f"who_paid.households.{y}.real"] + f[f"who_paid.businesses.{y}.real"] == pytest.approx(f[f"all.{y}.real"])
    assert f["who_paid.households.headline.real"] == pytest.approx(sum(f[f"who_paid.households.{y}.real"] for y in YEARS))
    assert (f["who_paid.households.headline.real"] + f["who_paid.businesses.headline.real"]
            == pytest.approx(f["all.headline.real"]))
    assert f["who_paid.households.headline.share"] == pytest.approx(
        f["who_paid.households.headline.real"] / f["all.headline.real"])


def test_the_households_total_is_the_money_behind_the_own_bills_figure(doc):
    """own_bills.per_household.<year>.real is this money over households: Great Britain's, but the UK's for the
    Obligation's part. So the total is the per-household figure times Great Britain's households, plus the
    Obligation's part times the gap between the two counts: never less, and never more than the whole Obligation
    with its VAT times that gap."""
    f = doc["figures"]
    for y in YEARS:
        gb, uk = f[f"households.gb.{y}"], f[f"households.uk.{y}"]
        over = f[f"who_paid.households.{y}.real"] - f[f"own_bills.per_household.{y}.real"] * gb
        assert 0 <= over <= (1 - gb / uk) * f[f"ro.{y}.real"] * (1 + f["vat.rate"])


def test_businesses_pay_all_of_the_climate_change_levy(doc):
    f = doc["figures"]
    for y in YEARS:
        assert f[f"who_paid.businesses.{y}.real"] >= f[f"ccl.{y}.real"]


def test_the_new_keys_are_described(doc):
    keys = doc["meta"]["keys"]
    for k in ("who_paid.households.<year>.real", "who_paid.businesses.<year>.real",
              "who_paid.households.headline.real", "who_paid.businesses.headline.real",
              "who_paid.households.headline.share"):
        assert k in keys and "household" in keys[k] or "business" in keys[k], k
