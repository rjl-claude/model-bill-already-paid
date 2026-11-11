"""The figures the approved outline of Report No. 2 asks of the bill already paid (version 1.2.0, the paper's plan
step 19, aios-harness#235; `report-series/price-of-the-climate-bill/outline-beats.md`, "Missing figures", M1 to M9).
Each is a sum, ratio or product of the figures file's own keys by the rule the outline's rulings give, or a figure
read from a publisher's saved file (billpaid.outline_sources). Northern Ireland's part (M11) is not sized
(report-series ADR 0240). The keys and their meanings: docs/figures.md, "The outline's figures (1.2.0)".
"""
from __future__ import annotations

import math
from pathlib import Path

from billpaid import outline_sources

LAST_CLOSED_YEAR = 2024   # as billpaid.figures: the headline runs 2002-2024


def add(out: dict, key: str, v: float) -> None:
    out[key] = out.get(key, 0.0) + v

YEARS = range(2002, LAST_CLOSED_YEAR + 1)
BASES = ("measured", "modelled", "estimated")


NOT_COUNTED = ("energy_saving_schemes",)   # shown beside the figure, never in it (ADR 0233)


def _lines(out: dict) -> list[str]:
    """The lines counted in the headline (each has a `<line>.basis` key)."""
    return [k[: -len(".basis")] for k in out if k.endswith(".basis") and k.count(".") == 1
            and k[: -len(".basis")] not in NOT_COUNTED]


def basis_of(out: dict, line: str, y: int) -> str:
    """A line's basis in a year: its own, or carbon's year by year (2005-2012 estimated)."""
    return out.get(f"{line}.{y}.basis", out[f"{line}.basis"]) if line == "carbon" else out[f"{line}.basis"]


def headline_parts(out: dict) -> None:
    """M1 (ADR 0007): the 2002-2024 headline split by each line's basis, year by year."""
    for m in ("real", "cash"):
        for b in BASES:
            out[f"all.headline.{b}.{m}"] = 0.0
        for line in _lines(out):
            for y in YEARS:
                v = out.get(f"{line}.{y}.{m}")
                if v is not None:
                    add(out, f"all.headline.{basis_of(out, line, y)}.{m}", v)


# M2 (ADR 0234, choice 2): the three lines whose figures are estimated rather than recorded payments, each changed
# on its own. The Capacity Market's own range is its low share to central (outline §8.5, §14.2): its high key
# (`capacity_market.range.high`) is the whole levy, a counting option shown apart, never a range end.
RANGE_LINES = {"carbon": ("carbon.range.low", "carbon.range.high"),
               "constraint_turnup": ("constraint_turnup.range.low", "constraint_turnup.range.high"),
               "capacity_market": ("capacity_market.range.low", None)}


def headline_range(out: dict) -> None:
    """The headline at each end: the one line, of the three, that moves it furthest that way, the others central."""
    for end, i, pick in (("low", 0, min), ("high", 1, max)):
        for m in ("real", "cash"):
            moves = {line: (out[f"{keys[i]}.headline.{m}"] - out[f"{line}.headline.{m}"]) if keys[i] else 0.0
                     for line, keys in RANGE_LINES.items()}
            line = pick(moves, key=moves.get)
            out[f"range.{end}.headline.{m}"] = out[f"all.headline.{m}"] + moves[line]
            if m == "real":
                out[f"range.{end}.headline.line"] = line


def per_household(out: dict, root: Path) -> None:
    """M3 (ADR 0025, 0027, 0232): each year's money paid over that year's UK households (ONS), 2002-2025, and the
    headline as the sum of the years 2002-2024."""
    hh = outline_sources.households(root)
    for y in range(2002, LAST_CLOSED_YEAR + 2):
        out[f"households.{y}"] = hh[y]
        out[f"per_household.{y}.real"] = out[f"all.{y}.real"] / hh[y]
    out["per_household.year_by_year.headline.real"] = sum(out[f"per_household.{y}.real"] for y in YEARS)


def own_bills(out: dict) -> None:
    """M4 (ADR 0025): what an average household paid on its own bills: households' share of every line but the CCL
    (the share 1.0.0's VAT line uses, from the gas model), plus the VAT line, over that year's households."""
    for y in range(2002, LAST_CLOSED_YEAR + 2):
        d = out[f"vat.domestic_share.{y}"]
        base = out[f"all.{y}.real"] - out.get(f"ccl.{y}.real", 0.0) - out[f"vat.{y}.real"]
        out[f"own_bills.per_household.{y}.real"] = (d * base + out[f"vat.{y}.real"]) / out[f"households.{y}"]
    out["own_bills.per_household.headline.real"] = sum(out[f"own_bills.per_household.{y}.real"] for y in YEARS)


def _vat_on(out: dict, y: int, v: float) -> float:
    """v with the VAT 1.0.0's rule charges on it: 5% on households' share (any line but the CCL)."""
    return v * (1 + out["vat.rate"] * out[f"vat.domestic_share.{y}"])


def _option(out: dict, name: str, change) -> None:
    """`option.<name>.headline.<m>`: the headline with each year changed by change(y, m) (£, VAT included)."""
    for m in ("real", "cash"):
        out[f"option.{name}.headline.{m}"] = out[f"all.headline.{m}"] + sum(change(y, m) for y in YEARS)


def _g(out: dict, key: str) -> float:
    return out.get(key, 0.0)


def energy_saving_schemes(out: dict, run: dict) -> None:
    """M6f (ADR 0233): suppliers' energy-saving schemes (EEC, CERT, CESP, ECO, GBIS), their cost on electricity
    bills, as Report No. 1's pinned release holds it (its NZ10, the lower end of each scheme's range, Great
    Britain), gross: No. 1's line nets off the 2001 scheme (EESoP) at its 2001 level, which the release records
    year by year (`on_the_road`), and a gross count adds it back. Not counted in the headline."""
    for y in YEARS:
        nz10 = next(r for r in run["bills"][str(y)]["netzero"] if r["id"] == "NZ10")["national_gbp_m_nominal"]
        cash = (nz10 + run["on_the_road"]["years"][str(y)]["nz10_on_the_road_gbp_m"]) * 1e6
        out[f"energy_saving_schemes.{y}.cash"] = cash
        out[f"energy_saving_schemes.{y}.real"] = cash * out[f"deflator.{y}.to_2024"]
        for m in ("real", "cash"):
            add(out, f"energy_saving_schemes.headline.{m}", out[f"energy_saving_schemes.{y}.{m}"])
    out["energy_saving_schemes.basis"] = "estimated"


def options(out: dict, root: Path, run: dict) -> None:
    """M6: the headline under each other counting option the paper argues (outline §6.2, §6.3, §6.5, §8.3-§8.5).
    A line taken out or added takes its VAT with it, by 1.0.0's rule; the CCL carries none."""
    v = lambda y, x: _vat_on(out, y, x)
    _option(out, "carbon_tax_only", lambda y, m: -v(y, _g(out, f"carbon.rest_in_price.{y}.{m}")))
    _option(out, "no_carbon", lambda y, m: -v(y, _g(out, f"carbon.{y}.{m}")))
    _option(out, "no_ccl", lambda y, m: -_g(out, f"ccl.{y}.{m}"))
    # the levy at its 2001 rate: the year's receipts over its calendar-year rate (a quarter at the rate from the
    # April before, three quarters at the rate from its own April) give the volume, priced at £0.0043/kWh
    # (Report No. 1's method, ccl_baseline, applied to the UK line)
    rates = outline_sources.ccl_electricity_rates(root)
    rate = lambda y: rates[max(k for k in rates if k <= y)]
    cy = lambda y: 0.25 * rate(y - 1) + 0.75 * rate(y)
    _option(out, "ccl_above_2001", lambda y, m: -_g(out, f"ccl.{y}.{m}") * rates[2001] / cy(y))
    _option(out, "grid_whole", lambda y, m: v(y, _g(out, f"tnuos.alternative.{y}.{m}")
                                              + _g(out, f"bsuos.alternative.{y}.{m}")))
    _option(out, "cm_whole_levy", lambda y, m: v(y, _g(out, f"capacity_market.raw.{y}.{m}")
                                                 - _g(out, f"capacity_market.{y}.{m}")))
    energy_saving_schemes(out, run)
    # households pay the schemes' whole cost (obligations on domestic supply), so VAT is on the whole
    _option(out, "energy_saving_schemes",
            lambda y, m: out[f"energy_saving_schemes.{y}.{m}"] * (1 + out["vat.rate"]))


def cfd_payments(doc: dict, root: Path):
    """LCCC's contract-by-contract CfD payments in the store snapshot the frozen file was built from (the latest
    written at or before its `generated_at`)."""
    import glob

    import polars as pl
    cut = doc["meta"]["generated_at"][:26].replace("-", "").replace(":", "")
    snap = [v for v in sorted(glob.glob(str(root / "data/raw/cfd/generation/full/*"))) if Path(v).name <= cut][-1]
    return pl.read_parquet(Path(snap) / "data.parquet")


def cfd_by_technology(out: dict, doc: dict, root: Path) -> None:
    """M8: CfD by technology, 2016-2024, from LCCC's payments (cfd_payments), by calendar year, priced by CPIH."""
    import re

    import polars as pl
    g = cfd_payments(doc, root).with_columns(pl.col("date").dt.year().alias("year")) \
        .filter(pl.col("year") <= LAST_CLOSED_YEAR)
    groups: dict[tuple[str, int], list[float]] = {}
    for tech, year, pay in g.select("technology", "year", "payment_gbp").iter_rows():
        groups.setdefault((tech, year), []).append(pay)
    # math.fsum: an exact sum, the same whatever the rows' order (a polars group sum can differ in its last digit)
    for (tech, year), pays in sorted(groups.items()):
        cash = math.fsum(pays)
        slug = re.sub(r"[^a-z0-9]+", "_", tech.lower()).strip("_")
        for k in (slug, "all"):
            add(out, f"cfd_renewable.by_technology.{k}.headline.cash", cash)
            add(out, f"cfd_renewable.by_technology.{k}.headline.real", cash * out[f"deflator.{year}.to_2024"])


def build(out: dict, root: Path, run: dict, doc: dict) -> None:
    headline_parts(out)
    headline_range(out)
    per_household(out, root)
    own_bills(out)
    options(out, root, run)
    cfd_by_technology(out, doc, root)
