"""The generators' share of grid and balancing charges, the part not paid out of subsidy (version 1.6.0; report-series
ADR 0264, Richard's ruling of 19 Nov 2026).

Power stations pay part of the grid (TNUoS) and balancing (BSUoS) charges. 1.0.0 to 1.5.0 leave that share out on
both sides (decision 0024). Stations with a subsidy (the Renewables Obligation, Feed-in Tariffs, a Contract for
Difference) pay their share out of subsidy income, which the model counts: that part stays out. Stations with none
recover it through the price of power, which the model does not count: that part is this line.

1. The generators' share of the cost above the gas-led alternative, each year, signed: the line counted with the
   share in, less the line counted with it out. For TNUoS, (whole charge - alternative with the share in) - (charge
   less the share - alternative without it). For BSUoS, the share of the residual balancing line only: switch-off
   payments and turn-up are counted whole in their own lines (decision 0027), so the share of the BSUoS charge left
   after them, less the alternative's share. The whole charge and the charge less the share are the pinned shared
   cost register's (the series, and the register's own row that takes the share out); the alternative with and
   without it are Report No. 1's release v4-s43 (its Clock export and its run file).
2. The part not paid out of subsidy: that times the share of the year's power made by stations with no subsidy,
   1 - (RO-eligible + CfD + FIT output) / all output (DUKES 6.2, LCCC, Ofgem). The range: every renewable station
   counted as subsidised (low), or FIT left out, as small stations on local wires pay neither charge (high).

The method and the figures: docs/figures.md, "Version 1.6.0".
"""
from __future__ import annotations

import functools
import hashlib
import io
import math
from pathlib import Path

import polars as pl
import yaml

from billpaid import outline, outline_sources, provisional
from billpaid import register as reg_mod

LINE = "generators_share"
YEARS = range(2002, 2026)
PIN = "reference/generators_share.yaml"


def _pin(root: Path) -> dict:
    return yaml.safe_load((root / PIN).read_text())


def source(root: Path, name: str) -> bytes:
    """A saved source, from reference/generators_share.yaml or else reference/outline_sources.yaml, refused if its
    fingerprint is not the pinned one."""
    pins = _pin(root)["sources"]
    if name not in pins:
        return outline_sources.source(root, name)
    data = (root / pins[name]["file"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != pins[name]["sha256"]:
        raise ValueError(f"{pins[name]['file']} is not the pinned file")
    return data


@functools.cache
def _pdf_text(root: Path, name: str) -> str:
    import pypdf
    return "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(source(root, name))).pages)


def pdf_text(root: Path, name: str) -> str:
    """A saved PDF's text (pypdf), pages joined."""
    return _pdf_text(root, name)


def fit_generation(root: Path) -> dict[int, dict]:
    """{FIT year's starting year: {gwh, source, quote}}: the electricity FIT installations generated, Ofgem."""
    return {int(y): r for y, r in _pin(root)["fit_generation_gwh"].items()}


def _dukes(root: Path) -> dict[str, dict[int, float]]:
    """DUKES 6.2's generation rows, GWh by year: ro (eligible for the RO), renewables, total (all sources)."""
    t = pl.read_excel(io.BytesIO(source(root, "dukes-6.2")), sheet_name="6.2", has_header=False,
                      read_options={"header_row": None})
    rows = [list(r) for r in t.iter_rows()]
    head = next(i for i, r in enumerate(rows) if str(r[0]).startswith("Generation (GWh)"))
    years = [int(h) for h in rows[head][1:] if h]

    def row(start: str, exact: bool = False) -> dict[int, float]:
        r = next(r for r in rows[head:] if (str(r[0]).strip() == start if exact else str(r[0]).startswith(start)))
        return {y: float(v) for y, v in zip(years, r[1:]) if v not in (None, "[x]")}

    return {"ro": row("Total generation from sources eligible for the Renewable Obligation"),
            "renewables": row("Total generation", exact=True),
            "total": row("Total electricity generation (GWh)")}


def generation(doc: dict, root: Path) -> dict[int, dict[str, float]]:
    """{year: GWh}, calendar years: ro, renewables and total (DUKES 6.2, UK), cfd (LCCC's daily generation in the
    store as the frozen file was built, Great Britain) and fit (Ofgem's FIT years by calendar year: a quarter of the
    one ending in the year, three quarters of the one starting in it; a FIT year not yet reported carries the last)."""
    d = _dukes(root)
    cfd = outline.cfd_payments(doc, root).with_columns(pl.col("date").dt.year().alias("year"))
    by_year: dict[int, list[float]] = {}
    for y, v in cfd.select("year", "generation_mwh").iter_rows():
        by_year.setdefault(y, []).append(v or 0.0)
    cfd = {y: math.fsum(v) for y, v in by_year.items()}   # exact: the same whatever the rows' order (#252)
    fit = {y: r["gwh"] for y, r in fit_generation(root).items()}
    last = max(fit)
    fy = lambda y: fit.get(y, fit[last] if y > last else 0.0)  # noqa: E731
    return {y: {"ro": d["ro"][y], "renewables": d["renewables"][y], "total": d["total"][y],
                "cfd": cfd.get(y, 0.0) / 1e3, "fit": 0.25 * fy(y - 1) + 0.75 * fy(y)} for y in YEARS}


def unsubsidised_share(gen: dict[int, dict[str, float]]) -> dict[int, dict[str, float]]:
    """{year: {central, low, high}}: the share of the year's output from stations with no subsidy. Central: 1 - (RO-
    eligible + CfD + FIT) / all. Low: every renewable station counted as subsidised. High: FIT left out (small
    stations on local wires, which pay neither generators' charge)."""
    return {y: {"central": 1 - (g["ro"] + g["cfd"] + g["fit"]) / g["total"],
                "low": 1 - g["renewables"] / g["total"],
                "high": 1 - (g["ro"] + g["cfd"]) / g["total"]} for y, g in gen.items()}


SHARE_OUT = "rb.BSUOS.generators_share_out"   # the register's row that takes the generators' share out of BSUoS


def _rows(doc: dict, line: str) -> dict[int, float]:
    s = next(s for s in doc["model"]["schemes"] if s["scheme_id"] == line)
    return {r["year"]: r["cost_gbp"] for r in s["annual"]["rows"]}


def charges(doc: dict, root: Path) -> dict[int, dict[str, float]]:
    """{year: parts}, £ cash: the generators' share of the cost above the gas-led alternative, signed. `doc` is the
    results file with wind constraint payments from primary records (billpaid.elexon_record.apply).
    - tnuos: the grid line's share.
    - bsuos: the residual balancing line's share: the share of the charge generators paid (bsuos_share_rate) times
      the charge less switch-off payments and turn-up as counted (switch_off_and_turn_up), less the alternative's
      share (the alternative holds no switch-off payments or turn-up: a system with no wind)."""
    reg = reg_mod.load_pinned(root)["register"]
    whole = {"tnuos": reg.series("TNUOS"), "bsuos": reg.series("BSUOS")}
    less_tnuos = provisional.register_line(root, "tnuos")
    share_out = reg.adjustments("BSUOS", "rb")[SHARE_OUT]
    ex, _ = reg_mod.engine_export(root)
    road = reg_mod.road_from_engine(root)
    con, tu = _rows(doc, "constraints"), _rows(doc, "constraint_turnup")
    out = {}
    for y in YEARS:
        alt = {k: (ex[sec]["years"][str(y)]["central_gbp"], road[k]["years"][y])
               for k, sec in (("tnuos", "grid"), ("bsuos", "balancing"))}
        bs_whole = whole["bsuos"][y] * 1e6
        rate = -share_out.get(y, 0.0) * 1e6 / bs_whole
        paid = con.get(y, 0.0) + tu.get(y, 0.0)
        out[y] = {"tnuos": (whole["tnuos"][y] * 1e6 - alt["tnuos"][0]) - (less_tnuos[y] - alt["tnuos"][1]),
                  "bsuos": rate * (bs_whole - paid) - (alt["bsuos"][0] - alt["bsuos"][1]),
                  "bsuos_share_rate": rate, "switch_off_and_turn_up": paid}
    return out


def _real(doc: dict, y: int, cash: float) -> float:
    """£ in 2024 prices by the model's own rule for a calendar-year line."""
    from billpaid.elexon_record import _real as real
    import polars as pl
    deflators = pl.DataFrame(doc["deflators"]["rows"],
                             schema={k: getattr(pl, v) for k, v in doc["deflators"]["schema"].items()}, orient="row")
    return real(cash, y, deflators)


def table(doc: dict, root: Path) -> dict[int, dict]:
    """{year: everything the figures file prints of the line}: the share above the alternative (tnuos, bsuos, £
    cash), the output (GWh), the unsubsidised share (central, low, high) and the line at each (£ cash)."""
    c, gen = charges(doc, root), generation(doc, root)
    u = unsubsidised_share(gen)
    out = {}
    for y in YEARS:
        share = c[y]["tnuos"] + c[y]["bsuos"]
        ends = sorted((share * u[y]["low"], share * u[y]["high"]))   # a year below the alternative is negative
        out[y] = {**c[y], "generation": gen[y], "unsubsidised": u[y],
                  "central": share * u[y]["central"], "low": ends[0], "high": ends[1]}
    return out


def apply(doc: dict, root: Path) -> tuple[dict, dict]:
    """(doc, table): `doc` (a copy, constraint payments from primary records) with the new line in it, 2002-2025,
    and the VAT on it added to the VAT line by 1.0.0's rule (5% of households' share each year)."""
    import copy

    from billpaid.schemes import vat as vat_mod
    doc = copy.deepcopy(doc)
    t = table(doc, root)
    rows = [{"year": y, "cost_gbp": t[y]["central"], "cost_gbp_2024": _real(doc, y, t[y]["central"])} for y in YEARS]
    doc["model"]["schemes"].append({
        "scheme_id": LINE, "label": "Generators' share of grid and balancing charges, not paid out of subsidy",
        "layer": "indirect", "perspectives": [], "cadence": "annual", "annual": {"rows": rows},
        "cumulative_gbp": math.fsum(r["cost_gbp"] for r in rows), "attribution_confidence": "low",
        "extras": {"method": "billpaid.generators_share; docs/figures.md, Version 1.6.0"}})
    vat = next(s for s in doc["model"]["schemes"] if s["scheme_id"] == "vat")
    share = {r["year"]: r["share"] for r in vat["extras"]["domestic_share"]}
    for r in vat["annual"]["rows"]:
        y = r["year"]
        if y in t:
            r["cost_gbp"] += vat_mod.RATE * share[y] * t[y]["central"]
            r["cost_gbp_2024"] = _real(doc, y, r["cost_gbp"])
    vat["extras"]["base_lines"] = [*vat["extras"]["base_lines"], LINE]
    return doc, t


METHOD = ("The line at the share of output from stations with no subsidy read two other ways: low, every renewable "
          "station counted as subsidised (DUKES 6.2, all renewable output); high, Feed-in Tariff stations left out, "
          "as small stations on local wires pay neither generators' charge. The generators' share above the "
          "gas-led alternative is held as it is")
GRIDS = ("tnuos", "bsuos")
OUTPUT = ("ro", "cfd", "fit", "renewables", "total")


def figures(out: dict, doc: dict, t: dict) -> None:
    """The line's own keys beside `<line>.<year>.<m>` (which billpaid.figures writes as for every line): its parts
    by charge, the unsubsidised share, the output, and its range, each year 2002-2025 (headlines 2002-2024)."""
    from billpaid import ranges
    deflate = lambda y, cash: _real(doc, y, cash)  # noqa: E731
    for y, r in t.items():
        money = {**{f"{LINE}.{g}": r[g] for g in GRIDS},
                 **{f"{LINE}.range.{b}": r[b] for b in ("low", "high")}}
        for key, cash in money.items():
            for m, v in (("cash", cash), ("real", deflate(y, cash))):
                out[f"{key}.{y}.{m}"] = v
                if y <= ranges.LAST_CLOSED_YEAR and ".range." not in key:
                    out[f"{key}.headline.{m}"] = out.get(f"{key}.headline.{m}", 0.0) + v
        for end, v in r["unsubsidised"].items():
            out[f"{LINE}.unsubsidised_share.{y}.{end}"] = v
        for g in OUTPUT:
            out[f"{LINE}.generation.{g}.{y}"] = r["generation"][g]
    out[f"{LINE}.range.years"] = ",".join(str(y) for y in t)
    out[f"{LINE}.range.method"] = METHOD
    for b in ("low", "high"):
        for m in ("cash", "real"):
            out[f"{LINE}.range.{b}.headline.{m}"] = math.fsum(
                out[f"{LINE}.range.{b}.{y}.{m}"] for y in t if y <= ranges.LAST_CLOSED_YEAR)
