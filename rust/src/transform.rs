use std::collections::{HashMap, HashSet};

use crate::state::DataTable;

pub fn restructure_dataframe(
    table: &DataTable,
    id_vars: &[String],
    value_vars: &[String],
    var_name: &str,
    value_name: &str,
) -> Result<DataTable, String> {
    if value_vars.is_empty() {
        return Err("At least one value column must be selected".to_owned());
    }

    let id_indices = resolve_column_indices(table, id_vars)?;
    let value_indices = resolve_column_indices(table, value_vars)?;
    let mut used = HashSet::new();
    for index in id_indices.iter().chain(value_indices.iter()) {
        if !used.insert(*index) {
            return Err("ID and value columns must not overlap".to_owned());
        }
    }

    let mut headers = id_vars.to_vec();
    headers.push(var_name.to_owned());
    headers.push(value_name.to_owned());

    let mut rows = Vec::with_capacity(table.rows.len() * value_indices.len());
    for (value_label, value_index) in value_vars.iter().zip(value_indices.iter()) {
        for row in &table.rows {
            let id_values = extract_cells(row, &id_indices);
            let mut new_row = id_values;
            new_row.push(value_label.clone());
            new_row.push(cell_value(row, *value_index));
            rows.push(new_row);
        }
    }

    Ok(DataTable::from_rows(headers, rows))
}

pub fn pivot_dataframe(
    table: &DataTable,
    id_vars: &[String],
    var_name: &str,
    value_name: &str,
) -> Result<DataTable, String> {
    let id_indices = resolve_column_indices(table, id_vars)?;
    let var_index = table
        .column_index(var_name)
        .ok_or_else(|| format!("Unknown pivot column '{var_name}'"))?;
    let value_index = table
        .column_index(value_name)
        .ok_or_else(|| format!("Unknown value column '{value_name}'"))?;

    let mut labels = Vec::new();
    let mut seen_labels = HashSet::new();
    for row in &table.rows {
        let label = cell_value(row, var_index);
        if seen_labels.insert(label.clone()) {
            labels.push(label);
        }
    }

    let mut groups: Vec<(Vec<String>, Vec<f64>, Vec<usize>)> = Vec::new();
    let mut group_lookup: HashMap<Vec<String>, usize> = HashMap::new();

    for row in &table.rows {
        let key = extract_cells(row, &id_indices);
        let Some(value_label_index) = labels
            .iter()
            .position(|label| label == &cell_value(row, var_index))
        else {
            continue;
        };

        let Ok(value) = cell_value(row, value_index).trim().parse::<f64>() else {
            continue;
        };

        let entry_index = if let Some(existing) = group_lookup.get(&key) {
            *existing
        } else {
            let new_index = groups.len();
            groups.push((key.clone(), vec![0.0; labels.len()], vec![0; labels.len()]));
            group_lookup.insert(key, new_index);
            new_index
        };

        let (_, sums, counts) = &mut groups[entry_index];
        sums[value_label_index] += value;
        counts[value_label_index] += 1;
    }

    let mut headers = id_vars.to_vec();
    headers.extend(labels.iter().cloned());

    let mut rows = Vec::with_capacity(groups.len());
    for (key, sums, counts) in groups {
        let mut row = key;
        for (sum, count) in sums.into_iter().zip(counts.into_iter()) {
            row.push(if count == 0 {
                String::new()
            } else {
                format_number(sum / count as f64)
            });
        }
        rows.push(row);
    }

    Ok(DataTable::from_rows(headers, rows))
}

pub fn subset_rows(table: &DataTable, row_indices: &[usize]) -> DataTable {
    let rows = row_indices
        .iter()
        .filter_map(|index| table.rows.get(*index).cloned())
        .collect();
    DataTable::from_rows(table.headers.clone(), rows)
}

fn resolve_column_indices(
    table: &DataTable,
    column_names: &[String],
) -> Result<Vec<usize>, String> {
    column_names
        .iter()
        .map(|column_name| {
            table
                .column_index(column_name)
                .ok_or_else(|| format!("Unknown column '{column_name}'"))
        })
        .collect()
}

fn extract_cells(row: &[String], indices: &[usize]) -> Vec<String> {
    indices
        .iter()
        .map(|index| cell_value(row, *index))
        .collect()
}

fn cell_value(row: &[String], index: usize) -> String {
    row.get(index).cloned().unwrap_or_default()
}

fn format_number(value: f64) -> String {
    if (value - value.round()).abs() < f64::EPSILON {
        format!("{}", value.round() as i64)
    } else {
        let mut text = format!("{value}");
        if text.contains('.') {
            while text.ends_with('0') {
                text.pop();
            }
            if text.ends_with('.') {
                text.pop();
            }
        }
        text
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_table() -> DataTable {
        DataTable::from_rows(
            vec![
                "category".to_owned(),
                "label".to_owned(),
                "value".to_owned(),
            ],
            vec![
                vec!["A".to_owned(), "x".to_owned(), "1".to_owned()],
                vec!["A".to_owned(), "y".to_owned(), "2".to_owned()],
                vec!["B".to_owned(), "x".to_owned(), "3".to_owned()],
                vec!["B".to_owned(), "y".to_owned(), "5".to_owned()],
                vec!["B".to_owned(), "y".to_owned(), "7".to_owned()],
            ],
        )
    }

    #[test]
    fn restructure_dataframe_melts_selected_columns() {
        let table = sample_table();
        let result = restructure_dataframe(
            &table,
            &[String::from("category")],
            &[String::from("label"), String::from("value")],
            "kind",
            "amount",
        )
        .expect("restructure");

        assert_eq!(result.headers, vec!["category", "kind", "amount"]);
        assert_eq!(result.rows.len(), 10);
        assert_eq!(result.rows[0], vec!["A", "label", "x"]);
        assert_eq!(result.rows[1], vec!["A", "label", "y"]);
    }

    #[test]
    fn pivot_dataframe_aggregates_numeric_values_by_label() {
        let table = sample_table();
        let result =
            pivot_dataframe(&table, &[String::from("category")], "label", "value").expect("pivot");

        assert_eq!(result.headers, vec!["category", "x", "y"]);
        assert_eq!(result.rows.len(), 2);
        assert_eq!(result.rows[0], vec!["A", "1", "2"]);
        assert_eq!(result.rows[1], vec!["B", "3", "6"]);
    }

    #[test]
    fn subset_rows_preserves_headers_and_selection_order() {
        let table = sample_table();
        let subset = subset_rows(&table, &[2, 0]);

        assert_eq!(subset.headers, table.headers);
        assert_eq!(
            subset.rows,
            vec![table.rows[2].clone(), table.rows[0].clone()]
        );
    }
}
