<!-- Draft, not yet reviewed with Richard (aios-harness#140; #88 rule) -->

# model-bill-already-paid

The Subsidy Clock's sums: what UK subsidies and their indirect costs have cost, scheme by scheme, from 2002 to the latest data. Its years 2002 to 2025 are the first half of Report No. 2, *The Price of the Climate Bill* (the second half is `/srv/aios/projects/model-bill-still-to-come`). Split out of `/srv/aios/projects/web-subsidy-clock` on 6 Nov 2026 (aios-harness#140; Richard's ruling Q2 on #89).

## What reads it

- The Clock's website (`/srv/aios/projects/web-subsidy-clock`): only `results/clock.json`, pinned by model version and file format in its `reference/results_pin.yaml`.
- `model-bill-still-to-come`: the Clock 2025 check (`src/billtocome/checks.py`) reads `results/clock.json`; its Capacity Market shares read `reference/engine/v4-s43.json` here.
- Report No. 2: one day's results file, pinned by version and fingerprint (the freeze, aios-harness#91).

## Rules

- A change that moves a figure gets a new version in `pyproject.toml`. The site and the reports move their pins only on Richard's say-so.
- `data/` and `results/` are written by the daily robot; a hand-made commit carries source only.
- Public repository on GitHub (`richardjlyon/model-bill-already-paid`); Gitea `rjl/model-bill-already-paid` is the working copy.

## Commands

- Run Python here: `uv run --frozen python`
- All tests: `tools/test.sh` (every test must pass)
- The results file: `uv run --frozen python -m billpaid results`

## Outside this folder

- Tickets: GitHub `richardjlyon/aios-harness`, label `subsidy-clock` (see `docs/agents/issue-tracker.md`)
- Rulings for the Clock release: `/srv/aios/projects/report-series/clock-alignment/decisions.md`
