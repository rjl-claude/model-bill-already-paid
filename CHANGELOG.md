# Changelog

Each version is a git tag. The Subsidy Clock reads `results/clock.json`; Report No. 2 reads `results/figures.json` as committed at its tag, pinned by sha256 in `report-series/model-register.yaml`. A version never changes an older one. The site's own changelog (`web-subsidy-clock`, `changelog.jsonl`) gets its entry when the Clock moves to a version.

## 1.1.0 (11 Nov 2026), the paper's figures file

For Report No. 2, *The Price of the Climate Bill* (its plan steps 6 to 10, aios-harness#222 to #226; report-series ADR 0222, 0226). Frozen on Gitea only, branch and tag `v1.1.0` (ADR 0228): **GitHub `master` and the live Clock stay on 1.0.0** until the paper's release, when Richard's "deploy" pushes 1.1.0 to GitHub and moves the Clock's pin to it in the same step. The Clock's site refuses a results file of any version but its pin, so this version must not reach GitHub before then.

**No 1.0.0 figure moves.** `results/clock.json` is written exactly as before, apart from the version in its stamp (`tests/test_results.py`). The figures file is built from the frozen 1.0.0 results file of 9 Nov 2026 (`results/clock.json` at `2a63b034`, sha256 `738ac005…`), not from a new run, and every key for 2002-2024 equals the 1.0.0 value it comes from (`tests/test_figures.py`).

Added: `results/figures.json`, one flat file read by key (2,066 keys; every key and its meaning in `docs/figures.md`; built by `python -m billpaid figures`; byte for byte reproducible, `tests/test_version_1_1_0.py`):

- **Every line, every year and the 2002-2024 headline** in 2024 prices and cash; direct, indirect and all; the parts the chapters argue (carbon's tax and the rest in the price, the Capacity Market's net-zero share and range, grid and balancing raw and against the gas-led alternative, VAT's household share, CfD by technology, the turn-up cross-check, the CfD reconciliation); each line's basis and confidence; the context keys (whole bill, share of bill, households, per household, deflator). #222.
- **The bridge with Report No. 1**: the walk from No. 2's money paid (£252.4bn, 2002-2024, 2024 prices) to No. 1's extra cost (£140.3bn), 13 steps, read from No. 1's pinned release v4-s43 and tested to add up every year. #223.
- **2025, the provisional year** (new method): every line's 2025 figure, published figures read from saved sources, and Sizewell C's levy from 1 Dec 2025 on its own line; the 2025 total, £23.96bn in 2024 prices, with its measured, modelled and estimated parts. Kept out of the headline. #224.
- **A range for each estimated line** (new method): constraint turn-up 2015-2025 (a re-walk of Elexon's settlement stacks, cheapest and dearest first) and carbon 2005-2012 (Phase I spot closes and the UK's Phase II auction prices). #225.

## 1.0.0

The Subsidy Clock's sums, split out of `web-subsidy-clock` on 6 Nov 2026 (aios-harness#140). Its history is the site's `changelog.jsonl`.
