"""Version 1.6.0 (report-series ADR 0264; Richard, 19 Nov 2026), as corrected by 1.6.1: what the new line moves from
1.5.0, the paper's pin, and that nothing else moves. 1.5.0's values come from its own frozen figures file at tag v1.5.0."""
import json
import math
import subprocess

import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT
from tests import v1_6_0


@pytest.fixture(scope="module")
def figs():
    return figures.build(figures.frozen_results(ROOT), bridge.no1_release(ROOT))


@pytest.fixture(scope="module")
def old():
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.5.0:results/figures.json"],
                                     capture_output=True, check=True).stdout)["figures"]


def _same(a, b) -> bool:
    return a == b or (isinstance(a, float) and math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-9))


def test_no_1_5_0_key_is_dropped_and_only_the_named_values_move(figs, old):
    assert set(old) <= set(figs)
    moved = {k for k in old if not _same(old[k], figs[k])}
    assert moved == {k for k in old if v1_6_0.moved(k)}, sorted(moved ^ {k for k in old if v1_6_0.moved(k)})
    assert all(v1_6_0.NEW.fullmatch(k) for k in set(figs) - set(old)), sorted(
        k for k in set(figs) - set(old) if not v1_6_0.NEW.fullmatch(k))


def test_every_moved_total_moves_by_the_line_and_its_vat(figs, old):
    """all moves by the line plus 5% of households' share of it, each year 2002-2025; the headline likewise."""
    for y in range(2002, 2026):
        for m in ("cash", "real"):
            line = figs[f"generators_share.{y}.{m}"]
            added = line * (1 + 0.05 * figs[f"vat.domestic_share.{y}"])
            assert figs[f"all.{y}.{m}"] == pytest.approx(old[f"all.{y}.{m}"] + added, rel=1e-12, abs=1e-3)
            assert figs[f"bridge.no2_money_paid.{y}.{m}"] == figs[f"all.{y}.{m}"] if y < 2025 else True


def test_the_version_is_1_6_2():
    import tomllib
    assert tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"] == "1.6.2"
