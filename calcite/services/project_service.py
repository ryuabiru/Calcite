from __future__ import annotations

import io
import json
import os
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype


PROJECT_SCHEMA_VERSION = 2
MANIFEST_FILENAME = "manifest.json"
DATAFRAME_FILENAME = "tables/main.csv"
SETTINGS_FILENAME = "state/settings.json"
ANALYSIS_FILENAME = "state/analysis.json"


class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Series):
            return obj.tolist()
        if isinstance(
            obj,
            (
                np.int_,
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            return int(obj)
        if isinstance(obj, (np.float64, np.float16, np.float32)):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


@dataclass(frozen=True)
class ProjectState:
    dataframe: pd.DataFrame | None
    settings: dict
    statistical_annotations: list
    paired_annotations: list
    regression_line_params: dict | None
    fit_params: dict | None


def optimize_imported_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    optimized_df = df.copy()
    for col in optimized_df.columns:
        if not (is_object_dtype(optimized_df[col]) or is_string_dtype(optimized_df[col])):
            continue
        num_unique_values = optimized_df[col].nunique()
        num_total_values = len(optimized_df[col])
        if num_total_values and num_unique_values / num_total_values < 0.5:
            optimized_df[col] = optimized_df[col].astype("category")
    return optimized_df


def dataframe_from_clipboard_text(text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(text), sep="\t")


def write_project_archive(file_path: str, state: ProjectState) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        manifest = {
            "schema_version": PROJECT_SCHEMA_VERSION,
            "files": {
                "dataframe": DATAFRAME_FILENAME if state.dataframe is not None else None,
                "settings": SETTINGS_FILENAME,
                "analysis": ANALYSIS_FILENAME,
            },
        }

        if state.dataframe is not None:
            _write_csv(os.path.join(temp_dir, DATAFRAME_FILENAME), state.dataframe)

        _write_json(os.path.join(temp_dir, SETTINGS_FILENAME), state.settings)

        analysis_data = {
            "statistical_annotations": state.statistical_annotations,
            "paired_annotations": state.paired_annotations,
            "regression_line_params": state.regression_line_params,
            "fit_params": state.fit_params,
        }
        _write_json(os.path.join(temp_dir, ANALYSIS_FILENAME), analysis_data, cls=NumpyArrayEncoder)
        _write_json(os.path.join(temp_dir, MANIFEST_FILENAME), manifest)

        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, temp_dir)
                    zf.write(full_path, arcname)


def read_project_archive(file_path: str) -> ProjectState:
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(file_path, "r") as zf:
            zf.extractall(temp_dir)

        manifest = _read_manifest(temp_dir)
        file_map = _resolve_project_files(manifest)

        dataframe = _read_csv_if_exists(os.path.join(temp_dir, file_map["dataframe"]))
        settings = _read_json_if_exists(os.path.join(temp_dir, file_map["settings"]))
        analysis_data = _read_json_if_exists(os.path.join(temp_dir, file_map["analysis"]))

    return ProjectState(
        dataframe=dataframe,
        settings=settings,
        statistical_annotations=analysis_data.get("statistical_annotations", []),
        paired_annotations=analysis_data.get("paired_annotations", []),
        regression_line_params=_restore_regression_line_params(analysis_data.get("regression_line_params")),
        fit_params=_restore_fit_params(analysis_data.get("fit_params")),
    )


def _write_csv(file_path: str, dataframe: pd.DataFrame) -> None:
    _ensure_parent_dir(file_path)
    dataframe.to_csv(file_path, index=False)


def _write_json(file_path: str, payload: dict, cls: type[json.JSONEncoder] | None = None) -> None:
    _ensure_parent_dir(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, cls=cls)


def _ensure_parent_dir(file_path: str) -> None:
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)


def _read_manifest(temp_dir: str) -> dict:
    manifest_path = os.path.join(temp_dir, MANIFEST_FILENAME)
    if not os.path.exists(manifest_path):
        return {"schema_version": 1}
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_project_files(manifest: dict) -> dict:
    if manifest.get("schema_version", 1) < 2:
        return {
            "dataframe": "data.csv",
            "settings": "settings.json",
            "analysis": "analysis.json",
        }

    files = manifest.get("files", {})
    return {
        "dataframe": files.get("dataframe") or "",
        "settings": files.get("settings") or SETTINGS_FILENAME,
        "analysis": files.get("analysis") or ANALYSIS_FILENAME,
    }


def _read_csv_if_exists(file_path: str) -> pd.DataFrame | None:
    if not file_path or not os.path.exists(file_path):
        return None
    return pd.read_csv(file_path)


def _read_json_if_exists(file_path: str) -> dict:
    if not file_path or not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _restore_regression_line_params(reg_params):
    if not reg_params:
        return reg_params
    if "x_line" in reg_params:
        reg_params["x_line"] = np.array(reg_params["x_line"])
        reg_params["y_line"] = np.array(reg_params["y_line"])
        return reg_params
    for group in reg_params:
        reg_params[group]["x_line"] = np.array(reg_params[group]["x_line"])
        reg_params[group]["y_line"] = np.array(reg_params[group]["y_line"])
    return reg_params


def _restore_fit_params(fit_params):
    if not fit_params:
        return fit_params
    if "params" in fit_params:
        fit_params["params"] = np.array(fit_params["params"])
        fit_params["log_x_data"] = np.array(fit_params["log_x_data"])
        return fit_params
    for group in fit_params:
        fit_params[group]["params"] = np.array(fit_params[group]["params"])
        fit_params[group]["log_x_data"] = np.array(fit_params[group]["log_x_data"])
    return fit_params
