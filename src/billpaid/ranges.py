"""A range for each line labelled estimated (version 1.1.0, part 4, aios-harness#225; spec: "a range for each
line labelled estimated"). Two lines are estimated by the model's own labels: constraint turn-up (every year) and
carbon in 2005-2012. 1.0.0 holds a range for neither. The method is written down in docs/figures.md, "The ranges".
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import re
import zipfile
from datetime import datetime
from pathlib import Path

import yaml

from billpaid.schemes import constraint_turnup as tu

ROOT = Path(__file__).resolve().parents[2]
MEASURES = ("real", "cash")
LAST_CLOSED_YEAR = 2024
PHASE_I_LAST_YEAR = 2007          # Phase I of the EU ETS: 2005-2007


def _walk(stack: list[dict], target: float) -> tuple[float, float]:
    """(MWh, £): `target` MWh taken from `stack` in its order, pro rata at the margin (Octopus's walk)."""
    n = r = 0.0
    for o in stack:
        v, p = float(o.get("volume") or 0), float(o["originalPrice"])
        take = min(max((target - n) / v, 0.0), 1.0) if v and n + v > target else 1.0
        n, r = n + v * take, r + p * v * take
        if n >= target:
            break
    return n, r


def turnup_walks(offers: list[dict], lost_mwh: float) -> dict[str, tuple[float, float]]:
    """One half-hour: the switched-off wind volume (`lost_mwh`, the system-flagged wind bids) priced on that
    half-hour's accepted offers (CADL offers left out), three ways: `central`, 1.0.0's own walk (Octopus's:
    unflagged first, then by acceptance order); `low`, the cheapest offers first; `high`, the dearest first.
    The volume is the same in all three: only which accepted offers replaced the wind is estimated."""
    target = abs(lost_mwh)
    usable = [o for o in offers if not o.get("cadlFlag") and o.get("originalPrice") is not None]
    if target <= 0:
        return {k: (0.0, 0.0) for k in ("central", "low", "high")}
    price = lambda o: float(o["originalPrice"])  # noqa: E731
    return {"central": tu.replacement_estimate(offers, lost_mwh),
            "low": _walk(sorted(usable, key=price), target),
            "high": _walk(sorted(usable, key=price, reverse=True), target)}


# ------------------------------------------------------------------ the saved sources


def sources(root: Path = ROOT) -> dict:
    """The saved sources the ranges read, as pinned (for the figures file's meta)."""
    return yaml.safe_load((root / "reference" / "ranges.yaml").read_text())["sources"]


def source(root: Path, name: str) -> bytes:
    """A saved source named in reference/ranges.yaml, refused if its fingerprint is not the pinned one."""
    pin = sources(root)[name]
    data = (root / pin["file"]).read_bytes()
    fp = hashlib.sha256(data).hexdigest()
    if fp != pin["sha256"]:
        raise ValueError(f"{pin['file']} has sha256 {fp}, not the pinned {pin['sha256']}")
    return data


# ------------------------------------------------------------------ carbon, 2005-2012

def _xlsx_rows(data: bytes, sheet: str = "xl/worksheets/sheet1.xml") -> list[list]:
    """A worksheet's rows, cells as numbers or shared strings (standard library only)."""
    x = zipfile.ZipFile(io.BytesIO(data))
    shared = [html.unescape(re.sub(r"<[^>]+>", "", s))
              for s in re.findall(r"<si>(.*?)</si>", x.read("xl/sharedStrings.xml").decode(), re.S)]
    rows = []
    for row in re.findall(r"<row[^>]*>(.*?)</row>", x.read(sheet).decode(), re.S):
        cells = []
        for attrs, v in re.findall(r"<c([^>]*?)(?:/>|>(.*?)</c>)", row, re.S):
            m = re.search(r"<v>(.*?)</v>", v or "")
            if not m:
                continue
            cells.append(shared[int(m.group(1))] if 't="s"' in attrs else float(m.group(1)))
        rows.append(cells)
    return rows


def eea_eua_price(root: Path = ROOT) -> dict[int, float]:
    """EUR/t by year, 2005-2020: the EEA's row "EUA price (EUR / t CO2-eq)", the price the engine's carbon line
    rests on in 2005-2012."""
    z = zipfile.ZipFile(io.BytesIO(source(root, "eea-eua-price")))
    rows = _xlsx_rows(z.read("FIG3-142383-Emissions-allowances-Data.xlsx"))
    years = next(r for r in rows if 2005.0 in r and 2020.0 in r)
    price = next(r for r in rows if r and r[0] == "EUA price (EUR / t CO2-eq)")
    return {int(y): p for y, p in zip(years, price[1:])}


def dmo_clearing_prices(root: Path = ROOT) -> dict[int, list[float]]:
    """EUR/t: each Phase II UK auction's clearing price, by calendar year of the auction (DMO notices)."""
    out: dict[int, list[float]] = {}
    for r in csv.DictReader(io.StringIO(source(root, "dmo-phase2-auctions").decode("utf-8"))):
        y = datetime.strptime(r["date"], "%d %B %Y").year
        out.setdefault(y, []).append(float(r["clearing_price_eur"]))
    return out


def bluenext_closes(root: Path = ROOT) -> dict[int, list[float]]:
    """EUR/t: each trading day's closing price of the Phase I spot allowance on BlueNext (Powernext Carbon),
    2005-2007, by calendar year (the file runs on to April 2008, after Phase I's last compliance year)."""
    out: dict[int, list[float]] = {}
    for r in csv.DictReader(io.StringIO(source(root, "bluenext-phase1-spot").decode("utf-8"))):
        y = datetime.strptime(r["Date"], "%d/%m/%Y").year
        if r["Product"] != "BNS EUA 05-07":
            raise ValueError(f"BlueNext file: unexpected product {r['Product']!r}")
        if y <= PHASE_I_LAST_YEAR:
            out.setdefault(y, []).append(float(r["Daily Closing Price"].replace(",", ".")))
    return out


def carbon_prices(root: Path = ROOT) -> dict[int, dict[str, float]]:
    """{year: {central, low, high}}, EUR/t, for the carbon line's estimated years: the range spans the EEA's price
    (central) and every price in that year's record, the Phase I spot exchange's daily closes for 2005-2007, the
    UK auctions' clearing prices for 2008-2012."""
    eea = eea_eua_price(root)
    record = {**bluenext_closes(root), **dmo_clearing_prices(root)}
    return {y: {"central": eea[y], "low": min(*p, eea[y]), "high": max(*p, eea[y])} for y, p in sorted(record.items())}


METHOD = {
    "constraint_turnup": ("2015-2025: the same switched-off wind volume priced on each half-hour's accepted offers "
                          "cheapest first (low) and dearest first (high) instead of 1.0.0's order, from a re-walk of "
                          "Elexon's settlement stacks held to 1.0.0's measured figure, never above 1.0.0's cap at the "
                          "BSUoS uplift; before Nov 2015 no stack data, so no turn-up line and no range"),
    "carbon": ("2005-2012: the line at the lowest and highest of the EEA's yearly allowance price and every "
               "price in that year's record: the Phase I spot exchange's daily closes (BlueNext, from 24 Jun 2005) "
               "for 2005-2007, the UK Government's auction clearing prices (DMO) for 2008-2012; the engine's merit "
               "order held as it is"),
}


def _headline(out: dict, line: str, years: list[int]) -> None:
    """`<line>.range.<bound>.headline.<m>`: 2002-2024, each year with a range at its low or high, central elsewhere."""
    out[f"{line}.range.years"] = ",".join(str(y) for y in years)
    out[f"{line}.range.method"] = METHOD[line]
    for bound in ("low", "high"):
        for m in MEASURES:
            out[f"{line}.range.{bound}.headline.{m}"] = out[f"{line}.headline.{m}"] + sum(
                out[f"{line}.range.{bound}.{y}.{m}"] - out[f"{line}.{y}.{m}"] for y in years if y <= LAST_CLOSED_YEAR)


# ------------------------------------------------------------------ constraint turn-up

def turnup_walks_by_year(root: Path = ROOT) -> dict[int, dict[str, float]]:
    """{year: {central, low, high}}, £ cash: the saved re-walk of Elexon's settlement stacks
    (tools/turnup_range.py), summed by calendar year."""
    out: dict[int, dict[str, float]] = {}
    for r in csv.DictReader(io.StringIO(source(root, "elexon-turnup-range").decode("utf-8"))):
        y = out.setdefault(int(r["date"][:4]), dict.fromkeys(("central", "low", "high"), 0.0))
        for k in y:
            y[k] += float(r[f"{k}_gbp"])
    return out


def _turnup(out: dict, doc: dict, root: Path) -> list[int]:
    """Each year 1.0.0 measures turn-up: the cheapest-first and dearest-first walks, scaled so the central walk
    is 1.0.0's own measured figure, then capped at the BSUoS uplift as 1.0.0 caps the line."""
    s = next(s for s in doc["model"]["schemes"] if s["scheme_id"] == "constraint_turnup")
    measured = {r["year"]: r["cost"] for r in s["extras"]["measured_annual"]}
    walks = turnup_walks_by_year(root)
    years = sorted(y for y in walks if y in measured)
    for y in years:
        central = out[f"constraint_turnup.{y}.cash"]
        cap = out[f"bsuos.{y}.cash"] + central
        scale = measured[y] / walks[y]["central"]
        for bound in ("low", "high"):
            cash = min(walks[y][bound] * scale, cap)
            out[f"constraint_turnup.range.{bound}.{y}.cash"] = cash
            out[f"constraint_turnup.range.{bound}.{y}.real"] = cash * out[f"constraint_turnup.{y}.real"] / central
    return years


def build(out: dict, doc: dict, root: Path = ROOT) -> None:
    """Add the range keys to `out` (the figures built so far from `doc`, the frozen results file)."""
    _headline(out, "constraint_turnup", _turnup(out, doc, root))
    prices = carbon_prices(root)
    for y, p in prices.items():
        for end, v in p.items():
            out[f"carbon.allowance_price.{end}.{y}"] = v
        for bound in ("low", "high"):
            for m in MEASURES:
                out[f"carbon.range.{bound}.{y}.{m}"] = out[f"carbon.{y}.{m}"] * p[bound] / p["central"]
    _headline(out, "carbon", sorted(prices))
