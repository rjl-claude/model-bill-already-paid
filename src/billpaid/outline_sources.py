"""The publishers' files version 1.2.0 reads (reference/outline_sources.yaml), each refused if its bytes are not the
pinned ones, and the figures read from them (aios-harness#235)."""
from __future__ import annotations

import functools
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
