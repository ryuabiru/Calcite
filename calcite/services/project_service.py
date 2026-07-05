from __future__ import annotations

import io
import json
import os
import tempfile
import zipfile
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype


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
        if state.dataframe is not None:
            state.dataframe.to_csv(os.path.join(temp_dir, "data.csv"), index=False)

        with open(os.path.join(temp_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump(state.settings, f, indent=4)

        analysis_data = {
            "statistical_annotations": state.statistical_annotations,
            "paired_annotations": state.paired_annotations,
            "regression_line_params": state.regression_line_params,
            "fit_params": state.fit_params,
        }
        with open(os.path.join(temp_dir, "analysis.json"), "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=4, cls=NumpyArrayEncoder)

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

        dataframe = None
        csv_path = os.path.join(temp_dir, "data.csv")
        if os.path.exists(csv_path):
            dataframe = pd.read_csv(csv_path)

        settings = {}
        settings_path = os.path.join(temp_dir, "settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

        analysis_data = {}
        analysis_path = os.path.join(temp_dir, "analysis.json")
        if os.path.exists(analysis_path):
            with open(analysis_path, "r", encoding="utf-8") as f:
                analysis_data = json.load(f)

    return ProjectState(
        dataframe=dataframe,
        settings=settings,
        statistical_annotations=analysis_data.get("statistical_annotations", []),
        paired_annotations=analysis_data.get("paired_annotations", []),
        regression_line_params=_restore_regression_line_params(analysis_data.get("regression_line_params")),
        fit_params=_restore_fit_params(analysis_data.get("fit_params")),
    )


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
