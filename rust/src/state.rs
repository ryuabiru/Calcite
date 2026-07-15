use std::cmp::Ordering;
use std::collections::BTreeSet;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::core::{FilterCondition, FilterConnector, FilterOperator};
use crate::formula::{evaluate_formula, format_number};
use crate::analysis::{
    ChiSquaredAnalysisResult, LinearRegressionAnalysisResult, TwoProportionAnalysisResult,
};

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
    pub row_filter_conditions: Vec<FilterCondition>,
    pub visible_row_indices: Vec<usize>,
}

impl TableViewState {
    pub fn reset(&mut self) {
        self.sort_column = None;
        self.sort_ascending = true;
        self.selected_rows.clear();
        self.row_filter_query.clear();
        self.row_filter_conditions.clear();
        self.visible_row_indices.clear();
    }

    pub fn toggle_row(&mut self, row_index: usize) {
        if !self.selected_rows.insert(row_index) {
            self.selected_rows.remove(&row_index);
        }
    }
}

pub fn resolved_row_indices(table: &DataTable, table_view: &TableViewState) -> Vec<usize> {
    if table.is_empty() {
        return Vec::new();
    }

    if table_view.row_filter_query.trim().is_empty() {
        (0..table.rows.len()).collect()
    } else {
        table_view.visible_row_indices.clone()
    }
}

#[derive(Clone, Debug, Default)]
pub struct ProjectState {
    pub loaded_file_path: Option<PathBuf>,
    pub current_graph_type: String,
    pub x_column: String,
    pub y_column: String,
    pub subgroup_column: String,
    pub y_log_scale: bool,
    pub heatmap_normalization_mode: HeatmapNormalizationMode,
    pub data_table: DataTable,
    pub table_view: TableViewState,
    pub linear_regression_result: Option<LinearRegressionAnalysisResult>,
    pub chi_squared_result: Option<ChiSquaredAnalysisResult>,
    pub two_proportion_result: Option<TwoProportionAnalysisResult>,
    pub graph_annotation_summary: String,
    pub results_preview: String,
    pub status_message: String,
}

impl ProjectState {
    pub fn new() -> Self {
        Self {
            current_graph_type: "Scatter Plot".to_owned(),
            results_preview: "Rust bootstrap shell\n\nReady for CSV loading and analysis.".to_owned(),
            graph_annotation_summary: String::new(),
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
            y_log_scale: snapshot.settings.y_log_scale,
            heatmap_normalization_mode: snapshot.settings.heatmap_normalization,
            data_table: table,
            table_view: TableViewState {
                sort_column: snapshot.table_view.sort_column,
                sort_ascending: snapshot.table_view.sort_ascending,
                selected_rows: snapshot.table_view.selected_rows.into_iter().collect(),
                row_filter_query: snapshot.table_view.row_filter_query,
                row_filter_conditions: snapshot.table_view.row_filter_conditions,
                visible_row_indices: Vec::new(),
            },
            ..Default::default()
        };
        state.results_preview = String::new();
        state.graph_annotation_summary = snapshot.analysis.graph_annotation_summary;
        state.status_message = "Project loaded".to_owned();
        state.refresh_visible_row_indices();
        state
    }

    pub fn replace_data_table(&mut self, table: DataTable) {
        self.data_table = table;
        self.table_view.reset();
        self.clear_analysis_results();
        self.refresh_visible_row_indices();
    }

    pub fn clear_analysis_results(&mut self) {
        self.linear_regression_result = None;
        self.chi_squared_result = None;
        self.two_proportion_result = None;
        self.graph_annotation_summary.clear();
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

    pub fn rename_column(&mut self, column_index: usize, name: String) -> Result<(), String> {
        if name.trim().is_empty() {
            return Err("Column name cannot be empty".to_owned());
        }
        if self
            .data_table
            .headers
            .iter()
            .enumerate()
            .any(|(index, header)| index != column_index && header == &name)
        {
            return Err(format!("Column '{name}' already exists"));
        }

        let old_name = self
            .data_table
            .headers
            .get(column_index)
            .cloned()
            .ok_or_else(|| format!("Column index {column_index} is out of range"))?;
        self.data_table.headers[column_index] = name.clone();
        self.data_table.rebuild_column_metadata();
        self.after_table_mutation();
        self.status_message = format!("Renamed column {old_name} to {name}");
        Ok(())
    }

    pub fn calculate_new_column(&mut self, name: String, formula: String) -> Result<(), String> {
        if name.trim().is_empty() {
            return Err("New column name cannot be empty".to_owned());
        }
        if self.data_table.column_index(&name).is_some() {
            return Err(format!("Column '{name}' already exists"));
        }

        let headers = self.data_table.headers.clone();
        let mut values = Vec::with_capacity(self.data_table.rows.len());
        for (row_index, row) in self.data_table.rows.iter().enumerate() {
            let value = evaluate_formula(&formula, &headers, row)
                .map_err(|error| format!("Row {}: {error}", row_index + 1))?;
            values.push(format_number(value));
        }

        self.data_table.headers.push(name);
        for (row, value) in self.data_table.rows.iter_mut().zip(values) {
            row.push(value);
        }
        self.data_table.rebuild_column_metadata();
        self.after_table_mutation();
        Ok(())
    }

    pub fn fill_down_selection(&mut self) -> Result<(), String> {
        let Some(&source_row_index) = self.table_view.selected_rows.iter().next() else {
            return Err("Select at least one row to fill down".to_owned());
        };

        let source_row = self
            .data_table
            .rows
            .get(source_row_index)
            .cloned()
            .ok_or_else(|| format!("Row index {source_row_index} is out of range"))?;

        for row_index in self.table_view.selected_rows.iter().copied() {
            if let Some(target_row) = self.data_table.rows.get_mut(row_index) {
                *target_row = source_row.clone();
            }
        }

        self.data_table.rebuild_column_metadata();
        self.after_table_mutation();
        self.status_message = format!(
            "Filled down {} selected row(s) from row {}",
            self.table_view.selected_rows.len(),
            source_row_index + 1
        );
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
        self.table_view.row_filter_conditions.clear();
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

    pub fn set_advanced_row_filter(
        &mut self,
        conditions: Vec<FilterCondition>,
    ) -> Result<(), String> {
        if conditions.is_empty() {
            self.set_row_filter("");
            return Ok(());
        }

        for condition in &conditions {
            if condition.column.trim().is_empty() {
                return Err("Filter column cannot be empty".to_owned());
            }
            if self.data_table.column_index(&condition.column).is_none() {
                return Err(format!("Unknown filter column '{}'", condition.column));
            }
        }

        self.table_view.row_filter_query = render_filter_summary(&conditions);
        self.table_view.row_filter_conditions = conditions.clone();
        self.table_view.visible_row_indices = evaluate_filter_conditions(
            &self.data_table.rows,
            &self.data_table.headers,
            &conditions,
        )?;
        self.status_message = format!(
            "Filtered {} of {} rows",
            self.table_view.visible_row_indices.len(),
            self.data_table.row_count()
        );
        Ok(())
    }

    pub fn paste_delimited_text(&mut self, text: &str, start_row: usize) -> Result<(), String> {
        if self.data_table.is_empty() {
            return Err("No CSV loaded".to_owned());
        }

        let pasted_rows = load_delimited_text_rows(text)?;
        if pasted_rows.is_empty() {
            return Err("Clipboard text is empty".to_owned());
        }

        let width = pasted_rows.first().map(|row| row.len()).unwrap_or(0);
        if width == 0 {
            return Err("Clipboard text does not contain any columns".to_owned());
        }
        if width > self.data_table.column_count() {
            return Err("Clipboard data is wider than the current table".to_owned());
        }

        let required_rows = start_row + pasted_rows.len();
        while self.data_table.rows.len() < required_rows {
            self.data_table
                .rows
                .push(vec![String::new(); self.data_table.column_count()]);
        }

        for (row_offset, pasted_row) in pasted_rows.iter().enumerate() {
            let target_row = start_row + row_offset;
            if let Some(existing_row) = self.data_table.rows.get_mut(target_row) {
                for (column_index, value) in pasted_row.iter().enumerate() {
                    if let Some(cell) = existing_row.get_mut(column_index) {
                        *cell = value.clone();
                    }
                }
            }
        }

        self.data_table.rebuild_column_metadata();
        self.after_table_mutation();
        Ok(())
    }

    pub fn refresh_visible_row_indices(&mut self) {
        self.table_view.visible_row_indices = if self.data_table.is_empty() {
            Vec::new()
        } else if !self.table_view.row_filter_conditions.is_empty() {
            evaluate_filter_conditions(
                &self.data_table.rows,
                &self.data_table.headers,
                &self.table_view.row_filter_conditions,
            )
            .unwrap_or_default()
        } else {
            build_visible_row_indices(&self.data_table.rows, &self.table_view.row_filter_query)
        };
    }

    fn after_table_mutation(&mut self) {
        self.clear_analysis_results();
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

fn render_filter_summary(conditions: &[FilterCondition]) -> String {
    conditions
        .iter()
        .enumerate()
        .map(|(index, condition)| {
            let operator = match condition.operator {
                FilterOperator::Equals => "==",
                FilterOperator::NotEquals => "!=",
                FilterOperator::GreaterThan => ">",
                FilterOperator::LessThan => "<",
                FilterOperator::GreaterThanOrEqual => ">=",
                FilterOperator::LessThanOrEqual => "<=",
                FilterOperator::Contains => "contains",
                FilterOperator::NotContains => "not contains",
                FilterOperator::StartsWith => "starts with",
                FilterOperator::EndsWith => "ends with",
            };
            let connector = match condition.connector {
                FilterConnector::And => "AND",
                FilterConnector::Or => "OR",
            };
            if index == 0 {
                format!("{} {} {}", condition.column, operator, condition.value)
            } else {
                format!(
                    "{} {} {} {}",
                    connector, condition.column, operator, condition.value
                )
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}

fn evaluate_filter_conditions(
    rows: &[Vec<String>],
    headers: &[String],
    conditions: &[FilterCondition],
) -> Result<Vec<usize>, String> {
    let mut visible = Vec::new();
    for (row_index, row) in rows.iter().enumerate() {
        if evaluate_row_filter(row, headers, conditions)? {
            visible.push(row_index);
        }
    }
    Ok(visible)
}

fn evaluate_row_filter(
    row: &[String],
    headers: &[String],
    conditions: &[FilterCondition],
) -> Result<bool, String> {
    let mut current: Option<bool> = None;
    for condition in conditions {
        let matches = evaluate_condition(row, headers, condition)?;
        current = Some(match current {
            None => matches,
            Some(previous) => match condition.connector {
                FilterConnector::And => previous && matches,
                FilterConnector::Or => previous || matches,
            },
        });
    }
    Ok(current.unwrap_or(true))
}

fn evaluate_condition(
    row: &[String],
    headers: &[String],
    condition: &FilterCondition,
) -> Result<bool, String> {
    let column_index = headers
        .iter()
        .position(|header| header == &condition.column)
        .ok_or_else(|| format!("Unknown filter column '{}'", condition.column))?;
    let cell = row.get(column_index).map(String::as_str).unwrap_or("").trim();
    let value = condition.value.trim();

    let result = match condition.operator {
        FilterOperator::Equals => cell.eq_ignore_ascii_case(value),
        FilterOperator::NotEquals => !cell.eq_ignore_ascii_case(value),
        FilterOperator::Contains => cell.to_lowercase().contains(&value.to_lowercase()),
        FilterOperator::NotContains => !cell.to_lowercase().contains(&value.to_lowercase()),
        FilterOperator::StartsWith => cell.to_lowercase().starts_with(&value.to_lowercase()),
        FilterOperator::EndsWith => cell.to_lowercase().ends_with(&value.to_lowercase()),
        FilterOperator::GreaterThan
        | FilterOperator::LessThan
        | FilterOperator::GreaterThanOrEqual
        | FilterOperator::LessThanOrEqual => {
            let left = cell.parse::<f64>().map_err(|_| {
                format!(
                    "Column '{}' must be numeric for comparison operators",
                    condition.column
                )
            })?;
            let right = value.parse::<f64>().map_err(|_| {
                format!("Filter value '{}' must be numeric for comparison operators", value)
            })?;
            match condition.operator {
                FilterOperator::GreaterThan => left > right,
                FilterOperator::LessThan => left < right,
                FilterOperator::GreaterThanOrEqual => left >= right,
                FilterOperator::LessThanOrEqual => left <= right,
                _ => unreachable!(),
            }
        }
    };
    Ok(result)
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

fn load_delimited_text_rows(text: &str) -> Result<Vec<Vec<String>>, String> {
    let delimiter = detect_delimiter(text);
    let mut reader = csv::ReaderBuilder::new()
        .has_headers(false)
        .delimiter(delimiter)
        .from_reader(Cursor::new(text));

    let mut rows = Vec::new();
    for record in reader.records() {
        let record = record.map_err(|error| format!("Failed to read clipboard row: {error}"))?;
        let row = record.iter().map(|value| value.to_owned()).collect::<Vec<_>>();
        if row.iter().all(|cell| cell.trim().is_empty()) {
            continue;
        }
        rows.push(row);
    }

    if rows.is_empty() {
        return Ok(rows);
    }

    let expected_width = rows[0].len();
    if rows.iter().any(|row| row.len() != expected_width) {
        return Err("Clipboard text must have a consistent column count".to_owned());
    }

    Ok(rows)
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
    fn project_state_applies_advanced_row_filter() {
        let mut state = ProjectState::new();
        state.set_loaded_table(
            PathBuf::from("/tmp/example.csv"),
            DataTable {
                headers: vec!["name".to_owned(), "value".to_owned(), "group".to_owned()],
                rows: vec![
                    vec!["Alpha".to_owned(), "1".to_owned(), "A".to_owned()],
                    vec!["beta".to_owned(), "5".to_owned(), "B".to_owned()],
                    vec!["Gamma".to_owned(), "9".to_owned(), "A".to_owned()],
                ],
                column_metadata: vec![],
            },
        );

        state
            .set_advanced_row_filter(vec![
                FilterCondition {
                    connector: FilterConnector::And,
                    column: "group".to_owned(),
                    operator: FilterOperator::Equals,
                    value: "A".to_owned(),
                },
                FilterCondition {
                    connector: FilterConnector::And,
                    column: "value".to_owned(),
                    operator: FilterOperator::GreaterThan,
                    value: "5".to_owned(),
                },
            ])
            .expect("advanced filter");

        assert_eq!(state.table_view.visible_row_indices, vec![2]);
        assert!(state
            .table_view
            .row_filter_query
            .contains("group == A"));

        state
            .set_advanced_row_filter(vec![
                FilterCondition {
                    connector: FilterConnector::And,
                    column: "name".to_owned(),
                    operator: FilterOperator::Contains,
                    value: "beta".to_owned(),
                },
                FilterCondition {
                    connector: FilterConnector::Or,
                    column: "value".to_owned(),
                    operator: FilterOperator::Equals,
                    value: "1".to_owned(),
                },
            ])
            .expect("advanced filter with or");

        assert_eq!(state.table_view.visible_row_indices, vec![0, 1]);
    }

    #[test]
    fn project_state_reapplies_advanced_filter_after_table_mutation() {
        let mut state = ProjectState::new();
        state.set_loaded_table(
            PathBuf::from("/tmp/example.csv"),
            DataTable {
                headers: vec!["name".to_owned(), "value".to_owned(), "group".to_owned()],
                rows: vec![
                    vec!["Alpha".to_owned(), "1".to_owned(), "A".to_owned()],
                    vec!["beta".to_owned(), "5".to_owned(), "B".to_owned()],
                    vec!["Gamma".to_owned(), "9".to_owned(), "A".to_owned()],
                ],
                column_metadata: vec![],
            },
        );

        state
            .set_advanced_row_filter(vec![
                FilterCondition {
                    connector: FilterConnector::And,
                    column: "group".to_owned(),
                    operator: FilterOperator::Equals,
                    value: "A".to_owned(),
                },
                FilterCondition {
                    connector: FilterConnector::And,
                    column: "value".to_owned(),
                    operator: FilterOperator::GreaterThan,
                    value: "5".to_owned(),
                },
            ])
            .expect("advanced filter");

        assert_eq!(state.table_view.visible_row_indices, vec![2]);

        state
            .edit_cell(0, 1, "8".to_owned())
            .expect("edit cell");
        state.after_table_mutation();

        assert_eq!(state.table_view.row_filter_conditions.len(), 2);
        assert_eq!(state.table_view.visible_row_indices, vec![0, 2]);
    }

    #[test]
    fn project_state_pastes_delimited_text_over_existing_rows() {
        let mut state = ProjectState::new();
        state.replace_data_table(DataTable::from_rows(
            vec!["name".to_owned(), "value".to_owned()],
            vec![
                vec!["A".to_owned(), "1".to_owned()],
                vec!["B".to_owned(), "2".to_owned()],
                vec!["C".to_owned(), "3".to_owned()],
            ],
        ));

        state
            .paste_delimited_text("X\t10\nY\t20\n", 1)
            .expect("paste data");

        assert_eq!(state.data_table.rows[0], vec!["A", "1"]);
        assert_eq!(state.data_table.rows[1], vec!["X", "10"]);
        assert_eq!(state.data_table.rows[2], vec!["Y", "20"]);
    }

    #[test]
    fn project_state_renames_columns_and_fills_down_selection() {
        let mut state = ProjectState::new();
        state.replace_data_table(DataTable::from_rows(
            vec!["name".to_owned(), "value".to_owned()],
            vec![
                vec!["A".to_owned(), "1".to_owned()],
                vec!["B".to_owned(), "2".to_owned()],
                vec!["C".to_owned(), "3".to_owned()],
            ],
        ));

        state
            .rename_column(1, "amount".to_owned())
            .expect("rename column");
        assert_eq!(state.data_table.headers, vec!["name", "amount"]);

        state.toggle_row_selection(0);
        state.toggle_row_selection(2);
        state.fill_down_selection().expect("fill down");

        assert_eq!(state.data_table.rows[0], vec!["A", "1"]);
        assert_eq!(state.data_table.rows[2], vec!["A", "1"]);
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
    fn project_state_calculates_new_column_from_formula() {
        let mut state = ProjectState::new();
        state.replace_data_table(DataTable::from_rows(
            vec!["value".to_owned(), "scale".to_owned()],
            vec![
                vec!["1".to_owned(), "100".to_owned()],
                vec!["2".to_owned(), "100".to_owned()],
            ],
        ));

        state
            .calculate_new_column("scaled".to_owned(), "'value' * 'scale' / 100".to_owned())
            .expect("calculate new column");

        assert_eq!(
            state.data_table.headers,
            vec!["value", "scale", "scaled"]
        );
        assert_eq!(state.data_table.rows[0][2], "1");
        assert_eq!(state.data_table.rows[1][2], "2");
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
