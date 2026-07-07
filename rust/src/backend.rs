use std::path::PathBuf;

use crate::core::AppCommand;
use crate::project_persistence::{load_project_directory, save_project_directory};
use crate::state::ProjectState;
use crate::transform::{pivot_dataframe, restructure_dataframe};

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
            AppCommand::ImportDelimitedText { text, source_label } => {
                self.import_delimited_text(text, source_label)
            }
            AppCommand::ExportCsv { path } => self.export_csv(path),
            AppCommand::SaveProject { directory } => self.save_project(directory),
            AppCommand::LoadProject { directory } => self.load_project(directory),
            AppCommand::RestructureData {
                id_vars,
                value_vars,
                var_name,
                value_name,
            } => self.restructure_data(id_vars, value_vars, var_name, value_name),
            AppCommand::PivotData {
                id_vars,
                var_name,
                value_name,
            } => self.pivot_data(id_vars, var_name, value_name),
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
            AppCommand::SetRowFilter { query } => {
                self.project.set_row_filter(query);
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
            AppCommand::EditCell {
                row_index,
                column_index,
                value,
            } => self.edit_cell(row_index, column_index, value),
            AppCommand::InsertRow { row_index } => self.insert_row(row_index),
            AppCommand::RemoveRow { row_index } => self.remove_row(row_index),
            AppCommand::InsertColumn { column_index, name } => {
                self.insert_column(column_index, name)
            }
            AppCommand::RemoveColumn { column_index } => self.remove_column(column_index),
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

    fn import_delimited_text(&mut self, text: String, source_label: String) -> Result<(), String> {
        self.project.import_delimited_text(&text, &source_label)?;
        Ok(())
    }

    fn export_csv(&mut self, path: PathBuf) -> Result<(), String> {
        self.project.export_csv_path(&path)?;
        self.project.status_message = format!("Exported CSV to {}", path.display());
        self.project.results_preview = format!(
            "Exported {} rows and {} columns",
            self.project.data_table.row_count(),
            self.project.data_table.column_count()
        );
        Ok(())
    }

    fn save_project(&mut self, directory: PathBuf) -> Result<(), String> {
        save_project_directory(&directory, &self.project)?;
        self.project.status_message = format!("Project saved to {}", directory.display());
        self.project.results_preview = format!(
            "Saved project snapshot with {} rows and {} columns",
            self.project.data_table.row_count(),
            self.project.data_table.column_count()
        );
        Ok(())
    }

    fn load_project(&mut self, directory: PathBuf) -> Result<(), String> {
        let snapshot = load_project_directory(&directory)?;
        self.project = ProjectState::from(snapshot);
        self.project.status_message = format!("Project loaded from {}", directory.display());
        self.project.results_preview = format!(
            "Loaded project snapshot with {} rows and {} columns",
            self.project.data_table.row_count(),
            self.project.data_table.column_count()
        );
        Ok(())
    }

    fn restructure_data(
        &mut self,
        id_vars: Vec<String>,
        value_vars: Vec<String>,
        var_name: String,
        value_name: String,
    ) -> Result<(), String> {
        let table = if self.project.data_table.is_empty() {
            return Err("No CSV loaded".to_owned());
        } else {
            &self.project.data_table
        };

        let new_table =
            restructure_dataframe(table, &id_vars, &value_vars, &var_name, &value_name)?;
        self.project.replace_data_table(new_table);
        self.project.status_message = format!(
            "Restructured data using {} id column(s) and {} value column(s)",
            id_vars.len(),
            value_vars.len()
        );
        self.project.results_preview = format!(
            "Restructured into {} rows and {} columns",
            self.project.data_table.row_count(),
            self.project.data_table.column_count()
        );
        Ok(())
    }

    fn pivot_data(
        &mut self,
        id_vars: Vec<String>,
        var_name: String,
        value_name: String,
    ) -> Result<(), String> {
        let table = if self.project.data_table.is_empty() {
            return Err("No CSV loaded".to_owned());
        } else {
            &self.project.data_table
        };

        let new_table = pivot_dataframe(table, &id_vars, &var_name, &value_name)?;
        self.project.replace_data_table(new_table);
        self.project.status_message = format!("Pivoted data with {} id column(s)", id_vars.len());
        self.project.results_preview = format!(
            "Pivoted into {} rows and {} columns",
            self.project.data_table.row_count(),
            self.project.data_table.column_count()
        );
        Ok(())
    }

    fn edit_cell(
        &mut self,
        row_index: usize,
        column_index: usize,
        value: String,
    ) -> Result<(), String> {
        self.project.edit_cell(row_index, column_index, value)?;
        self.project.results_preview = format!(
            "Edited cell in row {} column {}",
            row_index + 1,
            column_index + 1
        );
        Ok(())
    }

    fn insert_row(&mut self, row_index: usize) -> Result<(), String> {
        self.project.insert_row(row_index)?;
        self.project.results_preview = format!(
            "Inserted row {} ({} rows total)",
            row_index + 1,
            self.project.data_table.row_count()
        );
        Ok(())
    }

    fn remove_row(&mut self, row_index: usize) -> Result<(), String> {
        self.project.remove_row(row_index)?;
        self.project.results_preview = format!(
            "Removed row {} ({} rows total)",
            row_index + 1,
            self.project.data_table.row_count()
        );
        Ok(())
    }

    fn insert_column(&mut self, column_index: usize, name: String) -> Result<(), String> {
        self.project.insert_column(column_index, name.clone())?;
        self.project.results_preview =
            format!("Inserted column {name} at position {}", column_index + 1);
        Ok(())
    }

    fn remove_column(&mut self, column_index: usize) -> Result<(), String> {
        self.project.remove_column(column_index)?;
        self.project.results_preview = format!(
            "Removed column {} ({} columns total)",
            column_index + 1,
            self.project.data_table.column_count()
        );
        Ok(())
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

    #[test]
    fn set_row_filter_updates_visible_rows_and_status() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_filter_test.csv");
        fs::write(&path, "name,value\nAlpha,1\nbeta,2\nGamma,3\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::SetRowFilter {
                query: "beta".to_owned(),
            })
            .expect("set row filter");

        assert_eq!(backend.project().table_view.visible_row_indices, vec![1]);
        assert_eq!(backend.project().status_message, "Filtered 1 of 3 rows");

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn restructure_data_creates_long_format_table() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_restructure_test.csv");
        fs::write(&path, "id,left,right\nA,1,2\nB,3,4\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RestructureData {
                id_vars: vec!["id".to_owned()],
                value_vars: vec!["left".to_owned(), "right".to_owned()],
                var_name: "kind".to_owned(),
                value_name: "amount".to_owned(),
            })
            .expect("restructure data");

        assert_eq!(
            backend.project().data_table.headers,
            vec!["id", "kind", "amount"]
        );
        assert_eq!(backend.project().data_table.rows.len(), 4);
        assert_eq!(backend.project().data_table.rows[0], vec!["A", "left", "1"]);
        assert_eq!(
            backend.project().status_message,
            "Restructured data using 1 id column(s) and 2 value column(s)"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn pivot_data_creates_wide_format_table() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_pivot_test.csv");
        fs::write(
            &path,
            "id,kind,amount\nA,left,1\nA,right,2\nB,left,3\nB,right,5\nB,right,7\n",
        )
        .expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::PivotData {
                id_vars: vec!["id".to_owned()],
                var_name: "kind".to_owned(),
                value_name: "amount".to_owned(),
            })
            .expect("pivot data");

        assert_eq!(
            backend.project().data_table.headers,
            vec!["id", "left", "right"]
        );
        assert_eq!(backend.project().data_table.rows.len(), 2);
        assert_eq!(backend.project().data_table.rows[0], vec!["A", "1", "2"]);
        assert_eq!(backend.project().data_table.rows[1], vec!["B", "3", "6"]);
        assert_eq!(
            backend.project().status_message,
            "Pivoted data with 1 id column(s)"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn save_and_load_project_directory_round_trips_state() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_project_roundtrip");
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).expect("create temp dir");
        fs::write(path.join("input.csv"), "name,value\nA,1\nB,2\n").expect("write csv");

        backend
            .dispatch(AppCommand::LoadCsv {
                path: path.join("input.csv"),
            })
            .expect("load csv");
        backend
            .dispatch(AppCommand::SetRowFilter {
                query: "A".to_owned(),
            })
            .expect("set filter");
        backend
            .dispatch(AppCommand::SaveProject {
                directory: path.clone(),
            })
            .expect("save project");

        let mut restored = AppBackend::new();
        restored
            .dispatch(AppCommand::LoadProject {
                directory: path.clone(),
            })
            .expect("load project");

        assert_eq!(restored.project().data_table.headers, vec!["name", "value"]);
        assert_eq!(restored.project().table_view.row_filter_query, "A");
        assert_eq!(
            restored.project().status_message,
            format!("Project loaded from {}", path.display())
        );

        let _ = fs::remove_dir_all(&path);
    }

    #[test]
    fn import_delimited_text_updates_table_state() {
        let mut backend = AppBackend::new();

        backend
            .dispatch(AppCommand::ImportDelimitedText {
                text: "name\tvalue\nA\t1\nB\t2\n".to_owned(),
                source_label: "clipboard".to_owned(),
            })
            .expect("import text");

        assert_eq!(backend.project().data_table.headers, vec!["name", "value"]);
        assert_eq!(
            backend.project().status_message,
            "Imported clipboard (2 rows, 2 columns)"
        );
    }

    #[test]
    fn export_csv_writes_current_table() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_export_backend_test.csv");
        backend
            .project_mut()
            .replace_data_table(crate::state::DataTable::from_rows(
                vec!["name".to_owned(), "value".to_owned()],
                vec![
                    vec!["A".to_owned(), "1".to_owned()],
                    vec!["B".to_owned(), "2".to_owned()],
                ],
            ));

        backend
            .dispatch(AppCommand::ExportCsv { path: path.clone() })
            .expect("export csv");

        let exported = fs::read_to_string(&path).expect("read exported csv");
        assert!(exported.contains("name,value"));
        assert!(exported.contains("A,1"));
        assert!(exported.contains("B,2"));

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn edit_insert_and_remove_table_structure() {
        let mut backend = AppBackend::new();
        backend
            .project_mut()
            .replace_data_table(crate::state::DataTable::from_rows(
                vec!["name".to_owned(), "value".to_owned()],
                vec![
                    vec!["A".to_owned(), "1".to_owned()],
                    vec!["B".to_owned(), "2".to_owned()],
                ],
            ));

        backend
            .dispatch(AppCommand::EditCell {
                row_index: 0,
                column_index: 1,
                value: "10".to_owned(),
            })
            .expect("edit cell");
        assert_eq!(backend.project().data_table.rows[0][1], "10");

        backend
            .dispatch(AppCommand::InsertRow { row_index: 1 })
            .expect("insert row");
        assert_eq!(backend.project().data_table.row_count(), 3);

        backend
            .dispatch(AppCommand::InsertColumn {
                column_index: 1,
                name: "group".to_owned(),
            })
            .expect("insert column");
        assert_eq!(
            backend.project().data_table.headers,
            vec!["name", "group", "value"]
        );

        backend
            .dispatch(AppCommand::RemoveRow { row_index: 1 })
            .expect("remove row");
        assert_eq!(backend.project().data_table.row_count(), 2);

        backend
            .dispatch(AppCommand::RemoveColumn { column_index: 1 })
            .expect("remove column");
        assert_eq!(backend.project().data_table.headers, vec!["name", "value"]);
    }
}
