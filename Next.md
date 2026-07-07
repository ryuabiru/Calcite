# Next Steps

## Current State

- Core handlers were split into thinner facades and specialized modules.
- An application/use-case layer now exists under `calcite/application/`.
- Plot preparation logic lives in `calcite/services/plot_service.py`.
- Statistical logic lives in `calcite/services/statistics_service.py` and `calcite/application/statistics_use_cases.py`.
- Project persistence, data reshape/filter logic, and export/import flows are separated into service/use-case modules.
- Snapshot-based undo/redo for DataFrame edits is implemented.
- Analysis results can be exported from the UI.
- Dedicated proportion plots with 95% Wilson confidence intervals are implemented.
- Categorical heatmaps now support configurable colormaps, cell-label toggles, and normalization modes.
- Chi-squared and 2-proportion analysis results now drive lightweight plot highlights.
- Categorical charts now support ordering controls, stacked labels, percentage ticks, and cleaner legend defaults.
- The desktop UI now uses a unified warm-toned application theme with styled panels and controls.
- Renderer smoke tests now cover `proportion_plot` and normalized heatmap output.
- Renderer smoke tests now also cover `stacked_bar`, `stacked_bar_100`, `mosaic`, and `correlation_heatmap`.
- Legend alpha handling now uses a matplotlib-compatible frame update path.
- The Rust bootstrap now supports CSV loading, table sorting, row selection, and case-insensitive row filtering in the preview.
- Rust now renders a first native bar chart from the loaded table in the `egui` graph area.
- Rust now also renders a native stacked bar chart from the loaded table and subgroup column.
- Rust now renders a native correlation heatmap from numeric columns.
- Rust now renders a native categorical heatmap from the loaded table's X/Y columns.
- Rust heatmap rendering now supports count, row, column, and total normalization modes.
- The Tauri React DataFrame pane now renders a CSV table preview from the Rust snapshot query.

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
- `paired_scatter`
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
- Reduced `MainWindow` responsibilities by moving orchestration into builders, persistence helpers, controllers, and use-cases.
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
- Added an application-wide UI theme for the main window, panels, tabs, toolbar, and controls.

### Statistical additions

- Expanded chi-squared output with:
  - standardized residuals
  - cell contributions
  - Cramer's V
- Added Pearson correlation analysis.
- Added 2-proportion z-test.
- Added 95% confidence intervals for each group's proportion and the difference in proportions.

### Quality checks

- `python -m compileall calcite tests` passes.
- `uv run python -m unittest tests.test_services` passes.

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

1. Add renderer smoke tests for `proportion_plot` and normalized heatmaps.
2. Tune sparse heatmap presentation defaults.
3. Expand statistical overlays beyond the current lightweight highlights.
4. Manually inspect the refreshed GUI and tune the theme where needed.
