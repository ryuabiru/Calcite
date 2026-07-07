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
    headers: Vec<String>,
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
            headers: project.data_table.headers.clone(),
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
            set_row_filter,
            set_columns,
            restructure_data,
            pivot_data,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Calcite Tauri app");
}
