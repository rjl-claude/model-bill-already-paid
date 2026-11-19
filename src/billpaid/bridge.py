"""The bridge with Report No. 1 (version 1.1.0, part 2, aios-harness#223; ADR 0222, 0036): the walk from
Report No. 2's money paid (gross, scheme by scheme) to Report No. 1's extra cost (net: two whole bills
compared), every year 2002-2024 and the headline, each step named.

Both ends are frozen: No. 2's lines are the 1.0.0 values of the frozen results file; No. 1's are read from its
pinned release, the v4-s43 run file (reference/model_pin.yaml: run_file, run_sha256). Nothing is modelled
here: each step is a No. 1 figure less the No. 2 lines it answers to. The keys are listed in docs/figures.md.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

LAST_CLOSED_YEAR = 2024
YEARS = range(2002, LAST_CLOSED_YEAR + 1)
M = 1e6   # No. 1's run file is in £m


@dataclass(frozen=True)
class No1Release:
    """Report No. 1's pinned release: its version, its run file's fingerprint and the run file itself."""
    version: str
    file: str
    sha256: str
    run: dict

    def meta(self) -> dict:
        return {"model": "model-gas-counterfactual", "version": self.version, "file": self.file, "sha256": self.sha256}


def no1_release(root: Path) -> No1Release:
    """No. 1's pinned run file, refused if its fingerprint is not the pinned one."""
    pin = yaml.safe_load((root / "reference" / "model_pin.yaml").read_text())
    data = (root / pin["run_file"]).read_bytes()
    fp = hashlib.sha256(data).hexdigest()
    if fp != pin["run_sha256"]:
        raise ValueError(f"{pin['run_file']} has sha256 {fp}, not the pinned {pin['run_sha256']}")
    return No1Release(pin["engine_version"], pin["run_file"], fp, json.loads(data))


# Each step of the walk, in order: its name, No. 1's lines (its run file's ids, signed: NZ = the actual bill,
# GO = the gas-led alternative's) and the No. 2 lines they answer to. A step is No. 1's figure less No. 2's.
STEPS = (
    # the two reports count these alike (the same shared cost register and the same gas model): zero
    ("cfd_renewable", "NZ4 + NZ4b", ("cfd_renewable",)),
    ("capacity_market", "NZ5", ("capacity_market",)),
    ("carbon", "NZ1c", ("carbon",)),
    ("tnuos", "NZ7 - GO5", ("tnuos",)),
    ("balancing", "NZ6 - GO4", ("constraints", "constraint_turnup", "bsuos")),
    # counted differently
    ("ro", "NZ2", ("ro",)),
    ("fit", "NZ3", ("fit",)),
    ("ccl", "NZ8", ("ccl",)),
    ("vat", "NZ11 - GO7", ("vat",)),
    # 1.6.0 (ADR 0264): No. 1 counts the whole net-zero part of the generators' share of grid and balancing charges,
    # inside its price of power (GEN: its run file's fleet.<year>.gen_nz_charge, taken out of the gas-led
    # alternative's market price, 0167 way 2); No. 2 counts the part not paid out of subsidy (from 1.6.1 with the
    # share of switch-off payments and turn-up), so the step is the subsidised stations' part. The power step loses
    # No. 1's figure, so the walk still adds up.
    ("generators_share", "GEN", ("generators_share",)),
    # in No. 1 only
    ("energy_saving_schemes", "NZ10", ()),
    ("power_before_carbon", "NZ1 - NZ1c - GO1 - GO1k - GEN", ()),
)
START, END = "no2_money_paid", "no1_extra_cost"
KIND = {**{n: "same" for n in ("cfd_renewable", "capacity_market", "carbon", "tnuos", "balancing")},
        **{n: "counted_differently" for n in ("ro", "fit", "ccl", "vat", "generators_share")},
        **{n: "no1_only" for n in ("energy_saving_schemes", "power_before_carbon")},
        START: "total", END: "total"}
# The table's row labels, in the series glossary's words (report-series/GLOSSARY.md).
LABELS = {
    START: "Money paid: Report No. 2's twelve lines, gross",
    "cfd_renewable": "Contracts for Difference: counted alike in both reports",
    "capacity_market": "Capacity Market, the part net zero caused: counted alike",
    "carbon": "Carbon in the price of power: counted alike",
    "tnuos": "High-voltage grid above the gas-led alternative's: counted alike",
    "balancing": "Balancing and constraints above the gas-led alternative's: counted alike",
    "ro": "Renewables Obligation: No. 1 counts Great Britain only, by calendar year, above the 2001 levy",
    "fit": "Feed-in Tariffs: No. 1 counts by calendar year, No. 2 by scheme year",
    "ccl": "Climate Change Levy: No. 1 counts only the levy above its 2001 rate, Great Britain only",
    "vat": "VAT: No. 1 charges it on households' share of the extra cost, No. 2 on the money paid",
    "generators_share": ("Generators' grid and balancing charges: No. 1 counts all net zero added, No. 2 only what "
                         "unsubsidised stations pay"),
    "energy_saving_schemes": "Suppliers' energy-saving schemes on electricity bills: in No. 1 only",
    "power_before_carbon": ("Power itself, before carbon and generators' grid charges: the actual cost less the gas-led "
                            "alternative's"),
    END: "Extra cost: Report No. 1's figure, net",
}
TOLERANCE = 0.001   # £: a tenth of a penny


def _no1_lines(no1: dict, year: int) -> dict[str, float]:
    """Every line of No. 1's two bills that year, by id, £ cash."""
    bills = no1["bills"][str(year)]
    lines = [*bills["netzero"], *bills["gasonly"], bills["nz1c"]]
    out = {x["id"]: x["national_gbp_m_nominal"] * M for x in lines}
    out["GEN"] = no1["fleet"][str(year)]["gen_nz_charge"]["gbp_m"] * M
    return out


def _signed(formula: str, lines: dict[str, float]) -> float:
    total, sign = 0.0, 1
    for token in formula.split():
        if token in "+-":
            sign = 1 if token == "+" else -1
        else:
            total += sign * lines[token]
    return total


def build(out: dict, doc: dict, no1: No1Release) -> None:
    """Add the bridge's keys to the figures in `out` (which already holds every line's `<line>.<year>.<m>`
    and `all.<year>.<m>`). Refuses to write a walk that does not add up, or that leaves a No. 2 line out."""
    counted = sorted(line for _, _, no2 in STEPS for line in no2)
    if counted != sorted(s["scheme_id"] for s in doc["model"]["schemes"]):
        raise ValueError(f"the bridge's No. 2 lines {counted} are not the model's lines, each once")
    cpih = {r["year"]: r["index"] for r in doc["deflators"]["rows"]}
    names = [START, *(name for name, _, _ in STEPS), END]
    out["bridge.steps"] = ",".join(names)
    if no1.run["meta"]["engine_version"] != no1.version:
        raise ValueError(f"No. 1's run file is {no1.run['meta']['engine_version']}, not the pinned {no1.version}")
    out["bridge.no1.version"], out["bridge.no1.sha256"] = no1.version, no1.sha256
    for n in names:
        out[f"bridge.{n}.label"], out[f"bridge.{n}.kind"] = LABELS[n], KIND[n]
    for y in YEARS:
        factor = {"cash": 1.0, "real": cpih[LAST_CLOSED_YEAR] / cpih[y]}
        lines = _no1_lines(no1.run, y)
        gap = no1.run["gap"][str(y)]["national_gbp_m_nominal"] * M
        for m in ("cash", "real"):
            row = {START: out[f"all.{y}.{m}"], END: gap * factor[m]}
            for name, formula, no2 in STEPS:
                row[name] = _signed(formula, lines) * factor[m] - sum(out.get(f"{line}.{y}.{m}", 0.0) for line in no2)
            miss = sum(row[n] for n in names[:-1]) - row[END]
            if abs(miss) > TOLERANCE:
                raise ValueError(f"the bridge misses No. 1's extra cost by £{miss:.4f} in {y} ({m})")
            for n in names:
                out[f"bridge.{n}.{y}.{m}"] = row[n]
                out[f"bridge.{n}.headline.{m}"] = out.get(f"bridge.{n}.headline.{m}", 0.0) + row[n]
