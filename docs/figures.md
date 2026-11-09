# The paper's figures file

Version 1.1.0, part 1 (aios-harness#222, Report No. 2's plan step 6, map #206). Report No. 2, *The Price of the Climate Bill*, prints every bill-already-paid figure by key from this file, as it does the bill still to come's from that model's `results/figures.json` (spec: `report-series/price-of-the-climate-bill/spec.md`, "The bill already paid moves to version 1.1.0"; ADR 0222).

## What it is

- One flat JSON file, `{"figures": {key: value}, "meta": {...}}`, keyed like model-bill-still-to-come's.
- Built by `uv run --frozen python -m billpaid figures` (default output `results/figures.json`, with its fingerprint beside it in `figures.json.sha256`). Code: `src/billpaid/figures.py`. Tests: `tests/test_figures.py`.
- Built from the frozen results file the paper pins, not from a new run: `results/clock.json` as committed at `2a63b034` (the robot's file of 9 Nov 2026, model 1.0.0, sha256 `738ac005…`, pinned in `report-series/model-register.yaml`). The command refuses that file if its fingerprint differs.
- Each key is a 1.0.0 value, or a sum, ratio or product of them by 1.0.0's own rules (CPIH pricing, the Capacity Market range); no new method. The tests check every key against the 1.0.0 table it comes from, so no 1.0.0 value moves, and check that the model still writes `results/clock.json` exactly as before.
- `meta` names the model and version, the file it was built from (path, commit, sha256, version, date), the headline years, and every key template with its meaning.

## The years

- Each year and the headline run 2002 to 2024, the closed years. The headline is the sum of those years.
- 2025, the provisional year, comes in part 3 (#224): every line's 2025 figure, the missing lines filled, Sizewell C, the total's measured and estimated parts.
- 2026 (the year to date) is not in the paper and has no key.
- A line has a key for a year only where 1.0.0 has a row for it (CfD from 2016, constraints from 2010, and so on).

## The keys

A `<name>` stands for any of its values:

- `<line>`: `cfd_renewable`, `constraints`, `ro`, `fit` (direct); `ccl`, `capacity_market`, `carbon`, `tnuos`, `bsuos`, `constraint_turnup`, `vat` (indirect)
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

Every key in the file matches exactly one of these templates (tested):

- `<line>.<year>.<m>`: each line, each year, as 1.0.0 holds it.
- `<line>.headline.<m>`: each line, 2002-2024.
- `<total>.<year>.<m>`: the direct lines, the indirect lines, or all together, each year (equal to 1.0.0's own totals).
- `<total>.headline.<m>`: the same, 2002-2024.
- `<line>.basis`: measured, modelled or estimated (below).
- `<line>.confidence`: 1.0.0's confidence (high, medium or low); high for the four direct lines, which 1.0.0 leaves blank.
- `<line>.layer`: direct or indirect.
- `carbon.<year>.basis`: the carbon line's basis that year, as 1.0.0 gives it (2005-2012 estimated, the rest modelled).
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

## Each line's basis

1.0.0 labels some years and parts but gives no basis for a whole line. Part 1 reads it from 1.0.0's own account of each line:

- measured (payments or receipts as recorded): CfD (LCCC settlement), constraints (Elexon; REF's history before 6 Nov 2015), RO and FiT (Ofgem), the Climate Change Levy (HMRC receipts, electricity's published share);
- modelled (a share or alternative from the pinned gas model): Capacity Market, carbon, TNUoS, BSUoS, VAT (households' share from the gas model);
- estimated: constraint turn-up (1.0.0: "Estimated cost of paying other stations…").

Part 4 (#225) gives a range to each estimated line that has none in 1.0.0 (constraint turn-up, carbon's estimated years).

## Against the spec's proposed names

The spec proposed names and left them to this ticket; the freeze (#226) checks the spec against the frozen file. Where they differ:

- every money key ends in `.real` or `.cash`, as the bill still to come's end in a measure (spec: `carbon.tax_collected.<year>`, `tnuos.raw.<year>` and so on, with no measure);
- `capacity_market.netzero_share.<year>` is `.central`, `.low`, `.high`; `capacity_market.range.low|high` is by year and headline;
- `cfd_renewable.by_technology.<technology>` is `.cash`, `.mwh`, `.share`, to the data's end;
- `constraint_turnup.cross_check` is three figures and its window;
- `deflator.<year>` is `.cpih` and `.to_2024`.

## Not yet

- The version in `pyproject.toml` stays 1.0.0 until the freeze (#226): the live Clock refuses a results file of any other version, so the number moves only with Richard's ruling on how 1.1.0 reaches GitHub.
- The work is on branch `v1.1.0`, on Gitea only; `master` (and so the live Clock) is untouched until the freeze.
- `results/` is the robot's: the figures file is not committed until the freeze writes and pins it.
- Still to come in 1.1.0: the bridge with Report No. 1 (#223), 2025 (#224), the ranges (#225).
