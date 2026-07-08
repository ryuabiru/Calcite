use std::sync::Mutex;

use calcite_rust::backend::AppBackend;
use calcite_rust::core::{AppCommand, FilterCondition};
use rfd::FileDialog;
use serde::Serialize;
use tauri::State;

struct SharedBackend(Mutex<AppBackend>);

#[derive(Clone, Serialize)]
struct BackendSnapshot {
    status_message: String,
    results_preview: String,
    current_graph_type: String,
    loaded_file_name: Option<String>,
    loaded_file_path: Option<String>,
    row_count: usize,
    column_count: usize,
    x_column: String,
    y_column: String,
    subgroup_column: String,
    y_log_scale: bool,
    row_filter_query: String,
    visible_row_count: usize,
    selected_row_count: usize,
    selected_row_indices: Vec<usize>,
    graph_annotation_summary: String,
    sort_column: Option<usize>,
    sort_ascending: bool,
    visible_row_indices: Vec<usize>,
    headers: Vec<String>,
    rows: Vec<Vec<String>>,
}

impl BackendSnapshot {
    fn from_backend(backend: &AppBackend) -> Self {
        let project = backend.project();
        Self {
            status_message: project.status_message.clone(),
            results_preview: project.results_preview.clone(),
            current_graph_type: project.current_graph_type.clone(),
            loaded_file_name: project.loaded_file_name(),
            loaded_file_path: project
                .loaded_file_path
                .as_ref()
                .map(|path| path.display().to_string()),
            row_count: project.data_table.row_count(),
            column_count: project.data_table.column_count(),
            x_column: project.x_column.clone(),
            y_column: project.y_column.clone(),
            subgroup_column: project.subgroup_column.clone(),
            y_log_scale: project.y_log_scale,
            row_filter_query: project.table_view.row_filter_query.clone(),
            visible_row_count: project.table_view.visible_row_indices.len(),
            selected_row_count: project.table_view.selected_rows.len(),
            selected_row_indices: project.table_view.selected_rows.iter().copied().collect(),
            graph_annotation_summary: project.graph_annotation_summary.clone(),
            sort_column: project.table_view.sort_column,
            sort_ascending: project.table_view.sort_ascending,
            visible_row_indices: project.table_view.visible_row_indices.clone(),
            headers: project.data_table.headers.clone(),
            rows: project.data_table.rows.clone(),
        }
    }
}

#[tauri::command]
fn get_snapshot(state: State<'_, SharedBackend>) -> Result<BackendSnapshot, String> {
    let backend = state
        .0
        .lock()
        .map_err(|_| "backend state is poisoned".to_owned())?;
    Ok(BackendSnapshot::from_backend(&backend))
}

#[tauri::command]
fn dispatch_command(state: State<'_, SharedBackend>, command: AppCommand) -> Result<(), String> {
    let mut backend = state
        .0
        .lock()
        .map_err(|_| "backend state is poisoned".to_owned())?;
    backend.dispatch(command)
}

#[tauri::command]
fn load_csv(state: State<'_, SharedBackend>, path: String) -> Result<(), String> {
    dispatch_command(state, AppCommand::LoadCsv { path: path.into() })
}

#[tauri::command]
fn pick_csv_path() -> Result<Option<String>, String> {
    Ok(FileDialog::new()
        .add_filter("CSV", &["csv"])
        .pick_file()
        .map(|path| path.display().to_string()))
}

#[tauri::command]
fn pick_project_directory() -> Result<Option<String>, String> {
    Ok(FileDialog::new()
        .pick_folder()
        .map(|path| path.display().to_string()))
}

#[tauri::command]
fn pick_export_csv_path() -> Result<Option<String>, String> {
    Ok(FileDialog::new()
        .add_filter("CSV", &["csv"])
        .set_file_name("calcite-export.csv")
        .save_file()
        .map(|path| path.display().to_string()))
}

#[tauri::command]
fn import_delimited_text(
    state: State<'_, SharedBackend>,
    text: String,
    source_label: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::ImportDelimitedText { text, source_label },
    )
}

#[tauri::command]
fn calculate_new_column(
    state: State<'_, SharedBackend>,
    name: String,
    formula: String,
) -> Result<(), String> {
    dispatch_command(state, AppCommand::CalculateNewColumn { name, formula })
}

#[tauri::command]
fn set_advanced_row_filter(
    state: State<'_, SharedBackend>,
    conditions: Vec<FilterCondition>,
) -> Result<(), String> {
    dispatch_command(state, AppCommand::SetAdvancedRowFilter { conditions })
}

#[tauri::command]
fn paste_delimited_text(
    state: State<'_, SharedBackend>,
    text: String,
    start_row: usize,
) -> Result<(), String> {
    dispatch_command(state, AppCommand::PasteDelimitedText { text, start_row })
}

#[tauri::command]
fn export_csv(state: State<'_, SharedBackend>, path: String) -> Result<(), String> {
    dispatch_command(state, AppCommand::ExportCsv { path: path.into() })
}

#[tauri::command]
fn edit_cell(
    state: State<'_, SharedBackend>,
    row_index: usize,
    column_index: usize,
    value: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::EditCell {
            row_index,
            column_index,
            value,
        },
    )
}

#[tauri::command]
fn insert_row(state: State<'_, SharedBackend>, row_index: usize) -> Result<(), String> {
    dispatch_command(state, AppCommand::InsertRow { row_index })
}

#[tauri::command]
fn remove_row(state: State<'_, SharedBackend>, row_index: usize) -> Result<(), String> {
    dispatch_command(state, AppCommand::RemoveRow { row_index })
}

#[tauri::command]
fn insert_column(
    state: State<'_, SharedBackend>,
    column_index: usize,
    name: String,
) -> Result<(), String> {
    dispatch_command(state, AppCommand::InsertColumn { column_index, name })
}

#[tauri::command]
fn rename_column(
    state: State<'_, SharedBackend>,
    column_index: usize,
    name: String,
) -> Result<(), String> {
    dispatch_command(state, AppCommand::RenameColumn { column_index, name })
}

#[tauri::command]
fn remove_column(state: State<'_, SharedBackend>, column_index: usize) -> Result<(), String> {
    dispatch_command(state, AppCommand::RemoveColumn { column_index })
}

#[tauri::command]
fn toggle_row_selection(state: State<'_, SharedBackend>, row_index: usize) -> Result<(), String> {
    dispatch_command(state, AppCommand::ToggleRowSelection { row_index })
}

#[tauri::command]
fn fill_down_selection(state: State<'_, SharedBackend>) -> Result<(), String> {
    dispatch_command(state, AppCommand::FillDownSelection)
}

#[tauri::command]
fn save_project(state: State<'_, SharedBackend>, directory: String) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::SaveProject {
            directory: directory.into(),
        },
    )
}

#[tauri::command]
fn load_project(state: State<'_, SharedBackend>, directory: String) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::LoadProject {
            directory: directory.into(),
        },
    )
}

#[tauri::command]
fn set_graph_type(state: State<'_, SharedBackend>, graph_type: String) -> Result<(), String> {
    dispatch_command(state, AppCommand::SetGraphType { graph_type })
}

#[tauri::command]
fn set_y_log_scale(state: State<'_, SharedBackend>, enabled: bool) -> Result<(), String> {
    dispatch_command(state, AppCommand::SetYLogScale { enabled })
}

#[tauri::command]
fn toggle_sort_by_column(state: State<'_, SharedBackend>, column_index: usize) -> Result<(), String> {
    dispatch_command(state, AppCommand::ToggleSortByColumn { column_index })
}

#[tauri::command]
fn set_row_filter(state: State<'_, SharedBackend>, query: String) -> Result<(), String> {
    dispatch_command(state, AppCommand::SetRowFilter { query })
}

#[tauri::command]
fn set_columns(
    state: State<'_, SharedBackend>,
    x_column: String,
    y_column: String,
    subgroup_column: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::SetColumns {
            x_column,
            y_column,
            subgroup_column,
        },
    )
}

#[tauri::command]
fn run_pearson_correlation_analysis(
    state: State<'_, SharedBackend>,
    col1: String,
    col2: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunPearsonCorrelationAnalysis { col1, col2 },
    )
}

#[tauri::command]
fn run_spearman_correlation_analysis(
    state: State<'_, SharedBackend>,
    col1: String,
    col2: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunSpearmanCorrelationAnalysis { col1, col2 },
    )
}

#[tauri::command]
fn run_independent_t_test_analysis(
    state: State<'_, SharedBackend>,
    col1: String,
    col2: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunIndependentTTestAnalysis { col1, col2 },
    )
}

#[tauri::command]
fn run_paired_t_test_analysis(
    state: State<'_, SharedBackend>,
    col1: String,
    col2: String,
) -> Result<(), String> {
    dispatch_command(state, AppCommand::RunPairedTTestAnalysis { col1, col2 })
}

#[tauri::command]
fn run_one_way_anova_analysis(
    state: State<'_, SharedBackend>,
    group_col: String,
    value_col: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunOneWayAnovaAnalysis {
            group_col,
            value_col,
        },
    )
}

#[tauri::command]
fn run_tukey_hsd_analysis(
    state: State<'_, SharedBackend>,
    group_col: String,
    value_col: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunTukeyHsdAnalysis {
            group_col,
            value_col,
        },
    )
}

#[tauri::command]
fn run_shapiro_wilk_analysis(
    state: State<'_, SharedBackend>,
    group_col: String,
    value_col: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunShapiroWilkAnalysis {
            group_col,
            value_col,
        },
    )
}

#[tauri::command]
fn run_mann_whitney_u_analysis(
    state: State<'_, SharedBackend>,
    col1: String,
    col2: String,
) -> Result<(), String> {
    dispatch_command(state, AppCommand::RunMannWhitneyUAnalysis { col1, col2 })
}

#[tauri::command]
fn run_wilcoxon_signed_rank_analysis(
    state: State<'_, SharedBackend>,
    col1: String,
    col2: String,
) -> Result<(), String> {
    dispatch_command(state, AppCommand::RunWilcoxonSignedRankAnalysis { col1, col2 })
}

#[tauri::command]
fn run_kruskal_wallis_analysis(
    state: State<'_, SharedBackend>,
    group_col: String,
    value_col: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunKruskalWallisAnalysis {
            group_col,
            value_col,
        },
    )
}

#[tauri::command]
fn run_dunn_post_hoc_analysis(
    state: State<'_, SharedBackend>,
    group_col: String,
    value_col: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunDunnPostHocAnalysis {
            group_col,
            value_col,
        },
    )
}

#[tauri::command]
fn run_linear_regression_analysis(
    state: State<'_, SharedBackend>,
    col1: String,
    col2: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunLinearRegressionAnalysis { col1, col2 },
    )
}

#[tauri::command]
fn run_four_pl_regression_analysis(
    state: State<'_, SharedBackend>,
    col1: String,
    col2: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunFourPlRegressionAnalysis { col1, col2 },
    )
}

#[tauri::command]
fn run_two_proportion_analysis(
    state: State<'_, SharedBackend>,
    rows_col: String,
    cols_col: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunTwoProportionAnalysis { rows_col, cols_col },
    )
}

#[tauri::command]
fn run_chi_squared_analysis(
    state: State<'_, SharedBackend>,
    rows_col: String,
    cols_col: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RunChiSquaredAnalysis { rows_col, cols_col },
    )
}

#[tauri::command]
fn restructure_data(
    state: State<'_, SharedBackend>,
    id_vars: Vec<String>,
    value_vars: Vec<String>,
    var_name: String,
    value_name: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::RestructureData {
            id_vars,
            value_vars,
            var_name,
            value_name,
        },
    )
}

#[tauri::command]
fn pivot_data(
    state: State<'_, SharedBackend>,
    id_vars: Vec<String>,
    var_name: String,
    value_name: String,
) -> Result<(), String> {
    dispatch_command(
        state,
        AppCommand::PivotData {
            id_vars,
            var_name,
            value_name,
        },
    )
}

fn main() {
    tauri::Builder::default()
        .manage(SharedBackend(Mutex::new(AppBackend::new())))
        .invoke_handler(tauri::generate_handler![
            get_snapshot,
            load_csv,
            pick_csv_path,
            pick_project_directory,
            pick_export_csv_path,
            import_delimited_text,
            calculate_new_column,
            set_advanced_row_filter,
            paste_delimited_text,
            export_csv,
            edit_cell,
            insert_row,
            remove_row,
            insert_column,
            rename_column,
            remove_column,
            toggle_row_selection,
            fill_down_selection,
            save_project,
            load_project,
            set_graph_type,
            set_y_log_scale,
            toggle_sort_by_column,
            set_row_filter,
            set_columns,
            run_pearson_correlation_analysis,
            run_spearman_correlation_analysis,
            run_independent_t_test_analysis,
            run_paired_t_test_analysis,
            run_one_way_anova_analysis,
            run_tukey_hsd_analysis,
            run_shapiro_wilk_analysis,
            run_mann_whitney_u_analysis,
            run_wilcoxon_signed_rank_analysis,
            run_kruskal_wallis_analysis,
            run_dunn_post_hoc_analysis,
            run_linear_regression_analysis,
            run_four_pl_regression_analysis,
            run_two_proportion_analysis,
            run_chi_squared_analysis,
            restructure_data,
            pivot_data,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Calcite Tauri app");
}
