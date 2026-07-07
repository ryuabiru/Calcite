import { useEffect, useState } from "react";

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
  removeColumn,
  removeRow,
  saveProject,
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
  const [graphType, setGraphType] = useState("Bar Chart");
  const [rowFilter, setRowFilter] = useState("");
  const [xColumn, setXColumn] = useState("");
  const [yColumn, setYColumn] = useState("");
  const [subgroupColumn, setSubgroupColumn] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

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

  async function runAction(action) {
    try {
      await action();
      await refreshSnapshot();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setErrorMessage(message);
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

  const displayedStatus = errorMessage ? "Error" : snapshot.status_message;
  const displayedResults = errorMessage || snapshot.results_preview;
  const previewRows = snapshot.rows.slice(0, 25);
  const previewRowOffset = previewRows.length > 0 ? 1 : 0;

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
                <button onClick={() => runAction(() => saveProject(projectDir.trim()))}>Save Project</button>
                <button onClick={() => runAction(() => loadProject(projectDir.trim()))}>Load Project</button>
                <button onClick={() => runAction(() => exportCsv(csvPath.trim()))}>Export CSV</button>
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
                  <li className="chip" key={header}>{header}</li>
                ))}
              </ul>
            </div>
            <div className="subpanel">
              <div className="subpanel-heading">
                <h3>Table Preview</h3>
                <span>{snapshot.row_count} rows total</span>
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
                          <th key={`${header}-${columnIndex}`}>{header}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewRows.map((row, rowIndex) => (
                        <tr key={`preview-row-${rowIndex}`}>
                          <th className="row-index-cell">{rowIndex + previewRowOffset}</th>
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
              {snapshot.rows.length > previewRows.length ? (
                <p className="table-preview-note">
                  Showing first {previewRows.length} of {snapshot.rows.length} rows.
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
