# The bill already paid

The sums behind **[the Subsidy Clock](https://subsidyclock.co.uk)**: the subsidies paid to UK renewable and low-carbon electricity generators since 2002, and the indirect costs they cause, scheme by scheme. Its years 2002 to 2025 are the first half of Report No. 2, *The Price of the Climate Bill*.

Figures are reconstructed bottom-up from official sources (LCCC, Elexon, NESO, Ofgem, HMRC, DESNZ, the NAO, with REF for cross-checks and constraint history), with full provenance: every retrieved data point links to its source URL, retrieval timestamp and content hash.

This repository holds the data engine, the raw data store and the reference inputs. The website is [richardjlyon/subsidy-clock](https://github.com/richardjlyon/subsidy-clock); it reads only this model's results file. Until 6 Nov 2026 both were one repository; the history of every file here is kept from it.

## Quickstart

Requires Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
tools/test.sh                                   # the standard test run; every test passes
uv run python -m billpaid update all            # fetch latest data from all sources
uv run python -m billpaid backfill-constraints --start 2024-01-01 --end 2024-03-31
uv run python -m billpaid results               # run the model: results/clock.json and its fingerprint
```

The raw data store is committed, so **every figure is reproducible from a clone with no network access**.

## The results file

`results/clock.json` holds everything the website and Report No. 2 read: each scheme's yearly cost (cash and 2024 prices), run-rate and data end, the totals, the context figures, deflators and bill, data freshness, restatements, the Scottish constraints figures and the CfD reconciliation. Its `meta` block names the model, its version (`pyproject.toml`), the file format and the commit. `results/clock.json.sha256` is the file's fingerprint. A reader pins the version (the website: `reference/results_pin.yaml` there; a report: version and fingerprint of one day's file) and refuses any other.

## Layout

```
src/billpaid/   retrieval (ckan.py, elexon.py, schemes/), money model (money.py), the model run
                (build.py, inputs.py), the shared cost register (register.py, cost_register.py,
                findings.py), splice and uplift, reconciliation (reconcile.py), reference loaders
                (reference.py), station mapping (stations.py), immutable store (store.py),
                the results file (results.py)
reference/      reference inputs: CPIH deflators, buy-out prices, bill denominator, indirect-cost
                annuals and REF cross-checks (*.yaml); the pinned register and engine release
data/raw/       the Parquet store
results/        the results file and its fingerprint
tests/          pytest suite
```

## Data integrity

```
data/raw/{scheme}/{table}/{partition}/{retrieved-at}/data.parquet
data/raw/{scheme}/{table}/{partition}/{retrieved-at}/manifest.json
```

`manifest.json` records `source_url`, `retrieved_at`, `sha256` (content hash of the table's canonical CSV serialisation) and `row_count`. The store is append-only: nothing is ever deleted. When a source revises history, the new version is stored alongside the old and the change is logged in `restatements.jsonl`. Bottom-up totals are checked against official aggregates and REF's published series when the model runs.

## Schemes

| Scheme | Layer | Source | Cadence | Method |
|---|---|---|---|---|
| Contracts for Difference | Direct | LCCC data portal | Daily | Per-contract generation × (strike − reference price), paybacks netted |
| Wind constraints | Direct | Elexon BMRS | Daily | Settlement bid stacks; earlier years from REF annual totals |
| Renewables Obligation | Direct | Ofgem annual reports | Annual | ROCs presented × (buy-out price + recycle value) |
| Feed-in Tariffs | Direct | Ofgem annual reports | Annual | Official levelisation totals |
| Capacity Market | Indirect | LCCC data portal | Monthly | Obligation volumes × auction clearing prices |
| CCL & Carbon Price Support | Indirect | HMRC bulletin | Annual | Electricity share of receipts |
| Emissions trading (UK/EU ETS) | Indirect | DESNZ trust statement | Annual | Power-sector share of auction revenue |
| Transmission (TNUoS) | Indirect | NESO charging statements | Annual | Uplift above pre-renewables baseline, floored at zero |
| Balancing (BSUoS) | Indirect | NESO data portal (history: NAO) | Daily | Uplift above baseline, constraints netted to avoid double-counting |

Attribution rules and their confidence levels are quoted in full on the [methodology page](https://subsidyclock.co.uk/methodology#indirect).

Attribution rules and their confidence levels are quoted in full on the [methodology page](https://subsidyclock.co.uk/methodology#indirect).

## Automation

A GitHub Action (`.github/workflows/update.yml`) runs daily at 05:30 UTC, after LCCC and Elexon publish: it updates all schemes (a failing scheme does not block the others), extends the constraints backfill by one week, writes the results file and commits. The website's own Action waits for that day's file, then builds from it.

## Licence

- **Code**: [MIT](LICENSE).
- **Results** (the results file): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), credit "The Subsidy Clock — subsidyclock.co.uk".
- **Upstream official data** (LCCC, Elexon, NESO, Ofgem, HMRC, DESNZ, NAO): subject to the source bodies' own terms, generally the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
