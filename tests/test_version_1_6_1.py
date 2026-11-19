"""Version 1.6.1 (the coordinator's ruling of 19 Nov 2026 on 1.6.0's judgement 6, under report-series ADR 0264): the
new line's balancing part takes the generators' share of the whole BSUoS charge, switch-off payments and turn-up
included. What moves against 1.6.0 (tagged, never pinned); against 1.5.0, the paper's pin: tests/test_version_1_6_0.py."""
import json
import math
import re
import subprocess

import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT
from tests import v1_6_0

# Against 1.6.0: what holds the balancing part of the new line. The grid part, the unsubsidised share, the output and
# the headline without the line do not move. 2024 and 2025 do not move (the generators' share of BSUoS is nil from
# April 2023).
MOVED = re.compile(r"generators_share\.(bsuos\.)?(20(0[2-9]|1\d|2[0-3])|headline)\.(cash|real)"
                   r"|generators_share\.range\.(low|high)\.(20(0[2-9]|1\d|2[0-3])|headline)\.(cash|real)"
                   r"|bridge\.generators_share\.(20(0[2-9]|1\d|2[0-3])|headline)\.(cash|real)")


@pytest.fixture(scope="module")
def figs():
    return figures.build(figures.frozen_results(ROOT), bridge.no1_release(ROOT))


@pytest.fixture(scope="module")
def v160():
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.6.0:results/figures.json"],
                                     capture_output=True, check=True).stdout)["figures"]


def _same(a, b) -> bool:
    return a == b or (isinstance(a, float) and math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-9))


def test_against_1_6_0_only_the_balancing_part_and_what_holds_it_move(figs, v160):
    assert set(figs) == set(v160)
    moved = {k for k in v160 if not _same(v160[k], figs[k])}
    from tests.test_version_1_6_2 import CHANGED_TEXT   # 1.6.2 rewrites these words, no number
    allowed = {k for k in v160 if MOVED.fullmatch(k) or v1_6_0.moved(k)} | CHANGED_TEXT
    assert moved <= allowed, sorted(moved - allowed)
    for k in ("generators_share.headline.real", "generators_share.bsuos.headline.cash", "all.headline.real",
              "bridge.generators_share.headline.real", "vat.headline.real"):
        assert k in moved, k
    for k in ("generators_share.tnuos.headline.real", "generators_share.unsubsidised_share.2015.central",
              "option.no_generators_share.headline.real", "generators_share.2024.cash", "bridge.no1_extra_cost.headline.real"):
        assert k not in moved, k


def test_the_bridge_step_is_now_only_the_subsidised_stations_part(figs):
    """No. 1's generators' share less the line is the subsidised stations' part of it, every year: the share above
    the alternative (grid and balancing) times the subsidised share of output."""
    for y in range(2002, 2025):
        for m in ("cash", "real"):
            share = figs[f"generators_share.tnuos.{y}.{m}"] + figs[f"generators_share.bsuos.{y}.{m}"]
            sub = share * (1 - figs[f"generators_share.unsubsidised_share.{y}.central"])
            assert math.isclose(figs[f"bridge.generators_share.{y}.{m}"], sub, rel_tol=1e-9, abs_tol=1.0), (y, m)
