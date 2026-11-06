"""Fix 5 guard, wired into the build (robustness spec, 17 Oct 2026; aios-harness#37).

The guard itself (which years bottom-up replaces, and which pins are refused) is tested
through the splice module's interface in test_splice.py. Here: that build() goes through
it for constraints and BSUoS, and what the model hands the site."""
from datetime import date, timedelta

import polars as pl
import pytest

from billpaid.reference import ReferenceScheme
from billpaid.store import SnapshotStore
from billpaid import build as uk_build

REF = {2022: 227.2e6, 2023: 310.5e6, 2024: 394.3e6, 2025: 382.1e6}


def _deflators():
    return pl.DataFrame({"year": [2022, 2023, 2024, 2025], "index": [120.5, 128.6, 132.9, 138.0]},
                        schema={"year": pl.Int64, "index": pl.Float64})


def _annual(sid, values, bottom_up_from=None):
    df = pl.DataFrame({"year": list(values), "cost_gbp": list(values.values())},
                      schema={"year": pl.Int64, "cost_gbp": pl.Float64})
    return ReferenceScheme(sid, sid, ["renewables", "low_carbon"], "annual", "s", "https://s",
                           True, df, bottom_up_from=bottom_up_from)


def _store(path, earliest, latest=date(2025, 1, 3)):
    store = SnapshotStore(path)
    d = earliest
    while d <= latest:
        store.write("constraints", "daily",
                    pl.DataFrame({"date": [d], "bmu": ["T_W-1"], "lead_party": ["W"],
                                  "volume_mwh": [-1.0], "cost_gbp": [1.0e6]}),
                    source_url="u", partition=d.isoformat())
        d += timedelta(days=1)
    return store


def _refs(pin=2024):
    return {"constraints_history": _annual("constraints_history", REF, pin),
            "ro": _annual("ro", {2024: 1.0}), "fit": _annual("fit", {2024: 1.0})}


def test_the_build_refuses_a_partly_held_constraints_pin(tmp_path):
    with pytest.raises(ValueError, match=r"constraints bottom_up_from 2023 .*not every day"):
        uk_build.build(_store(tmp_path, date(2023, 8, 25)), _refs(2023), deflators=_deflators())


def test_the_build_refuses_a_bsuos_history_with_no_pin(tmp_path):
    store = _store(tmp_path, date(2023, 8, 25))
    store.write("bsuos", "daily", pl.DataFrame(
        {"date": [date(2024, 12, 30)], "cost_gbp": [1.0]},
        schema={"date": pl.Date, "cost_gbp": pl.Float64}), source_url="u", partition="2024-2025")
    refs = _refs() | {"bsuos_history": _annual("bsuos_history", {2016: 1.0})}
    with pytest.raises(ValueError, match="bsuos history states no bottom_up_from"):
        uk_build.build(store, refs, deflators=_deflators(), road={"bsuos": {"years": {2025: 0.1}, "carry_forward_from": 2025,
                                                            "engine_version": "test", "what": "test road"}})


def test_the_pinned_year_and_the_held_window_are_in_the_model(tmp_path):
    # the pages say from which year Elexon replaces REF and from which day data is held
    m = uk_build.build(_store(tmp_path / "store", date(2023, 8, 25)), _refs(), deflators=_deflators())
    assert m["elexon_first_year"] == 2024
    con = next(s for s in m["schemes"] if s.scheme_id == "constraints")
    assert (con.extras["held_from"], con.extras["held_to"]) == ("2023-08-25", "2025-01-03")
    assert "bottom_up_from" not in con.extras


def test_with_no_elexon_data_the_elexon_year_is_none(tmp_path):
    # nothing from Elexon is used then, so publishing 2024 would be false
    m = uk_build.build(SnapshotStore(tmp_path / "store"), _refs(), deflators=_deflators())
    assert m["elexon_first_year"] is None
