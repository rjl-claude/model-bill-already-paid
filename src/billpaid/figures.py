"""The paper's figures file (version 1.1.0, part 1, aios-harness#222): every figure Report No. 2 prints from
the bill already paid, flat and read by key, like model-bill-still-to-come's `results/figures.json`.

It is built from the frozen results file the paper pins (`results/clock.json` as committed at FROZEN_REF,
9 Nov 2026, sha256 FROZEN_SHA256), not from a new run: each key is a 1.0.0 value, or a sum, ratio or product
of them by 1.0.0's own rules, so no 1.0.0 value can move. The keys are listed in docs/figures.md.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import polars as pl

from billpaid.money import REAL_BASE_YEAR, add_real
from billpaid.results import MODEL, model_version

FROZEN_REF = "2a63b034"
FROZEN_PATH = "results/clock.json"
FROZEN_SHA256 = "738ac005d5fca69015139cbf6857fa1cf87320c6e16a8a234fcdf1557f2f059b"
LAST_CLOSED_YEAR = 2024          # the headline runs 2002-2024; 2025 is the provisional year (#224)


def frozen_bytes(root: Path) -> bytes:
    """The frozen results file, exactly as committed."""
    return subprocess.run(["git", "-C", str(root), "show", f"{FROZEN_REF}:{FROZEN_PATH}"],
                          capture_output=True, check=True).stdout


def frozen_results(root: Path) -> dict:
    """The frozen results file, refused if its fingerprint is not the pinned one."""
    data = frozen_bytes(root)
    fp = hashlib.sha256(data).hexdigest()
    if fp != FROZEN_SHA256:
        raise ValueError(f"{FROZEN_PATH} at {FROZEN_REF} has sha256 {fp}, not the pinned {FROZEN_SHA256}")
    return json.loads(data)


# Each line's basis (aios-harness#222), read from 1.0.0's own account of the line: measured (payments or
# receipts as recorded), modelled (a share or alternative taken from the pinned gas model) or estimated.
BASIS = {
    "cfd_renewable": "measured",      # LCCC settlement payments
    "constraints": "measured",        # Elexon bids; REF's history before 6 Nov 2015
    "ro": "measured",                 # Ofgem annual reports
    "fit": "measured",                # the levelisation fund, Ofgem
    "ccl": "measured",                # HMRC receipts, electricity's published share
    "capacity_market": "modelled",    # LCCC payments times the gas model's net-zero share
    "carbon": "modelled",             # the gas model's carbon in the price (2005-2012 estimated: carbon.<year>.basis)
    "tnuos": "modelled",              # the charge above the gas model's alternative
    "bsuos": "modelled",              # the same, net of the constraint lines
    "vat": "modelled",                # 5% on households' share, the share from the gas model
    "constraint_turnup": "estimated",  # 1.0.0: "Estimated cost of paying other stations..."
}
NO_CONFIDENCE = "high"   # 1.0.0 gives no confidence for the direct lines: counted in full, as paid

# Every kind of key, with its meaning: the file's `meta.keys`, and docs/figures.md lists the same.
# A <name> stands for any of PLACEHOLDERS[name]; each key in the file matches exactly one template.
PLACEHOLDERS = {
    "line": "|".join(BASIS), "total": "direct|indirect|all", "year": r"\d{4}", "m": "real|cash",
    "part": "tax_collected|rest_in_price", "grid": "tnuos|bsuos", "side": "raw|alternative",
    "end": "central|low|high", "bound": "low|high", "technology": "[a-z0-9_]+", "tm": "cash|mwh|share",
    "rec": r"divergence_pct|bottom_up\.cash|official\.cash|tolerance_pct|matched_days",
    "cc": "estimate|accepted_offers|accepted_offers_wind", "when": "from|to", "d": "cpih|to_2024",
}
MONEY = "real: £ in 2024 prices (CPIH); cash: £ as paid"
KEYS = {
    "<line>.<year>.<m>": f"each line, each year, 2002-2024 where 1.0.0 has the year ({MONEY})",
    "<line>.headline.<m>": "each line, 2002-2024",
    "<total>.<year>.<m>": "the direct lines, the indirect lines, or all together, each year",
    "<total>.headline.<m>": "the same, 2002-2024",
    "<line>.basis": "measured, modelled or estimated",
    "<line>.confidence": "1.0.0's confidence (high, medium or low); high for the direct lines, which it leaves blank",
    "<line>.layer": "direct or indirect",
    "carbon.<year>.basis": "the carbon line's basis that year (2005-2012 estimated)",
    "carbon.<part>.<year>.<m>": "carbon split: the tax collected by the Treasury, and the rest of the carbon in the price",
    "carbon.<part>.headline.<m>": "the same, 2002-2024",
    "<grid>.<side>.<year>.<m>": "grid (TNUoS) or balancing (BSUoS): the whole charge (raw) and the gas-led alternative's",
    "<grid>.<side>.headline.<m>": "the same, 2002-2024",
    "<grid>.alternative.<year>.basis": "the alternative's basis that year",
    "capacity_market.raw.<year>.<m>": "the Capacity Market levy paid in full",
    "capacity_market.raw.headline.<m>": "the same, 2002-2024",
    "capacity_market.netzero_share.<year>.<end>": "the share of the levy net zero caused (0 to 1)",
    "capacity_market.range.<bound>.<year>.<m>": "the line at the low or high share",
    "capacity_market.range.<bound>.headline.<m>": "the same, 2002-2024",
    "vat.rate": "the VAT rate on households' bills (0 to 1)",
    "vat.domestic_share.<year>": "households' share of the lines VAT is charged on (0 to 1)",
    "cfd_renewable.by_technology.<technology>.<tm>": ("CfD by technology from the first payment to the data's "
                                                     "end: £ cash, MWh, share of the total (all: every technology)"),
    "cfd_renewable.by_technology.to": "the data's end for CfD by technology (a date)",
    "cfd_renewable.reconciliation.<rec>": ("the contract-by-contract CfD payments against LCCC's own daily totals "
                                           "over the matched days: divergence and tolerance in per cent, £ cash"),
    "constraint_turnup.cross_check.<cc>.cash": ("the turn-up estimate beside the offers accepted (all, and while "
                                                "wind was constrained) over the measured window, £ cash"),
    "constraint_turnup.cross_check.<when>": "the measured window's first and last day (dates)",
    "bill.<year>.<m>": "the whole UK electricity bill (DUKES 1.3)",
    "bill.headline.<m>": "the same, 2002-2024",
    "share_of_bill.<year>": "all lines over the whole bill, 2024 prices (0 to 1)",
    "share_of_bill.headline": "the same, 2002-2024",
    "households": "UK households (ONS)",
    "per_household.headline": "all lines 2002-2024, 2024 prices, over today's households",
    "per_household.<year>": "all lines that year, 2024 prices, over today's households",
    "deflator.<year>.<d>": "CPIH (2015 = 100), and the factor to 2024 prices",
}


def template_regex(template: str) -> str:
    """A key template as a regular expression (each <name> one of PLACEHOLDERS[name])."""
    parts = re.split(r"(<[a-z]+>)", template)
    return "".join(f"(?:{PLACEHOLDERS[p[1:-1]]})" if p.startswith("<") else re.escape(p) for p in parts)


MEASURES = {"real": "cost_gbp_2024", "cash": "cost_gbp"}
LAYERS = ("direct", "indirect")


def _add(out: dict, key: str, v: float) -> None:
    out[key] = out.get(key, 0.0) + v


def _deflators(doc: dict) -> pl.DataFrame:
    t = doc["deflators"]
    return pl.DataFrame(t["rows"], schema={k: getattr(pl, v) for k, v in t["schema"].items()}, orient="row")


def _part(out: dict, doc: dict, key: str, cash: dict[int, float]) -> None:
    """`<key>.<year>.cash|real` and `<key>.headline.cash|real` for a part of a calendar-year line, priced to
    2024 by the model's own rule (billpaid.money.add_real)."""
    years = sorted(y for y in cash if y <= LAST_CLOSED_YEAR)
    t = add_real(pl.DataFrame({"year": years, "cost_gbp": [float(cash[y]) for y in years]},
                              schema={"year": pl.Int64, "cost_gbp": pl.Float64}), _deflators(doc))
    for r in t.iter_rows(named=True):
        for m, col in MEASURES.items():
            out[f"{key}.{r['year']}.{m}"] = cash[r["year"]] if m == "cash" else r[col]
            _add(out, f"{key}.headline.{m}", out[f"{key}.{r['year']}.{m}"])


def _carbon(out: dict, doc: dict, s: dict) -> None:
    parts = s["extras"]["parts"]
    _part(out, doc, "carbon.tax_collected", {p["year"]: p["tax_collected"] for p in parts})
    _part(out, doc, "carbon.rest_in_price", {p["year"]: p["rest_of_carbon_in_price"] for p in parts})
    for p in parts:
        if p["year"] <= LAST_CLOSED_YEAR:
            out[f"carbon.{p['year']}.basis"] = p["basis"]


def _road(out: dict, doc: dict, s: dict) -> None:
    """The whole charge as paid (`raw`) and what the gas-led alternative would have paid (`alternative`)."""
    line = s["scheme_id"]
    _part(out, doc, f"{line}.raw", {r["year"]: r["cost"] for r in s["extras"]["raw_annual"]})
    _part(out, doc, f"{line}.alternative", {r["year"]: r["cost"] for r in s["extras"]["road_annual"]})
    for r in s["extras"]["road_annual"]:
        if r["year"] <= LAST_CLOSED_YEAR:
            out[f"{line}.alternative.{r['year']}.basis"] = r["basis"]


def _capacity_market(out: dict, doc: dict, s: dict) -> None:
    """The levy paid in full (`raw`), the share net zero caused (central, low, high) and the line at the low
    and high shares (`range`): each year's levy times that year's share, 1.0.0's rule for its range."""
    raw = {r["year"]: r["cost"] for r in s["extras"]["raw_annual"]}
    share = {r["year"]: r for r in s["extras"]["netzero_share"]}
    _part(out, doc, "capacity_market.raw", raw)
    for y, r in share.items():
        if y <= LAST_CLOSED_YEAR:
            for end, col in (("central", "share"), ("low", "share_low"), ("high", "share_high")):
                out[f"capacity_market.netzero_share.{y}.{end}"] = r[col]
    for end in ("low", "high"):
        _part(out, doc, f"capacity_market.range.{end}", {y: raw[y] * share[y][f"share_{end}"] for y in raw})


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _vat(out: dict, doc: dict, s: dict) -> None:
    out["vat.rate"] = s["extras"]["rate"]
    for r in s["extras"]["domestic_share"]:
        if r["year"] <= LAST_CLOSED_YEAR:
            out[f"vat.domestic_share.{r['year']}"] = r["share"]


def _cfd(out: dict, doc: dict, s: dict) -> None:
    """By technology, as 1.0.0 holds it: paid from the first contract to the data's end, not by year."""
    techs = s["extras"]["by_technology"]
    total = sum(t["cost"] for t in techs)
    out["cfd_renewable.by_technology.all.cash"] = total
    out["cfd_renewable.by_technology.to"] = s["data_to"]
    for t in techs:
        k = f"cfd_renewable.by_technology.{_slug(t['technology'])}"
        out[f"{k}.cash"], out[f"{k}.mwh"], out[f"{k}.share"] = t["cost"], t["generation_mwh"], t["cost"] / total
    rec = doc["reconciliation"]
    k = "cfd_renewable.reconciliation"
    out[f"{k}.divergence_pct"] = rec["overall"]["divergence_pct"]
    out[f"{k}.bottom_up.cash"] = rec["overall"]["bottom_up"]
    out[f"{k}.official.cash"] = rec["overall"]["official"]
    out[f"{k}.tolerance_pct"] = rec["tolerance_pct"]
    out[f"{k}.matched_days"] = rec["matched_days"]


def _turnup(out: dict, doc: dict, s: dict) -> None:
    """The estimate beside the offers actually accepted, over the measured window (from 6 Nov 2015)."""
    cc = s["extras"]["cross_check_cumulative"]
    out["constraint_turnup.cross_check.estimate.cash"] = s["cumulative_gbp"]
    out["constraint_turnup.cross_check.accepted_offers.cash"] = cc["accepted_offers"]
    out["constraint_turnup.cross_check.accepted_offers_wind.cash"] = cc["accepted_offers_wind"]
    out["constraint_turnup.cross_check.from"] = s["extras"]["measured_from"]
    out["constraint_turnup.cross_check.to"] = s["data_to"]


PARTS = {"carbon": _carbon, "capacity_market": _capacity_market, "vat": _vat, "cfd_renewable": _cfd,
         "constraint_turnup": _turnup, "tnuos": _road, "bsuos": _road}


def build(doc: dict) -> dict[str, float | str]:
    out: dict[str, float | str] = {}
    for s in doc["model"]["schemes"]:
        line, layer = s["scheme_id"], s["layer"]
        if layer not in LAYERS:
            raise ValueError(f"line {line} is in layer {layer!r}, not one of {LAYERS}")
        for r in s["annual"]["rows"]:
            y = r["year"]
            if y > LAST_CLOSED_YEAR:
                continue
            for m, col in MEASURES.items():
                out[f"{line}.{y}.{m}"] = r[col]
                for head in (line, layer, "all"):
                    _add(out, f"{head}.headline.{m}", r[col])
                for head in (layer, "all"):
                    _add(out, f"{head}.{y}.{m}", r[col])
        if line not in BASIS:
            raise KeyError(f"line {line} has no basis in billpaid.figures.BASIS")
        out[f"{line}.basis"] = BASIS[line]
        out[f"{line}.confidence"] = s["attribution_confidence"] or NO_CONFIDENCE
        out[f"{line}.layer"] = layer
        if line in PARTS:
            PARTS[line](out, doc, s)
    _context(out, doc)
    return out


def _context(out: dict, doc: dict) -> None:
    """The whole electricity bill (DUKES), the share of it, households, per household, and CPIH."""
    for r in doc["bill"]["rows"]:
        y = r["year"]
        if y <= LAST_CLOSED_YEAR:
            out[f"bill.{y}.real"], out[f"bill.{y}.cash"] = r["total_bill_gbp_2024"], r["total_bill_gbp"]
            _add(out, "bill.headline.real", r["total_bill_gbp_2024"])
            _add(out, "bill.headline.cash", r["total_bill_gbp"])
            out[f"share_of_bill.{y}"] = out[f"all.{y}.real"] / out[f"bill.{y}.real"]
    out["share_of_bill.headline"] = out["all.headline.real"] / out["bill.headline.real"]
    households = doc["context"]["households"]["value"]
    out["households"] = households
    out["per_household.headline"] = out["all.headline.real"] / households
    out[f"per_household.{LAST_CLOSED_YEAR}"] = out[f"all.{LAST_CLOSED_YEAR}.real"] / households
    cpih = {r["year"]: r["index"] for r in doc["deflators"]["rows"]}
    for y, v in cpih.items():
        if y <= LAST_CLOSED_YEAR:
            out[f"deflator.{y}.cpih"] = v
            out[f"deflator.{y}.to_2024"] = cpih[REAL_BASE_YEAR] / v


def document(doc: dict) -> dict:
    """The figures file: the keys, and where they come from."""
    return {"figures": build(doc),
            "meta": {"model": MODEL, "version": model_version(),
                     "built_from": {"file": FROZEN_PATH, "ref": FROZEN_REF, "sha256": FROZEN_SHA256,
                                    "version": doc["meta"]["version"], "generated_at": doc["meta"]["generated_at"]},
                     "headline_years": [2002, LAST_CLOSED_YEAR], "keys": KEYS, "placeholders": PLACEHOLDERS}}
