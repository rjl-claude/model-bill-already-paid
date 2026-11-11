"""The paid side checked against the totals others publish (version 1.2.0, aios-harness#235; outline §4.2, §4.3,
Annex B; missing figure M7). Each check is `check.<publisher>.<what>.headline.<model|reference|gap|ratio>`, £ cash
as paid, over the years both cover (`.years`), with what each side holds in words (`.basis`): gap is model less
reference, ratio model over reference. Each reference is read from the publisher's saved file
(billpaid.outline_sources). Method: docs/figures.md, "The checks (1.2.0)".
"""
from __future__ import annotations

import math
from pathlib import Path

from billpaid import outline_sources as src

LAST = 2024


def _put(out: dict, name: str, model: float, reference: float, years: str, basis: str) -> None:
    k = f"check.{name}"
    out[f"{k}.headline.model"], out[f"{k}.headline.reference"] = model, reference
    out[f"{k}.headline.gap"], out[f"{k}.headline.ratio"] = model - reference, model / reference
    out[f"{k}.years"], out[f"{k}.basis"] = years, basis


def ccl(out: dict, root: Path) -> None:
    hmrc = src.hmrc_ccl_electricity(root)
    years = range(2002, LAST + 1)
    _put(out, "hmrc.ccl", sum(out[f"ccl.{y}.cash"] for y in years), sum(hmrc[y] for y in years), "2002-2024",
         "the CCL line against HMRC's electricity declarations by calendar year (Table 1b), the UK: the line is "
         "HMRC's figure")


def levies(out: dict, root: Path, doc: dict) -> None:
    """OBR's environmental levies outturn against the RO line (obligation years, April-March) and CfD (LCCC's
    payments summed April-March), 2002-03 to 2024-25. The OBR's series also holds the Warm Home Discount and the
    green gas levy, which the model does not count, and not the Capacity Market or Feed-in Tariffs (ONS)."""
    obr = src.obr_environmental_levies(root)
    cfd = _cfd_by_fy(doc, root)
    years = range(2002, LAST + 1)
    model = sum(out[f"ro.{y}.cash"] + cfd.get(y, 0.0) for y in years)
    _put(out, "obr.levies", model, sum(obr[y] for y in years), "2002-03 to 2024-25",
         "the RO line and CfD by financial year against the OBR's environmental levies outturn (public finances "
         "databank, October 2026), which also holds the Warm Home Discount and the green gas levy, not counted here")


def ro(out: dict, root: Path) -> None:
    """The RO line against Ofgem's scheme value, SY1 to SY23: the gap is the mutualisation received
    (2017-18 to 2021-22), which the line adds and the scheme value leaves out."""
    ofgem = src.ofgem_ro_scheme_value(root)
    years = range(2002, LAST + 1)
    _put(out, "ofgem.ro", sum(out[f"ro.{y}.cash"] for y in years), sum(ofgem[y] for y in years),
         "2002-03 to 2024-25",
         "the RO line (obligation years, UK) against Ofgem's scheme value, ROCs presented x the worth of a ROC; "
         "the line adds the mutualisation payments received in 2017-18 to 2021-22")


def fit(out: dict, root: Path) -> None:
    years = range(2010, LAST + 1)
    ofgem = src.ofgem_fit_levelisation(root, years)
    _put(out, "ofgem.fit", sum(out[f"fit.{y}.cash"] for y in years), sum(ofgem[y] for y in years),
         "2010-11 to 2024-25",
         "the FiT line (scheme years, GB) against the levelisation fund printed in Ofgem's annual report or "
         "annual levelisation notice for each year: the line is Ofgem's figure")


def _cfd_by_fy(doc: dict, root: Path) -> dict[int, float]:
    import polars as pl

    from billpaid.outline import cfd_payments
    g = cfd_payments(doc, root).with_columns(
        (pl.col("date").dt.year() - (pl.col("date").dt.month() < 4).cast(pl.Int32)).alias("fy"))
    by: dict[int, list[float]] = {}
    for fy, pay in g.select("fy", "payment_gbp").iter_rows():
        by.setdefault(fy, []).append(pay)
    return {fy: math.fsum(v) for fy, v in by.items()}   # exact, whatever the rows' order


def ref(out: dict, root: Path, doc: dict) -> None:
    """REF's published direct series (April 2025, Table 1, to 2023/24) against the four direct lines over the
    same years: RO and FiT by obligation year, CfD by financial year, constraints by calendar year (REF's own
    constraint figures are its calendar-year database). REGO is in REF's table, not in the model."""
    t = src.ref_direct_totals(root)
    cfd = _cfd_by_fy(doc, root)
    years = range(2002, 2024)
    model = sum(out.get(f"{line}.{y}.cash", 0.0) for line in ("ro", "fit", "constraints") for y in years) \
        + sum(cfd.get(y, 0.0) for y in years)
    _put(out, "ref.direct", model, t["ro"] + t["cfd"] + t["fit"] + t["constraints"], "2002-03 to 2023-24",
         "the RO, FiT, CfD and constraint lines against REF's Table 1 totals (£bn to one decimal), REGO left out; "
         "constraints from Elexon's record 2016-2023 here, REF's database in REF's figure")


def build(out: dict, root: Path, doc: dict) -> None:
    ccl(out, root)
    ro(out, root)
    fit(out, root)
    ref(out, root, doc)
    levies(out, root, doc)
