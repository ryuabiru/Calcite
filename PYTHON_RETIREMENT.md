# Python Retirement Checklist

## Purpose

This document tracks which Python pieces are still serving as:

- reference implementation for parity checks
- migration scaffolding
- temporary UI / workflow support

The goal is to retire the Python GUI only after the Rust path covers the same user flows and the remaining Python modules are clearly no longer needed.

## Keep For Now

These areas still matter as reference or supporting code:

- `calcite/application/`
- `calcite/services/`
- `calcite/main.py`
- `calcite/__init__.py`
- `calcite/application/statistics_use_cases.py`

## Retirement Candidates

These are the likely first modules to retire once parity is stable:

- `calcite/main_window.py`
- `calcite/main_window_builders.py`
- `calcite/main_window_history.py`
- `calcite/main_window_persistence.py`
- `calcite/main_window_table_interaction.py`
- `calcite/pandas_model.py`
- `calcite/properties_widget.py`
- `calcite/data_widget.py`
- `calcite/results_widget.py`
- `calcite/graph_widget.py`
- `calcite/plot.py`
- `calcite/ui_theme.py`
- `calcite/dialogs/`
- `calcite/tabs/`
- `calcite/handlers/action_*.py`
- `calcite/handlers/graph_*.py`
- `calcite/handlers/statistical_*.py`

The first deletion pass should start from modules that are:

- UI wiring only
- no longer required by parity tests
- not part of the Python reference path used by migration notes or fixture generation

Likely low-risk first candidates:

- `calcite/dialogs/`
- `calcite/tabs/`
- `calcite/handlers/action_*.py`
- `calcite/handlers/graph_*.py`
- `calcite/handlers/statistical_*.py`

## Retirement Order

1. Freeze Rust parity for the supported workflows.
2. Remove UI-specific Python entry points.
3. Remove dialog and handler modules that no longer back a reference workflow.
4. Remove persistence and table-interaction helpers once Rust state handling is trusted.
5. Remove remaining reference-only code after fixtures and golden outputs are updated.

## Verification Before Removal

- Rust tests continue to pass.
- Tauri frontend build continues to pass.
- Migration notes reflect the retired workflow.
- Fixture-based parity checks still pass for the workflow being removed.
- `rust/tests/python_parity.rs` continues to cover the workflows that still depend on Python as a reference.

## Current Status

- Rust now covers the core table, graph, and statistics slices needed for the first retirement pass.
- Python GUI is still the reference implementation for remaining parity checks.
- The Python GUI entrypoint now emits a retirement warning at launch.
- The main window module now emits a retirement warning on construction.
- The Python GUI main window now shows a retirement banner in the content area.
- The Python GUI now exposes migration notes from the Help menu and status bar.
- The Python dialogs package now emits a retirement warning on import.
- The main window builders module now emits a retirement warning on import.
- The main window persistence and history modules now emit retirement warnings on import.
- The main window table interaction module now emits a retirement warning on import.
- The pandas model and results widget now emit retirement warnings on import.
- The data widget and graph widget now emit retirement warnings on import.
- The properties widget and plot module now emit retirement warnings on import.
- The tabs package now emits a retirement warning on import.
- The tabs leaf modules now emit retirement warnings on import.
- The action base and statistical base classes now emit retirement warnings on import.
- The remaining dialog leaf modules now emit retirement warnings on import.
- All currently listed Python retirement candidates now emit at least one retirement warning.
- The action handler aggregate now emits a retirement warning on construction.
- The statistical handler aggregate now emits a retirement warning on construction.
- The graph renderer and statistical association handler now emit retirement warnings on import.
- The action/data/file/table/misc handler modules, dialog adapters, graph manager, and graph canvas handler now emit retirement warnings on import.
- Rust parity tests now cover CSV loading, reshape/pivot, Pearson correlation, chi-squared, two-proportion, linear regression, ANOVA, independent and paired t-tests, Mann-Whitney U, Wilcoxon signed-rank, and Shapiro-Wilk.
- Rust and Tauri test suites are green, so the remaining work is candidate selection and controlled deletion, not core correctness recovery.
- The next retirement move should target the lowest-risk UI wiring modules after confirming they are not needed for parity fixtures or reference workflows.
- `calcite/dialogs/license_dialog.py` has been removed together with the Help menu license action and handler bridge.
- `calcite/dialogs/filter_dialog.py` has been removed as an unreferenced legacy dialog leaf.
- `calcite/dialogs/advanced_filter_dialog.py` has been removed together with the Data menu filter action and handler bridge.
- `calcite/application/data_use_cases.py` has had its advanced filter use case removed.
- `calcite/services/data_service.py` has had its advanced filter query helpers removed.
- `calcite/dialogs/kruskal_dialog.py` has been removed together with the Kruskal-Wallis analysis menu action and handler bridge.
- The legacy Python `run_kruskal` service function has been removed after the UI bridge was retired.
- `calcite/dialogs/paired_ttest_dialog.py` has been removed together with the paired t-test menu action and handler bridge.
- `calcite/dialogs/wilcoxon_dialog.py` has been removed together with the Wilcoxon menu action and handler bridge.
- `calcite/handlers/statistical_paired_handler.py` has been removed after the paired analysis menu items were retired.
- `calcite/dialogs/mannwhitney_dialog.py` has been removed together with the Mann-Whitney analysis menu action and handler bridge.
- `calcite/application/export_use_cases.py` has been removed after the results export code was inlined.
- `calcite/dialogs/ttest_dialog.py` has been removed together with the independent t-test menu action and handler bridge.
- `calcite/dialogs/calculate_dialog.py` has been removed together with the Calculate New Column menu action and handler bridge.
- `calcite/dialogs/regression_dialog.py` has been removed together with the Regression menu action and handler bridge.
- `calcite/application/__init__.py` no longer exports the regression use case surface.
- `calcite/application/statistics_use_cases.py` has had its regression use case removed.
- `calcite/application/__init__.py` no longer exports the 4PL helper surface.
- `calcite/dialogs/correlation_dialog.py` has been removed together with the Pearson/Spearman menu actions and handler bridge.
- `calcite/application/statistics_formatters.py` no longer exports Pearson/Spearman result formatters.
- `calcite/handlers/statistical_association_handler.py` no longer exposes Pearson/Spearman correlation actions.
- `calcite/dialogs/contingency_dialog.py` has been removed together with the chi-squared / 2-proportion analysis bridge.
- `calcite/handlers/statistical_association_handler.py` has been removed after the contingency-based analysis actions were retired.
- `calcite/application/statistics_formatters.py` no longer exports the chi-squared / 2-proportion result formatters.
- `calcite/application/__init__.py` no longer exports the paired-test formatter.
- `calcite/tabs/data_tab_paired.py` has been removed together with the paired-scatter graph-entry bridge.
- `calcite/main_window_builders.py` no longer exposes the paired-scatter toolbar action.
- `calcite/handlers/graph_manager.py` and `calcite/handlers/graph_renderer.py` no longer expose the paired-scatter rendering path.
- `calcite/tabs/text_tab.py` and `calcite/properties_widget.py` no longer manage paired-scatter label state.
- `calcite/application/state.py` and `calcite/services/project_service.py` no longer persist paired-scatter annotations in Python.
- The first actual Python retirement deletion is now complete.
- The second low-risk Python retirement deletion is now complete.
- The third low-risk Python retirement deletion is now complete.
- The fourth low-risk Python retirement deletion is now complete.
- The fifth low-risk Python retirement deletion is now complete.
- The sixth low-risk Python retirement deletion is now complete.
- The seventh low-risk Python retirement deletion is now complete.
- The eighth low-risk Python retirement deletion is now complete.
- The ninth low-risk Python retirement deletion is now complete.
- The tenth low-risk Python retirement deletion is now complete.
- The eleventh low-risk Python retirement deletion is now complete.
- The twelfth low-risk Python retirement deletion is now complete.
- The thirteenth low-risk Python retirement deletion is now complete.
- The fourteenth low-risk Python retirement deletion is now complete.
- The fifteenth low-risk Python retirement deletion is now complete.
- The sixteenth low-risk Python retirement deletion is now complete.
- The seventeenth low-risk Python retirement deletion is now complete.
