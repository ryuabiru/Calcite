# Next Steps

## Current State

- Core handlers were split into thinner facades and specialized modules.
- An application/use-case layer now exists under `calcite/application/`.
- Plot preparation logic lives in `calcite/services/plot_service.py`.
- Statistical logic lives in `calcite/services/statistics_service.py` and `calcite/application/statistics_use_cases.py`.
- Project persistence, data reshape/filter logic, and export/import flows are separated into service/use-case modules.
- Snapshot-based undo/redo for DataFrame edits is implemented.
- Analysis results can be exported from the UI.

## Graphs Implemented

- `scatter`
- `summary_scatter`
- `bar`
- `countplot`
- `stacked_bar`
- `stacked_bar_100`
- `mosaic`
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

### 1. Proportion plots with confidence intervals

Goal:

- add a dedicated proportion bar plot
- show confidence intervals directly on chart
- align visually with `2-proportion z-test`

Why next:

- strongest follow-up to stacked/mosaic work
- improves interpretability for categorical comparisons

### 2. Better heatmap controls

Goal:

- configurable colormaps
- optional cell labels on/off
- normalization modes
- clearer handling of sparse categorical tables

### 3. Stronger graph-statistics linkage

Goal:

- let statistical outputs drive overlays or highlights where appropriate
- e.g. emphasize residual-heavy chi-squared cells or notable proportion gaps

### 4. Visual polish for categorical charts

Goal:

- percentage tick formatting for `stacked_bar_100`
- optional direct segment labels
- ordering controls for categories/subgroups
- cleaner legend placement defaults

### 5. Broader automated coverage

Next additions:

- renderer-level smoke tests for newly added graph types
- use-case tests for 2-proportion edge cases
- project round-trip coverage for newer state fields if more are added

## Practical Next Starting Point

If work resumes, start here:

1. Add a dedicated proportion plot with CI overlays.
2. Reuse the existing categorical aggregation path where possible.
3. Expose proportion-specific formatting controls in the UI.
4. Add tests for edge cases such as zero counts and asymmetric group sizes.
