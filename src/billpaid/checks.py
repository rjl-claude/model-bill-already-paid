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
    """OBR's environmental levies outturn (public finances databank), 2002-03 to 2024-25, like for like. ONS's own
    series of its parts add up to it every year: ROCs (EP89), CfDs (CW5G), the Warm Home Discount (JNJF) and the
    CRC Energy Efficiency Scheme (L8UA). It holds no Capacity Market (ONS has yet to include it, the OBR's note),
    no FiT and no green gas levy before 2025-26. The reference is the OBR's figure less WHD and CRC, which the
    model does not count; the model's side is the RO line and CfD by financial year. The gap is then the RO and
    CfD, each the model's less ONS's (`gap.ro`, `gap.cfd`), and any difference between ONS's parts and the OBR's
    figure (`ons_parts_less_obr`, rounding)."""
    obr = src.obr_environmental_levies(root)
    ons = {c: src.ons_series_fy(root, c) for c in ("ep89", "cw5g", "jnjf", "l8ua")}
    cfd = _cfd_by_fy(doc, root)
    years = range(2002, LAST + 1)
    tot = lambda d: math.fsum(d.get(y, 0.0) for y in years)
    whole, whd, crc = tot(obr), tot(ons["jnjf"]), tot(ons["l8ua"])
    ro_model = math.fsum(out[f"ro.{y}.cash"] for y in years)
    cfd_model = tot(cfd)
    k = "check.obr.levies"
    _put(out, "obr.levies", ro_model + cfd_model, whole - whd - crc, "2002-03 to 2024-25",
         "the RO line (obligation years) and CfD (LCCC's payments, April-March) against the OBR's environmental "
         "levies outturn (public finances databank, October 2026) less the Warm Home Discount and the CRC Energy "
         "Efficiency Scheme (ONS's series), which the model does not count; the OBR's figure holds no Capacity "
         "Market, FiT or green gas levy in these years")
    out[f"{k}.reference_whole"] = whole
    out[f"{k}.not_counted.whd"], out[f"{k}.not_counted.crc"] = whd, crc
    out[f"{k}.ons_parts_less_obr"] = math.fsum(tot(v) for v in ons.values()) - whole
    out[f"{k}.gap.ro"] = ro_model - tot(ons["ep89"])
    out[f"{k}.gap.cfd"] = cfd_model - tot(ons["cw5g"])


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


CAP_YEARS = range(2019, 2026)   # ADR 0241: 2019-20 to 2025-26; the cap began in January 2019


def price_cap(out: dict, root: Path) -> None:
    """ADR 0241: the schemes both Ofgem's price-cap policy-cost allowance and the model count, the RO and FiT, per
    typical household (single-rate electricity, Ofgem's typical consumption in force April 2018 to December 2025,
    3.1 MWh), 2019-20 to 2025-26. Ofgem's side: its allowance, £/MWh supplied for each cap period (Annex 4 tab 1a,
    the latest update of each half year), weighted summer and winter as Ofgem weights them (tab 3a), times the
    typical consumption: a forward allowance set before the period, not money paid. The model's side: its RO line
    (UK) over the ROCs obligated in the UK, times Great Britain's obligation level, so £ per MWh supplied in Great
    Britain; its FiT line (GB) over Great Britain's supply (the ROCs obligated in England, Wales and Scotland over
    that level, Ofgem's total obligation notices); each times the same typical consumption. Ofgem leaves out of
    its policy costs what the model counts elsewhere (CfDs and carbon, in its wholesale allowance) and counts what
    the model does not (ECO, WHD, AAHEDC, and from late 2025 the Sizewell C levy, not matched here)."""
    cap = src.cap_policy_costs(root)
    typical = cap["typical"]["April 2018 - December 2025"]
    w = cap["weights"]
    k = "check.ofgem.price_cap_policy_costs"
    model_t = ref_t = 0.0
    for y in CAP_YEARS:
        ob = src.ro_obligation(root, y)
        level = cap["ro_level"][y]
        gb_mwh = (ob["england_wales"] + ob["scotland"]) / level
        model = typical * (out[f"ro.{y}.cash"] / sum(ob.values()) * level + out[f"fit.{y}.cash"] / gb_mwh)
        ref = typical * sum(w["summer"] * r["summer"] + w["winter"] * r["winter"]
                            for r in (cap["rates"][y]["ro"], cap["rates"][y]["fit"]))
        out[f"{k}.{y}.model"], out[f"{k}.{y}.reference"] = model, ref
        out[f"{k}.{y}.gap"], out[f"{k}.{y}.ratio"] = model - ref, model / ref
        model_t, ref_t = model_t + model, ref_t + ref
    _put(out, "ofgem.price_cap_policy_costs", model_t, ref_t, "2019-20 to 2025-26",
         "£ per typical household (single-rate, 3.1 MWh a year), the RO and FiT only. Ofgem's side is its price-cap "
         "policy-cost allowance for the two schemes, a forward allowance set before each period, not money paid. "
         "The RO half uses Ofgem's own obligation level on both sides, so it tests the model's value per "
         "certificate obligated against Ofgem's forecast buy-out price; the FiT half sets the levelisation fund "
         "over Great Britain's supply against Ofgem's forecast. CfDs are left out on both sides in every year: "
         "Ofgem counted them as policy costs until v1.11 of its Annex 4 (15 May 2022), which \"Removed CfD costs "
         "from the annex (moved to annex 2 - wholesale costs)\". Carbon is in neither side. 2025-26 provisional on "
         "the model's side")
    out[f"{k}.2021.note"] = (
        "2021-22 is the one year below 0.95 (0.94). The cause is FiT: the levelisation fund fell to £1,273.1m "
        "(2020-21: £1,603.0m), because the value of exported power to suppliers, which is taken off the fund, "
        "rose to £301.7m (£160.8m) with high wholesale prices, and generation payments fell to £1,451.9m "
        "(£1,547.0m) (Ofgem's annual levelisation notices). The model's FiT half is £4.96/MWh against Ofgem's "
        "£6.85/MWh, set beforehand from a forecast; the RO half agrees within 0.1%")
    out[f"{k}.schemes"] = "ro,fit"
    out[f"{k}.typical_consumption_mwh"] = typical


def build(out: dict, root: Path, doc: dict) -> None:
    ccl(out, root)
    ro(out, root)
    fit(out, root)
    ref(out, root, doc)
    price_cap(out, root)
    levies(out, root, doc)
