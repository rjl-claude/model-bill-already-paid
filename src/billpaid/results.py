"""The model's one results file: everything the Subsidy Clock's website and Report No. 2 read.

`write` runs the whole model from the snapshot store and reference inputs and writes
results/clock.json, stamped with the model's version and commit, and beside it
results/clock.json.sha256, the file's fingerprint. A reader checks both: a file from
another model version, or one changed after the model wrote it, is refused.

Tables are written as {"schema": {column: polars dtype}, "rows": [...]}, so a reader
rebuilds exactly the tables the model held (same columns, same types, same values).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
from datetime import date, datetime
from importlib.metadata import version as _pkg_version
from pathlib import Path

import polars as pl

from billpaid import inputs, reconcile
from billpaid.money import SchemeResult
from billpaid.store import SnapshotStore
from billpaid import scotland
from billpaid.schemes import constraint_turnup

MODEL = "model-bill-already-paid"
FORMAT = 1                      # the file's layout; a reader refuses any other
FILE = "clock.json"

# the feeds whose freshness the site shows (scheme, table)
FRESHNESS = [("cfd", "generation"), ("constraints", "daily"), ("capacity_market", "payments"),
             ("bsuos", "daily"), ("constraint_turnup", "daily")]
FRESHNESS_KEYS = ("retrieved_at", "source_date", "source_url", "row_count")

_DTYPES = {"Int64": pl.Int64, "Int32": pl.Int32, "Float64": pl.Float64, "String": pl.String,
           "Boolean": pl.Boolean, "Date": pl.Date}


def model_version() -> str:
    return _pkg_version(MODEL)


def _commit(root: Path) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "src"],
                               capture_output=True, text=True, check=True).stdout.strip()
        return out + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return None


def _value(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def frame(df: pl.DataFrame | None) -> dict | None:
    """A polars table as JSON: its schema and its rows."""
    if df is None:
        return None
    schema = {}
    for name, dt in df.schema.items():
        key = str(dt)
        if key not in _DTYPES:
            raise TypeError(f"column {name!r} has type {key}, which the results file does not carry")
        schema[name] = key
    return {"schema": schema,
            "rows": [{k: _value(v) for k, v in r.items()} for r in df.iter_rows(named=True)]}


def _scheme(s: SchemeResult) -> dict:
    out = {}
    for f in dataclasses.fields(s):
        v = getattr(s, f.name)
        out[f.name] = frame(v) if isinstance(v, pl.DataFrame) else _value(v)
    return out


def _block(b: dict) -> dict:
    """A totals block (a perspective, or the indirect layer): its annual table as a table."""
    return {k: frame(v) if isinstance(v, pl.DataFrame) else v for k, v in b.items()}


def assemble(root: Path, *, generated_at: str) -> tuple[dict, dict]:
    """The results document, and the register overlay report (printed by the CLI)."""
    store = SnapshotStore(root / "data")
    inp = inputs.load(root)
    model, overlay = inputs.assemble_model(root, inp)

    freshness = {}
    for scheme_id, table in FRESHNESS:
        f = store.freshness(scheme_id, table)
        if f:
            freshness[scheme_id] = {k: f.get(k) for k in FRESHNESS_KEYS}

    scot = None
    con_daily = store.read_all_partitions("constraints", "daily")
    if con_daily is not None and con_daily.height:
        cons = inp.ctx["electricity_consumption_by_nation"]
        scot = scotland.build_payload(
            con_daily, inp.bmu_zones,
            scot_twh=cons["scotland_gwh"] / 1000, gb_twh=cons["gb_gwh"] / 1000,
            consumption_source=cons["source"], consumption_url=cons["source_url"],
            generated_at=generated_at, turnup_daily=constraint_turnup.daily_cost(store))

    recon = None
    gen, trk = store.latest("cfd", "generation"), store.latest("cfd", "tracking")
    if gen is not None and trk is not None:
        bottom_up = gen.group_by("date").agg(pl.col("payment_gbp").sum().alias("cost_gbp"))
        recon = reconcile.cfd_monthly(bottom_up, trk)

    doc = {
        "meta": {"model": MODEL, "version": model_version(), "format": FORMAT,
                 "commit": _commit(root), "generated_at": generated_at},
        "model": {**{k: v for k, v in model.items() if k not in ("schemes", "perspectives", "indirect")},
                  "schemes": [_scheme(s) for s in model["schemes"]],
                  "perspectives": {k: _block(b) for k, b in model["perspectives"].items()},
                  "indirect": _block(model["indirect"])},
        "context": inp.ctx,
        "deflators": frame(inp.deflators),
        "deflator_info": inp.deflator_info,
        "bill": frame(inp.bill),
        "bill_info": inp.bill_info,
        "freshness": freshness,
        "restatements": store.all_restatements(),
        "scotland": scot,
        "reconciliation": recon,
    }
    return doc, {"model": model, "overlay": overlay, "scotland": scot, "reconciliation": recon}


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(doc: dict, out: Path) -> str:
    """Write the results file and its fingerprint beside it; returns the fingerprint."""
    out.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=1, allow_nan=False) + "\n").encode()
    out.write_bytes(data)
    fp = fingerprint(data)
    out.with_name(out.name + ".sha256").write_text(f"{fp}  {out.name}\n")
    return fp
