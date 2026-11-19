"""Version 1.6.2 (the independent check of 1.6.1, 19 Nov 2026: three wording faults): words only, no number moves.
1.6.1's values come from its own figures file at tag v1.6.1."""
import json
import subprocess

import pytest

from billpaid import bridge, figures
from billpaid.__main__ import ROOT

# the text values 1.6.2 rewrites (docs/1.6.2-against-1.6.1.md)
CHANGED_TEXT = {"generators_share.range.method", "generators_share.2025.source"}


@pytest.fixture(scope="module")
def doc():
    return figures.document(figures.frozen_results(ROOT), bridge.no1_release(ROOT))


@pytest.fixture(scope="module")
def v161():
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "refs/tags/v1.6.1:results/figures.json"],
                                     capture_output=True, check=True).stdout)


def test_every_number_is_1_6_1s_exactly_and_only_the_named_words_change(doc, v161):
    new, old = doc["figures"], v161["figures"]
    assert set(new) == set(old)
    for k, v in old.items():
        if isinstance(v, str):
            assert (new[k] != v) == (k in CHANGED_TEXT), k
        else:
            assert new[k] == v, k


def test_no_text_says_residual_balancing_or_points_to_a_superseded_section(doc):
    texts = [v for v in doc["figures"].values() if isinstance(v, str)] + list(doc["meta"]["keys"].values())
    for t in texts:
        assert "residual balancing" not in t and "Version 1.6.0" not in t and "Version 1.6.1" not in t, t
    assert "Version 1.6.2" in doc["figures"]["generators_share.range.method"]
    assert "switch-off" in doc["meta"]["keys"]["generators_share.<grid>.<year>.<m>"]
    src = (ROOT / "src/billpaid/generators_share.py").read_text()
    assert '"Version 1.6.0"' not in src and "Version 1.6.0" not in src.split('"""')[1]


def test_the_docs_have_one_current_account_and_state_the_limits():
    docs = (ROOT / "docs" / "figures.md").read_text()
    current = docs[docs.index("## Version 1.6.2"):]
    for words in ("simplification", "spread by output", "Great Britain", "£5.9m", "£10-20m"):
        assert words in current, words
    assert "actually on the RO" not in docs and "end of their 20 years" not in docs
