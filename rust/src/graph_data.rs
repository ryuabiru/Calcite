use std::collections::HashMap;

use crate::state::{DataTable, TableViewState};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BarSegment {
    pub label: String,
    pub count: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BarChartData {
    pub column_name: String,
    pub segments: Vec<BarSegment>,
    pub visible_row_count: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StackedBarSubgroupSegment {
    pub label: String,
    pub count: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StackedBarCategory {
    pub label: String,
    pub segments: Vec<StackedBarSubgroupSegment>,
    pub total_count: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StackedBarChartData {
    pub category_column_name: String,
    pub subgroup_column_name: String,
    pub categories: Vec<StackedBarCategory>,
    pub visible_row_count: usize,
}

#[derive(Clone, Debug, PartialEq)]
pub struct CorrelationHeatmapData {
    pub column_names: Vec<String>,
    pub values: Vec<Vec<Option<f64>>>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct HeatmapChartData {
    pub row_column_name: String,
    pub column_column_name: String,
    pub row_labels: Vec<String>,
    pub column_labels: Vec<String>,
    pub counts: Vec<Vec<usize>>,
    pub visible_row_count: usize,
}

pub fn build_bar_chart_data(
    table: &DataTable,
    table_view: &TableViewState,
    column_name: &str,
) -> Option<BarChartData> {
    let column_index = table
        .headers
        .iter()
        .position(|header| header == column_name)?;
    let row_indices: Vec<usize> = if table_view.visible_row_indices.is_empty() {
        (0..table.rows.len()).collect()
    } else {
        table_view.visible_row_indices.clone()
    };

    if row_indices.is_empty() {
        return None;
    }

    let mut counts_by_label: HashMap<String, usize> = HashMap::new();
    let mut order: Vec<String> = Vec::new();

    for row_index in row_indices.iter().copied() {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let value = row
            .get(column_index)
            .map(String::as_str)
            .unwrap_or("")
            .trim();
        let label = if value.is_empty() {
            "(empty)".to_owned()
        } else {
            value.to_owned()
        };

        if !counts_by_label.contains_key(&label) {
            order.push(label.clone());
        }
        *counts_by_label.entry(label).or_insert(0) += 1;
    }

    if counts_by_label.is_empty() {
        return None;
    }

    let segments = order
        .into_iter()
        .map(|label| BarSegment {
            count: counts_by_label.get(&label).copied().unwrap_or(0),
            label,
        })
        .collect();

    Some(BarChartData {
        column_name: column_name.to_owned(),
        segments,
        visible_row_count: row_indices.len(),
    })
}

pub fn build_stacked_bar_chart_data(
    table: &DataTable,
    table_view: &TableViewState,
    category_column_name: &str,
    subgroup_column_name: &str,
) -> Option<StackedBarChartData> {
    let category_index = table
        .headers
        .iter()
        .position(|header| header == category_column_name)?;
    let subgroup_index = table
        .headers
        .iter()
        .position(|header| header == subgroup_column_name)?;
    let row_indices: Vec<usize> = if table_view.visible_row_indices.is_empty() {
        (0..table.rows.len()).collect()
    } else {
        table_view.visible_row_indices.clone()
    };

    if row_indices.is_empty() {
        return None;
    }

    let mut category_order: Vec<String> = Vec::new();
    let mut subgroup_order: Vec<String> = Vec::new();
    let mut counts: HashMap<(String, String), usize> = HashMap::new();
    let mut total_counts: HashMap<String, usize> = HashMap::new();

    for row_index in row_indices.iter().copied() {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let category_label = normalize_label(row.get(category_index).map(String::as_str));
        let subgroup_label = normalize_label(row.get(subgroup_index).map(String::as_str));

        if !counts.contains_key(&(category_label.clone(), subgroup_label.clone())) {
            if !category_order.contains(&category_label) {
                category_order.push(category_label.clone());
            }
            if !subgroup_order.contains(&subgroup_label) {
                subgroup_order.push(subgroup_label.clone());
            }
        }

        *counts
            .entry((category_label.clone(), subgroup_label.clone()))
            .or_insert(0) += 1;
        *total_counts.entry(category_label).or_insert(0) += 1;
    }

    if category_order.is_empty() || subgroup_order.is_empty() {
        return None;
    }

    let categories = category_order
        .into_iter()
        .map(|category_label| {
            let segments = subgroup_order
                .iter()
                .map(|subgroup_label| StackedBarSubgroupSegment {
                    label: subgroup_label.clone(),
                    count: counts
                        .get(&(category_label.clone(), subgroup_label.clone()))
                        .copied()
                        .unwrap_or(0),
                })
                .collect::<Vec<_>>();
            let total_count = total_counts.get(&category_label).copied().unwrap_or(0);
            StackedBarCategory {
                label: category_label,
                segments,
                total_count,
            }
        })
        .collect::<Vec<_>>();

    Some(StackedBarChartData {
        category_column_name: category_column_name.to_owned(),
        subgroup_column_name: subgroup_column_name.to_owned(),
        categories,
        visible_row_count: row_indices.len(),
    })
}

fn normalize_label(value: Option<&str>) -> String {
    let value = value.unwrap_or("").trim();
    if value.is_empty() {
        "(empty)".to_owned()
    } else {
        value.to_owned()
    }
}

pub fn build_correlation_heatmap_data(table: &DataTable) -> Option<CorrelationHeatmapData> {
    let numeric_columns: Vec<(usize, String)> = table
        .column_metadata()
        .iter()
        .filter(|metadata| matches!(metadata.kind, crate::state::ColumnKind::Numeric))
        .map(|metadata| (metadata.index, metadata.name.clone()))
        .collect();

    if numeric_columns.len() < 2 {
        return None;
    }

    let mut values = vec![vec![None; numeric_columns.len()]; numeric_columns.len()];
    for left_index in 0..numeric_columns.len() {
        for right_index in left_index..numeric_columns.len() {
            let correlation = pearson_correlation(
                table,
                numeric_columns[left_index].0,
                numeric_columns[right_index].0,
            );
            values[left_index][right_index] = correlation;
            values[right_index][left_index] = correlation;
        }
    }

    Some(CorrelationHeatmapData {
        column_names: numeric_columns.into_iter().map(|(_, name)| name).collect(),
        values,
    })
}

pub fn build_heatmap_chart_data(
    table: &DataTable,
    table_view: &TableViewState,
    row_column_name: &str,
    column_column_name: &str,
) -> Option<HeatmapChartData> {
    let row_index = table
        .headers
        .iter()
        .position(|header| header == row_column_name)?;
    let column_index = table
        .headers
        .iter()
        .position(|header| header == column_column_name)?;
    let row_indices: Vec<usize> = if table_view.visible_row_indices.is_empty() {
        (0..table.rows.len()).collect()
    } else {
        table_view.visible_row_indices.clone()
    };

    if row_indices.is_empty() {
        return None;
    }

    let mut row_labels: Vec<String> = Vec::new();
    let mut column_labels: Vec<String> = Vec::new();
    let mut counts: HashMap<(String, String), usize> = HashMap::new();

    for row_index_value in row_indices.iter().copied() {
        let Some(row) = table.rows.get(row_index_value) else {
            continue;
        };
        let row_label = normalize_label(row.get(row_index).map(String::as_str));
        let column_label = normalize_label(row.get(column_index).map(String::as_str));

        if !row_labels.contains(&row_label) {
            row_labels.push(row_label.clone());
        }
        if !column_labels.contains(&column_label) {
            column_labels.push(column_label.clone());
        }

        *counts.entry((row_label, column_label)).or_insert(0) += 1;
    }

    if row_labels.is_empty() || column_labels.is_empty() {
        return None;
    }

    let matrix = row_labels
        .iter()
        .map(|row_label| {
            column_labels
                .iter()
                .map(|column_label| {
                    counts
                        .get(&(row_label.clone(), column_label.clone()))
                        .copied()
                        .unwrap_or(0)
                })
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();

    Some(HeatmapChartData {
        row_column_name: row_column_name.to_owned(),
        column_column_name: column_column_name.to_owned(),
        row_labels,
        column_labels,
        counts: matrix,
        visible_row_count: row_indices.len(),
    })
}

fn pearson_correlation(table: &DataTable, left_index: usize, right_index: usize) -> Option<f64> {
    let mut pairs: Vec<(f64, f64)> = Vec::new();
    for row in &table.rows {
        let Some(left_cell) = row.get(left_index) else {
            continue;
        };
        let Some(right_cell) = row.get(right_index) else {
            continue;
        };

        let Ok(left_value) = left_cell.trim().parse::<f64>() else {
            continue;
        };
        let Ok(right_value) = right_cell.trim().parse::<f64>() else {
            continue;
        };
        pairs.push((left_value, right_value));
    }

    if pairs.len() < 2 {
        return None;
    }

    let n = pairs.len() as f64;
    let sum_x: f64 = pairs.iter().map(|(x, _)| x).sum();
    let sum_y: f64 = pairs.iter().map(|(_, y)| y).sum();
    let mean_x = sum_x / n;
    let mean_y = sum_y / n;

    let mut numerator = 0.0;
    let mut sum_sq_x = 0.0;
    let mut sum_sq_y = 0.0;
    for (x, y) in pairs {
        let dx = x - mean_x;
        let dy = y - mean_y;
        numerator += dx * dy;
        sum_sq_x += dx * dx;
        sum_sq_y += dy * dy;
    }

    let denominator = (sum_sq_x * sum_sq_y).sqrt();
    if denominator <= f64::EPSILON {
        None
    } else {
        Some(numerator / denominator)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::{DataTable, TableViewState};
    use std::collections::BTreeSet;

    #[test]
    fn build_bar_chart_data_counts_visible_rows() {
        let table = DataTable {
            headers: vec!["category".to_owned()],
            rows: vec![
                vec!["A".to_owned()],
                vec!["B".to_owned()],
                vec!["A".to_owned()],
                vec!["".to_owned()],
            ],
            column_metadata: vec![],
        };
        let table_view = TableViewState {
            sort_column: None,
            sort_ascending: true,
            selected_rows: BTreeSet::new(),
            row_filter_query: String::new(),
            visible_row_indices: vec![0, 1, 2, 3],
        };

        let chart = build_bar_chart_data(&table, &table_view, "category").expect("bar chart data");

        assert_eq!(chart.visible_row_count, 4);
        assert_eq!(
            chart.segments,
            vec![
                BarSegment {
                    label: "A".to_owned(),
                    count: 2,
                },
                BarSegment {
                    label: "B".to_owned(),
                    count: 1,
                },
                BarSegment {
                    label: "(empty)".to_owned(),
                    count: 1,
                },
            ]
        );
    }

    #[test]
    fn build_bar_chart_data_uses_filtered_row_subset() {
        let table = DataTable {
            headers: vec!["category".to_owned()],
            rows: vec![
                vec!["A".to_owned()],
                vec!["B".to_owned()],
                vec!["A".to_owned()],
            ],
            column_metadata: vec![],
        };
        let table_view = TableViewState {
            sort_column: None,
            sort_ascending: true,
            selected_rows: BTreeSet::new(),
            row_filter_query: "a".to_owned(),
            visible_row_indices: vec![0, 2],
        };

        let chart = build_bar_chart_data(&table, &table_view, "category").expect("bar chart data");

        assert_eq!(chart.visible_row_count, 2);
        assert_eq!(
            chart.segments,
            vec![BarSegment {
                label: "A".to_owned(),
                count: 2
            }]
        );
    }

    #[test]
    fn build_stacked_bar_chart_data_counts_category_and_subgroup_pairs() {
        let table = DataTable {
            headers: vec!["category".to_owned(), "group".to_owned()],
            rows: vec![
                vec!["A".to_owned(), "g1".to_owned()],
                vec!["A".to_owned(), "g2".to_owned()],
                vec!["A".to_owned(), "g1".to_owned()],
                vec!["B".to_owned(), "g2".to_owned()],
            ],
            column_metadata: vec![],
        };
        let table_view = TableViewState {
            sort_column: None,
            sort_ascending: true,
            selected_rows: BTreeSet::new(),
            row_filter_query: String::new(),
            visible_row_indices: vec![0, 1, 2, 3],
        };

        let chart = build_stacked_bar_chart_data(&table, &table_view, "category", "group")
            .expect("stacked bar data");

        assert_eq!(chart.visible_row_count, 4);
        assert_eq!(chart.categories.len(), 2);
        assert_eq!(chart.categories[0].label, "A");
        assert_eq!(chart.categories[0].total_count, 3);
        assert_eq!(
            chart.categories[0].segments,
            vec![
                StackedBarSubgroupSegment {
                    label: "g1".to_owned(),
                    count: 2,
                },
                StackedBarSubgroupSegment {
                    label: "g2".to_owned(),
                    count: 1,
                },
            ]
        );
    }

    #[test]
    fn build_correlation_heatmap_data_returns_pairwise_matrix() {
        let table = DataTable {
            headers: vec!["x".to_owned(), "y".to_owned(), "z".to_owned()],
            rows: vec![
                vec!["1".to_owned(), "2".to_owned(), "3".to_owned()],
                vec!["2".to_owned(), "4".to_owned(), "6".to_owned()],
                vec!["3".to_owned(), "6".to_owned(), "9".to_owned()],
            ],
            column_metadata: vec![
                crate::state::ColumnMetadata {
                    index: 0,
                    name: "x".to_owned(),
                    kind: crate::state::ColumnKind::Numeric,
                    non_empty_count: 3,
                    distinct_count: 3,
                },
                crate::state::ColumnMetadata {
                    index: 1,
                    name: "y".to_owned(),
                    kind: crate::state::ColumnKind::Numeric,
                    non_empty_count: 3,
                    distinct_count: 3,
                },
                crate::state::ColumnMetadata {
                    index: 2,
                    name: "z".to_owned(),
                    kind: crate::state::ColumnKind::Numeric,
                    non_empty_count: 3,
                    distinct_count: 3,
                },
            ],
        };

        let heatmap = build_correlation_heatmap_data(&table).expect("heatmap data");

        assert_eq!(heatmap.column_names, vec!["x", "y", "z"]);
        assert_eq!(heatmap.values.len(), 3);
        assert_eq!(heatmap.values[0][0], Some(1.0));
        assert_eq!(heatmap.values[0][1], Some(1.0));
        assert_eq!(heatmap.values[1][2], Some(1.0));
    }

    #[test]
    fn build_heatmap_chart_data_counts_pairs() {
        let table = DataTable {
            headers: vec!["row".to_owned(), "column".to_owned()],
            rows: vec![
                vec!["A".to_owned(), "X".to_owned()],
                vec!["A".to_owned(), "X".to_owned()],
                vec!["A".to_owned(), "Y".to_owned()],
                vec!["B".to_owned(), "X".to_owned()],
            ],
            column_metadata: vec![],
        };
        let table_view = TableViewState {
            sort_column: None,
            sort_ascending: true,
            selected_rows: BTreeSet::new(),
            row_filter_query: String::new(),
            visible_row_indices: vec![0, 1, 2, 3],
        };

        let heatmap =
            build_heatmap_chart_data(&table, &table_view, "row", "column").expect("heatmap data");

        assert_eq!(heatmap.row_labels, vec!["A", "B"]);
        assert_eq!(heatmap.column_labels, vec!["X", "Y"]);
        assert_eq!(heatmap.counts, vec![vec![2, 1], vec![1, 0]]);
        assert_eq!(heatmap.visible_row_count, 4);
    }
}
