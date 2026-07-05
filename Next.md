# Next Steps

## Current State

- Statistical logic has been moved into `calcite/services/statistics_service.py`.
- Plot data preparation and overlay construction have been moved into `calcite/services/plot_service.py`.
- Project I/O has been moved into `calcite/services/project_service.py`.
- Data reshape and filter logic have been moved into `calcite/services/data_service.py`.
- `ActionHandler`, `GraphManager`, and `StatisticalHandler` are thinner than before, but they still coordinate UI state directly.

## Remaining Architecture Work

### 1. Introduce an application/use-case layer

Current handlers still orchestrate multiple steps directly.

Candidates:

- `OpenCsvUseCase`
- `OpenProjectUseCase`
- `SaveProjectUseCase`
- `RestructureDataUseCase`
- `PivotDataUseCase`
- `ApplyAdvancedFilterUseCase`
- `RunStatisticalTestUseCase`
- `RenderPlotUseCase`

Goal:

- UI gathers input
- use-case executes workflow
- service layer performs pure logic

### 2. Reduce `MainWindow` responsibilities

`MainWindow` still owns too much state and too many cross-component references.

Examples:

- current graph type
- regression/fit state
- annotation state
- widget-to-widget coordination

Goal:

- centralize mutable application state in a smaller state container or controller
- make widgets depend on explicit inputs instead of `main_window`

### 3. Unify window creation flow

New windows for filtered/restructured/pivoted/subset tables are still created ad hoc.

Goal:

- extract a shared helper or use-case for child window creation
- standardize model setup, signal wiring, title updates, and app-level window retention

### 4. Separate UI state from persisted state

Project persistence works, but the saved structure is still implicit.

Goal:

- define a stable persisted project schema
- separate persisted settings from transient UI-only state
- make serialization/deserialization explicit and versionable

### 5. Expand tests around use-cases and integration seams

Current tests mainly cover service-layer functions.

Next additions:

- project open/save integration tests
- reshape/filter workflow tests
- regression result serialization tests
- plot request to prepared-data integration tests

### 6. Review remaining dead code and duplication

Examples to inspect:

- duplicate window setup patterns
- handler methods that still mix UI and data mutations
- methods in `MainWindow` that could move into a controller/use-case

## Practical Next Starting Point

If work resumes, start here:

1. Add a small application layer under `calcite/application/`.
2. Move child-window creation into one shared helper/use-case.
3. Move project open/save orchestration out of `ActionHandler`.
4. Reduce `MainWindow` mutable state by introducing a focused state object.
