"""The publishers' files version 1.2.0 reads (reference/outline_sources.yaml), each refused if its bytes are not the
pinned ones, and the figures read from them (aios-harness#235)."""
from __future__ import annotations

import functools
import math
import hashlib
import io
from pathlib import Path

import polars as pl
import yaml

ROOT = Path(__file__).resolve().parents[2]
PIN = "reference/outline_sources.yaml"


def sources(root: Path = ROOT) -> dict:
    """The saved sources, as pinned (for the figures file's meta)."""
    return yaml.safe_load((root / PIN).read_text())["sources"]


def source(root: Path, name: str) -> bytes:
    """A saved source named in the pin file, refused if its fingerprint is not the pinned one."""
    pin = sources(root)[name]
    data = (root / pin["file"]).read_bytes()
    fp = hashlib.sha256(data).hexdigest()
    if fp != pin["sha256"]:
        raise ValueError(f"{pin['file']} has sha256 {fp}, not the pinned {pin['sha256']}")
    return data


def _sheet(root: Path, name: str, sheet: str) -> pl.DataFrame:
    return pl.read_excel(io.BytesIO(source(root, name)), sheet_name=sheet, has_header=False,
                         read_options={"header_row": None})


def households(root: Path = ROOT) -> dict[int, float]:
    """UK households by year (ONS Table 5, "All households", thousands, as a count)."""
    t = _sheet(root, "ons-households", "5")
    rows = [list(r) for r in t.iter_rows()]
    head = next(r for r in rows if str(r[0]).startswith("Number of households"))
    total = next(r for r in rows if str(r[0]).strip() == "All households")
    out = {}
    for h, v in zip(head, total):
        if h and str(h).endswith(" Estimate"):
            out[int(str(h)[:4])] = float(v) * 1000
    return out


def ccl_electricity_rates(root: Path = ROOT) -> dict[int, float]:
    """{year: £/kWh}: the CCL main rate on electricity from 1 April of each year it changed (HMRC Table 1). The page
    holds its tables as escaped HTML inside a JSON block."""
    import html
    import re
    t = source(root, "hmrc-ccl-rates").decode("utf-8")
    t = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), t)
    i = t.index("Table 1. Main Climate Change Levy rates")
    table = t[i:t.index("</table>", i)]
    out = {}
    for row in re.findall(r"<tr>(.*?)</tr>", table, flags=re.S):
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td>(.*?)</td>", row, flags=re.S)]
        m = re.fullmatch(r"1 April (\d{4})", cells[0]) if cells else None
        if m:
            out[int(m.group(1))] = float(cells[1].lstrip("£"))
    return out


def hmrc_ccl_electricity(root: Path = ROOT) -> dict[int, float]:
    """{year: £}: CCL electricity declarations by calendar year (HMRC Table 1b; 2025 is HMRC's provisional)."""
    t = _sheet(root, "hmrc-envtax-bulletin", "CCL_and_CPF_statistics_tables")
    rows = [list(r) for r in t.iter_rows()]
    i = next(i for i, r in enumerate(rows) if str(r[0]).startswith("Table 1b."))
    col = next(j for j, h in enumerate(rows[i]) if str(h).startswith("Electricity declarations"))
    out = {}
    for r in rows[i + 1:]:
        lab = str(r[0])
        if not lab[:4].isdigit():
            break
        out[int(lab[:4])] = float(r[col]) * 1e6
    return out


def obr_environmental_levies(root: Path = ROOT) -> dict[int, float]:
    """{first calendar year of the financial year: £}: OBR's environmental levies receipts (databank)."""
    t = _sheet(root, "obr-databank", "Receipts (£bn)")
    rows = [list(r) for r in t.iter_rows()]
    head = next(r for r in rows if any(str(c).startswith("Environmental levies") for c in r))
    col = next(j for j, h in enumerate(head) if str(h).startswith("Environmental levies"))
    out = {}
    for r in rows:
        fy = str(r[0])   # the reader drops the sheet's empty first column
        if len(fy) == 7 and fy[:4].isdigit() and fy[4] == "-" and r[col] not in (None, ""):
            out[int(fy[:4])] = float(r[col]) * 1e9
    return out


@functools.lru_cache(maxsize=None)
def pdf_text(root: Path, name: str) -> str:
    """A saved PDF's text (pypdf), pages joined; read once a run."""
    import pypdf
    return "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(source(root, name))).pages)


def _after(seg: str, label: str, n: int, money: bool) -> list[float]:
    import re
    rest = seg[seg.index(label) + len(label):]
    rx = r"£([\d,]+\.\d\d)" if money else r"(?<![\d,.])(\d{1,3}(?:,\d{3})+)(?![\d,])"
    return [float(x.replace(",", "")) for x in re.findall(rx, rest)[:n]]


def ofgem_ro_scheme_value(root: Path = ROOT) -> dict[int, float]:
    """{obligation year (its April): £}: Ofgem's scheme value, ROCs presented x the worth of a ROC to a supplier,
    each country at its own worth where they differ (to 2004-05)."""
    import re
    out: dict[int, float] = {}
    t = pdf_text(root, "ofgem-ro-2005-06")
    b = re.split(r"Table [123]: How suppliers complied", t)[1:4]
    ew, ew_w = _after(b[0], "Total number", 4, False), _after(b[0], "What a ROC", 4, True)
    sc, sc_w = _after(b[1], "Total number", 4, False), _after(b[1], "What a ROC", 4, True)
    ni, ni_w = _after(b[2], "Total number of ROCs presented", 1, False)[0], _after(b[2], "What a ROC", 1, True)[0]
    for k, y in enumerate(range(2002, 2006)):
        out[y] = ew[k] * ew_w[k] + sc[k] * sc_w[k] + (ni * ni_w if y == 2005 else 0.0)
    t = pdf_text(root, "ofgem-ro-2009-10")
    b = re.split(r"Table [123]: How suppliers complied", t)[1:4]
    rocs = [_after(x, "Total ROCs presented", 4, False) for x in b]
    worth = [_after(x, "Worth' of a ROC", 4, True) for x in b]
    if not worth[0] == worth[1] == worth[2]:
        raise ValueError(f"Ofgem 2009-10: the three countries' ROC worth differ: {worth}")
    for k, y in enumerate(range(2006, 2010)):
        out[y] = sum(r[k] for r in rocs) * worth[0][k]
    t = pdf_text(root, "ofgem-ro-sy23")
    a = t[t.rindex("Figure A4.1"):]
    for sy in range(9, 24):
        m = re.search(rf"SY{sy}\s*\(\d{{4}}-\d\d\)\s*£[\d,]+m\s+([\d.]+)m\s+£[\d.]+\s+£([\d.]+)", a)
        out[2001 + sy] = float(m.group(1)) * 1e6 * float(m.group(2))
    return out


def ofgem_fit_levelisation(root: Path, years: range) -> dict[int, float]:
    """{FIT year (its April): £}: the levelisation fund as printed in Ofgem's document for that year, found under its
    label ("levelisation fund"); refused if the document prints no such figure."""
    import re
    out = {}
    for y in years:
        t = pdf_text(root, f"ofgem-fit-{y}")
        # the label, then the figure within a short gap (a formula such as "(D) (A + B + C)", or "for the year was
        # calculated at"), with no other £ figure between; the fund is the largest such figure (a footnote can give
        # a part of it under the same words, as 2011-12's deemed element does)
        hits = re.findall(r"levelisation\s*f\s*und[^£]{0,60}£\s?([\d,]{5,}(?:\.\d+)?)", t, flags=re.I)
        if not hits:
            raise ValueError(f"no levelisation fund figure found in ofgem-fit-{y}")
        found = max(float(h.replace(",", "")) for h in hits)
        out[y] = found
    return out


def ref_direct_totals(root: Path = ROOT) -> dict[str, float]:
    """{column: £}: REF's Table 1 totals row (RO, CfD, FiT, Constraints, REGO, Totals), £bn nominal as printed."""
    import html
    import re
    t = source(root, "ref-2025").decode("utf-8", errors="replace")
    s = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))
    i = s.index("Table 1: Direct Subsidies")
    m = re.search(r"Totals\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", s[i:])
    return dict(zip(("ro", "cfd", "fit", "constraints", "rego", "total"), (float(x) * 1e9 for x in m.groups())))


GB_NATIONS = ("England", "Wales", "Scotland")
GB_NEW_FROM = 2015   # first year read from the 2025 workbook (as Report No. 1)


def households_gb(root: Path = ROOT) -> dict[int, float]:
    """Great Britain households by year, ONS Labour Force Survey (April-June): England + Wales + Scotland, 2015 on
    from the 2025 workbook, earlier years from ad hoc 005374 (as Report No. 1 counts them)."""
    out: dict[int, float] = {}
    new: dict[int, float] = {}
    for nation in GB_NATIONS:
        rows = [list(r) for r in _sheet(root, "ons-households-gb-2015-2025", nation).iter_rows()]
        head = next(r for r in rows if str(r[0]).startswith("Number of households"))
        total = next(r for r in rows if r[0] == "All households")
        for h, v in zip(head, total):
            if h and str(h).endswith(" Estimate"):
                new[int(str(h)[:4])] = new.get(int(str(h)[:4]), 0.0) + float(v) * 1000
    t = pl.read_excel(io.BytesIO(source(root, "ons-households-gb-1996-2017")), sheet_id=1, has_header=False,
                      read_options={"header_row": None})
    rows = {str(r[0]).strip(): r for r in t.iter_rows() if r[0] is not None}
    years = [int(y) for y in rows["Region"][1:] if y not in (None, "")]
    for i, y in enumerate(years, start=1):
        if y < GB_NEW_FROM:
            out[y] = sum(float(rows[n][i]) for n in ("England (Total)", "Wales", "Scotland"))
    out.update(new)
    return dict(sorted(out.items()))


def ons_series_fy(root: Path, cdid: str) -> dict[int, float]:
    """{first calendar year of the financial year: £}: an ONS public sector finances series (£m by quarter)
    summed April-March, whole years only."""
    import json
    d = json.loads(source(root, f"ons-psf-{cdid}"))
    by: dict[int, list[float]] = {}
    for q in d["quarters"]:
        if q["value"] in ("", None):
            continue
        y, quarter = int(q["date"][:4]), q["date"][-2:]
        by.setdefault(y - 1 if quarter == "Q1" else y, []).append(float(q["value"]) * 1e6)
    return {fy: math.fsum(v) for fy, v in by.items() if len(v) == 4}


def ro_obligation(root: Path, fy: int) -> dict[str, float]:
    """{england_wales, scotland, northern_ireland: ROCs obligated}: Ofgem's total obligation notice for obligation
    year fy (its April)."""
    import html
    import re
    t = source(root, f"ofgem-ro-obligation-{fy}").decode("utf-8", errors="replace")
    s = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))   # &nbsp; too
    out = {}
    for key, label in (("england_wales", "England and Wales"), ("scotland", "Scotland"),
                       ("northern_ireland", "Northern Ireland")):
        m = re.search(rf"([\d,]{{7,}}) ROCs in {label}", s)
        out[key] = float(m.group(1).replace(",", ""))
    return out


def _row_with(t: list[list], text: str, start: int = 0, exact: bool = False) -> int:
    """The first row at or after `start` with a cell that starts with (or is) `text`."""
    for i in range(start, len(t)):
        if any((str(c).strip() == text) if exact else str(c).startswith(text) for c in t[i] if c is not None):
            return i
    raise ValueError(f"no row with {text!r}")


def _num(c) -> float | None:
    try:
        return float(c)
    except (TypeError, ValueError):
        return None


def cap_policy_costs(root: Path = ROOT) -> dict:
    """Ofgem's price cap, Annex 4: {"rates": {fy: {scheme: {"summer"|"winter": £/MWh}}} for single-rate
    electricity, RO and FiT, each half the latest update for its cap periods (later columns are later updates);
    "weights": the single-rate summer and winter weights; "typical": {effective dates: single-rate typical
    consumption, MWh}; "ro_level": {fy: GB obligation, ROCs/MWh}}. The reader drops empty columns, so every row is
    found by its label."""
    t = [list(r) for r in _sheet(root, "ofgem-cap-annex-4", "1a Policy Cost Allowance").iter_rows()]
    head = _row_with(t, "2. Scheme by scheme")
    period, fyrow = t[_row_with(t, "28AD Charge Restriction Period", head)], t[_row_with(t, "Fiscal year", head)]
    ro_i = _row_with(t, "Electricity - Single-Rate", head)
    if "RO" not in [str(c).strip() for c in t[ro_i]]:
        raise ValueError("Annex 4 1a: the single-rate block does not start with the RO")
    fit_i = _row_with(t, "FiT", ro_i + 1, exact=True)
    rows = {"ro": t[ro_i], "fit": t[fit_i]}
    rates: dict[int, dict] = {}
    for j, fy in enumerate(fyrow):
        fy = str(fy)
        if not (len(fy) >= 7 and fy[:4].isdigit() and fy[4] == "/") or _num(rows["ro"][j]) is None:
            continue
        half = "summer" if str(period[j]).strip().startswith("April") else "winter"
        for sch, r in rows.items():
            rates.setdefault(int(fy[:4]), {}).setdefault(sch, {})[half] = _num(r[j])
    d = [list(r) for r in _sheet(root, "ofgem-cap-annex-4", "3a Demand").iter_rows()]
    w = d[_row_with(d, "Electricity - Single-Rate", _row_with(d, "Weights"))]
    ws = [x for x in (_num(c) for c in w) if x is not None]
    notes = [list(r) for r in _sheet(root, "ofgem-cap-annex-4", "Notes").iter_rows()]
    i = _row_with(notes, "Typical consumption (MWh) effective dates")
    dates = [c for c in notes[_row_with(notes, "Fuel / Benchmark Metering Arrangement", i)] if c][1:]
    vals = [x for x in (_num(c) for c in notes[_row_with(notes, "Electricity - Single-Rate", i)]) if x is not None]
    b = [list(r) for r in _sheet(root, "ofgem-cap-annex-4", "3b RO").iter_rows()]
    yr, lv = b[_row_with(b, "RO charging year")], b[_row_with(b, "Obligation level for scheme year")]
    level = {int(str(fy)[:4]): _num(lv[j]) for j, fy in enumerate(yr)
             if str(fy)[:4].isdigit() and _num(lv[j]) is not None}
    return {"rates": rates, "weights": {"summer": ws[0], "winter": ws[1]},
            "typical": dict(zip(dates, vals)), "ro_level": level}
