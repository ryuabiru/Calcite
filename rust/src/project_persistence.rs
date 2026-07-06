use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::state::{ColumnKind, ProjectState, TableViewState};

pub const PROJECT_SCHEMA_VERSION: u32 = 2;
pub const MANIFEST_FILENAME: &str = "manifest.json";
pub const DATAFRAME_FILENAME: &str = "tables/main.csv";
pub const SETTINGS_FILENAME: &str = "state/settings.json";
pub const ANALYSIS_FILENAME: &str = "state/analysis.json";

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProjectArchiveManifest {
    pub schema_version: u32,
    pub files: ProjectArchiveFiles,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProjectArchiveFiles {
    pub dataframe: Option<String>,
    pub settings: String,
    pub analysis: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProjectSettingsSnapshot {
    pub loaded_file_path: Option<String>,
    pub current_graph_type: String,
    pub x_column: String,
    pub y_column: String,
    pub subgroup_column: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PersistedColumnMetadata {
    pub index: usize,
    pub name: String,
    pub kind: ColumnKind,
    pub non_empty_count: usize,
    pub distinct_count: usize,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PersistedTable {
    pub headers: Vec<String>,
    pub rows: Vec<Vec<String>>,
    pub column_metadata: Vec<PersistedColumnMetadata>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PersistedTableView {
    pub sort_column: Option<usize>,
    pub sort_ascending: bool,
    pub selected_rows: Vec<usize>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct PersistedAnalysisState {
    pub statistical_annotations: Vec<Value>,
    pub paired_annotations: Vec<Value>,
    pub regression_line_params: Option<Value>,
    pub fit_params: Option<Value>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct PersistedProjectState {
    pub settings: ProjectSettingsSnapshot,
    pub table: PersistedTable,
    pub table_view: PersistedTableView,
    pub analysis: PersistedAnalysisState,
}

impl ProjectArchiveManifest {
    pub fn new(dataframe_present: bool) -> Self {
        Self {
            schema_version: PROJECT_SCHEMA_VERSION,
            files: ProjectArchiveFiles {
                dataframe: dataframe_present.then(|| DATAFRAME_FILENAME.to_owned()),
                settings: SETTINGS_FILENAME.to_owned(),
                analysis: ANALYSIS_FILENAME.to_owned(),
            },
        }
    }
}

impl From<&ProjectState> for PersistedProjectState {
    fn from(state: &ProjectState) -> Self {
        Self {
            settings: ProjectSettingsSnapshot {
                loaded_file_path: state
                    .loaded_file_path
                    .as_ref()
                    .map(|path| path.display().to_string()),
                current_graph_type: state.current_graph_type.clone(),
                x_column: state.x_column.clone(),
                y_column: state.y_column.clone(),
                subgroup_column: state.subgroup_column.clone(),
            },
            table: PersistedTable {
                headers: state.data_table.headers.clone(),
                rows: state.data_table.rows.clone(),
                column_metadata: state
                    .data_table
                    .column_metadata()
                    .iter()
                    .map(|metadata| PersistedColumnMetadata {
                        index: metadata.index,
                        name: metadata.name.clone(),
                        kind: metadata.kind.clone(),
                        non_empty_count: metadata.non_empty_count,
                        distinct_count: metadata.distinct_count,
                    })
                    .collect(),
            },
            table_view: PersistedTableView {
                sort_column: state.table_view.sort_column,
                sort_ascending: state.table_view.sort_ascending,
                selected_rows: state.table_view.selected_rows.iter().copied().collect(),
            },
            analysis: PersistedAnalysisState {
                statistical_annotations: Vec::new(),
                paired_annotations: Vec::new(),
                regression_line_params: None,
                fit_params: None,
            },
        }
    }
}

impl From<&TableViewState> for PersistedTableView {
    fn from(state: &TableViewState) -> Self {
        Self {
            sort_column: state.sort_column,
            sort_ascending: state.sort_ascending,
            selected_rows: state.selected_rows.iter().copied().collect(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::{ColumnKind, DataTable, ProjectState, TableViewState};
    use std::collections::BTreeSet;
    use std::path::PathBuf;

    #[test]
    fn manifest_uses_schema_version_and_file_paths() {
        let manifest = ProjectArchiveManifest::new(true);

        assert_eq!(manifest.schema_version, PROJECT_SCHEMA_VERSION);
        assert_eq!(MANIFEST_FILENAME, "manifest.json");
        assert_eq!(
            manifest.files.dataframe.as_deref(),
            Some(DATAFRAME_FILENAME)
        );
        assert_eq!(manifest.files.settings, SETTINGS_FILENAME);
        assert_eq!(manifest.files.analysis, ANALYSIS_FILENAME);
    }

    #[test]
    fn snapshot_from_project_state_preserves_settings_and_table_state() {
        let mut selected_rows = BTreeSet::new();
        selected_rows.insert(2);
        selected_rows.insert(0);

        let mut project = ProjectState::new();
        project.loaded_file_path = Some(PathBuf::from("/tmp/example.csv"));
        project.current_graph_type = "Heatmap".to_owned();
        project.x_column = "x".to_owned();
        project.y_column = "y".to_owned();
        project.subgroup_column = "group".to_owned();
        project.data_table = DataTable {
            headers: vec!["x".to_owned(), "y".to_owned()],
            rows: vec![vec!["A".to_owned(), "1".to_owned()]],
            column_metadata: vec![],
        };
        project.data_table.column_metadata = vec![
            crate::state::ColumnMetadata {
                index: 0,
                name: "x".to_owned(),
                kind: ColumnKind::Text,
                non_empty_count: 1,
                distinct_count: 1,
            },
            crate::state::ColumnMetadata {
                index: 1,
                name: "y".to_owned(),
                kind: ColumnKind::Numeric,
                non_empty_count: 1,
                distinct_count: 1,
            },
        ];
        project.table_view = TableViewState {
            sort_column: Some(1),
            sort_ascending: false,
            selected_rows,
        };

        let snapshot = PersistedProjectState::from(&project);

        assert_eq!(
            snapshot.settings.loaded_file_path.as_deref(),
            Some("/tmp/example.csv")
        );
        assert_eq!(snapshot.settings.current_graph_type, "Heatmap");
        assert_eq!(snapshot.table.headers, vec!["x", "y"]);
        assert_eq!(snapshot.table.column_metadata[1].kind, ColumnKind::Numeric);
        assert_eq!(snapshot.table_view.sort_column, Some(1));
        assert_eq!(snapshot.table_view.selected_rows, vec![0, 2]);
    }

    #[test]
    fn snapshots_serialize_to_stable_json() {
        let manifest = ProjectArchiveManifest::new(false);
        let json = serde_json::to_string(&manifest).expect("serialize manifest");

        assert!(json.contains("\"schema_version\":2"));
        assert!(json.contains("\"dataframe\":null"));
    }
}
