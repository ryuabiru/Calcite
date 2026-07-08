import { invoke } from "@tauri-apps/api/core";

export async function getSnapshot() {
  return invoke("get_snapshot");
}

export async function loadCsv(path) {
  return invoke("load_csv", { path });
}

export async function pickCsvPath() {
  return invoke("pick_csv_path");
}

export async function pickProjectDirectory() {
  return invoke("pick_project_directory");
}

export async function pickExportCsvPath() {
  return invoke("pick_export_csv_path");
}

export async function importDelimitedText(text, sourceLabel) {
  return invoke("import_delimited_text", { text, source_label: sourceLabel });
}

export async function saveProject(directory) {
  return invoke("save_project", { directory });
}

export async function loadProject(directory) {
  return invoke("load_project", { directory });
}

export async function exportCsv(path) {
  return invoke("export_csv", { path });
}

export async function editCell(rowIndex, columnIndex, value) {
  return invoke("edit_cell", {
    row_index: rowIndex,
    column_index: columnIndex,
    value,
  });
}

export async function insertRow(rowIndex) {
  return invoke("insert_row", { row_index: rowIndex });
}

export async function removeRow(rowIndex) {
  return invoke("remove_row", { row_index: rowIndex });
}

export async function insertColumn(columnIndex, name) {
  return invoke("insert_column", { column_index: columnIndex, name });
}

export async function renameColumn(columnIndex, name) {
  return invoke("rename_column", { column_index: columnIndex, name });
}

export async function removeColumn(columnIndex) {
  return invoke("remove_column", { column_index: columnIndex });
}

export async function applyGraphControls(graphType, query, xColumn, yColumn, subgroupColumn, yLogScale) {
  await invoke("set_graph_type", { graph_type: graphType });
  await invoke("set_row_filter", { query });
  await invoke("set_columns", {
    x_column: xColumn,
    y_column: yColumn,
    subgroup_column: subgroupColumn,
  });
  await invoke("set_y_log_scale", { enabled: yLogScale });
}

export async function setYLogScale(enabled) {
  return invoke("set_y_log_scale", { enabled });
}

export async function setAdvancedRowFilter(conditions) {
  return invoke("set_advanced_row_filter", { conditions });
}

export async function pasteDelimitedText(text, startRow) {
  return invoke("paste_delimited_text", { text, start_row: startRow });
}

export async function toggleRowSelection(rowIndex) {
  return invoke("toggle_row_selection", { row_index: rowIndex });
}

export async function fillDownSelection() {
  return invoke("fill_down_selection");
}

export async function toggleSortByColumn(columnIndex) {
  return invoke("toggle_sort_by_column", { column_index: columnIndex });
}

export async function runPearsonCorrelationAnalysis(col1, col2) {
  return invoke("run_pearson_correlation_analysis", { col1, col2 });
}

export async function runSpearmanCorrelationAnalysis(col1, col2) {
  return invoke("run_spearman_correlation_analysis", { col1, col2 });
}

export async function runIndependentTTestAnalysis(col1, col2) {
  return invoke("run_independent_t_test_analysis", { col1, col2 });
}

export async function runPairedTTestAnalysis(col1, col2) {
  return invoke("run_paired_t_test_analysis", { col1, col2 });
}

export async function runOneWayAnovaAnalysis(groupCol, valueCol) {
  return invoke("run_one_way_anova_analysis", { group_col: groupCol, value_col: valueCol });
}

export async function runTukeyHsdAnalysis(groupCol, valueCol) {
  return invoke("run_tukey_hsd_analysis", { group_col: groupCol, value_col: valueCol });
}

export async function runShapiroWilkAnalysis(groupCol, valueCol) {
  return invoke("run_shapiro_wilk_analysis", { group_col: groupCol, value_col: valueCol });
}

export async function runMannWhitneyUAnalysis(col1, col2) {
  return invoke("run_mann_whitney_u_analysis", { col1, col2 });
}

export async function runWilcoxonSignedRankAnalysis(col1, col2) {
  return invoke("run_wilcoxon_signed_rank_analysis", { col1, col2 });
}

export async function runKruskalWallisAnalysis(groupCol, valueCol) {
  return invoke("run_kruskal_wallis_analysis", { group_col: groupCol, value_col: valueCol });
}

export async function runDunnPostHocAnalysis(groupCol, valueCol) {
  return invoke("run_dunn_post_hoc_analysis", { group_col: groupCol, value_col: valueCol });
}

export async function runLinearRegressionAnalysis(col1, col2) {
  return invoke("run_linear_regression_analysis", { col1, col2 });
}

export async function runFourPlRegressionAnalysis(col1, col2) {
  return invoke("run_four_pl_regression_analysis", { col1, col2 });
}

export async function runTwoProportionAnalysis(rowsCol, colsCol) {
  return invoke("run_two_proportion_analysis", { rows_col: rowsCol, cols_col: colsCol });
}

export async function runChiSquaredAnalysis(rowsCol, colsCol) {
  return invoke("run_chi_squared_analysis", { rows_col: rowsCol, cols_col: colsCol });
}

export async function restructureData(idVars, valueVars, varName, valueName) {
  return invoke("restructure_data", {
    id_vars: idVars,
    value_vars: valueVars,
    var_name: varName,
    value_name: valueName,
  });
}

export async function pivotData(idVars, varName, valueName) {
  return invoke("pivot_data", {
    id_vars: idVars,
    var_name: varName,
    value_name: valueName,
  });
}

export async function calculateNewColumn(name, formula) {
  return invoke("calculate_new_column", {
    name,
    formula,
  });
}
