"""The freeze of version 1.1.0 (aios-harness#226; Report No. 2's plan step 10, ADR 0228 in report-series).

1.1.0 is frozen on Gitea only (branch and tag `v1.1.0`); GitHub `master` and the Clock stay on 1.0.0 until the
paper's release. The paper reads `results/figures.json` as committed at the tag, pinned by its sha256."""
import json

from billpaid import bridge, figures, results
from billpaid.__main__ import ROOT


def test_the_model_is_version_1_1_0_and_its_figures_file_says_so():
    assert results.model_version() == "1.1.0"
    doc = figures.document(figures.frozen_results(ROOT), bridge.no1_release(ROOT))
    assert doc["meta"]["version"] == "1.1.0"
    # built from the frozen 1.0.0 file, which stays as it was
    assert doc["meta"]["built_from"]["version"] == "1.0.0"


def test_the_committed_figures_file_is_the_one_the_model_builds(tmp_path):
    """The file the paper pins is reproducible: a fresh build is byte for byte the committed file, and the
    fingerprint beside it is that file's."""
    out = tmp_path / "figures.json"
    fp = results.write(figures.document(figures.frozen_results(ROOT), bridge.no1_release(ROOT)), out)
    committed = ROOT / "results" / "figures.json"
    assert committed.read_bytes() == out.read_bytes()
    assert (ROOT / "results" / "figures.json.sha256").read_text() == f"{fp}  figures.json\n"
    assert json.loads(committed.read_text())["meta"]["version"] == "1.1.0"
