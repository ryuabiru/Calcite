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
- The Tauri React graph panel now renders scatter-family plots and can export the current SVG.
- The Tauri React graph panel now also shows axis tick labels for continuous plots and paired-scatter axes.
- Post-hoc graph annotation summaries now persist through project save/load.
- Post-hoc graph annotation summaries now render as an overlay inside the graph panel.
- Post-hoc graph annotations now also draw directly on categorical plots.
- The Tauri React shell now remembers graph and CSV input controls in local storage.
- The Tauri React shell now lets you dismiss the current error message from the results panel.
- The Tauri React shell now lets you close the About / License dialog with Escape or backdrop click.
- The Tauri React shell now restores the last loaded CSV path from backend state.
- The Tauri React graph export filename now encodes `y_log_scale` for log-scaled graphs.
- The Tauri React graph and results panels now present shared file, graph, filter, selection, and annotation state in aligned cards.
- The Tauri React graph panel now shows export-name preview text and stronger grid/label framing for reading plots.
- The Tauri React shell now remembers the last project directory in local storage.
- The Tauri React shell now makes project save/load a reusable restore path for table and graph state.
- Project save/load now has roundtrip coverage for graph annotation summaries and `y_log_scale`.
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
- The Tauri React shell can now import pasted CSV/TSV text from the load pane.
- The Tauri React analysis pane now exposes chi-squared analysis from the existing Rust backend.
- The Tauri React header now exposes project load alongside project save.
- The Tauri shell now supports native CSV/project pickers, CSV export save dialogs, file-drop import, and a File menu.

## Main Branch Parity Check

Main branch と Rust/Tauri 現状を比較した結果を、機能領域ごとに整理すると次の通りです。

| 領域 | `main` にあった内容 | Rust/Tauri の現状 | 判定 |
| --- | --- | --- | --- |
| File / Project | CSV open/save, project open/save, graph export | CSV load/save project/load project/export CSV と SVG graph export はある。project graph state も保存される | 主要機能は移植済み |
| Table | sort, edit, insert/remove row/column, copy/paste, header rename, fill down, selection | sort/edit/insert/remove row/column/selection/copy-paste/header rename/fill down はある | 主要機能は移植済み |
| Data transforms | wide/long reshape, pivot, advanced multi-condition filter, calculate new column | reshape/pivot/calculate new column/advanced filter はある | 主要機能は移植済み |
| Graph types | scatter, summary scatter, bar, box, violin, line, point, paired scatter, histogram | Tauri frontend は scatter / summary scatter / box / violin / line / point / paired scatter / bar / count / stacked bar / histogram / heatmap / correlation heatmap を実装済み。Rust egui 側には他の既存描画もある | 主要プロットは移植済み |
| Graph styling | legend, axes, fonts, log scale, markers, spines, individual points | 基本の軸・凡例・注釈・補助グリッド・目盛り・マーカー・スパインはある。SVG フォントを明示し、Y 軸 log scale の切り替え、連続軸の tick ラベル、個別点ラベル / hover title、集計マークの hover 値も追加済みで、細かなスタイル調整と一部の高度設定はまだ限定的 | 部分移植 |
| Statistics | t-test, ANOVA, non-parametric tests, correlation, regression, chi-squared, 2-proportion, post-hoc, annotations | 基本検定と回帰、chi-squared、2-proportion に加えて Tukey HSD / Dunn post-hoc と graph linkage 用の注釈要約を追加済み | 主要分析は移植済み |
| Help / License | license dialog | Tauri frontend に About / License ダイアログを追加済み | 実装済み |

## Parallel Next Work

今後は「補填」と「充実」を並行して進める。

### 1. 補填

- 旧 `main` にあったが Rust 側で落ちている操作を先に埋める
- 残る優先対象は、graph styling の細部、individual point レベルの見え方、そして残っている UI の文言調整
- scatter 系と summary scatter 系のグラフは既にあるので、見た目と使い勝手の詰めを進める
- Tukey / Dunn の post-hoc と自動注釈の導線はあるので、より自然な見せ方に寄せる

### 2. 充実

- すでに移植済みの table / analysis / graph の UX を上げる
- 主要状態の保存・復元をさらに堅くする
- 表示文言、エラー表示、結果要約を読みやすくする
- グラフと結果の見た目を整えて、Rust/Tauri 側の操作感を安定させる

## Development Plan

`Next.md` を、これからの実作業の基準にする。

### Sprint 1: Data Parity

Goal:

- main のデータ操作との差分を埋める

Targets:

- `calculate new column`
- advanced filter
- copy/paste
- header rename
- fill down
- graph save/load state (`graph annotation summary`, `y_log_scale`)

Exit Criteria:

- CSV を読み込んだあと、旧 Python UI と同等の基本データ操作が Rust/Tauri 側で一通りできる

Progress:

- `calculate new column` is implemented in Rust/Tauri
- advanced filter is implemented in Rust/Tauri with multi-condition AND/OR support
- copy/paste of selected rows is implemented in Rust/Tauri
- header rename is implemented in Rust/Tauri
- fill down of selected rows is implemented in Rust/Tauri

### Sprint 2: Graph Parity

Goal:

- main の主要プロットを Rust 側へ戻す

Targets:

- scatter
- summary scatter
- box
- violin
- line
- point
- paired scatter
- graph export

Exit Criteria:

- 旧 UI の主要な可視化が Rust/Tauri 側で再現できる

Progress:

- scatter is implemented in the Tauri frontend graph panel
- summary scatter is implemented in the Tauri frontend graph panel
- box plot is implemented in the Tauri frontend graph panel
- violin plot is implemented in the Tauri frontend graph panel
- line plot is implemented in the Tauri frontend graph panel
- point plot is implemented in the Tauri frontend graph panel
- paired scatter is implemented in the Tauri frontend graph panel
- bar chart, count plot, stacked bar, histogram, heatmap, and correlation heatmap are implemented in the Tauri frontend graph panel
- continuous graph axes now render tick labels in the Tauri frontend graph panel
- graph export is implemented as an SVG download from the rendered graph panel
- Sprint 2 exit criteria is met; next work can move to statistical parity

### Sprint 3: Statistical Parity

Goal:

- 主要分析の補完と見た目の統合を進める

Targets:

- Tukey HSD
- Dunn post-hoc
- 自動注釈
- 既存分析結果の graph linkage 強化

Exit Criteria:

- 主要な検定結果が結果欄だけでなく、グラフにも自然に反映される

Progress:

- Tukey HSD is implemented in the Rust analysis backend
- Dunn post-hoc is implemented in the Rust analysis backend
- post-hoc significance summaries now flow into the graph panel as annotations
- Results パネルのプレビューに補足説明を入れて、分析出力の意味を伝えやすくした
- Results パネルの分析ログをカード化して、要約と長文表示を分離した
- Tauri React の Analysis パネルから chi-squared analysis を実行できるようにした

### Sprint 4: UX and Quality

Goal:

- 使い勝手と安定性を上げる

Targets:

- 保存・復元の堅牢化
- エラー表示の整理
- 画面レイアウトの微調整
- renderer / use-case tests の追加
- ネイティブのファイル選択、ドラッグ&ドロップ、メニュー連携を広げる

Exit Criteria:

- 日常利用で気になる欠点が減り、回帰検知がしやすい状態になる

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
- Tukey HSD
- Mann-Whitney U test
- Wilcoxon signed-rank test
- Kruskal-Wallis test
- Dunn post-hoc
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
- Added Rust-native Tukey HSD post-hoc analysis with pairwise adjusted comparisons.
- Added Rust-native Mann-Whitney U, Wilcoxon signed-rank, and Kruskal-Wallis analyses with result summaries.
- Added Rust-native Dunn post-hoc analysis with Holm-adjusted pairwise rank comparisons.
- Added Rust-native Shapiro-Wilk normality tests with grouped results and skipped-sample handling.
- Added Rust-native 4PL regression with fitted parameters and R-squared reporting.
- Added graph-linked post-hoc annotation summaries to the Tauri graph panel.
- Added persistence for graph annotation summaries in project snapshots.
- Moved graph annotations into an in-panel overlay for better visibility.
- Added direct pair markers to categorical graph renders for post-hoc comparisons.
- Added an in-app About / License dialog with bundled license notices.
- Added local-storage persistence for the shell's CSV and graph control inputs.
- Added a results-panel control for clearing the active error message.
- Added Escape/backdrop dismissal for the About / License dialog.
- Added backend-to-frontend CSV path restoration after load/open actions.
- Improved SVG graph export naming to include dataset and graph type.
- Added aligned summary cards for shared file, graph, filter, selection, and annotation state in the Graph and Results panels.
- Added reshape and pivot controls to the Tauri React DataFrame pane.
- Added project directory recall and a restore-last-project button in the Tauri shell.
- Added project save/load state restoration to the Tauri shell with persisted graph/table settings.
- Added roundtrip coverage for persisted graph annotation summaries in project save/load tests.
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

## Quality Checks

- `cargo test` should stay green after each parity slice.
- `npm run build` should stay green after each parity slice.
- `cd tauri && npm run build` should stay green after each frontend change.
- Add or update tests alongside each parity item instead of deferring validation.
- Project save/load and graph-control use-case tests now cover roundtrip state restoration.
