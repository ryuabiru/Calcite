use std::path::PathBuf;

#[derive(Clone, Debug)]
pub enum AppCommand {
    LoadCsv {
        path: PathBuf,
    },
    ImportDelimitedText {
        text: String,
        source_label: String,
    },
    ExportCsv {
        path: PathBuf,
    },
    SaveProject {
        directory: PathBuf,
    },
    LoadProject {
        directory: PathBuf,
    },
    RestructureData {
        id_vars: Vec<String>,
        value_vars: Vec<String>,
        var_name: String,
        value_name: String,
    },
    PivotData {
        id_vars: Vec<String>,
        var_name: String,
        value_name: String,
    },
    SetGraphType {
        graph_type: String,
    },
    ToggleSortByColumn {
        column_index: usize,
    },
    ToggleRowSelection {
        row_index: usize,
    },
    SetRowFilter {
        query: String,
    },
    SetColumns {
        x_column: String,
        y_column: String,
        subgroup_column: String,
    },
    EditCell {
        row_index: usize,
        column_index: usize,
        value: String,
    },
    InsertRow {
        row_index: usize,
    },
    RemoveRow {
        row_index: usize,
    },
    InsertColumn {
        column_index: usize,
        name: String,
    },
    RemoveColumn {
        column_index: usize,
    },
}
