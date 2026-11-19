"""2025, the provisional year (version 1.1.0, part 3, aios-harness#224; ADR 0226).

Every line's 2025 figure for the paper, kept out of the 2002-2024 headline. A line 1.0.0 holds the whole of 2025
for keeps its 1.0.0 value. A line 1.0.0 stops before 2025 takes its published 2025 figure, read the way 1.0.0 reads
the line's closed years. The method is written down in docs/figures.md, "2025, the provisional year".
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

import polars as pl
import yaml

from billpaid import register as reg_mod
from billpaid.calendar_years import OBLIGATION_YEAR_LINES
from billpaid.money import add_real
from billpaid.schemes import vat as vat_mod

ROOT = Path(__file__).resolve().parents[2]
YEAR = 2025
MEASURES = {"real": "cost_gbp_2024", "cash": "cost_gbp"}
# 1.0.0 holds the whole of 2025 for these lines: their data run into 2026
FROM_1_0_0 = ("cfd_renewable", "constraints", "capacity_market", "constraint_turnup", "bsuos",
              "generators_share")   # 1.6.0: its 2025 row is billpaid.generators_share's, from the same sources
# where each line's 2025 figure comes from: `<line>.2025.source`, for the paper's annexes
SOURCES = {
    "cfd_renewable": "1.0.0 (LCCC settlement), the whole year",
    "constraints": "1.0.0 (Elexon), the whole year",
    "capacity_market": "1.0.0 (LCCC payments x the gas model's net-zero share), the whole year",
    "constraint_turnup": "1.0.0 (Elexon, estimated), the whole year",
    "bsuos": "1.0.0 (NESO, above the gas-led alternative), the whole year",
    "ro": ("Ofgem, ROCs presented and buy-out fund redistributed 2025-26 (2 Nov 2026); provisional: the "
           "late-payment fund is not yet paid out"),
    "fit": ("Ofgem FiT quarterly reports 61-64, the four levelisations of 2025-26 (shared cost register "
            "v4-s43); provisional: before Ofgem's annual reconciliation"),
    "ccl": ("HMRC Environmental Taxes Bulletin, 31 Mar 2026, Table 1b, electricity, calendar 2025 (shared cost "
            "register v4-s43); provisional"),
    "carbon": ("Report No. 1's release v4-s43, carbon in the wholesale price 2025; provisional there (CPS and "
               "UK ETS auction receipts not yet final)"),
    "tnuos": ("NESO final TNUoS reports 2024-25 and 2025-26 (shared cost register v4-s43), above the gas-led "
              "alternative of Report No. 1's release v4-s43"),
    "vat": "1.0.0's rule on every line above, the Climate Change Levy apart",
    "generators_share": ("ADR 0264: the shared cost register's TNUoS and BSUoS 2025 and Report No. 1's release v4-s43 "
                         "(the gas-led alternative), times the share of 2025's output with no subsidy (DUKES 2026 "
                         "Table 6.2, LCCC; Feed-in Tariff output for April to December 2025 carried from Ofgem's "
                         "2024-25 report, the 2025-26 one not yet published)"),
    "sizewell_c": "LCCC, actual nuclear RAB supplier payments, December 2025; provisional: settlement runs continue",
}
# lines read from the shared cost register, as 1.0.0 reads their closed years (billpaid.register.REF_LINES)
FROM_REGISTER = ("fit", "ccl")


def _pinned(root: Path) -> dict:
    """The pinned shared cost register with the Clock's findings applied, exactly as 1.0.0's build reads it."""
    from billpaid import findings as findings_mod
    pinned = reg_mod.load_pinned(root)
    pinned["selection"] = findings_mod.load(root / "reference" / "clock_findings.yaml", pinned["register"],
                                            product=pinned["product"])
    return pinned


def register_line(root: Path, line: str) -> dict[int, float]:
    """£ cash by year: the line as the pinned shared cost register holds it for the Clock, every year it has."""
    pinned = _pinned(root)
    vals = reg_mod.line_values(pinned["register"], pinned["product"], reg_mod.REF_LINES[line],
                               pinned["selection"])
    return {y: v * 1e6 for y, v in vals.items()}


def sources(root: Path = ROOT) -> dict:
    """The saved sources 2025 reads beyond the frozen file, as pinned (for the figures file's meta)."""
    return yaml.safe_load((root / "reference" / "provisional_2025.yaml").read_text())["sources"]


def source(root: Path, name: str) -> bytes:
    """A saved source named in reference/provisional_2025.yaml, refused if its fingerprint is not the pinned one."""
    pin = sources(root)[name]
    data = (root / pin["file"]).read_bytes()
    fp = hashlib.sha256(data).hexdigest()
    if fp != pin["sha256"]:
        raise ValueError(f"{pin['file']} has sha256 {fp}, not the pinned {pin['sha256']}")
    return data


def _page_text(data: bytes) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", data.decode("utf-8"), flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def ro_outturn(root: Path, year: str) -> float:
    """£ cash: the RO's value for an obligation year (`year` like "2025-26") by Ofgem's definition, ROCs presented
    x (buy-out price + recycle value), from Ofgem's ROCs-presented and buy-out redistribution page (UK total row):
    ROCs presented x buy-out price + the buy-out fund redistributed. The late-payment fund, paid out later, is
    not in it."""
    t = _page_text(source(root, f"ofgem-ro-{year}"))
    price = re.search(r"making a buy-out payment of £(\d+\.\d{2}) per Renewables Obligation Certificate", t)
    total = re.search(r"\bTotal ([\d,]+) ([\d,]+) [\d.]+% £[\d,.]+ £([\d,]+)", t)
    if not (price and total):
        raise ValueError(f"Ofgem RO {year}: buy-out price or the total row moved")
    rocs, redistributed = (int(total.group(i).replace(",", "")) for i in (2, 3))
    pence = round(float(price.group(1)) * 100)
    return rocs * pence / 100 + redistributed


def _deflators(doc: dict) -> pl.DataFrame:
    t = doc["deflators"]
    return pl.DataFrame(t["rows"], schema={k: getattr(pl, v) for k, v in t["schema"].items()}, orient="row")


def _real(doc: dict, line: str, cash: float) -> float:
    """2024 prices by 1.0.0's rule: calendar years at their index, April-March years by quarter."""
    t = add_real(pl.DataFrame({"year": [YEAR], "cost_gbp": [float(cash)]},
                              schema={"year": pl.Int64, "cost_gbp": pl.Float64}), _deflators(doc),
                 "obligation_apr" if line in OBLIGATION_YEAR_LINES else "calendar")
    return t["cost_gbp_2024"][0]


def carbon(run: dict) -> dict[str, float]:
    """£ cash, 2025: the carbon in the wholesale price (NZ1c, GB) and the part collected as tax on power, from
    No. 1's pinned run file (provisional there), read as billpaid.register.carbon_from_engine reads 2002-24."""
    row, bill = run["carbon_crosscheck"][str(YEAR)], run["bills"][str(YEAR)]["nz1c"]
    if bill.get("geo") != "GB" or abs(bill["national_gbp_m_nominal"] - row["in_wholesale_gbp_m"]) > 1e-6:
        raise ValueError(f"carbon {YEAR}: run file's NZ1c and carbon_crosscheck disagree, or not GB")
    total, tax = row["in_wholesale_gbp_m"] * 1e6, row["collected_gbp_m"] * 1e6
    return {"carbon": total, "carbon.tax_collected": tax, "carbon.rest_in_price": total - tax}


def tnuos_parts(root: Path) -> tuple[dict[int, float], dict[int, float]]:
    """(raw, alternative), £ cash by year: the whole TNUoS charge less the generators' share, as the register
    holds it for the Clock, and the gas-led alternative's (the engine's GO5, generators' share removed), each
    read as 1.0.0 reads them (billpaid.register)."""
    return register_line(root, "tnuos"), reg_mod.road_from_engine(root)["tnuos"]["years"]


def sizewell_c(root: Path) -> float:
    """£ cash, 2025: what suppliers paid LCCC of the Sizewell C levy (nuclear RAB), which began on 1 Dec 2025,
    from LCCC's monthly actuals (Actual_Supplier_Payments_GBP)."""
    doc = json.loads(source(root, "lccc-nuclear-rab-actual"))
    rows = [r for r in doc["result"]["records"] if r["Month"].startswith(f"{YEAR}-")]
    if [r["Month"][:7] for r in rows] != [f"{YEAR}-12"]:
        raise ValueError(f"Sizewell C levy: expected December {YEAR} only, got {[r['Month'] for r in rows]}")
    return float(rows[0]["Actual_Supplier_Payments_GBP"])


def vat(lines: dict[str, float], share: float) -> float:
    """£ cash: VAT on households' share of `lines` ({line: £ cash}), 1.0.0's rule (billpaid.schemes.vat): 5% of
    households' share, the Climate Change Levy apart, which households do not pay."""
    return vat_mod.RATE * share * sum(v for line, v in lines.items() if line not in vat_mod.NOT_IN_BASE)


def _put(out: dict, doc: dict, key: str, line: str, cash: float) -> None:
    out[f"{key}.{YEAR}.cash"], out[f"{key}.{YEAR}.real"] = cash, _real(doc, line, cash)


def build(out: dict, doc: dict, run: dict, root: Path = ROOT) -> None:
    """Add the 2025 keys to `out` from `doc`, the frozen results file, `run`, No. 1's pinned run file, and the
    pinned sources under `root`."""
    for s in doc["model"]["schemes"]:
        if s["scheme_id"] not in FROM_1_0_0:
            continue
        r = next(r for r in s["annual"]["rows"] if r["year"] == YEAR)
        for m, col in MEASURES.items():
            out[f"{s['scheme_id']}.{YEAR}.{m}"] = r[col]
    for line in FROM_REGISTER:
        _put(out, doc, line, line, register_line(root, line)[YEAR])
    _put(out, doc, "ro", "ro", ro_outturn(root, "2025-26"))
    for key, cash in carbon(run).items():
        _put(out, doc, key, "carbon", cash)
    raw, alt = (v[YEAR] for v in tnuos_parts(root))
    _put(out, doc, "tnuos.raw", "tnuos", raw)
    _put(out, doc, "tnuos.alternative", "tnuos", alt)
    _put(out, doc, "tnuos", "tnuos", raw - alt)
    out[f"tnuos.alternative.{YEAR}.basis"] = "modelled"
    _put(out, doc, "sizewell_c", "sizewell_c", sizewell_c(root))
    out.update({"sizewell_c.basis": "measured", "sizewell_c.confidence": "high", "sizewell_c.layer": "direct"})
    # VAT: 1.0.0's base lines and Sizewell C, now that each has a 2025 figure, at the engine's 2025 share
    v = next(s for s in doc["model"]["schemes"] if s["scheme_id"] == "vat")["extras"]
    share = next(r["share"] for r in v["domestic_share"] if r["year"] == YEAR)
    base = {line: out[f"{line}.{YEAR}.cash"] for line in [*v["base_lines"], "sizewell_c"]}
    _put(out, doc, "vat", "vat", vat(base, share))
    out[f"vat.domestic_share.{YEAR}"] = share
    out[f"carbon.{YEAR}.basis"] = "modelled"
    _totals(out)


def _totals(out: dict) -> None:
    """direct, indirect and all for 2025, and all's measured, modelled and estimated parts (each line's basis)."""
    for line, text in SOURCES.items():
        out[f"{line}.{YEAR}.source"] = text
        for m in MEASURES:
            v = out[f"{line}.{YEAR}.{m}"]
            for key in (f"{out[f'{line}.layer']}.{YEAR}.{m}", f"all.{YEAR}.{m}",
                        f"all.{YEAR}.{out[f'{line}.basis']}.{m}"):
                out[key] = out.get(key, 0.0) + v
