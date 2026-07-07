use std::collections::HashMap;

use crate::state::{DataTable, HeatmapNormalizationMode, TableViewState, resolved_row_indices};

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
pub struct ProportionPlotSegment {
    pub label: String,
    pub count: usize,
    pub proportion: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct ProportionPlotData {
    pub column_name: String,
    pub segments: Vec<ProportionPlotSegment>,
    pub visible_row_count: usize,
}

#[derive(Clone, Debug, PartialEq)]
pub struct MosaicChartData {
    pub row_column_name: String,
    pub column_column_name: String,
    pub row_labels: Vec<String>,
    pub column_labels: Vec<String>,
    pub counts: Vec<Vec<usize>>,
    pub visible_row_count: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct HistogramBin {
    pub label: String,
    pub count: usize,
}

#[derive(Clone, Debug, PartialEq)]
pub struct HistogramChartData {
    pub column_name: String,
    pub bins: Vec<HistogramBin>,
    pub visible_row_count: usize,
    pub min_value: f64,
    pub max_value: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct CorrelationHeatmapData {
    pub column_names: Vec<String>,
    pub values: Vec<Vec<Option<f64>>>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct HeatmapChartData {
    pub row_column_name: String,
    pub column_column_name: String,
    pub row_labels: Vec<String>,
    pub column_labels: Vec<String>,
    pub counts: Vec<Vec<usize>>,
    pub values: Vec<Vec<f64>>,
    pub normalization_mode: HeatmapNormalizationMode,
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
    let row_indices = resolved_row_indices(table, table_view);

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

pub fn build_proportion_plot_data(
    table: &DataTable,
    table_view: &TableViewState,
    column_name: &str,
) -> Option<ProportionPlotData> {
    let bar_data = build_bar_chart_data(table, table_view, column_name)?;
    let visible_row_count = bar_data.visible_row_count.max(1) as f64;
    let segments = bar_data
        .segments
        .into_iter()
        .map(|segment| ProportionPlotSegment {
            proportion: segment.count as f64 / visible_row_count,
            count: segment.count,
            label: segment.label,
        })
        .collect::<Vec<_>>();

    Some(ProportionPlotData {
        column_name: bar_data.column_name,
        segments,
        visible_row_count: bar_data.visible_row_count,
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
    let row_indices = resolved_row_indices(table, table_view);

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

pub fn build_mosaic_chart_data(
    table: &DataTable,
    table_view: &TableViewState,
    row_column_name: &str,
    column_column_name: &str,
) -> Option<MosaicChartData> {
    let row_index = table
        .headers
        .iter()
        .position(|header| header == row_column_name)?;
    let column_index = table
        .headers
        .iter()
        .position(|header| header == column_column_name)?;
    let row_indices = resolved_row_indices(table, table_view);

    if row_indices.is_empty() {
        return None;
    }

    let mut row_labels: Vec<String> = Vec::new();
    let mut column_labels: Vec<String> = Vec::new();
    let mut counts: HashMap<(String, String), usize> = HashMap::new();

    for row_idx in row_indices.iter().copied() {
        let Some(row) = table.rows.get(row_idx) else {
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

    Some(MosaicChartData {
        row_column_name: row_column_name.to_owned(),
        column_column_name: column_column_name.to_owned(),
        row_labels,
        column_labels,
        counts: matrix,
        visible_row_count: row_indices.len(),
    })
}

pub fn build_histogram_chart_data(
    table: &DataTable,
    table_view: &TableViewState,
    column_name: &str,
) -> Option<HistogramChartData> {
    let column_index = table
        .headers
        .iter()
        .position(|header| header == column_name)?;
    let row_indices = resolved_row_indices(table, table_view);

    let values = row_indices
        .iter()
        .filter_map(|row_index| table.rows.get(*row_index))
        .filter_map(|row| row.get(column_index))
        .filter_map(|value| value.trim().parse::<f64>().ok())
        .collect::<Vec<_>>();

    if values.is_empty() {
        return None;
    }

    let min_value = values
        .iter()
        .copied()
        .fold(f64::INFINITY, f64::min);
    let max_value = values
        .iter()
        .copied()
        .fold(f64::NEG_INFINITY, f64::max);
    let bin_count = (values.len() as f64).sqrt().round().clamp(1.0, 8.0) as usize;
    let span = (max_value - min_value).max(f64::EPSILON);
    let bin_width = span / bin_count as f64;
    let mut counts = vec![0usize; bin_count];

    for value in values {
        let mut bin_index = ((value - min_value) / bin_width).floor() as usize;
        if bin_index >= bin_count {
            bin_index = bin_count - 1;
        }
        counts[bin_index] += 1;
    }

    let bins = (0..bin_count)
        .map(|index| {
            let lower = min_value + (index as f64 * bin_width);
            let upper = if index == bin_count - 1 {
                max_value
            } else {
                min_value + ((index + 1) as f64 * bin_width)
            };
            HistogramBin {
                label: format!(
                    "{}-{}",
                    compact_float(lower),
                    compact_float(upper)
                ),
                count: counts[index],
            }
        })
        .collect();

    Some(HistogramChartData {
        column_name: column_name.to_owned(),
        bins,
        visible_row_count: row_indices.len(),
        min_value,
        max_value,
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
    normalization_mode: HeatmapNormalizationMode,
) -> Option<HeatmapChartData> {
    let row_index = table
        .headers
        .iter()
        .position(|header| header == row_column_name)?;
    let column_index = table
        .headers
        .iter()
        .position(|header| header == column_column_name)?;
    let row_indices = resolved_row_indices(table, table_view);

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

    let values = normalize_heatmap_counts(&matrix, normalization_mode);

    Some(HeatmapChartData {
        row_column_name: row_column_name.to_owned(),
        column_column_name: column_column_name.to_owned(),
        row_labels,
        column_labels,
        counts: matrix,
        values,
        normalization_mode,
        visible_row_count: row_indices.len(),
    })
}

fn normalize_heatmap_counts(
    counts: &[Vec<usize>],
    normalization_mode: HeatmapNormalizationMode,
) -> Vec<Vec<f64>> {
    let rows = counts.len();
    let cols = counts.first().map(|row| row.len()).unwrap_or(0);

    match normalization_mode {
        HeatmapNormalizationMode::Count => counts
            .iter()
            .map(|row| row.iter().map(|count| *count as f64).collect())
            .collect(),
        HeatmapNormalizationMode::Row => counts
            .iter()
            .map(|row| {
                let total: usize = row.iter().sum();
                if total == 0 {
                    vec![0.0; row.len()]
                } else {
                    row.iter()
                        .map(|count| *count as f64 / total as f64)
                        .collect()
                }
            })
            .collect(),
        HeatmapNormalizationMode::Column => {
            let column_totals: Vec<usize> = (0..cols)
                .map(|column_index| {
                    counts
                        .iter()
                        .map(|row| row.get(column_index).copied().unwrap_or(0))
                        .sum()
                })
                .collect();

            counts
                .iter()
                .map(|row| {
                    row.iter()
                        .enumerate()
                        .map(|(column_index, count)| {
                            let total = column_totals.get(column_index).copied().unwrap_or(0);
                            if total == 0 {
                                0.0
                            } else {
                                *count as f64 / total as f64
                            }
                        })
                        .collect()
                })
                .collect()
        }
        HeatmapNormalizationMode::Total => {
            let total: usize = counts.iter().flatten().copied().sum();
            if total == 0 {
                vec![vec![0.0; cols]; rows]
            } else {
                counts
                    .iter()
                    .map(|row| {
                        row.iter()
                            .map(|count| *count as f64 / total as f64)
                            .collect()
                    })
                    .collect()
            }
        }
    }
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

fn compact_float(value: f64) -> String {
    if (value - value.round()).abs() < f64::EPSILON {
        format!("{}", value.round() as i64)
    } else {
        let mut text = format!("{value:.2}");
        while text.contains('.') && text.ends_with('0') {
            text.pop();
        }
        if text.ends_with('.') {
            text.pop();
        }
        text
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::{DataTable, HeatmapNormalizationMode, TableViewState};
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
    fn build_proportion_plot_data_normalizes_counts() {
        let table = DataTable {
            headers: vec!["category".to_owned()],
            rows: vec![
                vec!["A".to_owned()],
                vec!["A".to_owned()],
                vec!["B".to_owned()],
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

        let chart = build_proportion_plot_data(&table, &table_view, "category")
            .expect("proportion plot data");

        assert_eq!(chart.visible_row_count, 4);
        assert_eq!(chart.segments[0].label, "A");
        assert_eq!(chart.segments[0].count, 2);
        assert!((chart.segments[0].proportion - 0.5).abs() < 1e-6);
        assert_eq!(chart.segments[2].label, "(empty)");
    }

    #[test]
    fn build_mosaic_chart_data_counts_pairs() {
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

        let chart = build_mosaic_chart_data(&table, &table_view, "row", "column")
            .expect("mosaic chart data");

        assert_eq!(chart.row_labels, vec!["A", "B"]);
        assert_eq!(chart.column_labels, vec!["X", "Y"]);
        assert_eq!(chart.counts, vec![vec![2, 1], vec![1, 0]]);
        assert_eq!(chart.visible_row_count, 4);
    }

    #[test]
    fn build_histogram_chart_data_bins_numeric_values() {
        let table = DataTable {
            headers: vec!["value".to_owned()],
            rows: vec![
                vec!["1".to_owned()],
                vec!["2".to_owned()],
                vec!["3".to_owned()],
                vec!["4".to_owned()],
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

        let chart = build_histogram_chart_data(&table, &table_view, "value").expect("histogram");

        assert_eq!(chart.visible_row_count, 4);
        assert_eq!(chart.bins.iter().map(|bin| bin.count).sum::<usize>(), 4);
        assert!(!chart.bins.is_empty());
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

        let heatmap = build_heatmap_chart_data(
            &table,
            &table_view,
            "row",
            "column",
            HeatmapNormalizationMode::Count,
        )
        .expect("heatmap data");

        assert_eq!(heatmap.row_labels, vec!["A", "B"]);
        assert_eq!(heatmap.column_labels, vec!["X", "Y"]);
        assert_eq!(heatmap.counts, vec![vec![2, 1], vec![1, 0]]);
        assert_eq!(heatmap.values, vec![vec![2.0, 1.0], vec![1.0, 0.0]]);
        assert_eq!(heatmap.normalization_mode, HeatmapNormalizationMode::Count);
        assert_eq!(heatmap.visible_row_count, 4);
    }

    #[test]
    fn build_heatmap_chart_data_normalizes_rows_columns_and_total() {
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

        let row_heatmap = build_heatmap_chart_data(
            &table,
            &table_view,
            "row",
            "column",
            HeatmapNormalizationMode::Row,
        )
        .expect("row-normalized heatmap");
        assert_eq!(
            row_heatmap.values,
            vec![vec![2.0 / 3.0, 1.0 / 3.0], vec![1.0, 0.0]]
        );

        let column_heatmap = build_heatmap_chart_data(
            &table,
            &table_view,
            "row",
            "column",
            HeatmapNormalizationMode::Column,
        )
        .expect("column-normalized heatmap");
        assert_eq!(
            column_heatmap.values,
            vec![vec![2.0 / 3.0, 1.0], vec![1.0 / 3.0, 0.0]]
        );

        let total_heatmap = build_heatmap_chart_data(
            &table,
            &table_view,
            "row",
            "column",
            HeatmapNormalizationMode::Total,
        )
        .expect("total-normalized heatmap");
        assert_eq!(total_heatmap.values, vec![vec![0.5, 0.25], vec![0.25, 0.0]]);
    }
}
