# Calcite

**Calcite** is a desktop application designed for scientists, researchers, and students who need to perform data analysis and create publication-quality graphs without writing code. It provides a seamless workflow from data import to final plot export, all within a single, user-friendly interface.

[日本語のREADMEはこちら (Japanese README here)](README_ja.md)

## ✨ Features

### **Intuitive Data Handling**

- **Versatile Import**: Import data from CSV files or paste directly from spreadsheets (e.g., Excel) via the clipboard.
- **Interactive Table**:
  - Sort data in ascending/descending order with a single click or edit column names with a double click.
  - Export the current state of the data (after filtering or sorting) to a new CSV file.
- **Advanced Data Manipulation**:
  - **Reshaping**: Easily convert data between wide and long formats using a graphical interface.
  - **Filtering**: A powerful and advanced filtering tool allows for combining multiple conditions using AND/OR logic.
  - **Column Calculation**: Dynamically create new columns using formulas like `'ColumnA' * 100`.

### **Publication-Quality Graphing**

- **Variety of Plot Types**: Supports a wide range of plots, including Scatter, Bar, Box, Violin, Point, Line, and Paired Scatter plots.
- **Extensive Customization**:
  - Fine-tune every aspect of your plot from the GUI, including colors, markers, line styles, font sizes, axis ranges, and log scales.
  - Apply a "Prism-style" aesthetic by removing the top and right spines of the graph.
  - Overlay individual data points on summary plots like bar charts and box plots.

### **Comprehensive Statistical Analysis**

- **Basic Tests**: Independent & Paired t-tests, Mann-Whitney U, Wilcoxon signed-rank.
- **Group Comparisons**: One-way ANOVA & Kruskal-Wallis with post-hoc tests (Tukey, Dunn).
- **Regression**: Linear and non-linear (4-parameter logistic, 4PL) regression, with R² values displayed on the graph.
- **Correlations & Associations**: Spearman's correlation and Chi-squared tests.
- **Automatic Annotations**: Automatically adds statistical significance (`*`) to your plots based on the robust logic of the `statannotations` library.

e.g.
![e.g. Owe way anova](/images/one_way_anova.jpg)

### **High-Resolution Export**

- Save your graphs as PNG, JPEG, SVG, or PDF at 300 DPI, ready for any publication or presentation.

## 🛠️ Installation

This project is currently under development. The active desktop implementation lives in `rust/` and `tauri/`.

```bash
cd rust
cargo run
```

## 🧪 Rust Bootstrap

The repository now includes an early Rust migration bootstrap under [`rust/`](./rust) plus a Tauri GUI scaffold under [`tauri/`](./tauri).

- [`rust/`](./rust) contains the Rust core, data model, persistence, and the temporary `eframe/egui` shell used for migration validation.
- [`tauri/`](./tauri) contains the new Web UI direction for the Rust desktop shell.

Run the current Rust shell with:

```bash
cd rust
cargo run
```

Run the Tauri desktop scaffold with:

```bash
cd tauri
npm install
npm run tauri:dev
```

The repository is now Rust-first. The legacy Python runtime and test harness have been retired.

## 🚀 Quick Start

1. Launch the Rust/Tauri app from the `tauri/` workspace.

2. Import data using the Rust table workflow.

   - **💡 Tidy Data format (=Long-form) is recommended**
   - Calcite is designed around the principles of **Tidy Data**. This is a data structure where:
     - **Each variable forms a column** (e.g., "Genotype", "Concentration", "Measurement").
     - **Each observation forms a row**.
     - **Each type of observational unit forms a table**.
   - This format is the most suitable for statistical analysis and graphing on a computer. If your data is in a "wide" format (e.g., separate columns for Control Group, Drug A Group, etc.), you can easily convert it to Tidy Data using Calcite's **Data \> Restructure (Wide to Long)...** feature.

    Tidy data (Ref. Seaborn)
    (<https://seaborn.pydata.org/tutorial/data_structure.html>)
    ![Tidy data](./images/Tidy%20data.png)

3. Select a graph type from the toolbar.

4. Select the columns for the X and Y axes in the data controls.

5. Customize the graph's appearance using the Rust UI controls.

6. Perform statistical analysis from the Rust analysis controls.

7. Save your graph using **File \> Save Graph As...**.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
