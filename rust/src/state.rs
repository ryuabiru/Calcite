use std::cmp::Ordering;
use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ColumnKind {
    Empty,
    Numeric,
    Text,
    Mixed,
}

#[derive(Clone, Debug)]
pub struct ColumnMetadata {
    pub index: usize,
    pub name: String,
    pub kind: ColumnKind,
    pub non_empty_count: usize,
    pub distinct_count: usize,
}

#[derive(Clone, Debug, Default)]
pub struct DataTable {
    pub headers: Vec<String>,
    pub rows: Vec<Vec<String>>,
    pub column_metadata: Vec<ColumnMetadata>,
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

    pub fn column_metadata(&self) -> &[ColumnMetadata] {
        &self.column_metadata
    }

    pub fn preview_rows(&self, limit: usize) -> impl Iterator<Item = &[String]> {
        self.rows.iter().take(limit).map(Vec::as_slice)
    }

    pub fn sort_by_column(&mut self, column_index: usize, ascending: bool) -> Result<(), String> {
        if column_index >= self.headers.len() {
            return Err(format!("Column index {column_index} is out of range"));
        }

        self.rows.sort_by(|left, right| {
            let left_value = left.get(column_index).map(String::as_str).unwrap_or("");
            let right_value = right.get(column_index).map(String::as_str).unwrap_or("");
            compare_cells(left_value, right_value)
        });

        if !ascending {
            self.rows.reverse();
        }

        Ok(())
    }
}

#[derive(Clone, Debug, Default)]
pub struct TableViewState {
    pub sort_column: Option<usize>,
    pub sort_ascending: bool,
    pub selected_rows: BTreeSet<usize>,
}

impl TableViewState {
    pub fn reset(&mut self) {
        self.sort_column = None;
        self.sort_ascending = true;
        self.selected_rows.clear();
    }

    pub fn toggle_row(&mut self, row_index: usize) {
        if !self.selected_rows.insert(row_index) {
            self.selected_rows.remove(&row_index);
        }
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
    pub table_view: TableViewState,
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
        self.table_view.reset();
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

    pub fn toggle_sort_by_column(&mut self, column_index: usize) -> Result<(), String> {
        let ascending = match self.table_view.sort_column {
            Some(current) if current == column_index => !self.table_view.sort_ascending,
            _ => true,
        };

        self.data_table.sort_by_column(column_index, ascending)?;
        self.table_view.sort_column = Some(column_index);
        self.table_view.sort_ascending = ascending;
        self.status_message = format!(
            "Sorted by {} ({})",
            self.data_table.headers[column_index],
            if ascending { "ascending" } else { "descending" }
        );
        Ok(())
    }

    pub fn toggle_row_selection(&mut self, row_index: usize) {
        self.table_view.toggle_row(row_index);
        self.status_message = if self.table_view.selected_rows.is_empty() {
            "Selection cleared".to_owned()
        } else {
            format!("Selected {} row(s)", self.table_view.selected_rows.len())
        };
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

    let column_metadata = build_column_metadata(&headers, &rows);

    Ok(DataTable {
        headers,
        rows,
        column_metadata,
    })
}

fn compare_cells(left: &str, right: &str) -> Ordering {
    match (left.parse::<f64>(), right.parse::<f64>()) {
        (Ok(left_number), Ok(right_number)) => left_number
            .partial_cmp(&right_number)
            .unwrap_or(Ordering::Equal),
        _ => left.cmp(right),
    }
}

fn build_column_metadata(headers: &[String], rows: &[Vec<String>]) -> Vec<ColumnMetadata> {
    headers
        .iter()
        .enumerate()
        .map(|(index, header)| {
            let mut non_empty_count = 0;
            let mut distinct_values = std::collections::BTreeSet::new();
            let mut saw_numeric = false;
            let mut saw_text = false;

            for row in rows {
                let value = row.get(index).map(String::as_str).unwrap_or("").trim();
                if value.is_empty() {
                    continue;
                }

                non_empty_count += 1;
                distinct_values.insert(value.to_owned());
                if value.parse::<f64>().is_ok() {
                    saw_numeric = true;
                } else {
                    saw_text = true;
                }
            }

            let kind = if non_empty_count == 0 {
                ColumnKind::Empty
            } else if saw_numeric && saw_text {
                ColumnKind::Mixed
            } else if saw_numeric {
                ColumnKind::Numeric
            } else {
                ColumnKind::Text
            };

            ColumnMetadata {
                index,
                name: header.clone(),
                kind,
                non_empty_count,
                distinct_count: distinct_values.len(),
            }
        })
        .collect()
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
        assert_eq!(table.column_metadata.len(), 2);
        assert_eq!(table.column_metadata[0].kind, ColumnKind::Text);
        assert_eq!(table.column_metadata[1].kind, ColumnKind::Numeric);
        assert_eq!(table.column_metadata[1].non_empty_count, 2);
        assert_eq!(table.column_metadata[1].distinct_count, 2);

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn project_state_reports_loaded_file_name() {
        let mut state = ProjectState::new();
        state.set_loaded_table(PathBuf::from("/tmp/example.csv"), DataTable::default());

        assert_eq!(state.loaded_file_name().as_deref(), Some("example.csv"));
    }

    #[test]
    fn data_table_sorts_numeric_columns_before_string_fallback() {
        let mut table = DataTable {
            headers: vec!["name".to_owned(), "value".to_owned()],
            rows: vec![
                vec!["beta".to_owned(), "10".to_owned()],
                vec!["alpha".to_owned(), "2".to_owned()],
                vec!["gamma".to_owned(), "3".to_owned()],
            ],
            column_metadata: vec![],
        };

        table.sort_by_column(1, true).expect("sort by column");

        assert_eq!(table.rows[0][0], "alpha");
        assert_eq!(table.rows[1][0], "gamma");
        assert_eq!(table.rows[2][0], "beta");
    }

    #[test]
    fn project_state_toggles_sort_and_row_selection() {
        let mut state = ProjectState::new();
        state.set_loaded_table(
            PathBuf::from("/tmp/example.csv"),
            DataTable {
                headers: vec!["name".to_owned(), "value".to_owned()],
                rows: vec![
                    vec!["beta".to_owned(), "10".to_owned()],
                    vec!["alpha".to_owned(), "2".to_owned()],
                ],
                column_metadata: vec![],
            },
        );

        state.toggle_sort_by_column(0).expect("sort by column");
        assert_eq!(state.data_table.rows[0][0], "alpha");
        assert_eq!(state.table_view.sort_column, Some(0));
        assert!(state.table_view.sort_ascending);

        state
            .toggle_sort_by_column(0)
            .expect("reverse sort by column");
        assert_eq!(state.data_table.rows[0][0], "beta");
        assert!(!state.table_view.sort_ascending);

        state.toggle_row_selection(1);
        assert!(state.table_view.selected_rows.contains(&1));
        state.toggle_row_selection(1);
        assert!(state.table_view.selected_rows.is_empty());
    }

    #[test]
    fn build_column_metadata_detects_mixed_and_empty_columns() {
        let headers = vec!["empty".to_owned(), "mixed".to_owned(), "numeric".to_owned()];
        let rows = vec![
            vec!["".to_owned(), "1".to_owned(), "10".to_owned()],
            vec!["".to_owned(), "A".to_owned(), "20".to_owned()],
            vec!["".to_owned(), "3".to_owned(), "30".to_owned()],
        ];

        let metadata = build_column_metadata(&headers, &rows);

        assert_eq!(metadata[0].kind, ColumnKind::Empty);
        assert_eq!(metadata[1].kind, ColumnKind::Mixed);
        assert_eq!(metadata[2].kind, ColumnKind::Numeric);
    }
}
