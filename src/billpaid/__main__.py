"""CLI: update schemes on their own cadences (F-2), backfill history (F-3), and write the
model's results file (billpaid.results)."""

from __future__ import annotations

import argparse
from pathlib import Path

from billpaid import cli

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="billpaid",
                                     description="The bill already paid: UK subsidies scheme by scheme")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    sub = parser.add_subparsers(dest="command", required=True)

    p_update = sub.add_parser("update", help="fetch latest data for scheme(s)")
    p_update.add_argument("scheme", choices=["all", "cfd", "constraints", "constraint_turnup", "cm",
                                   "bsuos", "remit"],
                          nargs="?", default="all")
    p_update.set_defaults(fn=cli.cmd_update)

    p_bf = sub.add_parser("backfill-constraints",
                          help="backfill constraint daily data for a date range")
    p_bf.add_argument("--start", required=True)
    p_bf.add_argument("--end", required=True)
    p_bf.set_defaults(fn=cli.cmd_backfill_constraints)

    p_tu = sub.add_parser("backfill-turnup",
                          help="backfill constraint turn-up daily data for a date range")
    p_tu.add_argument("--start", required=True)
    p_tu.add_argument("--end", required=True)
    p_tu.set_defaults(fn=cli.cmd_backfill_turnup)

    p_res = sub.add_parser("results", help="run the model and write its results file")
    p_res.add_argument("--out", type=Path, default=None,
                       help="file to write (default: <root>/results/clock.json)")
    p_res.set_defaults(fn=cli.cmd_results)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
