use std::path::PathBuf;

use crate::core::AppCommand;
use crate::state::ProjectState;

#[derive(Debug, Default)]
pub struct AppBackend {
    project: ProjectState,
}

impl AppBackend {
    pub fn new() -> Self {
        Self {
            project: ProjectState::new(),
        }
    }

    pub fn project(&self) -> &ProjectState {
        &self.project
    }

    pub fn project_mut(&mut self) -> &mut ProjectState {
        &mut self.project
    }

    pub fn dispatch(&mut self, command: AppCommand) -> Result<(), String> {
        match command {
            AppCommand::LoadCsv { path } => self.load_csv(path),
            AppCommand::SetGraphType { graph_type } => {
                self.project.set_graph_type(graph_type);
                Ok(())
            }
            AppCommand::ToggleSortByColumn { column_index } => {
                self.project.toggle_sort_by_column(column_index)
            }
            AppCommand::ToggleRowSelection { row_index } => {
                self.project.toggle_row_selection(row_index);
                Ok(())
            }
            AppCommand::SetColumns {
                x_column,
                y_column,
                subgroup_column,
            } => {
                self.project.x_column = x_column;
                self.project.y_column = y_column;
                self.project.subgroup_column = subgroup_column;
                Ok(())
            }
        }
    }

    fn load_csv(&mut self, path: PathBuf) -> Result<(), String> {
        match self.project.open_csv_path(&path) {
            Ok(()) => {
                let status = build_csv_load_status(&self.project, &path);
                let summary = build_csv_load_summary(&self.project, &path);
                self.project.status_message = status;
                self.project.results_preview = summary;
                Ok(())
            }
            Err(error) => {
                let status = build_csv_load_error_status(&path);
                let summary = build_csv_load_error_summary(&path, &error);
                self.project.status_message = status;
                self.project.results_preview = summary.clone();
                Err(summary)
            }
        }
    }
}

fn build_csv_load_summary(project: &ProjectState, path: &PathBuf) -> String {
    let file_name = path_label(path);
    let table = &project.data_table;
    let mut lines = vec![
        format!("Loaded {file_name}"),
        String::new(),
        format!("Rows: {}", table.row_count()),
        format!("Columns: {}", table.column_count()),
    ];

    if let Some(first_column) = table.column_metadata().first() {
        lines.push(format!("First column: {}", first_column.name));
        lines.push(format!(
            "Detected type: {}",
            column_kind_label(&first_column.kind)
        ));
    }

    lines.join("\n")
}

fn build_csv_load_status(project: &ProjectState, path: &PathBuf) -> String {
    let file_name = path_label(path);
    format!(
        "Loaded {file_name} ({} rows, {} columns)",
        project.data_table.row_count(),
        project.data_table.column_count()
    )
}

fn build_csv_load_error_status(path: &PathBuf) -> String {
    format!("Failed to load {}", path_label(path))
}

fn build_csv_load_error_summary(path: &PathBuf, error: &str) -> String {
    format!("Failed to load CSV '{}': {error}", path.display())
}

fn column_kind_label(kind: &crate::state::ColumnKind) -> &'static str {
    match kind {
        crate::state::ColumnKind::Empty => "empty",
        crate::state::ColumnKind::Numeric => "numeric",
        crate::state::ColumnKind::Text => "text",
        crate::state::ColumnKind::Mixed => "mixed",
    }
}

fn path_label(path: &PathBuf) -> String {
    path.file_name()
        .and_then(|name| name.to_str())
        .map(|name| name.to_owned())
        .unwrap_or_else(|| path.display().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn load_csv_sets_concise_status_and_detailed_summary() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_test.csv");
        fs::write(&path, "name,value\nA,1\nB,2\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");

        assert_eq!(
            backend.project().status_message,
            "Loaded calcite_rust_backend_test.csv (2 rows, 2 columns)"
        );
        assert!(backend.project().results_preview.contains("Rows: 2"));
        assert!(
            backend
                .project()
                .results_preview
                .contains("First column: name")
        );
        assert!(
            backend
                .project()
                .results_preview
                .contains("Detected type: text")
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn load_csv_failure_keeps_error_detail_in_results() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("missing_calcite_rust.csv");

        let result = backend.dispatch(AppCommand::LoadCsv { path: path.clone() });

        assert!(result.is_err());
        assert_eq!(
            backend.project().status_message,
            "Failed to load missing_calcite_rust.csv"
        );
        assert!(
            backend
                .project()
                .results_preview
                .contains("Failed to load CSV")
        );
    }
}
