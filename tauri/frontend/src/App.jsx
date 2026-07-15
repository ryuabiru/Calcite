import { useEffect, useRef, useState } from "react";
import { Menu } from "@tauri-apps/api/menu";
import { getCurrentWebview } from "@tauri-apps/api/webview";
import { WebviewWindow } from "@tauri-apps/api/webviewWindow";

import {
  applyGraphControls,
  editCell,
  exportCsv,
  getSnapshot,
  importDelimitedText,
  calculateNewColumn,
  insertColumn,
  insertRow,
  loadCsv,
  loadProject,
  fillDownSelection,
  pickCsvPath,
  pickExportCsvPath,
  pickProjectDirectory,
  pivotData,
  renameColumn,
  removeColumn,
  removeRow,
  restructureData,
  saveProject,
  runKruskalWallisAnalysis,
  runMannWhitneyUAnalysis,
  runLinearRegressionAnalysis,
  runIndependentTTestAnalysis,
  runOneWayAnovaAnalysis,
  runTukeyHsdAnalysis,
  runFourPlRegressionAnalysis,
  runChiSquaredAnalysis,
  runShapiroWilkAnalysis,
  runPairedTTestAnalysis,
  runPearsonCorrelationAnalysis,
  runSpearmanCorrelationAnalysis,
  runDunnPostHocAnalysis,
  runTwoProportionAnalysis,
  runWilcoxonSignedRankAnalysis,
  toggleSortByColumn,
  setAdvancedRowFilter,
  setYLogScale as setYLogScaleBackend,
  pasteDelimitedText,
  toggleRowSelection,
} from "./api";
import { GraphView } from "./GraphView";

const GRAPH_TYPES = [
  "Bar Chart",
  "Count Plot",
  "Stacked Bar",
  "100% Stacked Bar",
  "Proportion Plot",
  "Mosaic Plot",
  "Scatter Plot",
  "Summary Scatter",
  "Point Plot",
  "Line Plot",
  "Box Plot",
  "Violin Plot",
  "Paired Scatter",
  "Histogram",
  "Heatmap",
  "Correlation Heatmap",
];

const DATA_TABS = [
  { id: "load", label: "Load" },
  { id: "transform", label: "Transform" },
  { id: "table", label: "Table" },
];

const WORKSPACE_TABS = [
  { id: "data", label: "Data" },
  { id: "plot", label: "Plot" },
  { id: "analysis", label: "Analysis" },
];

const RESULTS_TABS = [
  { id: "summary", label: "Summary" },
  { id: "log", label: "Log" },
  { id: "annotations", label: "Notes" },
];

const EMPTY_SNAPSHOT = {
  status_message: "Ready",
  results_preview: "Rust backend summary output will appear here.",
  current_graph_type: "Bar Chart",
  loaded_file_name: null,
  loaded_file_path: null,
  row_count: 0,
  column_count: 0,
  x_column: "",
  y_column: "",
  subgroup_column: "",
  row_filter_query: "",
  row_filter_conditions: [],
  visible_row_count: 0,
  selected_row_count: 0,
  sort_column: null,
  sort_ascending: true,
  visible_row_indices: [],
  headers: [],
  rows: [],
  selected_row_indices: [],
  graph_annotation_summary: "",
  y_log_scale: false,
};

function createFilterCondition() {
  return {
    connector: "And",
    column: "",
    operator: "Contains",
    value: "",
  };
}

function parsePositiveIndex(value) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed - 1 : null;
}

function slugify(value, fallback) {
  const slug = String(value || "")
    .replace(/\.[^.]+$/, "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || fallback;
}

function buildGraphExportName(snapshot) {
  const fileSlug = slugify(snapshot.loaded_file_name || "graph", "graph");
  const graphSlug = slugify(snapshot.current_graph_type || "plot", "plot");
  const yLogSlug = snapshot.y_log_scale ? "-y_log_scale" : "";
  return `${fileSlug}-${graphSlug}${yLogSlug}.svg`;
}

function summarizeTextBlock(text) {
  const lines = String(text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length === 0) {
    return { title: "", summary: "" };
  }
  const [title, ...rest] = lines;
  return {
    title,
    summary: rest.slice(0, 2).join(" "),
  };
}

function buildOverviewItems({
  graphType,
  xColumn,
  yColumn,
  subgroupColumn,
  visibleCount,
  totalCount,
}) {
  return [
    { label: "Graph Type", value: graphType || "-" },
    { label: "X", value: xColumn || "-" },
    { label: "Y", value: yColumn || "-" },
    { label: "Group", value: subgroupColumn || "-" },
    { label: "Visible / Total", value: `${visibleCount}/${totalCount}` },
  ];
}

function buildResultsCards({
  fileName,
  filePath,
  graphType,
  xColumn,
  yColumn,
  subgroupColumn,
  visibleCount,
  totalCount,
  selectedCount,
  filterQuery,
  annotationTitle,
  annotationSummary,
  yLogLabel,
}) {
  return [
    {
      label: "Data",
      primary: fileName || "No file loaded",
      detail: `${visibleCount}/${totalCount} visible rows`,
      subdetail: `Selected ${selectedCount}${filterQuery ? ` • Filter ${filterQuery}` : ""}`,
      title: filePath || fileName || "No loaded file path",
    },
    {
      label: "Graph",
      primary: graphType || "-",
      detail: `${xColumn || "-"} × ${yColumn || "-"}`,
      subdetail: `Subgroup ${subgroupColumn || "-"} • Y Log ${yLogLabel}`,
      title: `${xColumn || "-"} / ${yColumn || "-"} / ${subgroupColumn || "-"}`,
    },
    {
      label: "Annotations",
      primary: annotationTitle || "None",
      detail: annotationSummary || "No graph annotations",
      subdetail: annotationSummary ? "Post-hoc summary carried from analysis output" : "No annotation summary available",
      title: annotationSummary || "No graph annotations",
    },
  ];
}

function renderOverviewItems(items, className) {
  return items.map((item) =>
    item.wide ? (
      <div key={item.label} className={className} title={item.title}>
        <span>{item.label}</span>
        <strong>{item.value}</strong>
        {item.summary ? <p>{item.summary}</p> : null}
      </div>
    ) : (
      <div key={item.label} title={item.title}>
        <span>{item.label}</span>
        <strong>{item.value}</strong>
      </div>
    ),
  );
}

function renderSummaryCards(cards) {
  return cards.map((card) => (
    <div key={card.label} className="summary-card" title={card.title}>
      <span>{card.label}</span>
      <strong>{card.primary}</strong>
      {card.detail ? <p className="summary-card-detail">{card.detail}</p> : null}
      {card.subdetail ? <p className="summary-card-subdetail">{card.subdetail}</p> : null}
    </div>
  ));
}

function TabStrip({ tabs, activeTab, onChange, compact = false }) {
  return (
    <div className={`tab-strip${compact ? " tab-strip-compact" : ""}`} role="tablist" aria-label="Section tabs">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={activeTab === tab.id}
          className={activeTab === tab.id ? "tab-button is-active" : "tab-button"}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

function readStoredUiState() {
  if (typeof window === "undefined") {
    return {};
  }

  const storedUiState = window.localStorage.getItem("calcite.uiState");
  if (!storedUiState) {
    return {};
  }

  try {
    return JSON.parse(storedUiState);
  } catch {
    return {};
  }
}

function readWindowMode() {
  if (typeof window === "undefined") {
    return "main";
  }
  const mode = new URL(window.location.href).searchParams.get("mode");
  return mode === "data-editor" ? "data-editor" : "main";
}

export default function App() {
  const windowMode = readWindowMode();
  const isDataEditorWindow = windowMode === "data-editor";
  const storedUiState = readStoredUiState();
  const [snapshot, setSnapshot] = useState(EMPTY_SNAPSHOT);
  const [csvPath, setCsvPath] = useState(() => storedUiState.csvPath || "");
  const [csvInput, setCsvInput] = useState("");
  const [projectDir, setProjectDir] = useState("");
  const [editRowIndex, setEditRowIndex] = useState("1");
  const [editColumnIndex, setEditColumnIndex] = useState("1");
  const [editCellValue, setEditCellValue] = useState("");
  const [newColumnName, setNewColumnName] = useState("");
  const [reshapeIdVars, setReshapeIdVars] = useState("");
  const [reshapeValueVars, setReshapeValueVars] = useState("");
  const [reshapeVarName, setReshapeVarName] = useState("kind");
  const [reshapeValueName, setReshapeValueName] = useState("amount");
  const [pivotIdVars, setPivotIdVars] = useState("");
  const [pivotVarName, setPivotVarName] = useState("kind");
  const [pivotValueName, setPivotValueName] = useState("amount");
  const [calculateColumnName, setCalculateColumnName] = useState(
    () => storedUiState.calculateColumnName || "Calculated",
  );
  const [calculateFormula, setCalculateFormula] = useState(
    () => storedUiState.calculateFormula || "'Value' * 100",
  );
  const [filterConditions, setFilterConditions] = useState(
    () => storedUiState.filterConditions || [createFilterCondition()],
  );
  const [graphType, setGraphType] = useState(() => storedUiState.graphType || "Bar Chart");
  const [rowFilter, setRowFilter] = useState(() => storedUiState.rowFilter || "");
  const [xColumn, setXColumn] = useState(() => storedUiState.xColumn || "");
  const [yColumn, setYColumn] = useState(() => storedUiState.yColumn || "");
  const [subgroupColumn, setSubgroupColumn] = useState(
    () => storedUiState.subgroupColumn || "",
  );
  const [yLogScale, setYLogScale] = useState(() => storedUiState.yLogScale || false);
  const [errorMessage, setErrorMessage] = useState("");
  const [showAbout, setShowAbout] = useState(false);
  const [workspaceTab, setWorkspaceTab] = useState(isDataEditorWindow ? "data" : "plot");
  const [dataTab, setDataTab] = useState(isDataEditorWindow ? "transform" : "table");
  const [resultsTab, setResultsTab] = useState("summary");
  const [contextMenu, setContextMenu] = useState(null);
  const [dragMessage, setDragMessage] = useState("");
  const [activeCell, setActiveCell] = useState(null);
  const [activeCellValue, setActiveCellValue] = useState("");
  const graphCanvasRef = useRef(null);
  const hasLoadedProjectDir = useRef(false);
  const hasLoadedUiState = useRef(false);

  async function refreshSnapshot() {
    try {
      const nextSnapshot = await getSnapshot();
      setSnapshot(nextSnapshot);
      if (nextSnapshot.loaded_file_path) {
        setCsvPath(nextSnapshot.loaded_file_path);
      }
      if (nextSnapshot.loaded_file_name || nextSnapshot.row_count > 0 || nextSnapshot.column_count > 0) {
        setGraphType(nextSnapshot.current_graph_type);
        setRowFilter(nextSnapshot.row_filter_query);
        setXColumn(nextSnapshot.x_column);
        setYColumn(nextSnapshot.y_column);
        setSubgroupColumn(nextSnapshot.subgroup_column);
        setFilterConditions(
          nextSnapshot.row_filter_conditions && nextSnapshot.row_filter_conditions.length > 0
            ? nextSnapshot.row_filter_conditions
            : [createFilterCondition()],
        );
      }
      setYLogScale(nextSnapshot.y_log_scale || false);
      setErrorMessage("");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setErrorMessage(`Failed to load Calcite state:\n${message}`);
      throw error;
    }
  }

  function parseCsvList(text) {
    return text
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
  }

  async function runAction(action) {
    try {
      await action();
      await refreshSnapshot();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setErrorMessage(message);
    }
  }

  async function runProjectDirAction(action, directory) {
    const nextDirectory = directory.trim();
    await runAction(action);
    if (nextDirectory) {
      setProjectDir(nextDirectory);
      window.localStorage.setItem("calcite.projectDir", nextDirectory);
    }
  }

  function isCsvPath(path) {
    return /\.csv$/i.test(String(path || ""));
  }

  async function openCsvPath(path) {
    if (!path) {
      return;
    }
    setCsvPath(path);
    await runAction(() => loadCsv(path));
  }

  async function openProjectDirectory(directory) {
    if (!directory) {
      return;
    }
    setProjectDir(directory);
    window.localStorage.setItem("calcite.projectDir", directory);
    await runAction(() => loadProject(directory));
  }

  async function saveProjectDirectory(directory) {
    if (!directory) {
      return;
    }
    setProjectDir(directory);
    window.localStorage.setItem("calcite.projectDir", directory);
    await runAction(() => saveProject(directory));
  }

  async function chooseCsvAndLoad() {
    const path = await pickCsvPath();
    if (path) {
      await openCsvPath(path);
    }
  }

  async function chooseProjectAndLoad() {
    const directory = await pickProjectDirectory();
    if (directory) {
      await openProjectDirectory(directory);
    }
  }

  async function chooseProjectAndSave() {
    const directory = await pickProjectDirectory();
    if (directory) {
      await saveProjectDirectory(directory);
    }
  }

  async function chooseExportCsvPath() {
    const path = await pickExportCsvPath();
    if (path) {
      await runAction(() => exportCsv(path));
    }
  }

  async function handleDroppedPath(path) {
    if (!path) {
      return;
    }
    if (isCsvPath(path)) {
      await openCsvPath(path);
      return;
    }
    await openProjectDirectory(path);
  }

  async function openDataEditorWindow() {
    const editorLabel = `data-editor-${Date.now()}`;
    const editorUrl = `${window.location.pathname}?mode=data-editor`;
    const editorWindow = new WebviewWindow(editorLabel, {
      url: editorUrl,
      title: "Calcite Data Editor",
      width: 1320,
      height: 920,
      minWidth: 980,
      minHeight: 720,
      resizable: true,
      center: true,
    });

    editorWindow.once("tauri://error", (event) => {
      const payload = event?.payload;
      setErrorMessage(`Failed to open data editor:\n${payload}`);
    });
  }

  useEffect(() => {
    refreshSnapshot().catch((error) => {
      const message = error instanceof Error ? error.message : String(error);
      setErrorMessage(`Startup failed:\n${message}`);
    });

    function onError(event) {
      setErrorMessage(`Unhandled error:\n${event.message}`);
    }

    function onUnhandledRejection(event) {
      const message = event.reason instanceof Error ? event.reason.message : String(event.reason);
      setErrorMessage(`Unhandled promise rejection:\n${message}`);
    }

    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onUnhandledRejection);

    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onUnhandledRejection);
    };
  }, []);

  useEffect(() => {
    const storedProjectDir = window.localStorage.getItem("calcite.projectDir");
    if (storedProjectDir !== null) {
      setProjectDir(storedProjectDir);
    }
    hasLoadedProjectDir.current = true;
  }, []);

  useEffect(() => {
    if (!hasLoadedProjectDir.current) {
      return;
    }
    window.localStorage.setItem("calcite.projectDir", projectDir);
  }, [projectDir]);

  useEffect(() => {
    hasLoadedUiState.current = true;
  }, []);

  useEffect(() => {
    if (!hasLoadedUiState.current) {
      return;
    }
    window.localStorage.setItem(
      "calcite.uiState",
      JSON.stringify({
        csvPath,
        calculateColumnName,
        calculateFormula,
        graphType,
        rowFilter,
        filterConditions,
        xColumn,
        yColumn,
        subgroupColumn,
        yLogScale,
      }),
    );
  }, [csvPath, calculateColumnName, calculateFormula, graphType, rowFilter, filterConditions, xColumn, yColumn, subgroupColumn, yLogScale]);

  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === "Escape") {
        setShowAbout(false);
        setContextMenu(null);
        setActiveCell(null);
      }
    }

    if (showAbout) {
      window.addEventListener("keydown", onKeyDown);
    }

    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [showAbout]);

  useEffect(() => {
    let cleanup = null;
    let mounted = true;

    getCurrentWebview()
      .onDragDropEvent(async (event) => {
        if (!mounted) {
          return;
        }
        if (event.payload.type === "enter" || event.payload.type === "over") {
          setDragMessage("Drop a CSV file or project folder");
          return;
        }
        if (event.payload.type === "leave") {
          setDragMessage("");
          return;
        }
        if (event.payload.type === "drop") {
          setDragMessage("");
          const [path] = event.payload.paths || [];
          await handleDroppedPath(path);
        }
      })
      .then((unlisten) => {
        cleanup = unlisten;
      })
      .catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        setErrorMessage(`Failed to initialize drag and drop:\n${message}`);
      });

    return () => {
      mounted = false;
      if (cleanup) {
        cleanup();
      }
    };
  }, []);

  useEffect(() => {
    Menu.new({
      items: [
        {
          text: "File",
          items: [
            { id: "open-csv", text: "Open CSV...", accelerator: "CmdOrCtrl+O", action: chooseCsvAndLoad },
            { id: "load-project", text: "Load Project...", accelerator: "CmdOrCtrl+Shift+O", action: chooseProjectAndLoad },
            { id: "save-project", text: "Save Project...", accelerator: "CmdOrCtrl+S", action: chooseProjectAndSave },
            { id: "export-csv", text: "Export CSV...", accelerator: "CmdOrCtrl+E", action: chooseExportCsvPath },
          ],
        },
      ],
    })
      .then((menu) => menu.setAsAppMenu())
      .catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        setErrorMessage(`Failed to initialize native menu:\n${message}`);
      });
  }, []);

  useEffect(() => {
    setFilterConditions((currentConditions) => {
      if (snapshot.headers.length === 0) {
        return currentConditions.map((condition) => ({ ...condition, column: "" }));
      }

      const headers = snapshot.headers;
      return currentConditions.map((condition, index) => {
        if (condition.column && headers.includes(condition.column)) {
          return condition;
        }
        return {
          ...condition,
          connector: index === 0 ? "And" : condition.connector,
          column: headers[0],
        };
      });
    });
  }, [snapshot.headers]);

  const selectedRowIndices = snapshot.selected_row_indices || [];

  const displayedStatus = errorMessage ? "Error" : snapshot.status_message;
  const displayedResults = errorMessage || snapshot.results_preview;
  const displayedResultsSummary = summarizeTextBlock(displayedResults);
  const graphAnnotationSummary = summarizeTextBlock(snapshot.graph_annotation_summary);
  const overviewItems = buildOverviewItems({
    graphType: snapshot.current_graph_type,
    xColumn: snapshot.x_column,
    yColumn: snapshot.y_column,
    subgroupColumn: snapshot.subgroup_column,
    visibleCount: snapshot.visible_row_count,
    totalCount: snapshot.row_count,
  });
  const resultsCards = buildResultsCards({
    fileName: snapshot.loaded_file_name,
    filePath: snapshot.loaded_file_path,
    graphType: snapshot.current_graph_type,
    xColumn: snapshot.x_column,
    yColumn: snapshot.y_column,
    subgroupColumn: snapshot.subgroup_column,
    visibleCount: snapshot.visible_row_count,
    totalCount: snapshot.row_count,
    selectedCount: snapshot.selected_row_count,
    filterQuery: snapshot.row_filter_query,
    annotationTitle: graphAnnotationSummary.title,
    annotationSummary: graphAnnotationSummary.summary,
    yLogLabel: yLogScale ? "On" : "Off",
  });
  const visibleRowIndices =
    snapshot.visible_row_indices.length > 0 || snapshot.row_filter_query.trim() !== ""
      ? snapshot.visible_row_indices
      : snapshot.rows.map((_, index) => index);
  const previewRowIndices = isDataEditorWindow
    ? visibleRowIndices
    : visibleRowIndices.slice(0, 25);
  const previewRows = previewRowIndices
    .map((rowIndex) => ({ rowIndex, row: snapshot.rows[rowIndex] }))
    .filter(({ row }) => Array.isArray(row));

  async function applyColumnSelection(role, columnName) {
    const nextXColumn = role === "x" ? columnName : xColumn;
    const nextYColumn = role === "y" ? columnName : yColumn;
    const nextSubgroupColumn = role === "subgroup" ? columnName : subgroupColumn;

    if (role === "x") {
      setXColumn(columnName);
    } else if (role === "y") {
      setYColumn(columnName);
    } else {
      setSubgroupColumn(columnName);
    }

    await runAction(() =>
      applyGraphControls(
        graphType,
        rowFilter,
        nextXColumn,
        nextYColumn,
        nextSubgroupColumn,
        yLogScale,
      ),
    );
  }

  async function updateYLogScale(enabled) {
    setYLogScale(enabled);
    await runAction(() => setYLogScaleBackend(enabled));
  }

  function updateFilterCondition(index, field, value) {
    setFilterConditions((currentConditions) =>
      currentConditions.map((condition, conditionIndex) =>
        conditionIndex === index ? { ...condition, [field]: value } : condition,
      ),
    );
  }

  function addFilterCondition() {
    setFilterConditions((currentConditions) => [
      ...currentConditions,
      {
        ...createFilterCondition(),
        connector: "And",
        column: snapshot.headers[0] || "",
      },
    ]);
  }

  function removeFilterCondition(index) {
    setFilterConditions((currentConditions) => {
      if (currentConditions.length <= 1) {
        return [createFilterCondition()];
      }
      return currentConditions.filter((_, conditionIndex) => conditionIndex !== index);
    });
  }

  function buildSelectedRowsTsv() {
    if (selectedRowIndices.length === 0) {
      return "";
    }

    return selectedRowIndices
      .map((rowIndex) => snapshot.rows[rowIndex] || [])
      .map((row) => row.map((cell) => cell ?? "").join("\t"))
      .join("\n");
  }

  function buildRowTsv(rowIndex) {
    const row = snapshot.rows[rowIndex] || [];
    return row.map((cell) => cell ?? "").join("\t");
  }

  async function copySelectedRows() {
    const text = buildSelectedRowsTsv();
    if (!text) {
      return;
    }
    await window.navigator.clipboard.writeText(text);
  }

  async function pasteClipboardRows() {
    const text = await window.navigator.clipboard.readText();
    if (!text) {
      return;
    }
    const startRow = selectedRowIndices.length > 0 ? Math.min(...selectedRowIndices) : 0;
    await pasteDelimitedText(text, startRow);
  }

  async function importTextAreaData() {
    if (!csvInput.trim()) {
      return;
    }
    await importDelimitedText(csvInput, "manual input");
  }

  async function exportGraphSvg() {
    const graphRoot = graphCanvasRef.current;
    const svgElement = graphRoot?.querySelector("svg");
    if (!svgElement) {
      return;
    }

    const serializer = new XMLSerializer();
    let svgSource = serializer.serializeToString(svgElement);
    if (!svgSource.includes('xmlns="http://www.w3.org/2000/svg"')) {
      svgSource = svgSource.replace(
        "<svg",
        '<svg xmlns="http://www.w3.org/2000/svg"',
      );
    }

    const blob = new Blob([svgSource], { type: "image/svg+xml;charset=utf-8" });
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = buildGraphExportName(snapshot);
    link.click();
    window.URL.revokeObjectURL(downloadUrl);
  }

  function closeContextMenu() {
    setContextMenu(null);
  }

  function beginCellEdit(rowIndex, columnIndex) {
    setActiveCell({ rowIndex, columnIndex });
    setActiveCellValue(snapshot.rows[rowIndex]?.[columnIndex] ?? "");
  }

  async function commitActiveCell() {
    if (!activeCell) {
      return;
    }
    const { rowIndex, columnIndex } = activeCell;
    await runAction(() => editCell(rowIndex, columnIndex, activeCellValue));
    setActiveCell(null);
  }

  function cancelActiveCell() {
    setActiveCell(null);
  }

  function openColumnContextMenu(event, header, role = null) {
    event.preventDefault();
    event.stopPropagation();
    setContextMenu({
      kind: "column",
      x: event.clientX,
      y: event.clientY,
      header,
      role,
    });
  }

  function openTableHeaderContextMenu(event, header, columnIndex) {
    event.preventDefault();
    event.stopPropagation();
    setContextMenu({
      kind: "tableHeader",
      x: event.clientX,
      y: event.clientY,
      header,
      columnIndex,
    });
  }

  async function copyText(text) {
    if (!text) {
      return;
    }
    await window.navigator.clipboard.writeText(text);
  }

  function renderContextMenu() {
    if (!contextMenu) {
      return null;
    }

    const baseStyle = {
      left: Math.min(contextMenu.x, window.innerWidth - 240),
      top: Math.min(contextMenu.y, window.innerHeight - 220),
    };

    const items =
      contextMenu.kind === "column"
        ? [
            { label: "Set as X", action: () => applyColumnSelection("x", contextMenu.header) },
            { label: "Set as Y", action: () => applyColumnSelection("y", contextMenu.header) },
            { label: "Set as Group", action: () => applyColumnSelection("subgroup", contextMenu.header) },
            { label: "Copy name", action: () => copyText(contextMenu.header) },
          ]
        : contextMenu.kind === "tableHeader"
        ? [
            {
              label: "Sort by this column",
              action: () => runAction(() => toggleSortByColumn(contextMenu.columnIndex)),
            },
            { label: "Set as X", action: () => applyColumnSelection("x", contextMenu.header) },
            { label: "Set as Y", action: () => applyColumnSelection("y", contextMenu.header) },
            { label: "Set as Group", action: () => applyColumnSelection("subgroup", contextMenu.header) },
            { label: "Copy name", action: () => copyText(contextMenu.header) },
          ]
        : [
            {
              label: "Toggle row selection",
              action: () => runAction(() => toggleRowSelection(contextMenu.rowIndex)),
            },
            {
              label: "Copy row",
              action: () => copyText(buildRowTsv(contextMenu.rowIndex)),
            },
          ];

    return (
      <div className="context-menu-backdrop" onClick={closeContextMenu}>
        <div className="context-menu" style={baseStyle} onClick={(event) => event.stopPropagation()}>
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              className="context-menu-item"
              onClick={async () => {
                closeContextMenu();
                await item.action();
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="app-header-main">
          <strong className="app-title">{isDataEditorWindow ? "Calcite Data Editor" : "Calcite"}</strong>
          <span className="header-divider" aria-hidden="true" />
          <span className="header-meta" title={snapshot.loaded_file_path || snapshot.loaded_file_name || ""}>
            {snapshot.loaded_file_name || "No file loaded"}
          </span>
          <span className={errorMessage ? "status-pill is-error" : "status-pill"} title={displayedStatus}>
            {displayedStatus}
          </span>
        </div>
        <div className="app-header-actions" aria-label="Primary actions">
          {!isDataEditorWindow ? (
            <button type="button" onClick={() => runAction(openDataEditorWindow)}>
              Open Data Editor
            </button>
          ) : null}
          <button type="button" className="primary-button" onClick={chooseCsvAndLoad}>
            Load CSV
          </button>
          <button type="button" onClick={() => runAction(pasteClipboardRows)}>
            Paste
          </button>
          <button
            type="button"
            onClick={() => (projectDir.trim() ? saveProjectDirectory(projectDir.trim()) : chooseProjectAndSave())}
          >
            Save Project
          </button>
          <button type="button" onClick={chooseProjectAndLoad}>
            Load Project
          </button>
          <button type="button" onClick={chooseExportCsvPath}>
            Export
          </button>
          <button type="button" onClick={() => refreshSnapshot().catch(() => {})}>
            Refresh
          </button>
          <button type="button" className="icon-button" onClick={() => setShowAbout(true)} title="About Calcite">
            i
          </button>
        </div>
      </header>

      {dragMessage ? (
        <div className="drop-overlay" aria-live="polite">
          <div>
            <strong>{dragMessage}</strong>
            <span>CSV files open as data tables. Folders open as Calcite projects.</span>
          </div>
        </div>
      ) : null}

      <section className={isDataEditorWindow ? "workbench workbench-data-editor" : "workbench"}>
        <aside className="workbench-sidebar workbench-left">
          <article className="panel dataframe-panel">
            <div className="panel-header">
              <div>
                <h2>{isDataEditorWindow ? "Data Editor" : "Data"}</h2>
              </div>
              {isDataEditorWindow ? (
                <TabStrip tabs={DATA_TABS} activeTab={dataTab} onChange={setDataTab} compact />
              ) : null}
            </div>
            <div className="panel-body">
              <>
                  <div className="panel-subtitle-row">
                    <span className="panel-subtitle-badge">Data</span>
                    <p>
                      {isDataEditorWindow
                        ? "Edit, reshape, pivot, and inspect the active table in a larger workspace."
                        : "Inspect the active table while setting up the graph."}
                    </p>
                  </div>
                  {!isDataEditorWindow ? (
                    <div className="subpanel workspace-callout">
                      <div className="subpanel-heading">
                        <h3>Open a larger editor when needed</h3>
                      </div>
                      <p className="panel-caption panel-caption-compact">
                        Keep this preview beside the graph, and move restructuring or heavy editing into a separate window.
                      </p>
                      <div className="actions">
                        <button type="button" onClick={() => runAction(openDataEditorWindow)}>
                          Open Data Editor Window
                        </button>
                      </div>
                    </div>
                  ) : null}
                  {dataTab === "load" ? (
                    <>
                      <div className="drop-target">
                        <strong>Drop CSV files or project folders anywhere</strong>
                        <span>Use the native picker buttons below when browsing is easier.</span>
                      </div>
                      <label>
                        CSV Path
                        <input value={csvPath} onChange={(event) => setCsvPath(event.target.value)} placeholder="/path/to/data.csv" />
                      </label>
                      <div className="actions">
                        <button type="button" className="primary-button" onClick={chooseCsvAndLoad}>
                          Choose CSV
                        </button>
                        <button type="button" onClick={() => runAction(() => loadCsv(csvPath.trim()))}>
                          Load Path
                        </button>
                      </div>
                      <textarea
                        value={csvInput}
                        onChange={(event) => setCsvInput(event.target.value)}
                        placeholder={"name,value\nA,1\nB,2"}
                      />
                      <div className="actions">
                        <button type="button" onClick={() => runAction(importTextAreaData)}>
                          Import Text
                        </button>
                        <button type="button" onClick={() => setCsvInput("")}>
                          Clear Text
                        </button>
                      </div>
                      <label>
                        Save Directory
                        <input
                          value={projectDir}
                          onChange={(event) => setProjectDir(event.target.value)}
                          placeholder="/path/to/project-dir"
                        />
                      </label>
                      <div className="actions">
                        <button type="button" onClick={chooseProjectAndLoad}>
                          Choose Project
                        </button>
                        <button
                          type="button"
                          onClick={() => (projectDir.trim() ? saveProjectDirectory(projectDir.trim()) : chooseProjectAndSave())}
                        >
                          Save Here
                        </button>
                        <button type="button" onClick={() => runProjectDirAction(() => loadProject(projectDir), projectDir)}>
                          Load Directory
                        </button>
                      </div>
                      <p className="panel-caption panel-caption-compact">
                        Native file actions are also available from the File menu.
                      </p>
                    </>
                  ) : null}
                  {dataTab === "transform" ? (
                    <>
                      <details className="subpanel accordion" open>
                        <summary>Advanced Filter</summary>
                        <div className="subpanel-content">
                          {filterConditions.map((condition, index) => (
                            <div className="filter-row" key={`filter-${index}`}>
                              <label>
                                {index === 0 ? "When" : "Then"}
                                <select
                                  value={condition.connector}
                                  onChange={(event) => updateFilterCondition(index, "connector", event.target.value)}
                                  disabled={index === 0}
                                >
                                  <option value="And">AND</option>
                                  <option value="Or">OR</option>
                                </select>
                              </label>
                              <label>
                                Column
                                <select
                                  value={condition.column}
                                  onChange={(event) => updateFilterCondition(index, "column", event.target.value)}
                                >
                                  <option value="">Select column</option>
                                  {snapshot.headers.map((header) => (
                                    <option value={header} key={`filter-col-${index}-${header}`}>
                                      {header}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label>
                                Operator
                                <select
                                  value={condition.operator}
                                  onChange={(event) => updateFilterCondition(index, "operator", event.target.value)}
                                >
                                  <option value="Contains">contains</option>
                                  <option value="NotContains">does not contain</option>
                                  <option value="Equals">equals</option>
                                  <option value="NotEquals">not equal</option>
                                  <option value="StartsWith">starts with</option>
                                  <option value="EndsWith">ends with</option>
                                  <option value="GreaterThan">greater than</option>
                                  <option value="LessThan">less than</option>
                                  <option value="GreaterThanOrEqual">greater than or equal</option>
                                  <option value="LessThanOrEqual">less than or equal</option>
                                </select>
                              </label>
                              <label>
                                Value
                                <input
                                  value={condition.value}
                                  onChange={(event) => updateFilterCondition(index, "value", event.target.value)}
                                  placeholder="beta"
                                />
                              </label>
                              <button onClick={() => removeFilterCondition(index)}>Remove</button>
                            </div>
                          ))}
                          <div className="actions">
                            <button onClick={addFilterCondition}>Add Condition</button>
                            <button
                              onClick={() =>
                                runAction(() => setAdvancedRowFilter(filterConditions))
                              }
                            >
                              Apply Advanced Filter
                            </button>
                          </div>
                        </div>
                      </details>
                      <details className="subpanel accordion">
                        <summary>Reshape</summary>
                        <div className="subpanel-content">
                          <label>
                            ID Vars
                            <input
                              value={reshapeIdVars}
                              onChange={(event) => setReshapeIdVars(event.target.value)}
                              placeholder="category,group"
                            />
                          </label>
                          <label>
                            Value Vars
                            <input
                              value={reshapeValueVars}
                              onChange={(event) => setReshapeValueVars(event.target.value)}
                              placeholder="left,right"
                            />
                          </label>
                          <label>
                            Var Name
                            <input
                              value={reshapeVarName}
                              onChange={(event) => setReshapeVarName(event.target.value)}
                              placeholder="kind"
                            />
                          </label>
                          <label>
                            Value Name
                            <input
                              value={reshapeValueName}
                              onChange={(event) => setReshapeValueName(event.target.value)}
                              placeholder="amount"
                            />
                          </label>
                          <div className="actions">
                            <button
                              onClick={() =>
                                runAction(() =>
                                  restructureData(
                                    parseCsvList(reshapeIdVars),
                                    parseCsvList(reshapeValueVars),
                                    reshapeVarName.trim() || "kind",
                                    reshapeValueName.trim() || "amount",
                                  ),
                                )
                              }
                            >
                              Restructure
                            </button>
                          </div>
                        </div>
                      </details>
                      <details className="subpanel accordion">
                        <summary>Pivot</summary>
                        <div className="subpanel-content">
                          <label>
                            ID Vars
                            <input
                              value={pivotIdVars}
                              onChange={(event) => setPivotIdVars(event.target.value)}
                              placeholder="category"
                            />
                          </label>
                          <label>
                            Var Name
                            <input
                              value={pivotVarName}
                              onChange={(event) => setPivotVarName(event.target.value)}
                              placeholder="kind"
                            />
                          </label>
                          <label>
                            Value Name
                            <input
                              value={pivotValueName}
                              onChange={(event) => setPivotValueName(event.target.value)}
                              placeholder="amount"
                            />
                          </label>
                          <div className="actions">
                            <button
                              onClick={() =>
                                runAction(() =>
                                  pivotData(
                                    parseCsvList(pivotIdVars),
                                    pivotVarName.trim() || "kind",
                                    pivotValueName.trim() || "amount",
                                  ),
                                )
                              }
                            >
                              Pivot
                            </button>
                          </div>
                        </div>
                      </details>
                      <details className="subpanel accordion">
                        <summary>Calculate</summary>
                        <div className="subpanel-content">
                          <label>
                            New Column Name
                            <input
                              value={calculateColumnName}
                              onChange={(event) => setCalculateColumnName(event.target.value)}
                              placeholder="Scaled Value"
                            />
                          </label>
                          <label>
                            Formula
                            <input
                              value={calculateFormula}
                              onChange={(event) => setCalculateFormula(event.target.value)}
                              placeholder="'Value' * 100"
                            />
                          </label>
                          <div className="actions">
                            <button
                              onClick={() =>
                                runAction(() =>
                                  calculateNewColumn(
                                    calculateColumnName.trim() || "Calculated",
                                    calculateFormula.trim(),
                                  ),
                                )
                              }
                            >
                              Calculate Column
                            </button>
                          </div>
                        </div>
                      </details>
                    </>
                  ) : null}
                  {dataTab === "table" ? (
                    <>
                      <div className="subpanel">
                        <div className="subpanel-heading">
                          <h3>Table Preview</h3>
                          <span>{snapshot.visible_row_count} visible rows</span>
                        </div>
                        <p className="table-preview-note">
                          Double-click a cell to edit it directly.
                        </p>
                        {snapshot.headers.length === 0 ? (
                          <div className="table-empty">Load a CSV to render the table preview.</div>
                        ) : (
                          <div className="table-preview-scroll">
                            <table className="table-preview">
                              <thead>
                                <tr>
                                  <th className="row-index-cell">#</th>
                                  {snapshot.headers.map((header, columnIndex) => (
                                    <th key={`${header}-${columnIndex}`} onContextMenu={(event) => openTableHeaderContextMenu(event, header, columnIndex)}>
                                      <button
                                        className="table-header-button"
                                        onClick={() => runAction(() => toggleSortByColumn(columnIndex))}
                                        title={`Sort by ${header}`}
                                      >
                                        {header}
                                        {snapshot.sort_column === columnIndex
                                          ? snapshot.sort_ascending
                                            ? " ▲"
                                            : " ▼"
                                          : ""}
                                      </button>
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {previewRows.map(({ row, rowIndex }) => (
                                  <tr
                                    key={`preview-row-${rowIndex}`}
                                    className={selectedRowIndices.includes(rowIndex) ? "row-selected" : ""}
                                    onClick={() => runAction(() => toggleRowSelection(rowIndex))}
                                    onContextMenu={(event) => {
                                      event.preventDefault();
                                      setContextMenu({
                                        kind: "row",
                                        x: event.clientX,
                                        y: event.clientY,
                                        rowIndex,
                                      });
                                    }}
                                  >
                                    <th className="row-index-cell">{rowIndex + 1}</th>
                                    {snapshot.headers.map((_, columnIndex) => {
                                      const isEditing =
                                        activeCell?.rowIndex === rowIndex &&
                                        activeCell?.columnIndex === columnIndex;
                                      return (
                                        <td
                                          key={`${rowIndex}-${columnIndex}`}
                                          className={isEditing ? "table-cell-editing" : "table-cell"}
                                          onDoubleClick={(event) => {
                                            event.stopPropagation();
                                            beginCellEdit(rowIndex, columnIndex);
                                          }}
                                        >
                                          {isEditing ? (
                                            <input
                                              autoFocus
                                              className="table-cell-input"
                                              value={activeCellValue}
                                              onChange={(event) => setActiveCellValue(event.target.value)}
                                              onClick={(event) => event.stopPropagation()}
                                              onBlur={() => commitActiveCell()}
                                              onKeyDown={(event) => {
                                                if (event.key === "Enter") {
                                                  event.preventDefault();
                                                  commitActiveCell();
                                                } else if (event.key === "Escape") {
                                                  event.preventDefault();
                                                  cancelActiveCell();
                                                }
                                              }}
                                            />
                                          ) : (
                                            row[columnIndex] ?? ""
                                          )}
                                        </td>
                                      );
                                    })}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                        {snapshot.visible_row_count > previewRows.length ? (
                          <p className="table-preview-note">
                            Showing first {previewRows.length} of {snapshot.visible_row_count} visible rows.
                          </p>
                        ) : snapshot.row_filter_query.trim() !== "" && snapshot.visible_row_count === 0 ? (
                          <p className="table-preview-note">
                            No rows matched filter "{snapshot.row_filter_query}".
                          </p>
                        ) : null}
                      </div>
                      <details className="subpanel accordion">
                        <summary>Columns</summary>
                        <div className="subpanel-content">
                          <ul className="chip-list">
                            {snapshot.headers.map((header) => (
                              <li className="chip" key={header}>
                                <span className="chip-label">{header}</span>
                                <span className="chip-actions">
                                  <button onContextMenu={(event) => openColumnContextMenu(event, header, "x")} onClick={() => applyColumnSelection("x", header)}>X</button>
                                  <button onContextMenu={(event) => openColumnContextMenu(event, header, "y")} onClick={() => applyColumnSelection("y", header)}>Y</button>
                                  <button onContextMenu={(event) => openColumnContextMenu(event, header, "subgroup")} onClick={() => applyColumnSelection("subgroup", header)}>
                                    Group
                                  </button>
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </details>
                      <details className="subpanel accordion" open={isDataEditorWindow}>
                        <summary>Table Edit</summary>
                        <div className="subpanel-content">
                          <label>
                            Row Index
                            <input type="number" min="1" value={editRowIndex} onChange={(event) => setEditRowIndex(event.target.value)} />
                          </label>
                          <label>
                            Column Index
                            <input type="number" min="1" value={editColumnIndex} onChange={(event) => setEditColumnIndex(event.target.value)} />
                          </label>
                          <label>
                            Cell Value
                            <input value={editCellValue} onChange={(event) => setEditCellValue(event.target.value)} placeholder="10" />
                          </label>
                          <label>
                            New Column Name
                            <input
                              value={newColumnName}
                              onChange={(event) => setNewColumnName(event.target.value)}
                              placeholder="New Column"
                            />
                          </label>
                          <div className="actions">
                            <button
                              onClick={() => {
                                const rowIndex = parsePositiveIndex(editRowIndex);
                                const columnIndex = parsePositiveIndex(editColumnIndex);
                                if (rowIndex === null || columnIndex === null) {
                                  return;
                                }
                                runAction(() => editCell(rowIndex, columnIndex, editCellValue));
                              }}
                            >
                              Edit Cell
                            </button>
                            <button
                              onClick={() => {
                                const rowIndex = parsePositiveIndex(editRowIndex);
                                if (rowIndex === null) {
                                  return;
                                }
                                runAction(() => insertRow(rowIndex));
                              }}
                            >
                              Insert Row
                            </button>
                            <button
                              onClick={() => {
                                const rowIndex = parsePositiveIndex(editRowIndex);
                                if (rowIndex === null) {
                                  return;
                                }
                                runAction(() => removeRow(rowIndex));
                              }}
                            >
                              Remove Row
                            </button>
                            <button
                              onClick={() => {
                                const columnIndex = parsePositiveIndex(editColumnIndex);
                                if (columnIndex === null) {
                                  return;
                                }
                                runAction(() => insertColumn(columnIndex, newColumnName.trim() || "New Column"));
                              }}
                            >
                              Insert Column
                            </button>
                            <button
                              onClick={() => {
                                const columnIndex = parsePositiveIndex(editColumnIndex);
                                if (columnIndex === null) {
                                  return;
                                }
                                runAction(() => renameColumn(columnIndex, newColumnName.trim() || "New Name"));
                              }}
                            >
                              Rename Column
                            </button>
                            <button
                              onClick={() => {
                                const columnIndex = parsePositiveIndex(editColumnIndex);
                                if (columnIndex === null) {
                                  return;
                                }
                                runAction(() => removeColumn(columnIndex));
                              }}
                            >
                              Remove Column
                            </button>
                            <button onClick={() => runAction(fillDownSelection)}>Fill Down Selection</button>
                          </div>
                        </div>
                      </details>
                    </>
                  ) : null}
              </>
            </div>
          </article>
        </aside>

        {!isDataEditorWindow ? (
          <section className="workbench-focus">
            <article className="panel graph-panel graph-focus-panel">
              <div className="graph-panel-header">
                <div>
                  <h2>Graph</h2>
                  <p className="panel-caption panel-caption-compact">
                    {snapshot.current_graph_type} from {snapshot.visible_row_count}/{snapshot.row_count} visible rows.
                  </p>
                </div>
                <button type="button" onClick={() => runAction(exportGraphSvg)} title={`Saves as ${buildGraphExportName(snapshot)}`}>
                  Save SVG
                </button>
              </div>
              <div className="panel-body">
                <div className="graph-summary">
                  {renderOverviewItems(overviewItems, "graph-summary-wide")}
                </div>
                <div className="graph-canvas graph-canvas-focus" ref={graphCanvasRef}>
                  <GraphView snapshot={snapshot} graphType={graphType} yLogScale={yLogScale} />
                </div>
              </div>
            </article>
          </section>
        ) : null}

        {!isDataEditorWindow ? (
          <aside className="workbench-sidebar workbench-right">
            <article className="panel results-panel plot-config-panel">
              <div className="panel-header">
                <div>
                  <h2>Plot</h2>
                  <p className="panel-caption">
                    Choose the graph type, columns, row filter, and scale while looking at the table.
                  </p>
                </div>
              </div>
              <div className="panel-body">
                <label>
                  Graph Type
                  <select value={graphType} onChange={(event) => setGraphType(event.target.value)}>
                    {GRAPH_TYPES.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                    {!GRAPH_TYPES.includes(graphType) ? <option value={graphType}>{graphType}</option> : null}
                  </select>
                </label>
                <label>
                  Row Filter
                  <input value={rowFilter} onChange={(event) => setRowFilter(event.target.value)} placeholder="beta" />
                </label>
                <label>
                  X Column
                  <input value={xColumn} onChange={(event) => setXColumn(event.target.value)} placeholder="Category" />
                </label>
                <label>
                  Y Column
                  <input value={yColumn} onChange={(event) => setYColumn(event.target.value)} placeholder="Value" />
                </label>
                <label>
                  Sub-group
                  <input value={subgroupColumn} onChange={(event) => setSubgroupColumn(event.target.value)} placeholder="Group" />
                </label>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={yLogScale}
                    onChange={(event) => updateYLogScale(event.target.checked)}
                  />
                  Y Log Scale
                </label>
                <div className="actions">
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() =>
                      runAction(() =>
                        applyGraphControls(
                          graphType,
                          rowFilter,
                          xColumn,
                          yColumn,
                          subgroupColumn,
                          yLogScale,
                        ),
                      )
                    }
                  >
                    Apply Plot
                  </button>
                  <button type="button" onClick={() => runAction(exportGraphSvg)}>
                    Save SVG
                  </button>
                </div>
              </div>
            </article>

            <article className="panel results-panel analysis-panel">
              <div className="panel-header">
                <div>
                  <h2>Analysis</h2>
                  <p className="panel-caption">
                    Run statistics against the current X and Y columns.
                  </p>
                </div>
              </div>
              <div className="panel-body">
                <div className="analysis-quick-actions">
                  <button onClick={() => runAction(() => runOneWayAnovaAnalysis(xColumn, yColumn))}>
                    ANOVA
                  </button>
                  <button onClick={() => runAction(() => runPearsonCorrelationAnalysis(xColumn, yColumn))}>
                    Pearson
                  </button>
                  <button onClick={() => runAction(() => runLinearRegressionAnalysis(xColumn, yColumn))}>
                    Regression
                  </button>
                  <button onClick={() => runAction(() => runChiSquaredAnalysis(xColumn, yColumn))}>
                    Chi-Squared
                  </button>
                </div>
                <details className="subpanel accordion">
                  <summary>More analyses</summary>
                  <div className="subpanel-content">
                    <div className="actions">
                      <button onClick={() => runAction(() => runTukeyHsdAnalysis(xColumn, yColumn))}>
                        Run Tukey HSD
                      </button>
                      <button onClick={() => runAction(() => runShapiroWilkAnalysis(xColumn, yColumn))}>
                        Run Shapiro-Wilk
                      </button>
                      <button onClick={() => runAction(() => runMannWhitneyUAnalysis(xColumn, yColumn))}>
                        Run Mann-Whitney U
                      </button>
                      <button onClick={() => runAction(() => runIndependentTTestAnalysis(xColumn, yColumn))}>
                        Run Independent t-test
                      </button>
                      <button onClick={() => runAction(() => runWilcoxonSignedRankAnalysis(xColumn, yColumn))}>
                        Run Wilcoxon
                      </button>
                      <button onClick={() => runAction(() => runPairedTTestAnalysis(xColumn, yColumn))}>
                        Run Paired t-test
                      </button>
                      <button onClick={() => runAction(() => runKruskalWallisAnalysis(xColumn, yColumn))}>
                        Run Kruskal-Wallis
                      </button>
                      <button onClick={() => runAction(() => runDunnPostHocAnalysis(xColumn, yColumn))}>
                        Run Dunn
                      </button>
                      <button onClick={() => runAction(() => runFourPlRegressionAnalysis(xColumn, yColumn))}>
                        Run 4PL
                      </button>
                      <button onClick={() => runAction(() => runSpearmanCorrelationAnalysis(xColumn, yColumn))}>
                        Run Spearman
                      </button>
                      <button onClick={() => runAction(() => runTwoProportionAnalysis(xColumn, yColumn))}>
                        Run 2-Proportion
                      </button>
                      <button onClick={() => runAction(() => runChiSquaredAnalysis(xColumn, yColumn))}>
                        Run Chi-Squared
                      </button>
                    </div>
                  </div>
                </details>
              </div>
            </article>

            <article className="panel results-panel">
              <div className="panel-header">
                <div>
                  <h2>Results</h2>
                  <p className="panel-caption">
                    Keep the latest summary visible, then open log or notes only when you need them.
                  </p>
                </div>
                <TabStrip tabs={RESULTS_TABS} activeTab={resultsTab} onChange={setResultsTab} compact />
              </div>
              <div className="panel-body">
                {resultsTab === "summary" ? (
                <>
                  <div className="results-toolbar">
                    <button onClick={() => setErrorMessage("")} disabled={!errorMessage}>
                      Clear Error
                    </button>
                    <button onClick={() => refreshSnapshot().catch(() => {})}>Refresh</button>
                  </div>
                  <div className="results-overview">
                    <div className="results-summary">{renderSummaryCards(resultsCards)}</div>
                    <div className="results-preview-card" title={displayedResults}>
                      <span>Analysis Preview</span>
                      <strong>{displayedResultsSummary.title || "No results yet"}</strong>
                      <p className="results-preview-note">Latest analysis output or error text.</p>
                      {displayedResultsSummary.summary ? (
                        <p>{displayedResultsSummary.summary}</p>
                      ) : null}
                    </div>
                  </div>
                  {errorMessage ? (
                    <div className="results-alert">
                      <div>
                        <strong>Error</strong>
                        <p>{errorMessage}</p>
                      </div>
                    </div>
                  ) : null}
                  {!errorMessage ? (
                    <div className="results-status">
                      <span>Status</span>
                      <strong>{snapshot.status_message}</strong>
                    </div>
                  ) : null}
                  {graphAnnotationSummary.title || graphAnnotationSummary.summary ? (
                    <details className="subpanel accordion" open>
                      <summary>Annotation Summary</summary>
                      <div className="subpanel-content">
                        <div className="results-annotation-card" title={snapshot.graph_annotation_summary || ""}>
                          <strong>{graphAnnotationSummary.title || "Post-hoc annotations"}</strong>
                          {graphAnnotationSummary.summary ? <p>{graphAnnotationSummary.summary}</p> : null}
                        </div>
                      </div>
                    </details>
                  ) : null}
                </>
              ) : null}
              {resultsTab === "log" ? (
                <details className="subpanel accordion" open>
                  <summary>Detailed Log</summary>
                  <div className="subpanel-content">
                    <div className="results-output-card" title={displayedResults}>
                      <strong>{displayedResultsSummary.title || "No output yet"}</strong>
                      {displayedResultsSummary.summary ? <p>{displayedResultsSummary.summary}</p> : null}
                      <pre>{displayedResults}</pre>
                    </div>
                  </div>
                </details>
              ) : null}
              {resultsTab === "annotations" ? (
                graphAnnotationSummary.title || graphAnnotationSummary.summary ? (
                  <details className="subpanel accordion" open>
                    <summary>Annotation Summary</summary>
                    <div className="subpanel-content">
                      <div className="results-annotation-card" title={snapshot.graph_annotation_summary || ""}>
                        <strong>{graphAnnotationSummary.title || "Post-hoc annotations"}</strong>
                        {graphAnnotationSummary.summary ? <p>{graphAnnotationSummary.summary}</p> : null}
                      </div>
                    </div>
                  </details>
                ) : (
                  <div className="results-status">
                    <span>Notes</span>
                    <strong>No graph annotations yet</strong>
                  </div>
                )
                ) : null}
              </div>
            </article>
          </aside>
        ) : null}
      </section>

      {renderContextMenu()}

      {showAbout ? (
        <div
          className="modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-label="About Calcite"
          onClick={() => setShowAbout(false)}
        >
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>About Calcite</h2>
                <p>Rust/Tauri desktop shell for Calcite migration work.</p>
              </div>
              <button onClick={() => setShowAbout(false)}>Close</button>
            </div>
            <div className="modal-body">
              <section>
                <h3>License</h3>
                <p>
                  Calcite is distributed under the MIT License. The project license text is stored in
                  <code>LICENSES/LICENSES_calcite.txt</code>.
                </p>
              </section>
              <section>
                <h3>Bundled notices</h3>
                <ul>
                  <li><code>LICENSES/LICENSES_numpy.txt</code></li>
                  <li><code>LICENSES/LICENSES_pandas.txt</code></li>
                  <li><code>LICENSES/LICENSES_scipy.txt</code></li>
                  <li><code>LICENSES/LICENSES_statsmodels.txt</code></li>
                  <li><code>LICENSES/LICENSES_matplotlib.txt</code></li>
                  <li><code>LICENSES/LICENSES_scikit-posthocs.txt</code></li>
                  <li><code>LICENSES/LICENSES_statannotations.txt</code></li>
                </ul>
              </section>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
