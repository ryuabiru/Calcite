# Next Steps

## Current State

- The runtime Python implementation under `calcite/` has been removed.
- The remaining Python test harness has been removed as well; the repo is now Rust-only at runtime and in tests.
- Rust/Tauri is now the only runtime path in the repo.
- The Rust bootstrap now supports CSV loading, table sorting, row selection, and case-insensitive row filtering in the preview.
- Rust now renders a first native bar chart from the loaded table in the `egui` graph area.
- Rust now also renders a native stacked bar chart from the loaded table and subgroup column.
- Rust now renders a native correlation heatmap from numeric columns.
- Rust now renders a native categorical heatmap from the loaded table's X/Y columns.
- Rust heatmap rendering now supports count, row, column, and total normalization modes.
- Rust now also renders native proportion, mosaic, and histogram variants from the loaded table.
- The Python runtime was retired in stages, ending with the removal of the remaining `calcite/` modules, console entrypoint, and test harness.
- The Tauri React DataFrame pane now renders a CSV table preview from the Rust snapshot query.
- The Tauri React DataFrame pane now mirrors visible-row filtering and sort order in the preview.
- The Tauri React column chips can push column names into graph settings fields.
- The Tauri React DataFrame pane now exposes reshape and pivot actions against the Rust backend.
- The Tauri React shell now remembers the last project directory in local storage.
- The Tauri React shell now makes project save/load a reusable restore path for table and graph state.
- The Rust bootstrap now can run chi-squared analysis and render a detailed statistical summary.
- The Rust bootstrap now can also run Pearson correlation analysis and render its summary.
- The Rust bootstrap now can also run Spearman correlation analysis and render its summary.
- The Rust bootstrap now can also run 2-proportion z-tests and render their summary.
- The Rust bootstrap now can also run simple linear regression and render its summary.
- The Rust bootstrap now can also run independent and paired t-tests and render their summaries.
- The Rust bootstrap now can also run one-way ANOVA and render its summary.
- The Rust bootstrap now can also run Mann-Whitney U, Wilcoxon signed-rank, and Kruskal-Wallis analyses.
- The Rust bootstrap now can also run Shapiro-Wilk normality tests and render their summaries.
- The Rust bootstrap now can also run 4PL regression and render its summary.
- Rust graph rendering now highlights chi-squared residuals and 2-proportion comparison groups.

## Rust Migration Direction

- Detailed migration notes live in [`RUST_MIGRATION.md`](./RUST_MIGRATION.md).
- Rust will own the UI shell first, then data loading, then table UX, then graphs, then transforms, and statistics last.
- Frontend/backend boundaries should stay explicit: UI emits commands, backend updates state and returns view models.
- The current Rust bootstrap lives under [`rust/`](./rust) and uses `eframe/egui`.

## Graphs Implemented

- `scatter`
- `summary_scatter`
- `bar`
- `countplot`
- `stacked_bar`
- `stacked_bar_100`
- `mosaic`
- `proportion_plot`
- `heatmap`
- `correlation_heatmap`
- `boxplot`
- `violin`
- `lineplot`
- `pointplot`
- `histogram`

## Statistical Features Implemented

- Independent t-test
- Paired t-test
- One-way ANOVA
- Mann-Whitney U test
- Wilcoxon signed-rank test
- Kruskal-Wallis test
- Shapiro-Wilk normality test
- Spearman correlation
- Pearson correlation
- Chi-squared test
- 2-proportion z-test
- Linear regression
- 4PL regression

## Recent Changes

### Architecture and maintainability

- Refactored large handlers into smaller modules.
- Removed the legacy Python GUI shell and its orchestration modules.
- Added broader service-layer and application-layer tests.

### Visualization additions

- Added `Count Plot`.
- Added categorical `Heatmap`.
- Added `Correlation Heatmap` with automatic numeric-column selection.
- Added `Stacked Bar` and `100% Stacked Bar`.
- Added `Mosaic Plot`.
- Added `Proportion Plot` with direct 95% CI overlays.
- Added proportion-specific UI controls for success category selection and label mode.
- Added heatmap controls for colormap selection, cell-label visibility, and row/column/overall normalization.
- Added heatmap residual highlighting after chi-squared analysis.
- Added proportion-plot comparison highlighting after 2-proportion analysis.
- Added category/subgroup order controls for categorical plots.
- Added direct labels for stacked bars and percentage tick formatting for `stacked_bar_100` and `proportion_plot`.
- Improved default legend placement for categorical plots.
- Added sortable table preview headers and filtered-row rendering in the Tauri React shell.
- Added DataFrame column chip actions for updating graph settings from the preview.
- Added Rust-native proportion plot, mosaic plot, and histogram renderers.
- Added Rust-native chi-squared analysis with p-value, residuals, and contribution tables.
- Added Rust-native Pearson correlation analysis with sample size and p-value reporting.
- Added Rust-native Spearman correlation analysis with rank-based correlation and p-value reporting.
- Added Rust-native 2-proportion z-test analysis with Wilson confidence intervals and difference testing.
- Added Rust-native simple linear regression analysis with slope, intercept, and R-squared reporting.
- Added Rust-native graph-statistics linkage for chi-squared residuals and 2-proportion comparison groups.
- Added Rust-native independent and paired t-test analyses with t-statistic and p-value reporting.
- Added Rust-native one-way ANOVA analysis with F-statistic and group mean reporting.
- Added Rust-native Mann-Whitney U, Wilcoxon signed-rank, and Kruskal-Wallis analyses with result summaries.
- Added Rust-native Shapiro-Wilk normality tests with grouped results and skipped-sample handling.
- Added Rust-native 4PL regression with fitted parameters and R-squared reporting.
- Added reshape and pivot controls to the Tauri React DataFrame pane.
- Added project directory recall and a restore-last-project button in the Tauri shell.
- Added project save/load state restoration to the Tauri shell with persisted graph/table settings.
- Retired the paired-scatter Python tab leaf, toolbar action, renderer, and paired annotation state.

### Statistical additions

- Expanded chi-squared output with:
  - standardized residuals
  - cell contributions
  - Cramer's V
- Added Pearson correlation analysis.
- Added 2-proportion z-test.
- Added simple linear regression.
- Added independent and paired t-tests.
- Added one-way ANOVA.
- Added 95% confidence intervals for each group's proportion and the difference in proportions.

### Quality checks

- `cargo test` passes for the Rust migration backend.
- `cd tauri && npm run build` passes for the Tauri frontend.
- Rust test suite now includes chi-squared analysis coverage.
- Rust test suite now includes Pearson correlation analysis coverage.
- Rust test suite now includes 2-proportion z-test coverage.
- Rust test suite now includes simple linear regression coverage.
- Rust test suite now includes independent and paired t-test coverage.
- Rust test suite now includes one-way ANOVA coverage.

## Highest-Value Next Work

### 1. Broader automated coverage

Next additions:

- renderer-level smoke tests for newer graph types, including `proportion_plot`
- use-case tests for 2-proportion edge cases
- project round-trip coverage for newer state fields if more are added

### 2. Sparse-table heatmap polish

Goal:

- clearer defaults for very sparse categorical tables
- better handling of zero-heavy matrices in normalized views
- optional display tuning for dense label grids

### 3. Deeper graph-statistics linkage

Goal:

- expand beyond lightweight highlights into richer statistical overlays
- consider contribution-aware heatmap annotations or difference-aware proportion labels

### 4. UI refinement follow-up

Goal:

- visually verify the new theme against real data states
- tune spacing, typography, and contrast where the current stylesheet overreaches
- consider graph-area framing and results-panel hierarchy refinements after manual inspection

## Practical Next Starting Point

If work resumes, start here:

1. Add renderer smoke tests for the new Rust-native graph variants.
2. Add analysis parity for the highest-use statistical flows.
3. Tune sparse heatmap presentation defaults.
4. Expand statistical overlays beyond the current lightweight highlights.
