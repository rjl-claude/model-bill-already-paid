"""Every reference input the model reads, loaded once, and the model built from them
(aios-harness#53). The CLI, tools and tests take their inputs and model from here. The
website's own inputs (map, equivalences) are in the web-subsidy-clock repository (#140)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl
import yaml

from billpaid import money, reference
from billpaid.store import SnapshotStore
from billpaid import build as uk_build
from billpaid import register as reg_mod
from billpaid import scotland, stations


@dataclass
class Inputs:
    refs: dict              # annual reference histories (overlaid by the register in assemble_model)
    deflators: pl.DataFrame
    deflator_info: dict     # provenance of the deflator series
    road: dict              # the engine's no-net-zero road, GO5 and GO4 (aios-harness#43)
    carbon: dict            # the engine's carbon in the price and tax collected (aios-harness#44)
    domestic_share: dict    # households' share of electricity, for VAT (aios-harness#45)
    station_map: dict
    ro_stations: list
    bmu_map: dict
    ctx: dict
    bill: pl.DataFrame      # electricity bill, cash and 2024 prices
    bill_info: dict
    bmu_zones: dict
    pinned: dict            # the pinned shared cost register (decision 0168)


def load(root: Path) -> Inputs:
    ref = root / "reference"
    refs = reference.load_annual_costs(ref / "annual_scheme_costs.yaml")
    refs.update(reference.load_annual_costs(ref / "indirect_annual.yaml"))
    deflators = reference.load_deflators(ref / "deflators.yaml")
    deflator_yaml = yaml.safe_load((ref / "deflators.yaml").read_text())
    bill_raw = reference.load_electricity_bill(ref / "electricity_bill.yaml")
    bill_yaml = yaml.safe_load((ref / "electricity_bill.yaml").read_text())
    return Inputs(
        refs=refs,
        deflators=deflators,
        deflator_info={"source": deflator_yaml["source"],
                       "source_url": deflator_yaml["source_url"],
                       "base_year": deflator_yaml["base_year"],
                       "verified": deflator_yaml.get("verified", False)},
        road=reg_mod.road_from_engine(root),
        carbon=reg_mod.carbon_from_engine(root),
        domestic_share=reg_mod.domestic_share_from_engine(root),
        station_map=stations.load_station_map(ref / "cfd_stations.csv"),
        ro_stations=stations.load_ro_stations(ref / "ro_stations.csv"),
        bmu_map=stations.load_station_bmus(ref / "station_bmu_map.csv"),
        ctx=reference.load_context(ref / "context.yaml"),
        bill=(money.add_real(bill_raw.rename({"total_bill_gbp": "cost_gbp"}), deflators)
              .rename({"cost_gbp": "total_bill_gbp", "cost_gbp_2024": "total_bill_gbp_2024"})),
        bill_info={"source": bill_yaml["source"], "source_url": bill_yaml["source_url"],
                   "verified": bill_yaml.get("verified", False)},
        bmu_zones=scotland.load_bmu_zones(ref / "bmu_zone.csv"),
        pinned=reg_mod.load_pinned(root),
    )


def assemble_model(root: Path, inp: Inputs | None = None) -> tuple[dict, dict]:
    """The model, and the register overlay report (decision 0168). Reads every covered
    series for a closed year from the pinned shared cost register (billpaid.register), less the
    register adjustments reference/clock_findings.yaml drops (billpaid.findings).
    ``inp`` is loaded from ``root`` when not given."""
    from billpaid import findings as findings_mod

    inp = inp or load(root)
    pinned = inp.pinned
    pinned["selection"] = findings_mod.load(root / "reference" / "clock_findings.yaml", pinned["register"],
                                            product=pinned["product"])
    moved = reg_mod.overlay_refs(inp.refs, pinned)
    cm_share = reg_mod.cm_share_from_engine(root, pinned)
    model = uk_build.build(SnapshotStore(root / "data"), inp.refs, deflators=inp.deflators,
                           road=inp.road, station_map=inp.station_map,
                           ro_stations=inp.ro_stations, bmu_map=inp.bmu_map,
                           cm_share=cm_share, to_register=reg_mod.ToRegister(pinned),
                           carbon=inp.carbon, domestic_share=inp.domestic_share)
    model["findings"] = pinned["selection"].record()
    return model, {"refs_moved": moved, "refs": inp.refs}
