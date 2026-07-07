use std::sync::Mutex;

use calcite_rust::backend::AppBackend;
use calcite_rust::core::AppCommand;
use serde::Serialize;
use tauri::State;

struct SharedBackend(Mutex<AppBackend>);

#[derive(Clone, Serialize)]
struct BackendSnapshot {
    status_message: String,
    results_preview: String,
    current_graph_type: String,
    loaded_file_name: Option<String>,
    row_count: usize,
    column_count: usize,
    x_column: String,
    y_column: String,
    subgroup_column: String,
    row_filter_query: String,
    visible_row_count: usize,
    selected_row_count: usize,
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
            row_count: project.data_table.row_count(),
            column_count: project.data_table.column_count(),
            x_column: project.x_column.clone(),
            y_column: project.y_column.clone(),
            subgroup_column: project.subgroup_column.clone(),
            row_filter_query: project.table_view.row_filter_query.clone(),
            visible_row_count: project.table_view.visible_row_indices.len(),
            selected_row_count: project.table_view.selected_rows.len(),
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
fn remove_column(state: State<'_, SharedBackend>, column_index: usize) -> Result<(), String> {
    dispatch_command(state, AppCommand::RemoveColumn { column_index })
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
            import_delimited_text,
            export_csv,
            edit_cell,
            insert_row,
            remove_row,
            insert_column,
            remove_column,
            save_project,
            load_project,
            set_graph_type,
            toggle_sort_by_column,
            set_row_filter,
            set_columns,
            run_pearson_correlation_analysis,
            run_spearman_correlation_analysis,
            run_independent_t_test_analysis,
            run_paired_t_test_analysis,
            run_one_way_anova_analysis,
            run_shapiro_wilk_analysis,
            run_mann_whitney_u_analysis,
            run_wilcoxon_signed_rank_analysis,
            run_kruskal_wallis_analysis,
            run_linear_regression_analysis,
            run_four_pl_regression_analysis,
            run_two_proportion_analysis,
            restructure_data,
            pivot_data,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Calcite Tauri app");
}
