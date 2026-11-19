# The paper's figures file

Version 1.1.0, parts 1 to 4 (aios-harness#222, #223, #224 and #225, Report No. 2's plan steps 6 to 9, map #206), and version 1.2.0, the figures the approved outline asks for (aios-harness#235, plan step 19; below, "Version 1.2.0"). Report No. 2, *The Price of the Climate Bill*, prints every bill-already-paid figure by key from this file, as it does the bill still to come's from that model's `results/figures.json` (spec: `report-series/price-of-the-climate-bill/spec.md`, "The bill already paid moves to version 1.1.0"; ADR 0222).

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
- `households`: UK households, 29 million, a round figure as of 2025 (ONS): 1.1.0's single divisor, kept for the Clock's comparisons. **Not the paper's divisor**: the paper divides by `households.<year>` (Great Britain, year by year), below, "Version 1.3.0".
- `per_household.headline`: all lines 2002-2024, 2024 prices, over today's 29 million UK households. 1.1.0's figure, kept unchanged. **The outline no longer uses it**: print `per_household.year_by_year.headline.real` instead.
- `per_household.<year>` (no `.real` at the end; 2024 only): all lines that year, 2024 prices, over today's 29 million UK households. 1.1.0's figure, kept unchanged. **The outline no longer uses it**: print `per_household.<year>.real` instead, which divides each line by its own area's households that year. Read the last part of the key: `per_household.2024` is the old one, `per_household.2024.real` the paper's.
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

- measured (payments or receipts as recorded): CfD (LCCC settlement), constraints (Elexon's record 2016-2025 from 1.2.0; National Grid's record 2010-2015 from 1.5.0, of which 2010-2013 are counted estimated: "Version 1.5.0" below), RO and FiT (Ofgem), the Climate Change Levy (HMRC receipts, electricity's published share);
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

Where the generators' share that No. 1 counts sits: inside No. 1's power-price step (`power_before_carbon`). No. 1 removes the generators' share from its grid and balancing lines on both roads, and counts the part the policies added through each road's market price (No. 1 §10.3). That is why the grid and balancing steps are zero (added 1.2.0, as the outline's Table B.1 beat asks).

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

The figures in the two tables above are 1.1.0's. From 1.2.0 the turn-up cap moves with Elexon's constraint figure in 2018 and 2022 (the high only): `docs/1.2.0-against-1.1.0.md`.

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

## Version 1.2.0: the outline's figures

Report No. 2's plan step 19 (aios-harness#235). The approved outline (`report-series/price-of-the-climate-bill/outline-beats.md`, "Missing figures", ADR 0240) asks the bill already paid for figures 1.1.0 does not hold, M1 to M9. 1.2.0 adds them, and takes Elexon's own record for wind constraint payments wherever Elexon holds the whole year. Code: `src/billpaid/elexon_record.py`, `outline.py`, `checks.py`, `outline_sources.py`. Tests: `tests/test_elexon_constraints.py`, `test_outline_figures.py`, `test_checks.py`. The publishers' files are saved in `reference/sources/` and pinned by sha256 in `reference/outline_sources.yaml`; the build refuses any whose bytes differ. Every value that moves from 1.1.0, and every key added, is listed in `docs/1.2.0-against-1.1.0.md`.

### Wind constraint payments: Elexon's own record (M9)

- 1.1.0 took 2010-2023 from an earlier third-party series and Elexon's settlement stacks from 2024.
- Elexon's settlement stacks start on 6 Nov 2015. 1.0.0's store holds every day since. Each calendar year before the pin that the store holds whole now comes from Elexon: 2016-2023. The store is read as it stood when the frozen results file was written (each day's latest version retrieved at or before its `generated_at`).
- 2010-2015 have no Elexon record: its API returns no settlement stack, acceptance (BOALF) or bid-offer (BOD) data before November 2015, and 2015 has only its last 55 days. From 1.5.0 they are National Grid's record ("Version 1.5.0" below). The evidence is saved (1.3.0): Elexon's own answers of 11 Nov 2026, each pinned by sha256 in `reference/outline_sources.yaml` (`elexon-*`): empty for the settlement stack of 1 Feb 2012 and of the last period of 5 Nov 2015, for acceptances (BOALF) and bid-offer data (BOD) on 1 Jun 2014 and for indicative bid cashflows on 1 Jun 2015; accepted bids for the last period of 6 Nov 2015 (`tests/test_elexon_constraints.py`).
- The three balancing lines are one measured total split three ways. 1.0.0's own split rule is applied again with the new figure: the uplift is that total less constraint payments; turn-up is its measured figure, never more than the uplift nor below zero; BSUoS takes the rest. So `all`, the bridge and VAT do not move. Money moves between the direct layer (constraints, up £34.8m cash over 2016-2023) and the indirect (BSUoS, and in 2018, when turn-up is capped and BSUoS is nil, turn-up).
- `results/clock.json`, the Clock's file, is unchanged at 1.2.0: the Clock moves to Elexon for those years once the history holds Elexon's sums for them (it does at 1.5.0, below).

### The keys

- `all.headline.<basis>.<m>`: M1 (ADR 0007). The 2002-2024 headline's measured, modelled and estimated parts, each line counted by its basis year by year (`<line>.basis`, carbon's `carbon.<year>.basis`: 2005-2012 estimated). They add up to the headline.
- `range.<bound>.headline.<m>`: M2 (ADR 0234, choice 2). The headline with one of the three estimated lines at its low or high and the other two central: carbon (`carbon.range.*`), turn-up (`constraint_turnup.range.*`) and the Capacity Market (low share to central: `capacity_market.range.low`; its `range.high` key is the whole levy, a counting option, never a range end). Each end is the one line that moves the headline furthest that way. No VAT is moved with a line's range, as in 1.1.0's line ranges.
- `range.<bound>.headline.line`: the line that sets that end.
- `households.<year>`: M3. In 1.2.0 UK households (from 1.3.0 Great Britain's: below, "Version 1.3.0"), 2002-2025, ONS *Families and households in the UK: 2025*, Table 5, "All households" (ADR 0027 year-matched; ADR 0232 each scheme over its own area, as the Clock, so UK households, as the whole bill is the UK's).
- `per_household.<year>.real`: each year's money paid (all lines, 2024 prices) per household; 2025 provisional. In 1.2.0 over that year's UK households; from 1.3.0 each line over its own area's households (below).
- `per_household.year_by_year.headline.real`: the per-household figures of 2002-2024 added up (ADR 0025, 0027). 1.1.0's `per_household.headline` (over today's 29 million) stays beside it, unchanged.
- `own_bills.per_household.<year>.real`: M4 (ADR 0025). On a household's own bills: households' share of every line but the CCL (the share 1.0.0's VAT line uses, `vat.domestic_share.<year>`), plus the VAT line, over that year's households, 2002-2025.
- `own_bills.per_household.headline.real`: the same, 2002-2024 added up.
- `bill.2025.real`, `bill.2025.cash` and `share_of_bill.2025` (M5) are new keys of the templates `bill.<year>.<m>` and `share_of_bill.<year>`: the whole 2025 bill (DUKES 2026, Table 1.3.A, as the frozen file holds it) and the provisional 2025 total's share of it.
- `option.<option>.headline.<m>`: M6. The headline under another counting option the paper argues. A line taken out or added takes its VAT with it by 1.0.0's rule (5% on households' share); the CCL carries none. Never the paper's figure.
  - `carbon_tax_only`: carbon counted as the tax collected only (§6.2).
  - `no_carbon`: no carbon (§6.2).
  - `ccl_above_2001`: the CCL only above its 2001 rate (§6.3). Each year's receipts over its calendar-year main rate (a quarter at the rate from the April before, three quarters at its own April's) give the taxable volume, priced at the 2001 rate, £0.0043/kWh, and taken off: Report No. 1's method (`gascf.ccl_baseline`) on the UK line, without No. 1's adjustment for exempt renewable output, which rests on No. 1's own road. Rates from HMRC's historical rates table.
  - `no_ccl`: no CCL (§6.3).
  - `grid_whole`: grid and balancing counted whole, the charges as paid (generators' share removed, as 1.0.0) rather than above the gas-led alternative's (§8.3, §8.4).
  - `cm_whole_levy`: the whole Capacity Market levy in place of the part net zero caused (§8.5).
  - `energy_saving_schemes`: the headline with suppliers' energy-saving schemes counted, plus 5% VAT on the whole of them (households pay them all) (§6.5, §15.1).
- `energy_saving_schemes.<year>.<m>`: M6f (ADR 0233: left out, size shown). Suppliers' energy-saving schemes (EEC, CERT, CESP, ECO, GBIS), their cost on electricity bills, Great Britain, as Report No. 1's pinned release v4-s43 holds it: its NZ10, the lower end of each scheme's range, gross of the 2001 scheme (EESoP) that No. 1 nets off at its 2001 level (the release's `on_the_road` block gives it year by year). Not counted in any headline. Priced by CPIH.
- `energy_saving_schemes.headline.<m>`: the same, 2002-2024.
- `energy_saving_schemes.basis`: estimated, as No. 1 labels the line. From 1.3.0 it has its range (ADR 0007): `energy_saving_schemes.range.*`, below.
- `cfd_renewable.by_technology.<technology>.headline.<m>`: M8. CfD by technology, 2002-2024 (payments from 2016), LCCC's contract-by-contract payments from the store snapshot the frozen file was built from, by calendar year, priced by CPIH; `all` is every technology and equals the CfD line to under £10.
- `check.<check>.headline.<cs>`: M7, a check against a published total, £ cash as paid, over the years both cover: `model`, `reference`, `gap` (model less reference), `ratio` (model over reference). `<check>`: `hmrc.ccl`, `ofgem.ro`, `ofgem.fit`, `obr.levies`, `ref.direct` (below). `<cs>`: `model`, `reference`, `gap`, `ratio`.
- `check.<check>.years`: the years the check covers.
- `check.<check>.basis`: what each side holds, in words.
- `constraints.national_grid_years` and `constraints.spread_years` (1.5.0, below) name the years not on Elexon's record. 1.2.0 to 1.4.0 named them in another key, gone at 1.5.0.

### The checks (1.2.0)

| Check | Model side | Reference (saved file) | Result (1.2.0 build) |
|---|---|---|---|
| `hmrc.ccl` | CCL line, 2002-2024 | HMRC Environmental Taxes Bulletin, Table 1b, electricity declarations | exact: the line is HMRC's figure |
| `ofgem.ro` | RO line, SY1-SY23 (2002-03 to 2024-25) | Ofgem's scheme value, ROCs presented x worth of a ROC (annual reports 2005-06, 2009-10, SY23 Figure A4.1) | the line is £525.5m higher: the mutualisation received 2017-18 to 2021-22, which the line adds |
| `ofgem.fit` | FiT line, 2010-11 to 2024-25 | the levelisation fund printed in Ofgem's document for each year (15 documents) | exact |
| `obr.levies` | RO line plus CfD by financial year, 2002-03 to 2024-25 | OBR public finances databank (October 2026), "Environmental levies" | the model is £10.3bn (11%) lower. The OBR's series also holds the Warm Home Discount and the green gas levy, which the model does not count; the rest of the gap is not explained here |

`check.ofgem.price_cap_policy_costs` was not built in 1.2.0; 1.3.0 builds it (ADR 0241, below). The `obr.levies` row above is 1.2.0's; 1.3.0 makes it like for like (below).

## Version 1.3.0: the checker's points and the households divisor

Report No. 2's plan step 19 (aios-harness#235), after the separate checker's pass over 1.2.0, and Richard's two rulings of 11 Nov 2026: the price-cap check (report-series ADR 0241) and the households divisor (ADR 0242). Every value that moves from 1.2.0 and every key added: `docs/1.3.0-against-1.2.0.md`. New publishers' files: `reference/sources/`, pinned in `reference/outline_sources.yaml`.

### Households: each line over its own area (ADR 0242)

> **For the writer: per household.** Print `per_household.<year>.real` (a year) and `per_household.year_by_year.headline.real` (2002-2024), and for a household's own bills `own_bills.per_household.<year>.real` and `own_bills.per_household.headline.real`. Say "households in Great Britain" (two lines, the RO and the CCL, are counted across the UK and divided by UK households; say so once). Never print `per_household.2024` or `per_household.headline` (no `.real`): they are 1.1.0's figures over a round 29 million UK households, kept only for the Clock.

Richard's ruling: each scheme's money is divided by the households of its own area, then added up: what a household in Great Britain paid. The RO and the CCL run across the UK (ADR 0232), so they go over UK households; every other line, Sizewell C's levy included, over Great Britain's. VAT follows its line: 1.0.0 charges 5% on households' share of every line but the CCL, so the VAT on the RO (5% x households' share x the RO) goes over UK households and the rest of the VAT line over Great Britain's.

- `households.<area>.<year>`: households that year, 2002-2025. `uk`: ONS, *Families and households in the UK: 2025*, Table 5, "All households". `gb`: ONS Labour Force Survey (April-June), England + Wales + Scotland: 2015-2025 from "Households by household size, regions of England and GB constituent countries" 2025, 2002-2014 from ONS ad hoc 005374 (to the nearest hundred). The same two files and the same reading as Report No. 1's GB households.
- `households.<year>`: **Great Britain's** households that year, the same as `households.gb.<year>` (in 1.2.0 it was the UK's). The paper's divisor is not one number: write "households in Great Britain" and name the two UK-wide lines once.
- `per_household.<year>.real`: money paid per household that year, 2024 prices: the Great Britain lines and their VAT over Great Britain's households, plus the RO, the CCL and the RO's VAT over the UK's. 2025 provisional.
- `per_household.year_by_year.headline.real`: the same, 2002-2024 added up.
- `own_bills.per_household.<year>.real`: on a household's own bills that year: households' share of every line but the CCL, plus its VAT, each over its own area's households, 2024 prices (ADR 0025). The CCL is business only and stays out.
- `own_bills.per_household.headline.real`: the same, 2002-2024 added up.
- Which key to print: `per_household.<year>.real` and `per_household.year_by_year.headline.real` are the paper's. `per_household.<year>` and `per_household.headline` (no `.real`, over the round 29 million UK) are 1.1.0's and are not used by the outline.

### The energy-saving schemes' range (ADR 0007)

- `energy_saving_schemes.range.<bound>.<year>.<m>`: the schemes' line at Report No. 1's lower or upper end of each scheme, as the pinned shared cost register holds them (row ENERGY_SAVING, `low_gbp_m` and `high_gbp_m`; the build checks the register's sha256 and that its central is the line). The line is the lower end, so `low` equals it.
- `energy_saving_schemes.range.<bound>.headline.<m>`: the same, 2002-2024.
- The range comes from the published ranges No. 1 read: EEC2's £5 to £9 per customer per fuel, the electricity share of CERT and CESP (50% to 55.6%), and ECO1/ECO2's two readings. From 2016 the schemes have a single published figure (the cap's ECO attribution), so low equals high.

### The OBR check, like for like

- The OBR's "environmental levies" outturn (public finances databank, October 2026) is ONS's. ONS's own series of its parts, saved here (public sector finances, EDP dataset, 21 Sep 2026), add up to it to the £1m in every year 2002-03 to 2024-25: ROCs (EP89), CfDs (CW5G), the Warm Home Discount (JNJF) and the CRC Energy Efficiency Scheme (L8UA, 2012-13 to 2019-20 only).
- It holds no Capacity Market: the OBR's own note to its receipts table 4.20 says ONS has yet to include Capacity Market auctions and the Sizewell C RAB charge in its outturn; the databank's footnote names the Capacity Market among what the column covers, but no ONS series of it is in the column (ONS's parts add up without one). No FiT (ONS has only lately added it, from 2025-26) and no green gas levy before 2025-26. So nothing is added to the model's side.
- The reference is the OBR's figure less the two schemes the model does not count, WHD and CRC (`check.obr.levies.not_counted.whd`, `.crc`). The OBR's figure as published is `check.obr.levies.reference_whole`.
- What is left is the RO and CfD on both sides. The gap splits into `check.obr.levies.gap.ro` (the RO line less ONS's ROC series) and `check.obr.levies.gap.cfd` (LCCC's payments by financial year less ONS's CfD series), and `check.obr.levies.ons_parts_less_obr` (nil). The RO part is most of it (£1.53bn): ONS's ROC receipts run above Ofgem's scheme value plus mutualisation in most years from 2012-13. It is not reconciled: ONS does not publish how it values the certificates. Looked for on 11 Nov 2026: the series' own metadata (EP89, EDP dataset: title "CG: D214/D31: Renewable Obligation Certificates (ROCs): CP NSA", no source or method field) and ONS's public sector finances methodology and classification articles, by search; none says how the RO's receipts are valued. So this part is named and sized, not explained.
- The keys: `check.obr.levies.reference_whole`; `check.obr.levies.not_counted.<nc>`; `check.obr.levies.ons_parts_less_obr`; `check.obr.levies.gap.<gl>`. In full: `check.obr.levies.not_counted.<nc>` (`<nc>`: `whd`, `crc`); `check.obr.levies.ons_parts_less_obr`; `check.obr.levies.gap.<gl>` (`<gl>`: `ro`, `cfd`).

### The price-cap check (ADR 0241)

- What it compares: the RO and FiT, the only schemes both Ofgem's price-cap policy-cost allowance and the model count, £ per typical household (single-rate electricity), 2019-20 to 2025-26 (`check.ofgem.price_cap_policy_costs.years`, `.schemes`).
- Ofgem's side: its allowance for each scheme, £ per MWh supplied, each cap period (Ofgem, Annex 4 v1.25, tab 1a; the latest update of each half year), weighted summer and winter as Ofgem weights them (tab 3a: 0.4324, 0.5676), times Ofgem's typical consumption, 3.1 MWh a year, the value in force from April 2018 to December 2025 (`check.ofgem.price_cap_policy_costs.typical_consumption_mwh`; Ofgem uses 2.7 MWh from January 2026; both sides use the same figure, so the ratio does not depend on it). **Ofgem's figure is a forward allowance**, set before each period from forecasts (the RO at the obligation level times the buy-out price; FiT from the OBR's forecast), not money paid.
- The model's side: the RO line (UK, obligation years) over the ROCs obligated in the UK, times Great Britain's obligation level (Annex 4 tab 3b), which gives £ per MWh supplied. Both sides use Ofgem's own obligation level, so the RO half tests the model's value per certificate obligated (what was paid, over the certificates owed) against Ofgem's forecast buy-out price: a value per certificate against a forward allowance, not money paid against money paid; the FiT line (Great Britain) over Great Britain's supply (the ROCs obligated in England, Wales and Scotland over that level, from Ofgem's total obligation notices); each times the same 3.1 MWh. 2025-26 is provisional on the model's side.
- **CfDs and carbon**: Ofgem counted CfD costs as policy costs until version 1.11 of its Annex 4, dated 15 May 2022, whose change log reads "Removed CfD costs from the annex (moved to annex 2 - wholesale costs)" (the saved workbook's front sheet); from then CfDs sit in Ofgem's wholesale allowance. The check leaves CfDs out on both sides in every year, so it stays like for like before and after the move. Carbon (the carbon price in the wholesale price) is in neither side. (1.3.0's wording, that Ofgem counts CfDs under wholesale, was true only from v1.11; corrected in 1.3.1.) Ofgem's policy costs also hold schemes the model does not count (ECO, the Warm Home Discount, AAHEDC, the network charging compensation scheme), and from late 2025 the Sizewell C levy (nRAB), which is left out here because the model's Sizewell C line covers December 2025 only.
- `check.ofgem.price_cap_policy_costs.<year>.<cs>`: each financial year from its April; `.headline.<cs>` the seven years added up.
- Year by year the ratio is 0.99 to 1.01 except 2021-22, 0.94 (`check.ofgem.price_cap_policy_costs.<year>.note`, 2021 only). The cause is FiT, and Ofgem's levelisation notices show it: the 2021-22 fund fell to £1,273.1m (2020-21: £1,603.0m) because the value of exported power to suppliers, which is taken off the fund, rose to £301.7m (£160.8m) with high wholesale prices, and generation payments fell to £1,451.9m (£1,547.0m). The model's FiT half is £4.96/MWh against Ofgem's £6.85/MWh, set beforehand from a forecast; the RO half agrees within 0.1%.
- `check.ofgem.price_cap_policy_costs.schemes`: the schemes matched (`ro,fit`).
- `check.ofgem.price_cap_policy_costs.typical_consumption_mwh`: the typical consumption both sides use (3.1).

## Version 1.4.0: Richard's rulings of 16 Nov 2026 (12e, 13b, 14c, 21a)

For Report No. 2 (aios-harness#243; the rulings sheet, `report-series/price-of-the-climate-bill/rulings-sheet.md`, points 12, 13, 14 and 21). Key by key against 1.3.1: `docs/1.4.0-against-1.3.1.md`.

### The headline without grid and balancing (ruling 12e)

- `option.no_grid_balancing.headline.<m>`: the headline with none of the grid and balancing cost above the gas-led alternative counted: the TNUoS and BSUoS lines taken out each year, with the VAT 1.0.0's rule charges on them (5% on households' share). Printed beside the headline. The switch-off payments (`constraints`, a measured direct line) and turn-up stay in: the ruling sizes the case as the two lines the paper's §1.1 names, £14.6bn and £2.0bn.
- `option.no_grid_balancing.less_than_headline.<m>`: the headline less that case (a positive £).
- `option.no_grid_balancing.words`: the case in words.

### Turn-up moves only the split (ruling 14c)

- `bsuos.turnup_range.<bound>.<year>.<m>`: the BSUoS line with turn-up at its low or high (`constraint_turnup.range.*`, kept as in 1.3.1). Switch-off payments, turn-up and balancing are one recorded total split three ways (paper §8.1), so turn-up's change comes off the BSUoS line and the total does not move. The cap at the BSUoS uplift keeps the BSUoS line at or above zero.
- `bsuos.turnup_range.<bound>.headline.<m>`: the same, 2002-2024.
- `range.lines`: the lines whose ranges set the headline's range. Turn-up is no longer one of them: changed alone, it moves no total, so the headline's range (`range.<bound>.headline.<m>`) is set by the others only. This changes ADR 0234's three lines.

### How fully the carbon charge passed into the price (ruling 13b)

The carbon line assumes the carbon charge passed into the price of power in full. Ruling 13b gives that assumption a range from published estimates (the research and its saved sources: `report-series/price-of-the-climate-bill/handover/research-13b-pass-through.md`, `price-of-the-climate-bill/sources/carbon-pass-through/`). Code: `billpaid.outline.pass_through`.

| Period | Low | Central | High | Basis |
|---|---:|---:|---:|---|
| 2005-2012 (EU scheme, Phases I and II) | 60% | 100% | 110% | Sijm, Neuhoff and Chen 2006 (60 to 100%, Germany and the Netherlands); Castagneto-Gissey 2014 (109%, UK) |
| 2013-2020 (EU scheme and the Carbon Price Support) | 75% | 100% | 120% | Guo and Castagneto Gissey 2019 (75.1%, the allowance, Britain 2015-2018); Guo and Newbery 2020 (120%, the Carbon Price Support, Britain 2015-2020) |
| 2021-2025 (UK scheme; 2025 provisional) | 75% | 100% | 120% | A judgement: no published estimate for Britain, so 2013-2020's settings carried forward |

- The setting scales the whole carbon line each year (the carbon price times the price-setting plant's carbon intensity times the power made). One bracket: every period at its low together, or at its high together, everything else central.
- **VAT moves with it**: a smaller charge passed into the price is a smaller price, so 5% on households' share of the change is moved with the line, as in the carbon counting options (`option.no_carbon`, `option.carbon_tax_only`). The carbon price range of 2005-2012 (`carbon.range.*`) still moves no VAT, as in 1.1.0.
- `carbon.pass_through.<pt>.<end>`, `carbon.pass_through.<pt>.years`, `carbon.pass_through.<pt>.basis`: the settings, years and their basis (`<pt>`: `2005_2012`, `2013_2020`, `2021_on`). `carbon.pass_through.<ptw>`: the method, sources and VAT in words (`<ptw>`: `method`, `sources`, `vat`).
- `carbon.pass_through.range.<bound>.<year>.<m>`, `carbon.pass_through.range.<bound>.headline.<m>`: the carbon line at each end (2025 provisional, never in the headline).
- `carbon.pass_through.swing.<bound>.<m>`, `carbon.pass_through.headline.<bound>.<m>`: the headline's move, and the headline, at each end.
- It joins the headline's range (`range.lines`: carbon, the Capacity Market and carbon pass-through; turn-up out under 14c). From 1.4.0 the pass-through sets both ends.

## Version 1.5.0: National Grid's record for 2010-2015, and primary sources only

aios-harness#266; Richard's rulings of 19 Nov 2026. Code: `src/billpaid/mbss.py`, `elexon_record.py`. Tests: `tests/test_national_grid_constraints.py`, `tests/test_mbss_wind_payments.py`. What moves from 1.4.0: `docs/1.5.0-against-1.4.0.md`.

### Wind constraint payments 2010-2015: National Grid's Monthly Balancing Services Summary

- The source is the payer's own monthly report, section "Payments to Wind Powered Generation". Eight reports, as NESO hosts them, are saved in `reference/sources/mbss/` and typed with their checksums in `reference/mbss_wind_payments.yaml`.
- National Grid prints each month from April 2013. Before that it prints one total for each April-March year: 2010/11 £0.2m, 2011/12 £34.1m, 2012/13 £7.6m, and says no payment was made earlier.
- 2014 and 2015 are the sums of their twelve printed months: £57.0m and £96.9m.
- The three April-March totals are spread by the model's rule for April-March years (`calendar_years.fy_to_cy`): a quarter to the calendar year they end in, three quarters to the one they start in. April to December 2013's printed months (£33.7m) are added to 2013. So 2010 is £0.15m, 2011 £25.625m, 2012 £14.225m, 2013 £35.6m.
- The four years' total is what National Grid printed, whatever the spread. Only its split between the four years is estimated, so those years carry `constraints.<year>.basis` = estimated and count in the headline's estimated part. `constraints.spread_years` names them; `constraints.national_grid_years` names all six.
- The widest the spread could be wrong in any one year: 2012 holds £14.2m and could hold anything from nil to £41.7m (all of 2011/12 and 2012/13); 2011 holds £25.6m and could hold nil to £34.3m.
- National Grid counts every payment to a wind farm "regardless of the reason", in or out of the Balancing Mechanism. Elexon's record, from 2016, counts accepted bids in the Balancing Mechanism. Where the two overlap, December 2015 to July 2016 agree within rounding, and August 2016 to March 2017 National Grid's count is £8.6m (14%) higher (`tests/test_mbss_wind_payments.py`).
- Elexon's own older record was not used: its open services return nothing before November 2015, and its portal's archive could not be opened (Richard, 19 Nov 2026: he could not log in, and it needs him to contact Elexon and register as a tenant, which he will not do).
- The three balancing lines are re-split by 1.0.0's rule as at 1.2.0, so `all`, the bridge and VAT do not move. Constraints rise £33.9m cash over 2010-2015; BSUoS falls £27.7m and turn-up £6.2m (2015, where turn-up is capped at the uplift and BSUoS is nil).
- `reference/annual_scheme_costs.yaml`, `constraints_history`, now holds these six years and, for 2016-2023, Elexon's own yearly sums; its pin (`bottom_up_from`) stays 2024. So a new run of the results file gives the same three balancing lines as the figures file (`tests/test_results.py`). `results/clock.json` as frozen is not rebuilt here.

### Primary sources only

- The check against a third party's published total (keys `check.ref.*`) and the key naming the years on its database are gone, with their saved page, the two reference files that fed the command line's printed cross-checks, and those cross-checks.
- `reference/register/shared-cost-register-v4-s43.csv` is Report No. 1's pinned register, kept byte for byte; its CONSTRAINTS rows are no longer read (`register.REF_LINES`). `reference/clock_findings.yaml` records what the live Clock's old histories were and stays as written.
