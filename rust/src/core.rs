use std::path::PathBuf;

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum FilterConnector {
    And,
    Or,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum FilterOperator {
    Equals,
    NotEquals,
    GreaterThan,
    LessThan,
    GreaterThanOrEqual,
    LessThanOrEqual,
    Contains,
    NotContains,
    StartsWith,
    EndsWith,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FilterCondition {
    pub connector: FilterConnector,
    pub column: String,
    pub operator: FilterOperator,
    pub value: String,
}

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
    CalculateNewColumn {
        name: String,
        formula: String,
    },
    SetGraphType {
        graph_type: String,
    },
    SetYLogScale {
        enabled: bool,
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
    PasteDelimitedText {
        text: String,
        start_row: usize,
    },
    SetAdvancedRowFilter {
        conditions: Vec<FilterCondition>,
    },
    SetColumns {
        x_column: String,
        y_column: String,
        subgroup_column: String,
    },
    RunPearsonCorrelationAnalysis {
        col1: String,
        col2: String,
    },
    RunSpearmanCorrelationAnalysis {
        col1: String,
        col2: String,
    },
    RunIndependentTTestAnalysis {
        col1: String,
        col2: String,
    },
    RunPairedTTestAnalysis {
        col1: String,
        col2: String,
    },
    RunOneWayAnovaAnalysis {
        group_col: String,
        value_col: String,
    },
    RunTukeyHsdAnalysis {
        group_col: String,
        value_col: String,
    },
    RunShapiroWilkAnalysis {
        group_col: String,
        value_col: String,
    },
    RunMannWhitneyUAnalysis {
        col1: String,
        col2: String,
    },
    RunWilcoxonSignedRankAnalysis {
        col1: String,
        col2: String,
    },
    RunKruskalWallisAnalysis {
        group_col: String,
        value_col: String,
    },
    RunDunnPostHocAnalysis {
        group_col: String,
        value_col: String,
    },
    RunLinearRegressionAnalysis {
        col1: String,
        col2: String,
    },
    RunFourPlRegressionAnalysis {
        col1: String,
        col2: String,
    },
    RunTwoProportionAnalysis {
        rows_col: String,
        cols_col: String,
    },
    RunChiSquaredAnalysis {
        rows_col: String,
        cols_col: String,
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
    RenameColumn {
        column_index: usize,
        name: String,
    },
    RemoveColumn {
        column_index: usize,
    },
    FillDownSelection,
}
