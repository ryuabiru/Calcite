import { useEffect, useRef, useState } from "react";

import {
  applyGraphControls,
  editCell,
  exportCsv,
  getSnapshot,
  importDelimitedText,
  insertColumn,
  insertRow,
  loadCsv,
  loadProject,
  pivotData,
  removeColumn,
  removeRow,
  restructureData,
  saveProject,
  runKruskalWallisAnalysis,
  runMannWhitneyUAnalysis,
  runLinearRegressionAnalysis,
  runIndependentTTestAnalysis,
  runOneWayAnovaAnalysis,
  runFourPlRegressionAnalysis,
  runShapiroWilkAnalysis,
  runPairedTTestAnalysis,
  runPearsonCorrelationAnalysis,
  runSpearmanCorrelationAnalysis,
  runTwoProportionAnalysis,
  runWilcoxonSignedRankAnalysis,
  toggleSortByColumn,
} from "./api";

const EMPTY_SNAPSHOT = {
  status_message: "Ready",
  results_preview: "Rust backend will stream summaries here.",
  current_graph_type: "Bar Chart",
  loaded_file_name: null,
  row_count: 0,
  column_count: 0,
  x_column: "",
  y_column: "",
  subgroup_column: "",
  row_filter_query: "",
  visible_row_count: 0,
  selected_row_count: 0,
  sort_column: null,
  sort_ascending: true,
  visible_row_indices: [],
  headers: [],
  rows: [],
};

function parsePositiveIndex(value) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed - 1 : null;
}

export default function App() {
  const [snapshot, setSnapshot] = useState(EMPTY_SNAPSHOT);
  const [csvPath, setCsvPath] = useState("");
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
  const [graphType, setGraphType] = useState("Bar Chart");
  const [rowFilter, setRowFilter] = useState("");
  const [xColumn, setXColumn] = useState("");
  const [yColumn, setYColumn] = useState("");
  const [subgroupColumn, setSubgroupColumn] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const hasLoadedProjectDir = useRef(false);

  async function refreshSnapshot() {
    try {
      const nextSnapshot = await getSnapshot();
      setSnapshot(nextSnapshot);
      setGraphType(nextSnapshot.current_graph_type);
      setRowFilter(nextSnapshot.row_filter_query);
      setXColumn(nextSnapshot.x_column);
      setYColumn(nextSnapshot.y_column);
      setSubgroupColumn(nextSnapshot.subgroup_column);
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
    }
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

  const displayedStatus = errorMessage ? "Error" : snapshot.status_message;
  const displayedResults = errorMessage || snapshot.results_preview;
  const visibleRowIndices =
    snapshot.visible_row_indices.length > 0 || snapshot.row_filter_query.trim() !== ""
      ? snapshot.visible_row_indices
      : snapshot.rows.map((_, index) => index);
  const previewRowIndices = visibleRowIndices.slice(0, 25);
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
      applyGraphControls(graphType, rowFilter, nextXColumn, nextYColumn, nextSubgroupColumn),
    );
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Calcite Tauri Bootstrap</p>
          <h1>Rust backend, React UI shell.</h1>
          <p className="lede">
            Calcite is moving to Tauri as the primary desktop shell. This scaffold now separates a
            React frontend from the Rust command bridge and keeps the four-pane workspace in place.
          </p>
        </div>
        <div className="status-card">
          <div><span>Status</span><strong>{displayedStatus}</strong></div>
          <div><span>File</span><strong>{snapshot.loaded_file_name || "-"}</strong></div>
          <div><span>Graph</span><strong>{snapshot.current_graph_type}</strong></div>
          <div><span>Rows</span><strong>{snapshot.row_count}</strong></div>
          <div><span>Columns</span><strong>{snapshot.column_count}</strong></div>
          <div><span>Visible</span><strong>{snapshot.visible_row_count}</strong></div>
          <div><span>Selected</span><strong>{snapshot.selected_row_count}</strong></div>
        </div>
      </section>

      <section className="workspace-grid">
        <article className="panel dataframe-panel">
          <h2>DataFrame</h2>
          <div className="panel-body">
            <label>
              CSV Path
              <input value={csvPath} onChange={(event) => setCsvPath(event.target.value)} placeholder="/path/to/data.csv" />
            </label>
            <textarea
              value={csvInput}
              onChange={(event) => setCsvInput(event.target.value)}
              placeholder={"name,value\nA,1\nB,2"}
            />
            <div className="actions">
              <button onClick={() => runAction(() => loadCsv(csvPath.trim()))}>Load CSV Path</button>
              <button onClick={() => runAction(() => importDelimitedText(csvInput, "clipboard"))}>Import CSV Text</button>
              <button onClick={() => setCsvInput("Category,Value\nA,1\nB,2\nC,3")}>Load Sample</button>
            </div>
            <div className="subpanel">
              <h3>Project</h3>
              <label>
                Save Directory
                <input
                  value={projectDir}
                  onChange={(event) => setProjectDir(event.target.value)}
                  placeholder="/path/to/project-dir"
                />
              </label>
              <div className="actions">
                <button onClick={() => runProjectDirAction(() => saveProject(projectDir), projectDir)}>
                  Save Project
                </button>
                <button onClick={() => runProjectDirAction(() => loadProject(projectDir), projectDir)}>
                  Load Project
                </button>
                <button
                  onClick={() => {
                    const rememberedProjectDir = window.localStorage.getItem("calcite.projectDir");
                    if (!rememberedProjectDir) {
                      return;
                    }
                    runProjectDirAction(() => loadProject(rememberedProjectDir), rememberedProjectDir);
                  }}
                >
                  Restore Last Project
                </button>
                <button onClick={() => runAction(() => exportCsv(csvPath.trim()))}>Export CSV</button>
              </div>
            </div>
            <div className="subpanel">
              <h3>Reshape</h3>
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
            <div className="subpanel">
              <h3>Pivot</h3>
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
            <div className="subpanel">
              <h3>Table Edit</h3>
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
                    runAction(() => removeColumn(columnIndex));
                  }}
                >
                  Remove Column
                </button>
              </div>
            </div>
            <div className="subpanel">
              <h3>Columns</h3>
              <ul className="chip-list">
                {snapshot.headers.map((header) => (
                  <li className="chip" key={header}>
                    <span className="chip-label">{header}</span>
                    <span className="chip-actions">
                      <button onClick={() => applyColumnSelection("x", header)}>X</button>
                      <button onClick={() => applyColumnSelection("y", header)}>Y</button>
                      <button onClick={() => applyColumnSelection("subgroup", header)}>
                        Group
                      </button>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="subpanel">
              <div className="subpanel-heading">
                <h3>Table Preview</h3>
                <span>{snapshot.visible_row_count} visible rows</span>
              </div>
              {snapshot.headers.length === 0 ? (
                <div className="table-empty">Load a CSV to render the table preview.</div>
              ) : (
                <div className="table-preview-scroll">
                  <table className="table-preview">
                    <thead>
                      <tr>
                        <th className="row-index-cell">#</th>
                        {snapshot.headers.map((header, columnIndex) => (
                          <th key={`${header}-${columnIndex}`}>
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
                        <tr key={`preview-row-${rowIndex}`}>
                          <th className="row-index-cell">{rowIndex + 1}</th>
                          {snapshot.headers.map((_, columnIndex) => (
                            <td key={`${rowIndex}-${columnIndex}`}>
                              {row[columnIndex] ?? ""}
                            </td>
                          ))}
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
          </div>
        </article>

        <article className="panel properties-panel">
          <h2>Properties</h2>
          <div className="panel-body">
            <label>
              Graph Type
              <input value={graphType} onChange={(event) => setGraphType(event.target.value)} />
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
            <div className="actions">
              <button
                onClick={() =>
                  runAction(() =>
                    applyGraphControls(graphType, rowFilter, xColumn, yColumn, subgroupColumn),
                  )
                }
              >
                Apply
              </button>
              <button onClick={() => refreshSnapshot().catch(() => {})}>Refresh</button>
            </div>
            <div className="actions">
              <button onClick={() => runAction(() => runOneWayAnovaAnalysis(xColumn, yColumn))}>
                Run ANOVA
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
              <button onClick={() => runAction(() => runLinearRegressionAnalysis(xColumn, yColumn))}>
                Run Linear Regression
              </button>
              <button onClick={() => runAction(() => runFourPlRegressionAnalysis(xColumn, yColumn))}>
                Run 4PL
              </button>
              <button
                onClick={() =>
                  runAction(() => runPearsonCorrelationAnalysis(xColumn, yColumn))
                }
              >
                Run Pearson
              </button>
              <button
                onClick={() =>
                  runAction(() => runSpearmanCorrelationAnalysis(xColumn, yColumn))
                }
              >
                Run Spearman
              </button>
              <button onClick={() => runAction(() => runTwoProportionAnalysis(xColumn, yColumn))}>
                Run 2-Proportion
              </button>
            </div>
          </div>
        </article>

        <article className="panel graph-panel">
          <h2>Graph</h2>
          <div className="panel-body">
            <div className="graph-summary">
              <div><span>Type</span><strong>{snapshot.current_graph_type}</strong></div>
              <div><span>X</span><strong>{snapshot.x_column || "-"}</strong></div>
              <div><span>Y</span><strong>{snapshot.y_column || "-"}</strong></div>
              <div><span>Sub-group</span><strong>{snapshot.subgroup_column || "-"}</strong></div>
            </div>
            <div className="graph-canvas">
              The Rust graph pipeline will be connected here.
            </div>
          </div>
        </article>

        <article className="panel results-panel">
          <h2>Results</h2>
          <div className="panel-body">
            <pre>{displayedResults}</pre>
          </div>
        </article>
      </section>
    </main>
  );
}
