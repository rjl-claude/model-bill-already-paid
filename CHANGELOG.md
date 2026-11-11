# Changelog

Each version is a git tag. The Subsidy Clock reads `results/clock.json`; Report No. 2 reads `results/figures.json` as committed at its tag, pinned by sha256 in `report-series/model-register.yaml`. A version never changes an older one. The site's own changelog (`web-subsidy-clock`, `changelog.jsonl`) gets its entry when the Clock moves to a version.

## 1.2.0 (11 Nov 2026), the outline's figures; Elexon in place of REF

For Report No. 2's approved outline (plan step 19, aios-harness#235; report-series ADR 0240). Frozen on Gitea only, branch and tag `v1.2.0`, as 1.1.0 (ADR 0228): **GitHub `master` and the live Clock stay on 1.0.0** until the paper's release. `results/figures.json`: 2,265 keys, sha256 `7d9a4d35...` (in `results/figures.json.sha256`). Every key and its meaning: `docs/figures.md`, "Version 1.2.0". Every value that moves and every key added, key by key: `docs/1.2.0-against-1.1.0.md`.

**Moved (minor version, not a patch): wind constraint payments 2016-2023 from Elexon's own record in place of REF's database** (Richard's standing ruling: primary sources, no REF where a primary record exists). Elexon's settlement stacks, which 1.0.0's store already holds, start on 6 Nov 2015, so 2016-2023 move; 2010-2015 stay on REF (`constraints.ref_years`). Elexon is higher every year, by 0.55% (2016) to 3.59% (2022): +£34.8m cash, +£39.9m in 2024 prices over 2016-2023. 1.0.0's split rule takes it out of the other two balancing lines (BSUoS; in 2018, when turn-up is capped at the uplift, turn-up). **The headline does not move**: £252.4bn in 2024 prices (£204.9bn cash) before and after; direct £125.8bn to £125.9bn, indirect £126.6bn to £126.5bn. Turn-up's range moves where its cap binds (2018; 2022's high): its 2002-2024 high £3.64bn to £3.63bn. 89 values move, all of them these years and their sums; 22 more differ only in the last binary digit of a float. `results/clock.json` is unchanged (the Clock moves only if the history's pin moves, a release decision).

Added (199 keys): the headline's measured, modelled and estimated parts (M1); the headline's range from the three estimated lines each changed on its own, £247.7bn to £257.8bn, early carbon prices setting both ends (M2, ADR 0234); UK households each year from ONS and money paid per household year by year, £9,216 (M3, ADR 0025, 0027, 0232); on a household's own bills, £3,281 (M4); the 2025 bill and its share, 38.2% (M5); the headline under seven counting options, among them suppliers' energy-saving schemes, £10.2bn beside the figure (M6, ADR 0233); checks against HMRC, Ofgem's RO and FiT, the OBR and REF (M7); CfD by technology 2002-2024 in 2024 prices (M8); the years still on REF (M9). New publishers' files in `reference/sources/`, pinned in `reference/outline_sources.yaml`. Not built: the check against Ofgem's price-cap policy costs (needs a ruling on the matched basis and the cap periods' workbooks) and Northern Ireland's part (not asked for, ADR 0240).

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
