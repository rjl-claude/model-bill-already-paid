"""The command implementations behind the billpaid CLI (the parser and ROOT are in
billpaid.__main__, the entry point: `python -m billpaid ...`)."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from billpaid import reconcile, reference, results
from billpaid.store import SnapshotStore
from billpaid import stations
from billpaid import elexon
from billpaid.schemes import (bsuos, capacity_market, cfd, constraint_turnup,
                                      constraints, remit)


def make_store(root: Path) -> SnapshotStore:
    return SnapshotStore(root / "data")


def cmd_update(args: argparse.Namespace) -> int:
    store = make_store(args.root)
    failures = []
    targets = {
        "cfd": lambda: cfd.update(store),
        "constraints": lambda: constraints.update(store),
        "constraint_turnup": lambda: constraint_turnup.update(store),
        "cm": lambda: capacity_market.update(store),
        "bsuos": lambda: bsuos.update(store),
        "remit": lambda: remit.update(
            store,
            sorted({b for ids in stations.load_station_bmus(
                args.root / "reference" / "station_bmu_map.csv").values()
                for b in ids})),
    }
    chosen = targets if args.scheme == "all" else {args.scheme: targets[args.scheme]}
    for name, fn in chosen.items():
        try:
            fn()
            print(f"[ok] {name} updated")
        except Exception as exc:  # F-8: failures visible, one scheme never blocks another
            failures.append(name)
            print(f"[FAIL] {name}: {exc}", file=sys.stderr)
    return 1 if failures else 0


# Exit code of a backward-backfill week with no bids (0176, option C): the daily workflow still builds and
# deploys, then turns the run red so Richard is alerted.
BACKFILL_STALLED = 3


def cmd_backfill_constraints(args: argparse.Namespace) -> int:
    store = make_store(args.root)
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    first = elexon.STACK_FIRST_DAY
    if end < first:
        print(f"[backfill] constraints: Elexon's data starts on {first:%-d %B %Y}; nothing earlier to fetch")
        return 0
    start = max(start, first)
    if constraints.backfill(store, start, end) == 0:
        print(f"[stall] constraints backfill: no bids from Elexon for {start} to {end}; the next run will ask "
              f"for the same week (0176: the site still updates; this run is marked failed)", file=sys.stderr)
        return BACKFILL_STALLED
    return 0


def cmd_backfill_turnup(args: argparse.Namespace) -> int:
    store = make_store(args.root)
    n, failed = constraint_turnup.backfill(store, date.fromisoformat(args.start),
                                           date.fromisoformat(args.end), progress=True)
    print(f"[ok] constraint_turnup: {n} days written")
    if failed:
        print(f"[FAIL] constraint_turnup: {len(failed)} day(s) failed, rerun to retry: "
              + ", ".join(d.isoformat() for d in failed), file=sys.stderr)
        return 1
    return 0


def cmd_results(args: argparse.Namespace) -> int:
    """Run the model and write its results file (billpaid.results), then print the internal checks
    against REF (printed only, never written: REF comparisons were taken off the site, 17 Oct 2026)."""
    import polars as pl

    generated_at = datetime.now(timezone.utc).isoformat()
    doc, run = results.assemble(args.root, generated_at=generated_at)
    model, overlay = run["model"], run["overlay"]
    if overlay["refs_moved"]:
        print(f"[register] closed years moved by the register: {overlay['refs_moved']}")
    scot, report = run["scotland"], run["reconciliation"]
    if scot is not None:
        print(f"[scotland] £{scot['scotland_cost'] / 1e6:,.0f}m of £{scot['gb_cost'] / 1e6:,.0f}m "
              f"({scot['scotland_share']:.1%}) to Scottish wind, {scot['window']['from']} to "
              f"{scot['window']['to']}")
    if report is not None:
        flag = "OK" if report["within_tolerance"] else "DIVERGENT"
        pct = report["overall"]["divergence_pct"]
        print(f"[reconciliation] {flag}: overall divergence {pct}% over "
              f"{report['matched_days']} matched days "
              f"({report['excluded_recent_days']} recent days excluded)")

    crosscheck_path = args.root / "reference" / "ref_crosscheck.yaml"
    if crosscheck_path.is_file():
        ref_cc = reference.load_ref_crosscheck(crosscheck_path)
        cc_year = int(ref_cc["year"][:4])
        ours = {}
        for s in model["schemes"]:
            if s.layer == "indirect":
                row = s.annual.filter(pl.col("year") == cc_year)
                key = REF_KEY.get(s.scheme_id, s.scheme_id)
                if key is None:
                    continue
                ours[key] = ours.get(key, 0.0) + (float(row["cost_gbp"][0]) if row.height else 0.0)
        # Internal check only: the result is printed, not written to the results file
        # (REF comparisons were taken off the site, 17 Oct 2026).
        cc = reconcile.indirect_crosscheck(ours, ref_cc)
        print(f"[crosscheck] {len(cc['components'])} components vs REF {cc['comparison_year']}; "
              f"{cc['unexplained_count']} unexplained beyond ±{cc['bound_pct']}%")

    ref_totals_path = args.root / "reference" / "ref_totals.yaml"
    if ref_totals_path.is_file():
        ref_t = reference.load_ref_totals(ref_totals_path)
        thru = int(ref_t["ours_through_year"])
        comp: dict[str, float] = {}
        real_total = 0.0
        for s in model["schemes"]:
            cut = s.annual.filter(pl.col("year") <= thru)
            nom = float(cut["cost_gbp"].sum()) if cut.height else 0.0
            if "cost_gbp_2024" in cut.columns and cut.height:
                real_total += float(cut["cost_gbp_2024"].sum())
            key = REF_KEY.get(s.scheme_id, s.scheme_id)
            if key is None:      # a line REF does not count at all (VAT, aios-harness#45)
                continue
            comp[key] = comp.get(key, 0.0) + nom
        unmapped = set(comp) - set(ref_t["components"])
        if unmapped:
            raise SystemExit(f"[ref-reconciliation] schemes not in REF table: {sorted(unmapped)}")
        # Internal check only: the result is printed, not written to the results file
        # (REF comparisons were taken off the site, 17 Oct 2026).
        recon = reconcile.ref_reconciliation(comp, real_total, ref_t)
        print(f"[ref-reconciliation] ours £{recon['ours_total']/1e9:.1f}bn vs "
              f"REF £{recon['ref_total']/1e9:.1f}bn to {thru}; "
              f"stricter choices remove £{recon['stricter_gap']/1e9:.1f}bn "
              f"against the £{recon['gap']/1e9:.1f}bn gap")

    out = args.out or args.root / "results" / results.FILE
    fp = results.write(doc, out)
    print(f"[ok] results written to {out} (model {doc['meta']['version']}, sha256 {fp[:12]})")
    return 0


# How our schemes map onto REF's components for the like-for-like checks.
# REF's BSUoS is the whole balancing charge, so constraint turn-up, which we
# carve out of the BSUoS uplift, folds back into it for comparison.
REF_KEY = {"cfd_renewable": "cfd", "cfd_low_carbon": "cfd",
           "constraint_turnup": "bsuos", "carbon": "ets", "vat": None}
