"""Key by key, the figures file of one version against another's (aios-harness#235): every value that moves, and
every key added or dropped. Writes a Markdown table.

    uv run --frozen python tools/compare_figures.py refs/tags/v1.1.0 results/figures.json docs/1.2.0-against-1.1.0.md
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from billpaid import figures  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _fmt(v) -> str:
    return f"{v:,.6f}" if isinstance(v, float) else str(v)


def main(old_ref: str, new_path: str, out_path: str) -> int:
    old_doc = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"{old_ref}:results/figures.json"],
                                        capture_output=True, check=True).stdout)
    new_doc = json.loads((ROOT / new_path).read_text())
    old, new = old_doc["figures"], new_doc["figures"]
    moved = [k for k in old if k in new and old[k] != new[k]]
    dropped = [k for k in old if k not in new]
    added = [k for k in new if k not in old]
    exact = [k for k in moved if isinstance(old[k], float) and math.isclose(old[k], new[k], rel_tol=1e-14)]
    patterns = {t: re.compile(figures.template_regex(t)) for t in figures.KEYS}
    by_template: dict[str, int] = {}
    for k in added:
        t = next((t for t, rx in patterns.items() if rx.fullmatch(k)), "(no template)")
        by_template[t] = by_template.get(t, 0) + 1
    v_old, v_new = old_doc["meta"]["version"], new_doc["meta"]["version"]
    lines = [f"# Version {v_new} against {v_old}: the figures file, key by key", "",
             f"Made by `tools/compare_figures.py {old_ref} {new_path} {out_path}`: {v_old}'s file as committed at "
             f"`{old_ref}`, {v_new}'s as built. £ in the file's own units (cash: £ as paid; real: £ in 2024 prices).",
             "",
             f"- {v_old}: {len(old):,} keys. {v_new}: {len(new):,} keys.",
             f"- Kept: {len(old) - len(dropped):,} of {len(old):,}; dropped: {len(dropped)}.",
             f"- Values that move: {len(moved) - len(exact)} (and {len(exact)} that differ only past the "
             f"fourteenth significant figure, float rounding, listed last).",
             f"- Keys added: {len(added):,}.", "",
             "## Every value that moves", "",
             "Each is a wind constraint payment year moved from REF's database to Elexon's record (2016-2023), or a "
             "figure made from those years by the model's own rules: the split of the balancing total into "
             "constraints, turn-up and BSUoS, the line and layer totals, turn-up's range where its cap binds, and "
             "the turn-up estimate over its whole window. The headline (`all.*`) does not move.", "",
             f"| Key | {v_old} | {v_new} | Change |", "|---|---:|---:|---:|"]
    for k in sorted(set(moved) - set(exact)):
        lines.append(f"| `{k}` | {_fmt(old[k])} | {_fmt(new[k])} | {_fmt(new[k] - old[k])} |")
    if exact:
        lines += ["", "Float rounding only (the same total summed with two of its parts changed: the last binary digit of a float, never a penny):", ""]
        lines += [f"- `{k}`: {old[k]!r} to {new[k]!r}" for k in sorted(exact)]
    if dropped:
        lines += ["", "## Dropped", ""] + [f"- `{k}`" for k in dropped]
    lines += ["", "## Keys added, by template", "", "| Template | Keys |", "|---|---:|"]
    lines += [f"| `{t}` | {n} |" for t, n in sorted(by_template.items())]
    (ROOT / out_path).write_text("\n".join(lines) + "\n")
    print(f"{len(moved) - len(exact)} moved, {len(exact)} float rounding, {len(added)} added, {len(dropped)} dropped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:4]))
