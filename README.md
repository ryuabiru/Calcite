# Calcite

**Calcite** is a desktop application designed for scientists, researchers, and students who need to perform data analysis and create publication-quality graphs without writing code. It provides a seamless workflow from data import to final plot export, all within a single, user-friendly interface.

[日本語のREADMEはこちら (Japanese README here)](README_ja.md)

## ✨ Features

- **Intuitive Data Handling**:
  - Import data from CSV files or paste directly from spreadsheets (e.g., Excel).
  - An interactive table view for easy data editing, sorting, and manipulation.
  - Powerful data reshaping tools (wide-to-long and long-to-wide).
  - Advanced filtering with multiple conditions (AND/OR).
  - Create new columns using mathematical formulas.

- **Publication-Quality Graphing**:
  - A wide variety of plot types: Scatter, Bar, Box, Violin, Point, and Line plots.
  - Extensive customization options: colors, markers, line styles, fonts, axis ranges, log scales, and more.
  - "Prism-style" aesthetics with top and right spines removed by default.
  - Overlay individual data points on summary plots.

- **Comprehensive Statistical Analysis**:
  - **Basic Tests**: Independent & Paired t-tests, Mann-Whitney U, Wilcoxon signed-rank.
  - **Group Comparisons**: One-way ANOVA & Kruskal-Wallis with post-hoc tests (Tukey, Dunn).
  - **Regression**: Linear and non-linear (4-parameter logistic, 4PL) regression on raw or summarized data.
  - **Correlations & Associations**: Spearman's correlation and Chi-squared tests.
  - **Automatic Annotations**: Automatically add statistical significance (`*`) to your plots.

- **High-Resolution Export**:
  - Save your graphs as PNG, JPEG, SVG, or PDF at 300 DPI, ready for any publication or presentation.

## 🛠️ Installation

Calcite is available on PyPI and can be installed with pip. Python 3.10 or higher is required.

```bash
pip install calcite
````

## 🚀 Quick Start

1. Launch Calcite from your terminal:

    ```bash
    calcite
    ```

2. Import data using **File \> Open CSV...** or paste from your clipboard using **Edit \> Paste**.
3. Select a graph type from the toolbar (e.g., Scatter Plot, Bar Chart).
4. In the **"Data"** tab, select the columns for the X and Y axes.
5. Customize the graph's appearance using the **"Format," "Text & Legend,"** and **"Axis"** tabs.
6. Perform statistical analysis from the **"Analysis"** menu.
7. Save your graph using **File \> Save Graph As...**.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
