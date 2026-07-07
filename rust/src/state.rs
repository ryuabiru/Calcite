use std::cmp::Ordering;
use std::collections::BTreeSet;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ColumnKind {
    Empty,
    Numeric,
    Text,
    Mixed,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum HeatmapNormalizationMode {
    #[default]
    Count,
    Row,
    Column,
    Total,
}

impl HeatmapNormalizationMode {
    pub const ALL: [Self; 4] = [Self::Count, Self::Row, Self::Column, Self::Total];

    pub fn label(self) -> &'static str {
        match self {
            Self::Count => "Counts",
            Self::Row => "Row proportion",
            Self::Column => "Column proportion",
            Self::Total => "Overall proportion",
        }
    }

    pub fn normalized_suffix(self) -> &'static str {
        match self {
            Self::Count => "count",
            Self::Row => "row",
            Self::Column => "column",
            Self::Total => "total",
        }
    }
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
    pub fn from_rows(headers: Vec<String>, rows: Vec<Vec<String>>) -> Self {
        let column_metadata = build_column_metadata(&headers, &rows);
        Self {
            headers,
            rows,
            column_metadata,
        }
    }

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

    pub fn column_index(&self, name: &str) -> Option<usize> {
        self.headers.iter().position(|header| header == name)
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

    pub fn rebuild_column_metadata(&mut self) {
        self.column_metadata = build_column_metadata(&self.headers, &self.rows);
    }

    pub fn edit_cell(
        &mut self,
        row_index: usize,
        column_index: usize,
        value: String,
    ) -> Result<(), String> {
        let row = self
            .rows
            .get_mut(row_index)
            .ok_or_else(|| format!("Row index {row_index} is out of range"))?;
        let cell = row
            .get_mut(column_index)
            .ok_or_else(|| format!("Column index {column_index} is out of range"))?;
        *cell = value;
        self.rebuild_column_metadata();
        Ok(())
    }

    pub fn insert_row(&mut self, row_index: usize) -> Result<(), String> {
        if row_index > self.rows.len() {
            return Err(format!("Row index {row_index} is out of range"));
        }
        self.rows
            .insert(row_index, vec![String::new(); self.headers.len()]);
        self.rebuild_column_metadata();
        Ok(())
    }

    pub fn remove_row(&mut self, row_index: usize) -> Result<(), String> {
        if row_index >= self.rows.len() {
            return Err(format!("Row index {row_index} is out of range"));
        }
        self.rows.remove(row_index);
        self.rebuild_column_metadata();
        Ok(())
    }

    pub fn insert_column(&mut self, column_index: usize, name: String) -> Result<(), String> {
        if column_index > self.headers.len() {
            return Err(format!("Column index {column_index} is out of range"));
        }
        self.headers.insert(column_index, name);
        for row in &mut self.rows {
            row.insert(column_index, String::new());
        }
        self.rebuild_column_metadata();
        Ok(())
    }

    pub fn remove_column(&mut self, column_index: usize) -> Result<(), String> {
        if column_index >= self.headers.len() {
            return Err(format!("Column index {column_index} is out of range"));
        }
        self.headers.remove(column_index);
        for row in &mut self.rows {
            if column_index < row.len() {
                row.remove(column_index);
            }
        }
        self.rebuild_column_metadata();
        Ok(())
    }
}

#[derive(Clone, Debug, Default)]
pub struct TableViewState {
    pub sort_column: Option<usize>,
    pub sort_ascending: bool,
    pub selected_rows: BTreeSet<usize>,
    pub row_filter_query: String,
    pub visible_row_indices: Vec<usize>,
}

impl TableViewState {
    pub fn reset(&mut self) {
        self.sort_column = None;
        self.sort_ascending = true;
        self.selected_rows.clear();
        self.row_filter_query.clear();
        self.visible_row_indices.clear();
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
    pub heatmap_normalization_mode: HeatmapNormalizationMode,
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
        self.replace_data_table(table);
        self.status_message = "CSV loaded".to_owned();
    }

    pub fn from_persisted_snapshot(
        snapshot: crate::project_persistence::PersistedProjectState,
    ) -> Self {
        let table = DataTable::from_rows(snapshot.table.headers, snapshot.table.rows);
        let mut state = Self {
            loaded_file_path: snapshot.settings.loaded_file_path.map(PathBuf::from),
            current_graph_type: snapshot.settings.current_graph_type,
            x_column: snapshot.settings.x_column,
            y_column: snapshot.settings.y_column,
            subgroup_column: snapshot.settings.subgroup_column,
            heatmap_normalization_mode: snapshot.settings.heatmap_normalization,
            data_table: table,
            table_view: TableViewState {
                sort_column: snapshot.table_view.sort_column,
                sort_ascending: snapshot.table_view.sort_ascending,
                selected_rows: snapshot.table_view.selected_rows.into_iter().collect(),
                row_filter_query: snapshot.table_view.row_filter_query,
                visible_row_indices: Vec::new(),
            },
            results_preview: String::new(),
            status_message: "Project loaded".to_owned(),
        };
        state.refresh_visible_row_indices();
        state
    }

    pub fn replace_data_table(&mut self, table: DataTable) {
        self.data_table = table;
        self.table_view.reset();
        self.refresh_visible_row_indices();
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

    pub fn import_delimited_text(&mut self, text: &str, source_label: &str) -> Result<(), String> {
        let table = load_delimited_text_table(text)?;
        self.loaded_file_path = None;
        self.replace_data_table(table);
        self.status_message = format!(
            "Imported {source_label} ({} rows, {} columns)",
            self.data_table.row_count(),
            self.data_table.column_count()
        );
        self.results_preview = format!(
            "Imported data from {source_label}\n\nRows: {}\nColumns: {}",
            self.data_table.row_count(),
            self.data_table.column_count()
        );
        Ok(())
    }

    pub fn set_graph_type(&mut self, graph_type: impl Into<String>) {
        self.current_graph_type = graph_type.into();
    }

    pub fn edit_cell(
        &mut self,
        row_index: usize,
        column_index: usize,
        value: String,
    ) -> Result<(), String> {
        self.data_table.edit_cell(row_index, column_index, value)?;
        self.after_table_mutation();
        self.status_message = format!(
            "Edited cell at row {}, column {}",
            row_index + 1,
            column_index + 1
        );
        Ok(())
    }

    pub fn insert_row(&mut self, row_index: usize) -> Result<(), String> {
        self.data_table.insert_row(row_index)?;
        self.shift_row_selection_after_insert(row_index);
        self.after_table_mutation();
        self.status_message = format!("Inserted row {}", row_index + 1);
        Ok(())
    }

    pub fn remove_row(&mut self, row_index: usize) -> Result<(), String> {
        self.data_table.remove_row(row_index)?;
        self.shift_row_selection_after_remove(row_index);
        self.after_table_mutation();
        self.status_message = format!("Removed row {}", row_index + 1);
        Ok(())
    }

    pub fn insert_column(&mut self, column_index: usize, name: String) -> Result<(), String> {
        self.data_table.insert_column(column_index, name.clone())?;
        self.adjust_sort_column_after_insert(column_index);
        self.after_table_mutation();
        self.status_message = format!("Inserted column {} at {}", name, column_index + 1);
        Ok(())
    }

    pub fn remove_column(&mut self, column_index: usize) -> Result<(), String> {
        let removed_name = self
            .data_table
            .headers
            .get(column_index)
            .cloned()
            .ok_or_else(|| format!("Column index {column_index} is out of range"))?;
        self.data_table.remove_column(column_index)?;
        self.adjust_sort_column_after_remove(column_index);
        self.after_table_mutation();
        self.status_message = format!("Removed column {}", removed_name);
        Ok(())
    }

    pub fn toggle_sort_by_column(&mut self, column_index: usize) -> Result<(), String> {
        let ascending = match self.table_view.sort_column {
            Some(current) if current == column_index => !self.table_view.sort_ascending,
            _ => true,
        };

        self.data_table.sort_by_column(column_index, ascending)?;
        self.table_view.sort_column = Some(column_index);
        self.table_view.sort_ascending = ascending;
        self.refresh_visible_row_indices();
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

    pub fn set_row_filter(&mut self, query: impl Into<String>) {
        self.table_view.row_filter_query = query.into();
        self.refresh_visible_row_indices();
        self.status_message = if self.table_view.row_filter_query.is_empty() {
            format!(
                "Filter cleared ({} rows visible)",
                self.table_view.visible_row_indices.len()
            )
        } else {
            format!(
                "Filtered {} of {} rows",
                self.table_view.visible_row_indices.len(),
                self.data_table.row_count()
            )
        };
    }

    pub fn refresh_visible_row_indices(&mut self) {
        self.table_view.visible_row_indices = if self.data_table.is_empty() {
            Vec::new()
        } else {
            build_visible_row_indices(&self.data_table.rows, &self.table_view.row_filter_query)
        };
    }

    fn after_table_mutation(&mut self) {
        if let Some(sort_column) = self.table_view.sort_column {
            let _ = self
                .data_table
                .sort_by_column(sort_column, self.table_view.sort_ascending);
        }
        self.refresh_visible_row_indices();
    }

    fn shift_row_selection_after_insert(&mut self, row_index: usize) {
        self.table_view.selected_rows = self
            .table_view
            .selected_rows
            .iter()
            .map(|selected| {
                if *selected >= row_index {
                    *selected + 1
                } else {
                    *selected
                }
            })
            .collect();
    }

    fn shift_row_selection_after_remove(&mut self, row_index: usize) {
        self.table_view.selected_rows = self
            .table_view
            .selected_rows
            .iter()
            .filter_map(|selected| {
                if *selected == row_index {
                    None
                } else if *selected > row_index {
                    Some(selected - 1)
                } else {
                    Some(*selected)
                }
            })
            .collect();
    }

    fn adjust_sort_column_after_insert(&mut self, column_index: usize) {
        if let Some(sort_column) = self.table_view.sort_column
            && sort_column >= column_index
        {
            self.table_view.sort_column = Some(sort_column + 1);
        }
    }

    fn adjust_sort_column_after_remove(&mut self, column_index: usize) {
        if let Some(sort_column) = self.table_view.sort_column {
            if sort_column == column_index {
                self.table_view.sort_column = None;
                self.table_view.sort_ascending = true;
            } else if sort_column > column_index {
                self.table_view.sort_column = Some(sort_column - 1);
            }
        }
    }

    pub fn export_csv_path(&self, path: impl AsRef<Path>) -> Result<(), String> {
        let path = path.as_ref();
        let mut writer = csv::Writer::from_path(path)
            .map_err(|error| format!("Failed to write CSV '{}': {error}", path.display()))?;
        writer
            .write_record(&self.data_table.headers)
            .map_err(|error| {
                format!("Failed to write CSV headers '{}': {error}", path.display())
            })?;
        for row in &self.data_table.rows {
            writer.write_record(row).map_err(|error| {
                format!("Failed to write CSV row '{}': {error}", path.display())
            })?;
        }
        writer
            .flush()
            .map_err(|error| format!("Failed to flush CSV '{}': {error}", path.display()))?;
        Ok(())
    }
}

fn build_visible_row_indices(rows: &[Vec<String>], query: &str) -> Vec<usize> {
    if query.trim().is_empty() {
        return (0..rows.len()).collect();
    }

    let needle = query.trim().to_lowercase();
    rows.iter()
        .enumerate()
        .filter_map(|(row_index, row)| {
            let matches = row.iter().any(|cell| cell.to_lowercase().contains(&needle));
            matches.then_some(row_index)
        })
        .collect()
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

pub fn load_delimited_text_table(text: &str) -> Result<DataTable, String> {
    let delimiter = detect_delimiter(text);
    let mut reader = csv::ReaderBuilder::new()
        .has_headers(true)
        .delimiter(delimiter)
        .from_reader(Cursor::new(text));

    let headers = reader
        .headers()
        .map_err(|error| format!("Failed to read clipboard headers: {error}"))?
        .iter()
        .map(|value| value.to_owned())
        .collect::<Vec<_>>();

    let mut rows = Vec::new();
    for record in reader.records() {
        let record = record.map_err(|error| format!("Failed to read clipboard row: {error}"))?;
        rows.push(record.iter().map(|value| value.to_owned()).collect());
    }

    Ok(DataTable::from_rows(headers, rows))
}

fn compare_cells(left: &str, right: &str) -> Ordering {
    match (left.parse::<f64>(), right.parse::<f64>()) {
        (Ok(left_number), Ok(right_number)) => left_number
            .partial_cmp(&right_number)
            .unwrap_or(Ordering::Equal),
        _ => left.cmp(right),
    }
}

fn detect_delimiter(text: &str) -> u8 {
    let has_tab = text.contains('\t');
    let has_semicolon = text.contains(';');
    if has_tab {
        b'\t'
    } else if has_semicolon && !text.contains(',') {
        b';'
    } else {
        b','
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
    fn load_delimited_text_table_uses_tab_when_present() {
        let table = load_delimited_text_table("name\tvalue\nA\t1\nB\t2\n").expect("load text");

        assert_eq!(table.headers, vec!["name", "value"]);
        assert_eq!(table.rows.len(), 2);
        assert_eq!(table.rows[1], vec!["B", "2"]);
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
    fn project_state_applies_case_insensitive_row_filter() {
        let mut state = ProjectState::new();
        state.set_loaded_table(
            PathBuf::from("/tmp/example.csv"),
            DataTable {
                headers: vec!["name".to_owned(), "value".to_owned()],
                rows: vec![
                    vec!["Alpha".to_owned(), "1".to_owned()],
                    vec!["beta".to_owned(), "2".to_owned()],
                    vec!["Gamma".to_owned(), "3".to_owned()],
                ],
                column_metadata: vec![],
            },
        );

        state.set_row_filter("a");

        assert_eq!(state.table_view.row_filter_query, "a");
        assert_eq!(state.table_view.visible_row_indices, vec![0, 1, 2]);

        state.set_row_filter("beta");

        assert_eq!(state.table_view.visible_row_indices, vec![1]);

        state.set_row_filter("");

        assert_eq!(state.table_view.visible_row_indices, vec![0, 1, 2]);
    }

    #[test]
    fn project_state_imports_delimited_text() {
        let mut state = ProjectState::new();

        state
            .import_delimited_text("name,value\nA,1\nB,2\n", "clipboard")
            .expect("import clipboard");

        assert_eq!(state.data_table.headers, vec!["name", "value"]);
        assert_eq!(state.data_table.rows.len(), 2);
        assert_eq!(
            state.status_message,
            "Imported clipboard (2 rows, 2 columns)"
        );
        assert!(
            state
                .results_preview
                .contains("Imported data from clipboard")
        );
    }

    #[test]
    fn project_state_exports_csv_to_path() {
        let state = ProjectState {
            data_table: DataTable::from_rows(
                vec!["name".to_owned(), "value".to_owned()],
                vec![
                    vec!["A".to_owned(), "1".to_owned()],
                    vec!["B".to_owned(), "2".to_owned()],
                ],
            ),
            ..ProjectState::new()
        };
        let path =
            std::env::temp_dir().join(format!("calcite_rust_export_{}.csv", std::process::id()));

        state.export_csv_path(&path).expect("export csv");
        let text = std::fs::read_to_string(&path).expect("read csv");

        assert!(text.contains("name,value"));
        assert!(text.contains("A,1"));
        assert!(text.contains("B,2"));

        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn project_state_edits_rows_and_columns() {
        let mut state = ProjectState::new();
        state.replace_data_table(DataTable::from_rows(
            vec!["name".to_owned(), "value".to_owned()],
            vec![
                vec!["A".to_owned(), "1".to_owned()],
                vec!["B".to_owned(), "2".to_owned()],
            ],
        ));

        state.edit_cell(0, 1, "10".to_owned()).expect("edit cell");
        assert_eq!(state.data_table.rows[0][1], "10");

        state.insert_row(1).expect("insert row");
        assert_eq!(state.data_table.row_count(), 3);

        state
            .insert_column(1, "group".to_owned())
            .expect("insert column");
        assert_eq!(state.data_table.headers, vec!["name", "group", "value"]);

        state.remove_row(1).expect("remove row");
        assert_eq!(state.data_table.row_count(), 2);

        state.remove_column(1).expect("remove column");
        assert_eq!(state.data_table.headers, vec!["name", "value"]);
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
