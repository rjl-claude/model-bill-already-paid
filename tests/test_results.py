"""The whole model run on the repository's own data, written to a temporary folder
(aios-harness#53; the results file since #140)."""
import hashlib
import math
import json

import polars as pl

from billpaid import inputs, results
from billpaid.__main__ import ROOT, main

TOP = ["meta", "model", "context", "deflators", "deflator_info", "bill", "bill_info",
       "freshness", "restatements", "scotland", "reconciliation"]


def test_results_writes_the_file_and_its_fingerprint_on_the_real_data(tmp_path):
    out = tmp_path / "clock.json"
    assert main(["results", "--out", str(out)]) == 0
    data = out.read_bytes()
    doc = json.loads(data)
    assert list(doc) == TOP
    assert doc["meta"]["model"] == "model-bill-already-paid"
    assert doc["meta"]["version"] == results.model_version()
    assert doc["meta"]["format"] == results.FORMAT
    fp, name = (out.parent / "clock.json.sha256").read_text().split()
    assert (fp, name) == (hashlib.sha256(data).hexdigest(), "clock.json")
    ids = [s["scheme_id"] for s in doc["model"]["schemes"]]
    assert {"ro", "fit", "cfd_renewable", "constraints", "capacity_market", "vat"} <= set(ids)
    assert doc["scotland"]["scotland_cost"] > 0
    assert doc["reconciliation"]["within_tolerance"] in (True, False)


def test_tables_come_back_with_their_columns_types_and_values():
    df = pl.DataFrame({"year": [2024, 2025], "cost_gbp": [1.5, 0.1 + 0.2], "label": ["a", None],
                       "date": [None, None]}, schema={"year": pl.Int64, "cost_gbp": pl.Float64,
                                                       "label": pl.String, "date": pl.Date})
    f = json.loads(json.dumps(results.frame(df)))
    back = pl.DataFrame(f["rows"], schema={k: getattr(pl, v) for k, v in f["schema"].items()},
                        orient="row")
    assert back.equals(df) and back.schema == df.schema


def test_the_loader_reads_every_reference_input_the_model_needs():
    i = inputs.load(ROOT)
    for name in ("refs", "deflators", "deflator_info", "road", "station_map",
                 "ro_stations", "bmu_map", "ctx", "bill", "bill_info", "bmu_zones", "pinned"):
        assert getattr(i, name) is not None, name
    assert "total_bill_gbp_2024" in i.bill.columns


def _same(a, b, path=""):
    """Equal, numbers to rounding (polars sums in no fixed order, so a rerun can differ in the last digit)."""
    assert type(a) is type(b), path
    if isinstance(a, dict):
        assert sorted(a) == sorted(b), path
        for k in a:
            _same(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _same(x, y, f"{path}[{i}]")
    elif isinstance(a, float):
        assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-6), (path, a, b)
    else:
        assert a == b, path


def test_the_model_still_writes_the_committed_results_file(tmp_path):
    """1.1.0 adds a figures file and changes nothing in results/clock.json (aios-harness#222): run on the
    repository's data, the model writes the committed file again, its stamp (meta) apart."""
    committed = json.loads((ROOT / "results" / results.FILE).read_text())
    doc, _ = results.assemble(ROOT, generated_at=committed["meta"]["generated_at"])
    doc = json.loads(json.dumps(doc, allow_nan=False))
    assert doc["meta"]["model"] == committed["meta"]["model"]
    assert doc["meta"]["format"] == committed["meta"]["format"]
    _same({k: v for k, v in doc.items() if k != "meta"}, {k: v for k, v in committed.items() if k != "meta"})
