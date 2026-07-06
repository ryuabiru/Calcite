use std::path::{Path, PathBuf};

#[derive(Clone, Debug, Default)]
pub struct DataTable {
    pub headers: Vec<String>,
    pub rows: Vec<Vec<String>>,
}

impl DataTable {
    pub fn row_count(&self) -> usize {
        self.rows.len()
    }

    pub fn column_count(&self) -> usize {
        self.headers.len()
    }

    pub fn is_empty(&self) -> bool {
        self.headers.is_empty()
    }

    pub fn preview_rows(&self, limit: usize) -> impl Iterator<Item = &[String]> {
        self.rows.iter().take(limit).map(Vec::as_slice)
    }
}

#[derive(Clone, Debug, Default)]
pub struct ProjectState {
    pub loaded_file_path: Option<PathBuf>,
    pub current_graph_type: String,
    pub x_column: String,
    pub y_column: String,
    pub subgroup_column: String,
    pub data_table: DataTable,
    pub results_preview: String,
    pub status_message: String,
}

impl ProjectState {
    pub fn new() -> Self {
        Self {
            current_graph_type: "Scatter Plot".to_owned(),
            results_preview: "Rust bootstrap shell\n\nThis panel will eventually show statistical outputs and analysis summaries.".to_owned(),
            status_message: "Ready".to_owned(),
            ..Default::default()
        }
    }

    pub fn set_loaded_table(&mut self, path: PathBuf, table: DataTable) {
        self.loaded_file_path = Some(path);
        self.data_table = table;
        self.status_message = "CSV loaded".to_owned();
    }

    pub fn loaded_file_name(&self) -> Option<String> {
        self.loaded_file_path
            .as_ref()
            .and_then(|path| path.file_name())
            .and_then(|name| name.to_str())
            .map(|name| name.to_owned())
    }

    pub fn open_csv_path(&mut self, path: impl AsRef<Path>) -> Result<(), String> {
        let path = path.as_ref();
        let table = load_csv_table(path)?;
        self.set_loaded_table(path.to_path_buf(), table);
        Ok(())
    }

    pub fn set_graph_type(&mut self, graph_type: impl Into<String>) {
        self.current_graph_type = graph_type.into();
    }
}

pub fn load_csv_table(path: impl AsRef<Path>) -> Result<DataTable, String> {
    let path = path.as_ref();
    let mut reader = csv::Reader::from_path(path)
        .map_err(|error| format!("Failed to open CSV '{}': {error}", path.display()))?;

    let headers = reader
        .headers()
        .map_err(|error| format!("Failed to read CSV headers '{}': {error}", path.display()))?
        .iter()
        .map(|value| value.to_owned())
        .collect::<Vec<_>>();

    let mut rows = Vec::new();
    for record in reader.records() {
        let record = record
            .map_err(|error| format!("Failed to read CSV row '{}': {error}", path.display()))?;
        rows.push(record.iter().map(|value| value.to_owned()).collect());
    }

    Ok(DataTable { headers, rows })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn load_csv_table_reads_headers_and_rows() {
        let path =
            std::env::temp_dir().join(format!("calcite_rust_test_{}.csv", std::process::id()));
        fs::write(&path, "name,value\nA,1\nB,2\n").expect("write temp csv");

        let table = load_csv_table(&path).expect("load csv table");

        assert_eq!(table.headers, vec!["name", "value"]);
        assert_eq!(table.rows.len(), 2);
        assert_eq!(table.rows[0], vec!["A", "1"]);
        assert_eq!(table.rows[1], vec!["B", "2"]);

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn project_state_reports_loaded_file_name() {
        let mut state = ProjectState::new();
        state.set_loaded_table(PathBuf::from("/tmp/example.csv"), DataTable::default());

        assert_eq!(state.loaded_file_name().as_deref(), Some("example.csv"));
    }
}
