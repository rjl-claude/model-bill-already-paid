<!-- Reviewed with Richard, 6 Nov 2026 (aios-harness#88) -->

# model-bill-already-paid

The Subsidy Clock's sums: what UK subsidies and their indirect costs have cost, scheme by scheme, from 2002 to the latest data. Its years 2002 to 2025 are the bill already paid, the first half of Report No. 2, *The Price of the Climate Bill* (the second half is `/srv/aios/projects/model-bill-still-to-come`). Split out of `/srv/aios/projects/web-subsidy-clock` on 6 Nov 2026 (aios-harness#140).

## What reads it

- The Clock's website (`/srv/aios/projects/web-subsidy-clock`): only `results/clock.json`, pinned by model version in its `reference/results_pin.yaml`. The site's robot refuses a file from any other version.
- `model-bill-still-to-come`: its Clock 2025 check (`src/billtocome/checks.py`) reads `results/clock.json`; its Capacity Market shares read `reference/engine/v4-s43.json` here.
- Report No. 2: one day's results file, pinned by version and fingerprint (the freeze, aios-harness#91).

## Rules (Richard, 6 Nov 2026: the same as model-bill-still-to-come's)

- Quotable figures come from a numbered version only (`pyproject.toml`, stamped in `results/clock.json`), and the answer names that version. "What if" runs are allowed but labelled **not the published figure**.
- Answer by running the model, never from memory or sums in chat. Name the version and what is covered (direct only or with indirect; 2024 prices or cash as paid).
- A change that moves a figure gets a new version number, with an entry in the site's `changelog.jsonl` saying what changed and by how much. The old version stays as it was. A change that moves a figure without a new version would reach the live Clock unseen.
- The site and the reports move their pins only on Richard's say-so.
- Pushing to GitHub `rjl-claude/model-bill-already-paid` publishes: the next morning's results reach the live Clock. Only on Richard's say-so, each time.
- This repository is public. Anything not for the public goes in `private/`, its own private repo on Gitea `rjl/model-bill-already-paid-private`, never on GitHub.

## Commands

- All tests: `tools/test.sh` (every test must pass). One file: `tools/test.sh tests/<file>.py`
- Run Python here: `uv run --frozen python`
- The results file: `uv run --frozen python -m billpaid results`

## How it runs

- GitHub `master` (remote `github`) is the live copy. Its robot (`.github/workflows/update.yml`, 05:30 UTC daily) fetches the data, writes `data/` and `results/`, and commits there. Gitea (`origin`) follows: fetch `github` before any commit, and keep the two the same.
- `data/` and `results/` are the robot's; a hand-made commit carries source only.
- The figures taken from the gas model (the Capacity Market's net-zero part, grid and balancing costs without net zero, carbon) are pinned in `reference/model_pin.yaml` (engine v4-s43). A new engine release is never applied by itself.

## Misleading places

- `reference/engine/v4-s43*.json` are the gas model's files, not this model's version (this model is 1.0.0).
- `scratch/` holds working notes from October; `private/history/vault-2026-11-06/` holds the old vault method notes word for word. As found, not all rulings confirmed.

## Outside this folder

- Open work: GitHub `richardjlyon/aios-harness` issues labelled `subsidy-clock`.
- Rulings for the Clock release: `/srv/aios/projects/report-series/clock-alignment/decisions.md`
