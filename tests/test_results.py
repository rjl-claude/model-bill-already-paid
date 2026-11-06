"""The whole model run on the repository's own data, written to a temporary folder
(aios-harness#53; the results file since #140)."""
import hashlib
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
