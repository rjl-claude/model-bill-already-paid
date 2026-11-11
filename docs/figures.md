# The paper's figures file

Version 1.1.0, parts 1 to 4 (aios-harness#222, #223, #224 and #225, Report No. 2's plan steps 6 to 9, map #206). Report No. 2, *The Price of the Climate Bill*, prints every bill-already-paid figure by key from this file, as it does the bill still to come's from that model's `results/figures.json` (spec: `report-series/price-of-the-climate-bill/spec.md`, "The bill already paid moves to version 1.1.0"; ADR 0222).

## What it is

- One flat JSON file, `{"figures": {key: value}, "meta": {...}}`, keyed like model-bill-still-to-come's.
- Built by `uv run --frozen python -m billpaid figures` (default output `results/figures.json`, with its fingerprint beside it in `figures.json.sha256`). Code: `src/billpaid/figures.py`, for the bridge `src/billpaid/bridge.py`, for 2025 `src/billpaid/provisional.py`, and for the ranges `src/billpaid/ranges.py`. Tests: `tests/test_figures.py`, `tests/test_bridge.py`, `tests/test_provisional.py`, `tests/test_ranges.py`.
- Built from the frozen results file the paper pins, not from a new run: `results/clock.json` as committed at `2a63b034` (the robot's file of 9 Nov 2026, model 1.0.0, sha256 `738ac005…`, pinned in `report-series/model-register.yaml`). The command refuses that file if its fingerprint differs.
- Each key for 2002-2024 is a 1.0.0 value, or a sum, ratio or product of them by 1.0.0's own rules (CPIH pricing, the Capacity Market range); no new method. Two parts add a new method: 2025 (below, "2025, the provisional year") and the ranges of the estimated lines (below, "The ranges"). The tests check every key against the 1.0.0 table it comes from, so no 1.0.0 value moves, and check that the model still writes `results/clock.json` exactly as before.
- `meta` names the model and version, the file it was built from (path, commit, sha256, version, date), the headline years, and every key template with its meaning.

## The years

- Each year and the headline run 2002 to 2024, the closed years. The headline is the sum of those years.
- 2025, the provisional year (part 3, #224): every line's 2025 figure, Sizewell C's levy on its own line, and the 2025 total with its measured, modelled and estimated parts. It is never in the headline (ADR 0035, 0226). Method below.
- 2026 (the year to date) is not in the paper and has no key.
- A line has a key for a year 2002-2024 only where 1.0.0 has a row for it (CfD from 2016, constraints from 2010, and so on). Every line has a 2025 key.

## The keys

A `<name>` stands for any of its values:

- `<line>`: `cfd_renewable`, `constraints`, `ro`, `fit`, `sizewell_c` (direct; Sizewell C has 2025 keys only); `ccl`, `capacity_market`, `carbon`, `tnuos`, `bsuos`, `constraint_turnup`, `vat` (indirect)
- `<total>`: `direct`, `indirect`, `all`
- `<year>`: a calendar year (RO and FiT: the obligation year starting April of that year, as 1.0.0 keys them)
- `<m>`: `real` (£ in 2024 prices, CPIH) or `cash` (£ as paid)
- `<part>`: `tax_collected`, `rest_in_price`
- `<grid>`: `tnuos` (grid), `bsuos` (balancing); `<side>`: `raw`, `alternative`
- `<end>`: `central`, `low`, `high`; `<bound>`: `low`, `high`
- `<technology>`: the CfD technologies, slugged (`offshore_wind`, `biomass_conversion`, `dedicated_biomass`, `onshore_wind`, `advanced_conversion_technology`, `energy_from_waste`, `solar_pv`), and `all`; `<tm>`: `cash`, `mwh`, `share`
- `<rec>`: `divergence_pct`, `bottom_up.cash`, `official.cash`, `tolerance_pct`, `matched_days`
- `<cc>`: `estimate`, `accepted_offers`, `accepted_offers_wind`; `<when>`: `from`, `to`
- `<d>`: `cpih`, `to_2024`
- `<basis>`: `measured`, `modelled`, `estimated`
- `<ranged>`: `carbon`, `constraint_turnup` (the lines labelled estimated, part 4)
- `<step>`: the bridge's steps, in the walk's order (below): `no2_money_paid`, `cfd_renewable`, `capacity_market`, `carbon`, `tnuos`, `balancing`, `ro`, `fit`, `ccl`, `vat`, `energy_saving_schemes`, `power_before_carbon`, `no1_extra_cost`

Every key in the file matches exactly one of these templates (tested):

- `<line>.<year>.<m>`: each line, each year, as 1.0.0 holds it; and 2025, the provisional year, for every line (below).
- `<line>.2025.source`: where the line's 2025 figure comes from, and why it is provisional.
- `all.2025.<basis>.<m>`: the 2025 total's measured, modelled and estimated parts, each line counted by its basis. The three add up to `all.2025.<m>`.
- `<line>.headline.<m>`: each line, 2002-2024.
- `<total>.<year>.<m>`: the direct lines, the indirect lines, or all together, each year (2002-2024 equal to 1.0.0's own totals; 2025 the provisional lines, Sizewell C among the direct ones).
- `<total>.headline.<m>`: the same, 2002-2024.
- `<line>.basis`: measured, modelled or estimated (below).
- `<line>.confidence`: 1.0.0's confidence (high, medium or low); high for the four direct lines, which 1.0.0 leaves blank.
- `<line>.layer`: direct or indirect.
- `carbon.<year>.basis`: the carbon line's basis that year, as 1.0.0 gives it (2005-2012 estimated, the rest modelled; 2025 modelled).
- `carbon.<part>.<year>.<m>`: carbon split into the tax collected by the Treasury and the rest of the carbon in the price. The two add up to the carbon line.
- `carbon.<part>.headline.<m>`: the same, 2002-2024.
- `<grid>.<side>.<year>.<m>`: grid (TNUoS) and balancing (BSUoS): the whole charge as paid (`raw`) and what the gas-led alternative would have paid (`alternative`). TNUoS counts raw minus alternative; for BSUoS, raw minus alternative is the BSUoS line plus constraint turn-up plus wind constraint payments (both tested every year).
- `<grid>.<side>.headline.<m>`: the same, 2002-2024.
- `<grid>.alternative.<year>.basis`: the alternative's basis that year (modelled: the gas model, engine v4-s43).
- `capacity_market.raw.<year>.<m>`: the Capacity Market levy paid in full.
- `capacity_market.raw.headline.<m>`: the same, 2002-2024.
- `capacity_market.netzero_share.<year>.<end>`: the share of the levy net zero caused, central, low and high (0 to 1). The line is the levy times the central share.
- `capacity_market.range.<bound>.<year>.<m>`: the line at the low or high share: the levy times that share, 1.0.0's own rule for its range (tested against 1.0.0's range to Aug 2026).
- `capacity_market.range.<bound>.headline.<m>`: the same, 2002-2024.
- `vat.rate`: the VAT rate on households' bills (0.05).
- `vat.domestic_share.<year>`: households' share of the lines VAT is charged on (0 to 1).
- `cfd_renewable.by_technology.<technology>.<tm>`: CfD by technology from the first payment to the data's end, as 1.0.0 holds it (not by year): £ cash, MWh, share of the total. `all` is every technology; it equals the CfD line's total to that day.
- `cfd_renewable.by_technology.to`: that end date (27 Oct 2026 in the 9 Nov file).
- `cfd_renewable.reconciliation.<rec>`: the contract-by-contract CfD payments against LCCC's own daily totals over the matched days: divergence and tolerance in per cent, the two totals in £ cash, the number of days.
- `constraint_turnup.cross_check.<cc>.cash`: the turn-up estimate beside the offers actually accepted (all offers, and offers while wind was constrained) over the measured window, £ cash.
- `constraint_turnup.cross_check.<when>`: the measured window's first and last day (6 Nov 2015 to 29 Oct 2026 in the 9 Nov file).
- `bill.<year>.<m>`: the whole UK electricity bill (DUKES 1.3).
- `bill.headline.<m>`: the same, 2002-2024.
- `share_of_bill.<year>`: all lines over the whole bill, both in 2024 prices (0 to 1).
- `share_of_bill.headline`: the same, 2002-2024.
- `households`: UK households (ONS, 29 million, as of 2025).
- `per_household.headline`: all lines 2002-2024, 2024 prices, over today's households.
- `per_household.<year>`: all lines that year (2024 only), 2024 prices, over today's households.
- `deflator.<year>.<d>`: CPIH (2015 = 100) and the factor to 2024 prices.
- `bridge.<step>.<year>.<m>`: the bridge with Report No. 1 (below): each step of the walk, each year 2002-2024, £ cash and £ in 2024 prices. A step has a key every year, zero where neither report has the line yet.
- `bridge.<step>.headline.<m>`: the same, 2002-2024.
- `bridge.<step>.label`: the step's row label for the bridge table, in the series glossary's words.
- `bridge.<step>.kind`: `total` (the two ends), `same`, `counted_differently` or `no1_only`.
- `bridge.steps`: the steps' names in the walk's order, comma-separated.
- `bridge.no1.version`: the Report No. 1 release the bridge reads (`v4-s43`).
- `bridge.no1.sha256`: that release's run file's fingerprint (the one pinned in `report-series/model-register.yaml`).
- `<ranged>.range.<bound>.<year>.<m>`: an estimated line at its low or high, each year it has a range (below, "The ranges"): turn-up 2015-2025, carbon 2005-2012.
- `<ranged>.range.<bound>.headline.<m>`: 2002-2024, each year with a range at its low or high, the other years central.
- `<ranged>.range.years`: the years the line has a range for, comma-separated.
- `<ranged>.range.method`: how the range is made, in one line.
- `carbon.allowance_price.<end>.<year>`: the allowance price carbon is priced at that year, central (the EEA's) and the low and high of the range, EUR/t.

## Each line's basis

1.0.0 labels some years and parts but gives no basis for a whole line. Part 1 reads it from 1.0.0's own account of each line:

- measured (payments or receipts as recorded): CfD (LCCC settlement), constraints (Elexon; REF's history before 6 Nov 2015), RO and FiT (Ofgem), the Climate Change Levy (HMRC receipts, electricity's published share);
- modelled (a share or alternative from the pinned gas model): Capacity Market, carbon, TNUoS, BSUoS, VAT (households' share from the gas model);
- estimated: constraint turn-up (1.0.0: "Estimated cost of paying other stations…").
- Sizewell C (part 3, 2025 only): measured (suppliers' levy payments to LCCC as recorded).

Part 4 (#225) gives a range to each estimated line that has none in 1.0.0 (below, "The ranges").

## The bridge with Report No. 1

Part 2 (aios-harness#223; ADR 0222, 0036, 0037). The two reports answer different questions: No. 2 counts money paid (gross, scheme by scheme); No. 1 counts extra cost (net: Britain's whole electricity bill less the gas-led alternative's). The bridge walks from one figure to the other so the paper can print the table by key and never adds or subtracts the two reports itself. The figures must never be added, and neither confirms the other (0037).

- **The two ends.** `bridge.no2_money_paid` is `all` (the eleven lines). `bridge.no1_extra_cost` is No. 1's yearly figure, read from its pinned release: the gas model's v4-s43 run file, `reference/engine/v4-s43-run.json` (`gap.<year>.national_gbp_m_nominal`), pinned in `reference/model_pin.yaml` and refused if its fingerprint differs. Its 2002-2024 total in 2024 prices is No. 1's published headline, £140.3bn (tested against No. 1's own figures file).
- **Each step is a No. 1 line less the No. 2 lines it answers to**, both frozen; nothing is modelled here. No. 1's lines are its run file's own (`bills.<year>`): NZ lines are the actual bill, GO lines the gas-led alternative's.
- **Prices.** `cash` is £ as paid. `real` is 2024 prices: No. 2's lines as 1.0.0 prices them, No. 1's cash priced by this model's CPIH, which is the index No. 1 uses (so its headline is reproduced exactly).
- **It adds up.** `no2_money_paid` plus the eleven steps equals `no1_extra_cost`, to a tenth of a penny, every year and in the headline, in cash and in 2024 prices: tested, and the build refuses to write a walk that does not. It also refuses a walk that leaves a No. 2 line out or counts one twice. The sums run in the walk's fixed order over the frozen file, so a rerun gives the same digits (aios-harness#252, the last-digit difference between two `results` runs, does not reach it: the bridge never reruns the model).

The steps, in order:

| Step | No. 1's lines | No. 2's lines | Why it differs |
|---|---|---|---|
| `cfd_renewable` | NZ4 + NZ4b | `cfd_renewable` | It does not: zero every year. |
| `capacity_market` | NZ5 | `capacity_market` | It does not (under a penny a year): No. 2 takes the net-zero share from No. 1's model. |
| `carbon` | NZ1c | `carbon` | It does not: zero. |
| `tnuos` | NZ7 − GO5 | `tnuos` | It does not: zero. |
| `balancing` | NZ6 − GO4 | `constraints`, `constraint_turnup`, `bsuos` | It does not: No. 2's three lines are No. 1's balancing cost above the gas-led alternative's, split three ways. |
| `ro` | NZ2 | `ro` | No. 1 counts Great Britain only (No. 2 the UK), by calendar year (No. 2 by obligation year), and takes off the Fossil Fuel Levy at its 2001 level, which the gas-led alternative would also have paid. |
| `fit` | NZ3 | `fit` | No. 1 counts by calendar year, No. 2 by scheme year (the same levelisation cost). |
| `ccl` | NZ8 | `ccl` | No. 2 counts electricity's whole levy (UK). No. 1 counts only what is above the levy at its 2001 rate, which the gas-led alternative would also have paid, Great Britain only. |
| `vat` | NZ11 − GO7 | `vat` | No. 1 charges 5% on households' share of the extra cost (so on the saving in power too), No. 2 on households' share of the money paid. |
| `energy_saving_schemes` | NZ10 | none | Suppliers' energy-saving schemes on electricity bills (EEC to GBIS): No. 1 counts them, No. 2 does not. |
| `power_before_carbon` | NZ1 − NZ1c − GO1 − GO1k | none | The cost of power itself, before carbon: actual less the gas-led alternative's. The largest step and a saving in every year but 2008: what the policies took off the price of power, which a gross figure does not net off. |

The headline walk, 2002-2024, from the 9 Nov frozen file and v4-s43 (£bn; run `python -m billpaid figures` for the keys):

| Step | Cash | 2024 prices |
|---|---|---|
| `no2_money_paid` | 204.9 | 252.4 |
| the five lines counted alike | 0.0 | 0.0 |
| `ro` | −5.9 | −7.2 |
| `fit` | −0.4 | −0.4 |
| `ccl` | −14.5 | −20.0 |
| `vat` | −1.2 | −1.4 |
| `energy_saving_schemes` | 7.1 | 9.2 |
| `power_before_carbon` | −79.4 | −92.2 |
| `no1_extra_cost` | 110.5 | 140.3 |

Not in the bridge: 2025. No. 1's release has a provisional 2025 and No. 2 now has its 2025 lines (part 3), but the walk still stops at 2024 with the headline: widening it is not part 3's work (`bridge.YEARS` is the one place to widen it). Its RO step would carry the difference between No. 1's 2025-26 estimate (obligation x buy-out price, £8,007.8m) and Ofgem's outturn used here (£7,946.2m).

## 2025, the provisional year

Part 3 (aios-harness#224; ADR 0226). The paper gives a provisional 2025 total with its parts beside it, kept out of the 2002-2024 headline. Code: `src/billpaid/provisional.py`; tests: `tests/test_provisional.py`.

**The rule (new method).** Each line's 2025 figure is, in this order:

1. 1.0.0's own 2025 figure, where 1.0.0 holds the whole of 2025 (its data run into 2026): CfD, constraints, Capacity Market, BSUoS, constraint turn-up.
2. Otherwise the published 2025 figure, read the way 1.0.0 reads that line's closed years (each reading is tested to give 1.0.0's figure in every year 2002-2024), from the shared cost register and Report No. 1's release that 1.0.0 already pins, or from a primary source saved for this part.
3. Otherwise the latest yearly figure carried forward, labelled estimated. As at the cut-off (9 Nov 2026) no line needs this: each of the five lines 1.0.0 stops before 2025 has a published 2025 figure.

VAT is recomputed by 1.0.0's rule (5% of households' share, the engine's 2025 share, of every counted line but the Climate Change Levy), now over every line, Sizewell C included: 1.0.0's own 2025 VAT covers only the lines it had a 2025 figure for. Prices: 2024 prices by 1.0.0's rule (CPIH from the frozen file; RO and FiT, April-March years, three quarters at 2025's index and one at 2026's).

**The five lines, and Sizewell C** (cash, as paid; 2024 prices in the file):

| Line | 2025 figure | Source | Basis |
|---|---|---|---|
| `ro` | £7,946.2m | Ofgem, "ROCs presented and Redistribution of Buy-Out Funds 2025 to 2026" (2 Nov 2026), UK total: 109,924,800 ROCs presented x £67.06 buy-out price + £574,621,217 redistributed, Ofgem's scheme value (ROCs presented x worth of a ROC). Provisional: the late-payment fund is not yet paid out (2024-25: £7.4m). The same reading of the 2024-25 page gives £7,695.9m against Ofgem's £7,706.3m (0.14% low). No mutualisation: the shortfalls were below the thresholds. | measured |
| `fit` | £1,877.6m | Ofgem FiT quarterly reports 61-64, the four levelisations of 2025-26, as the shared cost register (v4-s43) holds them. Provisional: before Ofgem's annual reconciliation (the register labels it estimated for that reason). | measured |
| `ccl` | £796.2m | HMRC Environmental Taxes Bulletin, 31 Mar 2026 (the latest edition), Table 1b, electricity, calendar 2025, as the register holds it. Provisional in HMRC's table. | measured |
| `carbon` | £6,860.6m | Report No. 1's release v4-s43 (its run file), carbon in the wholesale price 2025, of which £1,328.0m tax collected on power (`carbon.tax_collected.2025`). Provisional there: CPS about £428m (No. 1 decision 0054) and UK ETS auctions from ICE report 278 (0079), to be replaced by HMRC's and DESNZ's figures. | modelled |
| `tnuos` | £1,872.0m | The register's TNUoS 2025 (NESO final TNUoS reports 2024-25 and 2025-26, calendarised) less the generators' share, £3,750.9m (`tnuos.raw.2025`), above the gas-led alternative's £1,878.8m (`tnuos.alternative.2025`, No. 1's GO5 2025, generators' share removed). | modelled |
| `sizewell_c` | £85.4m | LCCC data portal, Actual Nuclear RAB ILR/TRA, December 2025: what suppliers paid of the levy, which began on 1 Dec 2025 (interim levy rate £3.494/MWh on 24.4 TWh of eligible demand). Provisional: settlement runs continue. Direct layer: a levy paid to one generator, like the RO. | measured |

**The total.** `all.2025.measured` counts the measured lines (CfD, constraints, RO, FiT, CCL, Sizewell C), `all.2025.modelled` the modelled ones (Capacity Market, carbon, TNUoS, BSUoS, VAT), `all.2025.estimated` constraint turn-up, the one line 1.0.0 itself calls an estimate. From the 11 Nov 2026 build (2024 prices): all £23.96bn = measured £13.16bn + modelled £9.76bn + estimated £1.04bn (2024: £21.70bn). Every 2025 figure is provisional; the paper says so wherever 2025 appears (spec, story 18).

**Saved sources.** The Ofgem pages (2025-26, and 2024-25 for the test of the reading) and the LCCC file are in `reference/sources/`, each pinned by sha256 in `reference/provisional_2025.yaml`, and refused if the bytes differ. The figures are read from the saved files, never typed. A newer edition (a later settlement run, Ofgem's late-payment fund, HMRC's next bulletin, DESNZ's ETS figure) is never picked up by itself.

## The ranges

Part 4 (aios-harness#225; spec: "a range for each line labelled estimated"; the review standard: an estimate passes only with its method and range given). Code: `src/billpaid/ranges.py`; tests: `tests/test_ranges.py`.

**What is labelled estimated.** By the model's own labels (`<line>.basis`, `carbon.<year>.basis`), every year 2002 to 2025:

| Line | Years labelled estimated | Range in 1.0.0 | Range in 1.1.0 |
|---|---|---|---|
| `constraint_turnup` | every year (the whole line) | none | 2015-2025, every year with a figure. 2002-2014 are zero: Elexon's settlement stacks start in November 2015, so 1.0.0 has no turn-up figure before then and any turn-up in those years sits inside the BSUoS line. There is nothing to range. |
| `carbon` | 2005-2012 (the engine's allowance price for those years is the EEA's yearly figure, whose origin the EEA does not state) | none | 2005-2012, every estimated year. |

No other line or year is labelled estimated. The one range 1.0.0 holds, the Capacity Market's, is on a modelled line (`capacity_market.range.*`). Some of the shared cost register's own rows are labelled estimated (for example BSUoS 2006-07, CPS 2013, FiT 2025), but those are the register's labels for inputs to measured or modelled lines, not this model's labels.

**Constraint turn-up (new method).** What is estimated is not the volume. The switched-off wind is a record: the system-flagged wind bids each half-hour. The estimate is which of the half-hour's accepted offers replaced that wind. 1.0.0 follows Octopus's walk: unflagged offers first, then in acceptance order, pro rata at the margin. The range holds the volume and the set of offers fixed and changes only the order:

- low: the same volume priced on the half-hour's accepted offers cheapest first. No choice of those offers costs less;
- high: the dearest first. No choice of those offers costs more.

The CADL offers stay out, as in 1.0.0. The re-walk is a new fetch of Elexon Insights' settlement stacks, the same public API and calls as 1.0.0's feed, every half-hour from 1 Nov 2015 to 31 Dec 2025. Offers are fetched only for half-hours with wind switched off, since every walk is zero in the others. It is made by `tools/turnup_range.py`, saved one row a day as `reference/sources/turnup-range-daily.csv` and pinned by sha256 in `reference/ranges.yaml`. Its central walk reproduces 1.0.0's measured turn-up every year (tested, within 0.5%). Each year's low and high are scaled by 1.0.0's measured figure over the re-walk's central figure, so the range sits on the frozen figure, not on a later fetch. They are then capped, as 1.0.0 caps the line, at the BSUoS uplift: turn-up is never more than it. In 2015 and 2018 the cap lies below even the cheapest walk, so low, central and high are all the line itself. In 2022 it caps the high only.

| Year | Re-walk, £m cash: cheapest / 1.0.0's walk / dearest | 1.0.0 measured, £m cash | £m, 2024 prices: low / central / high |
|---|---|---|---|
| 2015 | 24.8 / 25.0 / 34.1 | 25.0 | 30.5 / 30.5 / 30.5 (capped) |
| 2016 | 59.2 / 60.0 / 80.0 | 60.0 | 77.9 / 78.9 / 105.3 |
| 2017 | 88.3 / 89.3 / 109.3 | 89.3 | 113.3 / 114.6 / 140.3 |
| 2018 | 123.3 / 124.8 / 142.4 | 124.8 | 66.9 / 66.9 / 66.9 (capped) |
| 2019 | 103.6 / 107.0 / 128.8 | 107.0 | 127.7 / 132.0 / 158.7 |
| 2020 | 177.0 / 181.1 / 218.8 | 181.1 | 216.0 / 221.0 / 267.1 |
| 2021 | 383.0 / 387.0 / 448.6 | 387.0 | 456.1 / 460.9 / 534.3 |
| 2022 | 726.4 / 739.9 / 855.1 | 739.9 | 801.1 / 816.1 / 831.3 (high capped) |
| 2023 | 501.0 / 505.1 / 563.2 | 505.1 | 517.8 / 522.0 / 582.0 |
| 2024 | 827.6 / 835.2 / 919.2 | 835.2 | 827.6 / 835.2 / 919.2 |
| 2025 (provisional) | 1,079.0 / 1,083.6 / 1,195.4 | 1,083.6 | 1,039.1 / 1,043.6 / 1,151.3 |

The range is lopsided. 1.0.0's order, unflagged offers first, is already close to the cheapest: before the cap, the cheapest walk is 0.4-3.2% below 1.0.0's walk each year, and the dearest 10-36% above. Over 2002-2024, in 2024 prices, the line is £3.28bn, range £3.24bn to £3.64bn (`constraint_turnup.range.<bound>.headline.real`).

**Carbon, 2005-2012 (new method).** In these years the engine prices carbon at the EEA's yearly EUA price (EUR/t) at each month's Bank of England exchange rate. There is no Carbon Price Support before April 2013, so the line is that price times the engine's carbon intensity at the margin times the volume. The range moves only the price, the input that makes these years estimated. For each year the low and high are the lowest and highest of two things: the EEA's price, and every price in that year's primary record of what allowances actually changed hands at. The line at that price is the line times that price over the EEA's.

The record differs by phase:

- **2005-2007 (Phase I): traded prices.** These are the daily closing prices of the Phase I spot allowance on BlueNext, called Powernext Carbon until December 2007 and the leading Phase I spot exchange. The source is the exchange's own file, `2005-2007_BNS_STATS.csv`, captured from data.bluenext.fr by the Internet Archive on 8 Nov 2011. It agrees with Powernext's own annual reports (2005 average EUR 22.51, high 28.93 on 11 Jul; 2006 average 17.37; 2007 high 5.48 on 2 Jan) and with the NAO's Phase I peak (EUR 29.75, April 2006), all tested. Two differences from 2008-2012: these are traded closes, not auction clearing prices; and the record starts when the exchange opened on 24 Jun 2005, so 2005's range covers its second half only. The first half of 2005 has no exchange record here.
- **2008-2012 (Phase II): UK auction prices.** These are the clearing prices of the UK Government's auctions of EU allowances. The DMO ran them for DECC, 30 in all from 19 Nov 2008 to 25 Oct 2012, and each price is checked against the DMO's own result notice. In 2009-2012 the EEA's price lies inside the auctions' own spread. 2008 had one UK auction, on 19 Nov after the price had fallen, so its high is the EEA's price itself.

Through 2008 the engine prices carbon with gas at the margin, so the line moves exactly in proportion to the price. From January 2009 it uses its merit order (coal or gas at the margin, decision 0167), and the range holds that merit order as it is. A lower carbon price would put more coal at the margin, and a higher price less, so the true line moves a little less than in proportion. For 2009-2012 the range is therefore, if anything, wider than a full rerun would give.

2007 is very wide, and is left so. The Phase I price collapsed from EUR 5.48 on 2 Jan to EUR 0.02 by 28 Dec, because Phase I allowances could not be carried into Phase II. The high is over eight times central and the low a thirtieth of it. That is the year's own record, not smoothed.

| Year | EUR/t: low / EEA / high | £m, 2024 prices: low / central / high |
|---|---|---|
| 2005 (from 24 Jun) | 18.85 / 21.82 / 28.93 | 2,888.2 / 3,344.0 / 4,432.7 |
| 2006 | 6.40 / 17.27 / 29.75 | 972.0 / 2,622.7 / 4,518.2 |
| 2007 | 0.02 / 0.65 / 5.48 | 2.8 / 93.0 / 779.4 |
| 2008 | 16.15 / 20.02 / 20.02 | 2,563.0 / 3,176.9 / 3,176.9 |
| 2009 | 10.98 / 13.16 / 15.05 | 3,102.1 / 3,717.2 / 4,252.0 |
| 2010 | 12.15 / 14.34 / 15.60 | 2,939.5 / 3,469.0 / 3,774.2 |
| 2011 | 9.72 / 12.94 / 16.34 | 1,916.4 / 2,551.9 / 3,221.6 |
| 2012 | 6.67 / 7.37 / 8.55 | 1,263.3 / 1,395.9 / 1,619.4 |

Over 2002-2024, in 2024 prices, the carbon line is £82.86bn, range £78.14bn to £88.26bn. Only 2005-2012 move.

**The headline at the range.** `<ranged>.range.<bound>.headline.<m>` is the line's 2002-2024 total with each year that has a range at its low or high, and the other years at central. It is never added to the main headline.

**Saved sources.** `reference/ranges.yaml` pins each file by sha256, and the build refuses any file whose bytes differ: the re-walk of Elexon's stacks; the EEA data package, byte for byte the file Report No. 1's release v4-s43 read (its run file's input checksum, tested); the DMO auction table, byte for byte the table that release reads (its `ets_auctions` checksum, tested); and BlueNext's Phase I spot file, as the Internet Archive captured it. A newer edition of any of these is never picked up by itself.

## Against the spec's proposed names

The spec proposed names and left them to this ticket; the freeze (#226) checks the spec against the frozen file. Where they differ:

- every money key ends in `.real` or `.cash`, as the bill still to come's end in a measure (spec: `carbon.tax_collected.<year>`, `tnuos.raw.<year>` and so on, with no measure);
- `capacity_market.netzero_share.<year>` is `.central`, `.low`, `.high`; `capacity_market.range.low|high` is by year and headline;
- `cfd_renewable.by_technology.<technology>` is `.cash`, `.mwh`, `.share`, to the data's end;
- `constraint_turnup.cross_check` is three figures and its window;
- `deflator.<year>` is `.cpih` and `.to_2024`;
- `bridge.<step>.<year>` and `bridge.<step>.headline` end in `.real` or `.cash` like every money key, and each step also has `.label` and `.kind`.
- the 2025 total's parts `all.2025.measured` and `all.2025.estimated` are `all.2025.measured.real|cash` and `all.2025.estimated.real|cash`, with a third part, `all.2025.modelled.real|cash`, so that the parts add up to the total (the modelled lines are neither measured nor estimated);
- each line's 2025 basis is its line's `<line>.basis` (no line is carried forward); `<line>.2025.source` says where each 2025 figure comes from.

## The freeze

- Frozen 11 Nov 2026 (#226) as version 1.1.0, tag `v1.1.0`, with `results/figures.json` and its `figures.json.sha256` committed at the tag: the file the paper pins in `report-series/model-register.yaml`. A fresh build from the tag is byte for byte that file (`tests/test_version_1_1_0.py`). What changed: `CHANGELOG.md`.
- On Gitea only (report-series ADR 0228). GitHub `master`, and so the live Clock, stay on 1.0.0 until the paper's release: the Clock refuses a results file of any other version, so 1.1.0 goes to GitHub only on Richard's "deploy", in the same step as the Clock's pin moves.
