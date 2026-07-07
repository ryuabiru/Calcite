use std::path::PathBuf;

use crate::analysis::{
    format_chi_squared_result, format_four_pl_regression_result, format_independent_t_test_result,
    format_kruskal_wallis_result, format_linear_regression_result, format_mann_whitney_u_result,
    format_one_way_anova_result, format_paired_t_test_result, format_pearson_correlation_result,
    format_shapiro_wilk_result, format_spearman_correlation_result, format_two_proportion_result,
    format_wilcoxon_signed_rank_result,
    run_chi_squared_analysis, run_four_pl_regression_analysis, run_independent_t_test_analysis,
    run_kruskal_wallis_analysis, run_linear_regression_analysis, run_mann_whitney_u_analysis,
    run_one_way_anova_analysis, run_paired_t_test_analysis, run_pearson_correlation_analysis,
    run_shapiro_wilk_analysis, run_spearman_correlation_analysis, run_two_proportion_analysis,
    run_wilcoxon_signed_rank_analysis,
};
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
            AppCommand::RunPearsonCorrelationAnalysis { col1, col2 } => {
                self.run_pearson_correlation_analysis(col1, col2)
            }
            AppCommand::RunSpearmanCorrelationAnalysis { col1, col2 } => {
                self.run_spearman_correlation_analysis(col1, col2)
            }
            AppCommand::RunIndependentTTestAnalysis { col1, col2 } => {
                self.run_independent_t_test_analysis(col1, col2)
            }
            AppCommand::RunPairedTTestAnalysis { col1, col2 } => {
                self.run_paired_t_test_analysis(col1, col2)
            }
            AppCommand::RunOneWayAnovaAnalysis { group_col, value_col } => {
                self.run_one_way_anova_analysis(group_col, value_col)
            }
            AppCommand::RunShapiroWilkAnalysis { group_col, value_col } => {
                self.run_shapiro_wilk_analysis(group_col, value_col)
            }
            AppCommand::RunMannWhitneyUAnalysis { col1, col2 } => {
                self.run_mann_whitney_u_analysis(col1, col2)
            }
            AppCommand::RunWilcoxonSignedRankAnalysis { col1, col2 } => {
                self.run_wilcoxon_signed_rank_analysis(col1, col2)
            }
            AppCommand::RunKruskalWallisAnalysis { group_col, value_col } => {
                self.run_kruskal_wallis_analysis(group_col, value_col)
            }
            AppCommand::RunLinearRegressionAnalysis { col1, col2 } => {
                self.run_linear_regression_analysis(col1, col2)
            }
            AppCommand::RunFourPlRegressionAnalysis { col1, col2 } => {
                self.run_four_pl_regression_analysis(col1, col2)
            }
            AppCommand::RunTwoProportionAnalysis { rows_col, cols_col } => {
                self.run_two_proportion_analysis(rows_col, cols_col)
            }
            AppCommand::RunChiSquaredAnalysis { rows_col, cols_col } => {
                self.run_chi_squared_analysis(rows_col, cols_col)
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

    fn run_chi_squared_analysis(
        &mut self,
        rows_col: String,
        cols_col: String,
    ) -> Result<(), String> {
        let result = run_chi_squared_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &rows_col,
            &cols_col,
        )?;
        self.project.chi_squared_result = Some(result.clone());
        self.project.status_message = format!(
            "Chi-squared analysis completed for {} vs {}",
            rows_col, cols_col
        );
        self.project.results_preview = format_chi_squared_result(&result);
        Ok(())
    }

    fn run_two_proportion_analysis(
        &mut self,
        rows_col: String,
        cols_col: String,
    ) -> Result<(), String> {
        let result = run_two_proportion_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &rows_col,
            &cols_col,
        )?;
        self.project.two_proportion_result = Some(result.clone());
        self.project.status_message = format!(
            "2-proportion z-test completed for {} vs {}",
            rows_col, cols_col
        );
        self.project.results_preview = format_two_proportion_result(&result);
        Ok(())
    }

    fn run_pearson_correlation_analysis(
        &mut self,
        col1: String,
        col2: String,
    ) -> Result<(), String> {
        let result = run_pearson_correlation_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &col1,
            &col2,
        )?;
        self.project.status_message = format!(
            "Pearson correlation completed for {} vs {}",
            col1, col2
        );
        self.project.results_preview = format_pearson_correlation_result(&result);
        Ok(())
    }

    fn run_spearman_correlation_analysis(
        &mut self,
        col1: String,
        col2: String,
    ) -> Result<(), String> {
        let result = run_spearman_correlation_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &col1,
            &col2,
        )?;
        self.project.status_message = format!(
            "Spearman correlation completed for {} vs {}",
            col1, col2
        );
        self.project.results_preview = format_spearman_correlation_result(&result);
        Ok(())
    }

    fn run_independent_t_test_analysis(
        &mut self,
        col1: String,
        col2: String,
    ) -> Result<(), String> {
        let result = run_independent_t_test_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &col1,
            &col2,
        )?;
        self.project.status_message = format!("Independent t-test completed for {} vs {}", col1, col2);
        self.project.results_preview = format_independent_t_test_result(&result);
        Ok(())
    }

    fn run_paired_t_test_analysis(&mut self, col1: String, col2: String) -> Result<(), String> {
        let result = run_paired_t_test_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &col1,
            &col2,
        )?;
        self.project.status_message = format!("Paired t-test completed for {} vs {}", col1, col2);
        self.project.results_preview = format_paired_t_test_result(&result);
        Ok(())
    }

    fn run_one_way_anova_analysis(
        &mut self,
        group_col: String,
        value_col: String,
    ) -> Result<(), String> {
        let result = run_one_way_anova_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &group_col,
            &value_col,
        )?;
        self.project.status_message = format!("One-way ANOVA completed for {} vs {}", group_col, value_col);
        self.project.results_preview = format_one_way_anova_result(&result);
        Ok(())
    }

    fn run_shapiro_wilk_analysis(
        &mut self,
        group_col: String,
        value_col: String,
    ) -> Result<(), String> {
        let result = run_shapiro_wilk_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &group_col,
            &value_col,
        )?;
        self.project.status_message = format!("Shapiro-Wilk test completed for {} vs {}", group_col, value_col);
        self.project.results_preview = format_shapiro_wilk_result(&result);
        Ok(())
    }

    fn run_mann_whitney_u_analysis(&mut self, col1: String, col2: String) -> Result<(), String> {
        let result = run_mann_whitney_u_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &col1,
            &col2,
        )?;
        self.project.status_message = format!("Mann-Whitney U test completed for {} vs {}", col1, col2);
        self.project.results_preview = format_mann_whitney_u_result(&result);
        Ok(())
    }

    fn run_wilcoxon_signed_rank_analysis(
        &mut self,
        col1: String,
        col2: String,
    ) -> Result<(), String> {
        let result = run_wilcoxon_signed_rank_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &col1,
            &col2,
        )?;
        self.project.status_message = format!("Wilcoxon signed-rank test completed for {} vs {}", col1, col2);
        self.project.results_preview = format_wilcoxon_signed_rank_result(&result);
        Ok(())
    }

    fn run_kruskal_wallis_analysis(
        &mut self,
        group_col: String,
        value_col: String,
    ) -> Result<(), String> {
        let result = run_kruskal_wallis_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &group_col,
            &value_col,
        )?;
        self.project.status_message = format!("Kruskal-Wallis test completed for {} vs {}", group_col, value_col);
        self.project.results_preview = format_kruskal_wallis_result(&result);
        Ok(())
    }

    fn run_linear_regression_analysis(
        &mut self,
        col1: String,
        col2: String,
    ) -> Result<(), String> {
        let result = run_linear_regression_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &col1,
            &col2,
        )?;
        self.project.linear_regression_result = Some(result.clone());
        self.project.status_message = format!(
            "Linear regression completed for {} vs {}",
            col1, col2
        );
        self.project.results_preview = format_linear_regression_result(&result);
        Ok(())
    }

    fn run_four_pl_regression_analysis(
        &mut self,
        col1: String,
        col2: String,
    ) -> Result<(), String> {
        let result = run_four_pl_regression_analysis(
            &self.project.data_table,
            &self.project.table_view,
            &col1,
            &col2,
        )?;
        self.project.status_message = format!("4PL regression completed for {} vs {}", col1, col2);
        self.project.results_preview = format_four_pl_regression_result(&result);
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
    fn run_chi_squared_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_chi_squared_test.csv");
        fs::write(
            &path,
            "group,label\nA,Yes\nA,Yes\nA,No\nB,Yes\nB,No\nB,No\n",
        )
        .expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunChiSquaredAnalysis {
                rows_col: "group".to_owned(),
                cols_col: "label".to_owned(),
            })
            .expect("chi-squared analysis");

        assert!(
            backend
                .project()
                .results_preview
                .contains("Chi-squared Test Results")
        );
        assert!(backend.project().chi_squared_result.is_some());
        assert!(
            backend
                .project()
                .results_preview
                .contains("Cramer's V")
        );
        assert_eq!(
            backend.project().status_message,
            "Chi-squared analysis completed for group vs label"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_pearson_correlation_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_pearson_test.csv");
        fs::write(&path, "x,y\n1,2\n2,4\n3,6\n4,8\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunPearsonCorrelationAnalysis {
                col1: "x".to_owned(),
                col2: "y".to_owned(),
            })
            .expect("pearson analysis");

        assert!(
            backend
                .project()
                .results_preview
                .contains("Pearson Correlation Results")
        );
        assert!(
            backend
                .project()
                .results_preview
                .contains("Pearson's r")
        );
        assert_eq!(
            backend.project().status_message,
            "Pearson correlation completed for x vs y"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_spearman_correlation_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_spearman_test.csv");
        fs::write(&path, "x,y\n1,10\n2,30\n3,20\n4,40\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunSpearmanCorrelationAnalysis {
                col1: "x".to_owned(),
                col2: "y".to_owned(),
            })
            .expect("spearman analysis");

        assert!(
            backend
                .project()
                .results_preview
                .contains("Spearman Correlation Results")
        );
        assert!(
            backend
                .project()
                .results_preview
                .contains("Spearman's rho")
        );
        assert_eq!(
            backend.project().status_message,
            "Spearman correlation completed for x vs y"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_independent_t_test_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_independent_t_test.csv");
        fs::write(&path, "a,b\n1,2\n2,3\n3,4\n4,5\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunIndependentTTestAnalysis {
                col1: "a".to_owned(),
                col2: "b".to_owned(),
            })
            .expect("independent t-test");

        assert!(backend.project().results_preview.contains("Independent t-test Results"));
        assert!(backend.project().results_preview.contains("p-value"));
        assert_eq!(
            backend.project().status_message,
            "Independent t-test completed for a vs b"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_paired_t_test_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_paired_t_test.csv");
        fs::write(&path, "a,b\n1,1.5\n2,2.5\n3,3.5\n4,4.5\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunPairedTTestAnalysis {
                col1: "a".to_owned(),
                col2: "b".to_owned(),
            })
            .expect("paired t-test");

        assert!(backend.project().results_preview.contains("Paired t-test Results"));
        assert!(backend.project().results_preview.contains("Mean difference"));
        assert_eq!(
            backend.project().status_message,
            "Paired t-test completed for a vs b"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_one_way_anova_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_anova_test.csv");
        fs::write(&path, "group,value\nA,1\nA,2\nB,3\nB,4\nC,5\nC,6\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunOneWayAnovaAnalysis {
                group_col: "group".to_owned(),
                value_col: "value".to_owned(),
            })
            .expect("anova");

        assert!(backend.project().results_preview.contains("One-way ANOVA Results"));
        assert!(backend.project().results_preview.contains("F-statistic"));
        assert_eq!(
            backend.project().status_message,
            "One-way ANOVA completed for group vs value"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_shapiro_wilk_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_shapiro_test.csv");
        fs::write(&path, "group,value\nA,1\nA,2\nA,3\nB,4\nB,5\nB,6\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunShapiroWilkAnalysis {
                group_col: "group".to_owned(),
                value_col: "value".to_owned(),
            })
            .expect("shapiro");

        assert!(backend.project().results_preview.contains("Shapiro-Wilk Normality Test Results"));
        assert_eq!(
            backend.project().status_message,
            "Shapiro-Wilk test completed for group vs value"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_mann_whitney_u_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_mann_whitney_test.csv");
        fs::write(&path, "a,b\n1,5\n2,4\n3,3\n4,2\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunMannWhitneyUAnalysis {
                col1: "a".to_owned(),
                col2: "b".to_owned(),
            })
            .expect("mann whitney");

        assert!(backend.project().results_preview.contains("Mann-Whitney U Test Results"));
        assert_eq!(
            backend.project().status_message,
            "Mann-Whitney U test completed for a vs b"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_wilcoxon_signed_rank_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_wilcoxon_test.csv");
        fs::write(&path, "a,b\n1,1.5\n2,2.2\n3,2.8\n4,4.1\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunWilcoxonSignedRankAnalysis {
                col1: "a".to_owned(),
                col2: "b".to_owned(),
            })
            .expect("wilcoxon");

        assert!(backend.project().results_preview.contains("Wilcoxon Signed-rank Test Results"));
        assert_eq!(
            backend.project().status_message,
            "Wilcoxon signed-rank test completed for a vs b"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_kruskal_wallis_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_kruskal_test.csv");
        fs::write(&path, "group,value\nA,1\nA,2\nB,3\nB,4\nC,5\nC,6\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunKruskalWallisAnalysis {
                group_col: "group".to_owned(),
                value_col: "value".to_owned(),
            })
            .expect("kruskal");

        assert!(backend.project().results_preview.contains("Kruskal-Wallis Test Results"));
        assert_eq!(
            backend.project().status_message,
            "Kruskal-Wallis test completed for group vs value"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_linear_regression_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_linear_regression_test.csv");
        fs::write(&path, "x,y\n1,2\n2,4\n3,6\n4,8\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunLinearRegressionAnalysis {
                col1: "x".to_owned(),
                col2: "y".to_owned(),
            })
            .expect("linear regression analysis");

        assert!(
            backend
                .project()
                .results_preview
                .contains("Linear Regression Results")
        );
        assert!(backend.project().linear_regression_result.is_some());
        assert!(backend.project().results_preview.contains("R-squared"));
        assert_eq!(
            backend.project().status_message,
            "Linear regression completed for x vs y"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_four_pl_regression_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_four_pl_test.csv");
        fs::write(
            &path,
            "x,y\n0.1,0.25\n0.3,0.35\n1,0.7\n3,1.2\n10,1.75\n30,1.9\n",
        )
        .expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunFourPlRegressionAnalysis {
                col1: "x".to_owned(),
                col2: "y".to_owned(),
            })
            .expect("4pl");

        assert!(backend.project().results_preview.contains("Non-linear Regression (4PL) Results"));
        assert_eq!(
            backend.project().status_message,
            "4PL regression completed for x vs y"
        );

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn run_two_proportion_analysis_updates_results_preview() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_two_proportion_test.csv");
        fs::write(
            &path,
            "group,label\nA,Yes\nA,Yes\nA,No\nB,Yes\nB,No\nB,No\n",
        )
        .expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::RunTwoProportionAnalysis {
                rows_col: "group".to_owned(),
                cols_col: "label".to_owned(),
            })
            .expect("two proportion analysis");

        assert!(
            backend
                .project()
                .results_preview
                .contains("2-Proportion z-test Results")
        );
        assert!(backend.project().two_proportion_result.is_some());
        assert!(backend.project().results_preview.contains("95% CI for difference"));
        assert_eq!(
            backend.project().status_message,
            "2-proportion z-test completed for group vs label"
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
    fn filtered_out_rows_do_not_fall_back_to_full_dataset_for_analysis() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_empty_filter_test.csv");
        fs::write(&path, "x,y\n1,2\n3,4\n5,6\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::SetRowFilter {
                query: "missing".to_owned(),
            })
            .expect("set row filter");

        let result = backend.dispatch(AppCommand::RunPearsonCorrelationAnalysis {
            col1: "x".to_owned(),
            col2: "y".to_owned(),
        });

        assert!(result.is_err());
        assert_eq!(backend.project().table_view.visible_row_indices, Vec::<usize>::new());

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn toggle_sort_by_column_reorders_rows_and_updates_status() {
        let mut backend = AppBackend::new();
        let path = std::env::temp_dir().join("calcite_rust_backend_sort_test.csv");
        fs::write(&path, "name,value\nAlpha,3\nbeta,1\nGamma,2\n").expect("write temp csv");

        backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
            .expect("load csv");
        backend
            .dispatch(AppCommand::ToggleSortByColumn { column_index: 1 })
            .expect("sort by column");

        assert_eq!(backend.project().data_table.rows[0][0], "beta");
        assert_eq!(backend.project().data_table.rows[1][0], "Gamma");
        assert_eq!(backend.project().data_table.rows[2][0], "Alpha");
        assert_eq!(backend.project().table_view.sort_column, Some(1));
        assert!(backend.project().table_view.sort_ascending);
        assert_eq!(backend.project().status_message, "Sorted by value (ascending)");

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
            .dispatch(AppCommand::SetGraphType {
                graph_type: "Heatmap".to_owned(),
            })
            .expect("set graph type");
        backend
            .dispatch(AppCommand::SetColumns {
                x_column: "name".to_owned(),
                y_column: "value".to_owned(),
                subgroup_column: "group".to_owned(),
            })
            .expect("set columns");
        backend
            .dispatch(AppCommand::ToggleSortByColumn { column_index: 1 })
            .expect("sort by column");
        backend.project_mut().toggle_row_selection(1);
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
        assert_eq!(restored.project().current_graph_type, "Heatmap");
        assert_eq!(restored.project().x_column, "name");
        assert_eq!(restored.project().y_column, "value");
        assert_eq!(restored.project().subgroup_column, "group");
        assert_eq!(restored.project().table_view.sort_column, Some(1));
        assert_eq!(restored.project().table_view.selected_rows.len(), 1);
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
