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


BALANCING = ("constraints", "constraint_turnup", "bsuos")


def _rows(doc, line):
    s = next(s for s in doc["model"]["schemes"] if s["scheme_id"] == line)
    return {r["year"]: r["cost_gbp"] for r in s["annual"]["rows"]}


def test_a_new_run_differs_from_the_frozen_results_file_only_in_the_balancing_split(tmp_path):
    """1.1.0 to 1.4.0 changed nothing in results/clock.json. 1.5.0 (aios-harness#266) makes the constraints
    history National Grid's record (2010-2015) and Elexon's yearly sums (2016-2023), so a new run on the repository's data differs from the
    committed (frozen) file in the three balancing lines 2010-2023 and nowhere else among the lines; each year's
    three still add to the same total; and the new run's three lines are the ones the figures file holds.
    1.7.0 (billpaid.account) adds the generators' share of grid and balancing charges as a line of its own, after
    the others, and the VAT on it to the VAT line, by that line's own rule; no other line moves."""
    from billpaid import elexon_record
    committed = json.loads((ROOT / "results" / results.FILE).read_text())
    doc, _ = results.assemble(ROOT, generated_at=committed["meta"]["generated_at"])
    doc = json.loads(json.dumps(doc, allow_nan=False))
    assert doc["meta"]["model"] == committed["meta"]["model"]
    assert doc["meta"]["format"] == committed["meta"]["format"]
    assert doc["model"]["elexon_first_year"] == committed["model"]["elexon_first_year"] == 2024
    lines = [s["scheme_id"] for s in committed["model"]["schemes"]]
    assert [s["scheme_id"] for s in doc["model"]["schemes"]] == [*lines, "generators_share"]
    gs = _rows(doc, "generators_share")
    vat = next(s for s in doc["model"]["schemes"] if s["scheme_id"] == "vat")
    share = {r["year"]: r["share"] for r in vat["extras"]["domestic_share"]}
    for line in lines:
        new, old = _rows(doc, line), _rows(committed, line)
        assert sorted(new) == sorted(old), line
        for y in old:
            if line in BALANCING and 2010 <= y <= 2023:
                continue
            want = old[y] + (0.05 * share[y] * gs[y] if line == "vat" and y in gs else 0.0)
            assert math.isclose(new[y], want, rel_tol=1e-9, abs_tol=1e-6), (line, y)
    figures_doc, _, _ = elexon_record.apply(committed, ROOT, 2024)
    for y in range(2010, 2024):
        assert math.isclose(sum(_rows(doc, line).get(y, 0.0) for line in BALANCING),
                            sum(_rows(committed, line).get(y, 0.0) for line in BALANCING), rel_tol=1e-9), y
        for line in BALANCING:
            assert math.isclose(_rows(doc, line).get(y, 0.0), _rows(figures_doc, line).get(y, 0.0),
                                rel_tol=1e-9, abs_tol=1e-3), (line, y)


def test_the_results_file_is_counted_as_the_paper_counts_the_bill(tmp_path):
    """1.7.0 (Richard, 22 Nov 2026: "ensure the clock is consistent"): the Clock's file goes through the paper's
    account (billpaid.account), so it carries the generators' share of grid and balancing charges, and its indirect
    block is made from its lines."""
    out = tmp_path / "clock.json"
    assert main(["results", "--out", str(out)]) == 0
    m = json.loads(out.read_bytes())["model"]
    indirect = [s for s in m["schemes"] if s["layer"] == "indirect"]
    assert "generators_share" in {s["scheme_id"] for s in indirect}
    assert math.isclose(m["indirect"]["cumulative_gbp"], math.fsum(s["cumulative_gbp"] for s in indirect))
