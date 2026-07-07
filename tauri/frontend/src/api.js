import { invoke } from "@tauri-apps/api/core";

export async function getSnapshot() {
  return invoke("get_snapshot");
}

export async function loadCsv(path) {
  return invoke("load_csv", { path });
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

export async function removeColumn(columnIndex) {
  return invoke("remove_column", { column_index: columnIndex });
}

export async function applyGraphControls(graphType, query, xColumn, yColumn, subgroupColumn) {
  await invoke("set_graph_type", { graph_type: graphType });
  await invoke("set_row_filter", { query });
  await invoke("set_columns", {
    x_column: xColumn,
    y_column: yColumn,
    subgroup_column: subgroupColumn,
  });
}
