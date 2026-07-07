use std::collections::HashMap;

use crate::state::{DataTable, TableViewState, resolved_row_indices};

#[derive(Clone, Debug, PartialEq)]
pub struct PearsonCorrelationAnalysisResult {
    pub col1: String,
    pub col2: String,
    pub sample_size: usize,
    pub r: f64,
    pub p_value: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct SpearmanCorrelationAnalysisResult {
    pub col1: String,
    pub col2: String,
    pub sample_size: usize,
    pub rho: f64,
    pub p_value: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct LinearRegressionAnalysisResult {
    pub col1: String,
    pub col2: String,
    pub sample_size: usize,
    pub slope: f64,
    pub intercept: f64,
    pub r_squared: f64,
    pub p_value: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct FourPlRegressionAnalysisResult {
    pub col1: String,
    pub col2: String,
    pub sample_size: usize,
    pub bottom: f64,
    pub top: f64,
    pub hill_slope: f64,
    pub log_ec50: f64,
    pub ec50: f64,
    pub r_squared: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct IndependentTTestAnalysisResult {
    pub col1: String,
    pub col2: String,
    pub sample_size1: usize,
    pub sample_size2: usize,
    pub mean1: f64,
    pub mean2: f64,
    pub t_statistic: f64,
    pub p_value: f64,
    pub degrees_of_freedom: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct PairedTTestAnalysisResult {
    pub col1: String,
    pub col2: String,
    pub sample_size: usize,
    pub mean1: f64,
    pub mean2: f64,
    pub mean_difference: f64,
    pub t_statistic: f64,
    pub p_value: f64,
    pub degrees_of_freedom: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct OneWayAnovaGroupResult {
    pub label: String,
    pub sample_size: usize,
    pub mean: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct OneWayAnovaAnalysisResult {
    pub group_col: String,
    pub value_col: String,
    pub groups: Vec<OneWayAnovaGroupResult>,
    pub f_statistic: f64,
    pub p_value: f64,
    pub between_group_df: usize,
    pub within_group_df: usize,
}

#[derive(Clone, Debug, PartialEq)]
pub struct MannWhitneyUAnalysisResult {
    pub col1: String,
    pub col2: String,
    pub sample_size1: usize,
    pub sample_size2: usize,
    pub u_statistic: f64,
    pub p_value: f64,
    pub mean_rank1: f64,
    pub mean_rank2: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct WilcoxonSignedRankAnalysisResult {
    pub col1: String,
    pub col2: String,
    pub sample_size: usize,
    pub nonzero_difference_count: usize,
    pub w_statistic: f64,
    pub p_value: f64,
    pub positive_rank_sum: f64,
    pub negative_rank_sum: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct KruskalWallisGroupResult {
    pub label: String,
    pub sample_size: usize,
    pub mean_rank: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct KruskalWallisAnalysisResult {
    pub group_col: String,
    pub value_col: String,
    pub groups: Vec<KruskalWallisGroupResult>,
    pub h_statistic: f64,
    pub p_value: f64,
    pub degrees_of_freedom: usize,
}

#[derive(Clone, Debug, PartialEq)]
pub struct ShapiroGroupResult {
    pub group_name: String,
    pub sample_size: usize,
    pub statistic: Option<f64>,
    pub p_value: Option<f64>,
    pub skipped: bool,
}

#[derive(Clone, Debug, PartialEq)]
pub struct ShapiroAnalysisResult {
    pub value_col: String,
    pub group_col: String,
    pub groups: Vec<ShapiroGroupResult>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct TwoProportionAnalysisResult {
    pub rows_col: String,
    pub cols_col: String,
    pub group1_label: String,
    pub group2_label: String,
    pub success_label: String,
    pub success_count_group1: usize,
    pub success_count_group2: usize,
    pub total_group1: usize,
    pub total_group2: usize,
    pub proportion_group1: f64,
    pub proportion_group2: f64,
    pub ci_low_group1: f64,
    pub ci_high_group1: f64,
    pub ci_low_group2: f64,
    pub ci_high_group2: f64,
    pub difference_in_proportions: f64,
    pub ci_low_difference: f64,
    pub ci_high_difference: f64,
    pub z_statistic: f64,
    pub p_value: f64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct ChiSquaredAnalysisResult {
    pub rows_col: String,
    pub cols_col: String,
    pub contingency_table: Vec<Vec<usize>>,
    pub row_labels: Vec<String>,
    pub column_labels: Vec<String>,
    pub expected_table: Vec<Vec<f64>>,
    pub standardized_residuals: Vec<Vec<f64>>,
    pub contribution_table: Vec<Vec<f64>>,
    pub chi2: f64,
    pub p_value: f64,
    pub degrees_of_freedom: usize,
    pub cramers_v: f64,
}

pub fn run_pearson_correlation_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    col1: &str,
    col2: &str,
) -> Result<PearsonCorrelationAnalysisResult, String> {
    let left_index = table
        .headers
        .iter()
        .position(|header| header == col1)
        .ok_or_else(|| format!("Unknown column '{col1}'"))?;
    let right_index = table
        .headers
        .iter()
        .position(|header| header == col2)
        .ok_or_else(|| format!("Unknown column '{col2}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut pairs = Vec::new();
    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let Some(left) = row.get(left_index) else {
            continue;
        };
        let Some(right) = row.get(right_index) else {
            continue;
        };
        let Ok(left) = left.trim().parse::<f64>() else {
            continue;
        };
        let Ok(right) = right.trim().parse::<f64>() else {
            continue;
        };
        pairs.push((left, right));
    }

    if pairs.len() < 2 {
        return Err("Pearson correlation requires at least two numeric pairs".to_owned());
    }

    let sample_size = pairs.len();
    let mean_x = pairs.iter().map(|(x, _)| x).sum::<f64>() / sample_size as f64;
    let mean_y = pairs.iter().map(|(_, y)| y).sum::<f64>() / sample_size as f64;

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
        return Err("Pearson correlation is undefined for constant data".to_owned());
    }

    let r = numerator / denominator;
    let df = (sample_size - 2) as f64;
    let t = r * (df / (1.0 - r * r)).sqrt();
    let p_value = 2.0 * (1.0 - student_t_cdf(t.abs(), df));

    Ok(PearsonCorrelationAnalysisResult {
        col1: col1.to_owned(),
        col2: col2.to_owned(),
        sample_size,
        r,
        p_value,
    })
}

pub fn format_pearson_correlation_result(result: &PearsonCorrelationAnalysisResult) -> String {
    let mut text = String::from("Pearson Correlation Results\n===========================\n\n");
    text.push_str(&format!(
        "Comparing:\n- Variable 1: '{}'\n- Variable 2: '{}'\n(n={})\n\n---\nPearson's r: {:.4}\np-value: {:.4}\n\n",
        result.col1, result.col2, result.sample_size, result.r, result.p_value
    ));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: There is a statistically significant linear correlation.");
    } else {
        text.push_str("Conclusion: There is no statistically significant linear correlation.");
    }
    text
}

pub fn run_spearman_correlation_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    col1: &str,
    col2: &str,
) -> Result<SpearmanCorrelationAnalysisResult, String> {
    let pairs = collect_paired_numeric_columns(table, table_view, col1, col2)?;
    if pairs.len() < 2 {
        return Err("Spearman correlation requires at least two numeric pairs".to_owned());
    }

    let left_values = pairs.iter().map(|(left, _)| *left).collect::<Vec<_>>();
    let right_values = pairs.iter().map(|(_, right)| *right).collect::<Vec<_>>();
    let left_ranks = rank_with_ties(&left_values);
    let right_ranks = rank_with_ties(&right_values);

    let mean_left = left_ranks.iter().sum::<f64>() / left_ranks.len() as f64;
    let mean_right = right_ranks.iter().sum::<f64>() / right_ranks.len() as f64;
    let mut numerator = 0.0;
    let mut sum_sq_left = 0.0;
    let mut sum_sq_right = 0.0;
    for (left_rank, right_rank) in left_ranks.iter().zip(right_ranks.iter()) {
        let centered_left = left_rank - mean_left;
        let centered_right = right_rank - mean_right;
        numerator += centered_left * centered_right;
        sum_sq_left += centered_left * centered_left;
        sum_sq_right += centered_right * centered_right;
    }

    let denominator = (sum_sq_left * sum_sq_right).sqrt();
    if denominator <= f64::EPSILON {
        return Err("Spearman correlation is undefined for constant data".to_owned());
    }

    let rho = (numerator / denominator).clamp(-1.0, 1.0);
    let df = (pairs.len() - 2) as f64;
    let p_value = if rho.abs() >= 1.0 - f64::EPSILON {
        0.0
    } else {
        let t_statistic = rho * (df / (1.0 - rho * rho)).sqrt();
        2.0 * (1.0 - student_t_cdf(t_statistic.abs(), df))
    };

    Ok(SpearmanCorrelationAnalysisResult {
        col1: col1.to_owned(),
        col2: col2.to_owned(),
        sample_size: pairs.len(),
        rho,
        p_value,
    })
}

pub fn format_spearman_correlation_result(result: &SpearmanCorrelationAnalysisResult) -> String {
    let mut text = String::from("Spearman Correlation Results\n============================\n\n");
    text.push_str(&format!(
        "Comparing:\n- Variable 1: '{}'\n- Variable 2: '{}'\n(n={})\n\n---\nSpearman's rho: {:.4}\np-value: {:.4}\n\n",
        result.col1, result.col2, result.sample_size, result.rho, result.p_value
    ));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: There is a statistically significant monotonic correlation.");
    } else {
        text.push_str("Conclusion: There is no statistically significant monotonic correlation.");
    }
    text
}

pub fn run_linear_regression_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    col1: &str,
    col2: &str,
) -> Result<LinearRegressionAnalysisResult, String> {
    let left_index = table
        .headers
        .iter()
        .position(|header| header == col1)
        .ok_or_else(|| format!("Unknown column '{col1}'"))?;
    let right_index = table
        .headers
        .iter()
        .position(|header| header == col2)
        .ok_or_else(|| format!("Unknown column '{col2}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut pairs = Vec::new();
    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let Some(left) = row.get(left_index) else {
            continue;
        };
        let Some(right) = row.get(right_index) else {
            continue;
        };
        let Ok(left) = left.trim().parse::<f64>() else {
            continue;
        };
        let Ok(right) = right.trim().parse::<f64>() else {
            continue;
        };
        pairs.push((left, right));
    }

    if pairs.len() < 2 {
        return Err("Linear regression requires at least two numeric pairs".to_owned());
    }

    let sample_size = pairs.len();
    let mean_x = pairs.iter().map(|(x, _)| x).sum::<f64>() / sample_size as f64;
    let mean_y = pairs.iter().map(|(_, y)| y).sum::<f64>() / sample_size as f64;

    let mut ss_xx = 0.0;
    let mut ss_yy = 0.0;
    let mut ss_xy = 0.0;
    for (x, y) in &pairs {
        let dx = x - mean_x;
        let dy = y - mean_y;
        ss_xx += dx * dx;
        ss_yy += dy * dy;
        ss_xy += dx * dy;
    }

    if ss_xx <= f64::EPSILON {
        return Err("Linear regression is undefined for constant X data".to_owned());
    }

    let slope = ss_xy / ss_xx;
    let intercept = mean_y - slope * mean_x;
    let mut residual_sum_squares = 0.0;
    for (x, y) in &pairs {
        let predicted = slope * *x + intercept;
        let residual = *y - predicted;
        residual_sum_squares += residual * residual;
    }
    let r_squared = if ss_yy <= f64::EPSILON {
        0.0
    } else {
        (ss_xy * ss_xy) / (ss_xx * ss_yy)
    };

    let degrees_of_freedom = (sample_size as f64) - 2.0;
    let p_value = if degrees_of_freedom <= 0.0 {
        if slope.abs() <= f64::EPSILON {
            1.0
        } else {
            0.0
        }
    } else {
        let standard_error = (residual_sum_squares / degrees_of_freedom / ss_xx).sqrt();
        if standard_error <= f64::EPSILON {
            if slope.abs() <= f64::EPSILON {
                1.0
            } else {
                0.0
            }
        } else {
            let t_statistic = slope / standard_error;
            2.0 * (1.0 - student_t_cdf(t_statistic.abs(), degrees_of_freedom))
        }
    };

    Ok(LinearRegressionAnalysisResult {
        col1: col1.to_owned(),
        col2: col2.to_owned(),
        sample_size,
        slope,
        intercept,
        r_squared,
        p_value,
    })
}

pub fn format_linear_regression_result(result: &LinearRegressionAnalysisResult) -> String {
    let mut text = String::from("Linear Regression Results\n=========================\n\n");
    text.push_str(&format!(
        "Fitting '{}' as a function of '{}'.\n(n={})\n\n---\nY = {:.4} * X + {:.4}\nR-squared: {:.4}\np-value: {:.4}\n\n",
        result.col2,
        result.col1,
        result.sample_size,
        result.slope,
        result.intercept,
        result.r_squared,
        result.p_value
    ));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: The linear relationship is statistically significant (p < 0.05).");
    } else {
        text.push_str("Conclusion: The linear relationship is not statistically significant (p >= 0.05).");
    }
    text
}

pub fn run_four_pl_regression_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    col1: &str,
    col2: &str,
) -> Result<FourPlRegressionAnalysisResult, String> {
    let x_index = table
        .headers
        .iter()
        .position(|header| header == col1)
        .ok_or_else(|| format!("Unknown column '{col1}'"))?;
    let y_index = table
        .headers
        .iter()
        .position(|header| header == col2)
        .ok_or_else(|| format!("Unknown column '{col2}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut pairs = Vec::new();
    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let Some(x_value) = row.get(x_index) else {
            continue;
        };
        let Some(y_value) = row.get(y_index) else {
            continue;
        };
        let Ok(x_value) = x_value.trim().parse::<f64>() else {
            continue;
        };
        let Ok(y_value) = y_value.trim().parse::<f64>() else {
            continue;
        };
        if x_value <= 0.0 || !x_value.is_finite() || !y_value.is_finite() {
            continue;
        }
        pairs.push((x_value.log10(), y_value));
    }

    if pairs.len() < 4 {
        return Err("4PL regression requires at least four positive numeric pairs".to_owned());
    }

    let x_values = pairs.iter().map(|(x, _)| *x).collect::<Vec<_>>();
    let y_values = pairs.iter().map(|(_, y)| *y).collect::<Vec<_>>();
    let mut params = fit_four_pl_parameters(&x_values, &y_values);
    if !params.iter().all(|value| value.is_finite()) {
        return Err("4PL regression could not produce a stable fit".to_owned());
    }

    if params[1] < params[0] {
        params.swap(0, 1);
    }
    let predictions = x_values
        .iter()
        .map(|x| sigmoid_4pl(*x, params[0], params[1], params[2], params[3]))
        .collect::<Vec<_>>();
    let mean_y = y_values.iter().sum::<f64>() / y_values.len() as f64;
    let ss_res = y_values
        .iter()
        .zip(predictions.iter())
        .map(|(observed, predicted)| {
            let residual = observed - predicted;
            residual * residual
        })
        .sum::<f64>();
    let ss_tot = y_values
        .iter()
        .map(|value| {
            let diff = *value - mean_y;
            diff * diff
        })
        .sum::<f64>();
    let r_squared = if ss_tot <= f64::EPSILON {
        0.0
    } else {
        (1.0 - ss_res / ss_tot).clamp(0.0, 1.0)
    };

    Ok(FourPlRegressionAnalysisResult {
        col1: col1.to_owned(),
        col2: col2.to_owned(),
        sample_size: pairs.len(),
        bottom: params[0],
        top: params[1],
        hill_slope: params[2],
        log_ec50: params[3],
        ec50: 10_f64.powf(params[3]),
        r_squared,
    })
}

pub fn format_four_pl_regression_result(result: &FourPlRegressionAnalysisResult) -> String {
    let mut text = String::from("Non-linear Regression (4PL) Results\n===================================\n\n");
    text.push_str(&format!(
        "Fitting '{}' as a function of '{}'.\n(n={})\n\n---\nTop: {:.4}\nBottom: {:.4}\nHill Slope: {:.4}\nEC50: {:.4}\nR-squared: {:.4}\n\n",
        result.col2,
        result.col1,
        result.sample_size,
        result.top,
        result.bottom,
        result.hill_slope,
        result.ec50,
        result.r_squared
    ));
    if result.r_squared > 0.9 {
        text.push_str("Conclusion: The 4PL fit explains most of the variance.");
    } else if result.r_squared > 0.5 {
        text.push_str("Conclusion: The 4PL fit explains a moderate amount of variance.");
    } else {
        text.push_str("Conclusion: The 4PL fit is weak for this dataset.");
    }
    text
}

pub fn run_independent_t_test_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    col1: &str,
    col2: &str,
) -> Result<IndependentTTestAnalysisResult, String> {
    let left_index = table
        .headers
        .iter()
        .position(|header| header == col1)
        .ok_or_else(|| format!("Unknown column '{col1}'"))?;
    let right_index = table
        .headers
        .iter()
        .position(|header| header == col2)
        .ok_or_else(|| format!("Unknown column '{col2}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut sample1 = Vec::new();
    let mut sample2 = Vec::new();
    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let Some(left) = row.get(left_index) else {
            continue;
        };
        let Some(right) = row.get(right_index) else {
            continue;
        };
        let Ok(left) = left.trim().parse::<f64>() else {
            continue;
        };
        let Ok(right) = right.trim().parse::<f64>() else {
            continue;
        };
        sample1.push(left);
        sample2.push(right);
    }

    if sample1.len() < 2 || sample2.len() < 2 {
        return Err("Independent t-test requires at least two numeric values in each column".to_owned());
    }

    let mean1 = sample1.iter().sum::<f64>() / sample1.len() as f64;
    let mean2 = sample2.iter().sum::<f64>() / sample2.len() as f64;
    let var1 = sample_variance(&sample1, mean1);
    let var2 = sample_variance(&sample2, mean2);
    let df = (sample1.len() + sample2.len() - 2) as f64;
    if df <= 0.0 {
        return Err("Independent t-test requires at least two values per column".to_owned());
    }

    let pooled_variance = (((sample1.len() - 1) as f64 * var1) + ((sample2.len() - 1) as f64 * var2))
        / df;
    let standard_error = (pooled_variance * ((1.0 / sample1.len() as f64) + (1.0 / sample2.len() as f64))).sqrt();
    let t_statistic = if standard_error <= f64::EPSILON {
        0.0
    } else {
        (mean1 - mean2) / standard_error
    };
    let p_value = 2.0 * (1.0 - student_t_cdf(t_statistic.abs(), df));

    Ok(IndependentTTestAnalysisResult {
        col1: col1.to_owned(),
        col2: col2.to_owned(),
        sample_size1: sample1.len(),
        sample_size2: sample2.len(),
        mean1,
        mean2,
        t_statistic,
        p_value,
        degrees_of_freedom: df,
    })
}

pub fn format_independent_t_test_result(result: &IndependentTTestAnalysisResult) -> String {
    let mut text = String::from("Independent t-test Results\n===========================\n\n");
    text.push_str(&format!(
        "Comparing:\n- Group 1: '{}'\n- Group 2: '{}'\n\n---\nGroup 1 mean: {:.4} (n={})\nGroup 2 mean: {:.4} (n={})\nt-statistic: {:.4}\ndegrees of freedom: {:.1}\np-value: {:.4}\n\n",
        result.col1,
        result.col2,
        result.mean1,
        result.sample_size1,
        result.mean2,
        result.sample_size2,
        result.t_statistic,
        result.degrees_of_freedom,
        result.p_value
    ));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: The difference is statistically significant (p < 0.05).");
    } else {
        text.push_str("Conclusion: The difference is not statistically significant (p >= 0.05).");
    }
    text
}

pub fn run_paired_t_test_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    col1: &str,
    col2: &str,
) -> Result<PairedTTestAnalysisResult, String> {
    let left_index = table
        .headers
        .iter()
        .position(|header| header == col1)
        .ok_or_else(|| format!("Unknown column '{col1}'"))?;
    let right_index = table
        .headers
        .iter()
        .position(|header| header == col2)
        .ok_or_else(|| format!("Unknown column '{col2}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut pairs = Vec::new();
    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let Some(left) = row.get(left_index) else {
            continue;
        };
        let Some(right) = row.get(right_index) else {
            continue;
        };
        let Ok(left) = left.trim().parse::<f64>() else {
            continue;
        };
        let Ok(right) = right.trim().parse::<f64>() else {
            continue;
        };
        pairs.push((left, right));
    }

    if pairs.len() < 2 {
        return Err("Paired t-test requires at least two numeric pairs".to_owned());
    }

    let sample_size = pairs.len();
    let mean1 = pairs.iter().map(|(left, _)| left).sum::<f64>() / sample_size as f64;
    let mean2 = pairs.iter().map(|(_, right)| right).sum::<f64>() / sample_size as f64;
    let differences = pairs
        .iter()
        .map(|(left, right)| left - right)
        .collect::<Vec<_>>();
    let mean_difference = differences.iter().sum::<f64>() / sample_size as f64;
    let diff_variance = sample_variance(&differences, mean_difference);
    let standard_error = (diff_variance / sample_size as f64).sqrt();
    let degrees_of_freedom = (sample_size - 1) as f64;
    let t_statistic = if standard_error <= f64::EPSILON {
        0.0
    } else {
        mean_difference / standard_error
    };
    let p_value = if degrees_of_freedom <= 0.0 {
        1.0
    } else {
        2.0 * (1.0 - student_t_cdf(t_statistic.abs(), degrees_of_freedom))
    };

    Ok(PairedTTestAnalysisResult {
        col1: col1.to_owned(),
        col2: col2.to_owned(),
        sample_size,
        mean1,
        mean2,
        mean_difference,
        t_statistic,
        p_value,
        degrees_of_freedom,
    })
}

pub fn format_paired_t_test_result(result: &PairedTTestAnalysisResult) -> String {
    let mut text = String::from("Paired t-test Results\n=====================\n\n");
    text.push_str(&format!(
        "Comparing:\n- Column 1: '{}'\n- Column 2: '{}'\n\n---\nColumn 1 mean: {:.4}\nColumn 2 mean: {:.4}\nMean difference: {:.4}\nt-statistic: {:.4}\ndegrees of freedom: {:.1}\np-value: {:.4}\n\n",
        result.col1,
        result.col2,
        result.mean1,
        result.mean2,
        result.mean_difference,
        result.t_statistic,
        result.degrees_of_freedom,
        result.p_value
    ));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: The difference is statistically significant (p < 0.05).");
    } else {
        text.push_str("Conclusion: The difference is not statistically significant (p >= 0.05).");
    }
    text
}

pub fn run_one_way_anova_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    group_col: &str,
    value_col: &str,
) -> Result<OneWayAnovaAnalysisResult, String> {
    let group_index = table
        .headers
        .iter()
        .position(|header| header == group_col)
        .ok_or_else(|| format!("Unknown group column '{group_col}'"))?;
    let value_index = table
        .headers
        .iter()
        .position(|header| header == value_col)
        .ok_or_else(|| format!("Unknown value column '{value_col}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut grouped_values: HashMap<String, Vec<f64>> = HashMap::new();
    let mut order = Vec::new();

    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let group_label = normalize_label(row.get(group_index).map(String::as_str));
        let Some(value) = row.get(value_index) else {
            continue;
        };
        let Ok(value) = value.trim().parse::<f64>() else {
            continue;
        };
        if !grouped_values.contains_key(&group_label) {
            order.push(group_label.clone());
        }
        grouped_values.entry(group_label).or_default().push(value);
    }

    let groups = order
        .iter()
        .filter_map(|label| {
            let values = grouped_values.get(label)?;
            if values.len() < 2 {
                return None;
            }
            let mean = values.iter().sum::<f64>() / values.len() as f64;
            Some(OneWayAnovaGroupResult {
                label: label.clone(),
                sample_size: values.len(),
                mean,
            })
        })
        .collect::<Vec<_>>();

    let group_count = groups.len();
    let total_sample_size: usize = groups.iter().map(|group| group.sample_size).sum();
    if group_count < 2 || total_sample_size <= group_count {
        return Err("One-way ANOVA requires at least two groups with at least two samples each".to_owned());
    }

    let grand_mean = groups
        .iter()
        .map(|group| group.mean * group.sample_size as f64)
        .sum::<f64>()
        / total_sample_size as f64;

    let mut ss_between = 0.0;
    let mut ss_within = 0.0;
    for group in &groups {
        let values = grouped_values.get(&group.label).expect("group values exist");
        ss_between += group.sample_size as f64 * (group.mean - grand_mean).powi(2);
        ss_within += values
            .iter()
            .map(|value| (value - group.mean).powi(2))
            .sum::<f64>();
    }

    let between_group_df = group_count - 1;
    let within_group_df = total_sample_size - group_count;
    if within_group_df == 0 {
        return Err("One-way ANOVA requires variability within groups".to_owned());
    }

    let ms_between = ss_between / between_group_df as f64;
    let ms_within = ss_within / within_group_df as f64;
    let f_statistic = if ms_within <= f64::EPSILON {
        0.0
    } else {
        ms_between / ms_within
    };
    let p_value = f_distribution_p_value(f_statistic, between_group_df as f64, within_group_df as f64);

    Ok(OneWayAnovaAnalysisResult {
        group_col: group_col.to_owned(),
        value_col: value_col.to_owned(),
        groups,
        f_statistic,
        p_value,
        between_group_df,
        within_group_df,
    })
}

pub fn format_one_way_anova_result(result: &OneWayAnovaAnalysisResult) -> String {
    let mut text = String::from("One-way ANOVA Results\n=====================\n\n");
    text.push_str(&format!(
        "Grouping by: '{}'\nValue column: '{}'\n\n---\n",
        result.group_col, result.value_col
    ));
    for group in &result.groups {
        text.push_str(&format!(
            "- Group {}: mean {:.4} (n={})\n",
            group.label, group.mean, group.sample_size
        ));
    }
    text.push_str(&format!(
        "\nF-statistic: {:.4}\nDegrees of freedom: {} / {}\np-value: {:.4}\n\n",
        result.f_statistic, result.between_group_df, result.within_group_df, result.p_value
    ));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: At least one group mean differs significantly (p < 0.05).");
    } else {
        text.push_str("Conclusion: No significant difference between group means was detected (p >= 0.05).");
    }
    text
}

pub fn run_mann_whitney_u_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    col1: &str,
    col2: &str,
) -> Result<MannWhitneyUAnalysisResult, String> {
    let sample1 = collect_numeric_column(table, table_view, col1)?;
    let sample2 = collect_numeric_column(table, table_view, col2)?;
    if sample1.len() < 1 || sample2.len() < 1 {
        return Err("Mann-Whitney U test requires at least one numeric value in each column".to_owned());
    }

    let mut combined = Vec::with_capacity(sample1.len() + sample2.len());
    for value in &sample1 {
        combined.push((*value, 0usize));
    }
    for value in &sample2 {
        combined.push((*value, 1usize));
    }
    combined.sort_by(|left, right| left.0.partial_cmp(&right.0).unwrap_or(std::cmp::Ordering::Equal));
    let combined_values = combined.iter().map(|(value, _)| *value).collect::<Vec<_>>();
    let ranks = rank_with_ties(&combined_values);

    let mut rank_sum1 = 0.0;
    let mut rank_sum2 = 0.0;
    for ((_, group), rank) in combined.iter().zip(ranks.iter()) {
        if *group == 0 {
            rank_sum1 += *rank;
        } else {
            rank_sum2 += *rank;
        }
    }

    let n1 = sample1.len() as f64;
    let n2 = sample2.len() as f64;
    let u1 = rank_sum1 - n1 * (n1 + 1.0) / 2.0;
    let u2 = rank_sum2 - n2 * (n2 + 1.0) / 2.0;
    let u_statistic = u1.min(u2);
    let mean_u = n1 * n2 / 2.0;
    let std_u = (n1 * n2 * (n1 + n2 + 1.0) / 12.0).sqrt();
    let z = if std_u <= f64::EPSILON { 0.0 } else { (u_statistic - mean_u).abs() / std_u };
    let p_value = 2.0 * (1.0 - normal_cdf(z));
    let mean_rank1 = rank_sum1 / n1;
    let mean_rank2 = rank_sum2 / n2;

    Ok(MannWhitneyUAnalysisResult {
        col1: col1.to_owned(),
        col2: col2.to_owned(),
        sample_size1: sample1.len(),
        sample_size2: sample2.len(),
        u_statistic,
        p_value,
        mean_rank1,
        mean_rank2,
    })
}

pub fn format_mann_whitney_u_result(result: &MannWhitneyUAnalysisResult) -> String {
    let mut text = String::from("Mann-Whitney U Test Results\n===========================\n\n");
    text.push_str(&format!(
        "Comparing:\n- Group 1: '{}'\n- Group 2: '{}'\n\n---\nMean rank 1: {:.4} (n={})\nMean rank 2: {:.4} (n={})\nU-statistic: {:.4}\np-value: {:.4}\n\n",
        result.col1,
        result.col2,
        result.mean_rank1,
        result.sample_size1,
        result.mean_rank2,
        result.sample_size2,
        result.u_statistic,
        result.p_value
    ));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: The distributions differ significantly (p < 0.05).");
    } else {
        text.push_str("Conclusion: No significant distributional difference was detected (p >= 0.05).");
    }
    text
}

pub fn run_wilcoxon_signed_rank_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    col1: &str,
    col2: &str,
) -> Result<WilcoxonSignedRankAnalysisResult, String> {
    let pairs = collect_paired_numeric_columns(table, table_view, col1, col2)?;
    if pairs.len() < 2 {
        return Err("Wilcoxon signed-rank test requires at least two paired numeric values".to_owned());
    }

    let differences = pairs
        .iter()
        .map(|(left, right)| left - right)
        .filter(|difference| difference.abs() > f64::EPSILON)
        .collect::<Vec<_>>();
    if differences.is_empty() {
        return Err("Wilcoxon signed-rank test requires at least one non-zero difference".to_owned());
    }

    let abs_differences = differences.iter().map(|value| value.abs()).collect::<Vec<_>>();
    let ranks = rank_with_ties(&abs_differences);
    let mut positive_rank_sum = 0.0;
    let mut negative_rank_sum = 0.0;
    for (difference, rank) in differences.iter().zip(ranks.iter()) {
        if *difference > 0.0 {
            positive_rank_sum += *rank;
        } else {
            negative_rank_sum += *rank;
        }
    }

    let n = ranks.len() as f64;
    let mean_w = n * (n + 1.0) / 4.0;
    let std_w = (n * (n + 1.0) * (2.0 * n + 1.0) / 24.0).sqrt();
    let w_statistic = positive_rank_sum.min(negative_rank_sum);
    let z = if std_w <= f64::EPSILON { 0.0 } else { (w_statistic - mean_w).abs() / std_w };
    let p_value = 2.0 * (1.0 - normal_cdf(z));

    Ok(WilcoxonSignedRankAnalysisResult {
        col1: col1.to_owned(),
        col2: col2.to_owned(),
        sample_size: pairs.len(),
        nonzero_difference_count: differences.len(),
        w_statistic,
        p_value,
        positive_rank_sum,
        negative_rank_sum,
    })
}

pub fn format_wilcoxon_signed_rank_result(result: &WilcoxonSignedRankAnalysisResult) -> String {
    let mut text = String::from("Wilcoxon Signed-rank Test Results\n=================================\n\n");
    text.push_str(&format!(
        "Comparing:\n- Column 1: '{}'\n- Column 2: '{}'\n\n---\nPositive rank sum: {:.4}\nNegative rank sum: {:.4}\nW-statistic: {:.4}\nPairs used: {}\np-value: {:.4}\n\n",
        result.col1,
        result.col2,
        result.positive_rank_sum,
        result.negative_rank_sum,
        result.w_statistic,
        result.nonzero_difference_count,
        result.p_value
    ));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: The paired distributions differ significantly (p < 0.05).");
    } else {
        text.push_str("Conclusion: No significant paired difference was detected (p >= 0.05).");
    }
    text
}

pub fn run_kruskal_wallis_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    group_col: &str,
    value_col: &str,
) -> Result<KruskalWallisAnalysisResult, String> {
    let group_index = table
        .headers
        .iter()
        .position(|header| header == group_col)
        .ok_or_else(|| format!("Unknown group column '{group_col}'"))?;
    let value_index = table
        .headers
        .iter()
        .position(|header| header == value_col)
        .ok_or_else(|| format!("Unknown value column '{value_col}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut grouped_values: HashMap<String, Vec<f64>> = HashMap::new();
    let mut order = Vec::new();
    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let group_label = normalize_label(row.get(group_index).map(String::as_str));
        let Some(value) = row.get(value_index) else {
            continue;
        };
        let Ok(value) = value.trim().parse::<f64>() else {
            continue;
        };
        if !grouped_values.contains_key(&group_label) {
            order.push(group_label.clone());
        }
        grouped_values.entry(group_label).or_default().push(value);
    }

    if order.len() < 2 {
        return Err("Kruskal-Wallis test requires at least two groups".to_owned());
    }

    let mut pooled = Vec::new();
    for (label, values) in &grouped_values {
        for value in values {
            pooled.push((*value, label.clone()));
        }
    }
    pooled.sort_by(|left, right| left.0.partial_cmp(&right.0).unwrap_or(std::cmp::Ordering::Equal));
    let pooled_values = pooled.iter().map(|(value, _)| *value).collect::<Vec<_>>();
    let ranks = rank_with_ties(&pooled_values);

    let mut rank_sums: HashMap<String, f64> = HashMap::new();
    for ((_, label), rank) in pooled.iter().zip(ranks.iter()) {
        *rank_sums.entry(label.clone()).or_insert(0.0) += *rank;
    }
    let total_n = pooled.len() as f64;
    let mut h_statistic = 0.0;
    let mut group_results = Vec::new();
    for label in order {
        let values = grouped_values.get(&label).expect("group values exist");
        let n_i = values.len() as f64;
        if n_i <= 0.0 {
            continue;
        }
        let rank_sum = rank_sums.get(&label).copied().unwrap_or(0.0);
        let mean_rank = rank_sum / n_i;
        h_statistic += rank_sum * rank_sum / n_i;
        group_results.push(KruskalWallisGroupResult {
            label,
            sample_size: values.len(),
            mean_rank,
        });
    }
    h_statistic = (12.0 / (total_n * (total_n + 1.0))) * h_statistic - 3.0 * (total_n + 1.0);
    let degrees_of_freedom = group_results.len() - 1;
    let p_value = chi_square_p_value(h_statistic, degrees_of_freedom as f64);

    Ok(KruskalWallisAnalysisResult {
        group_col: group_col.to_owned(),
        value_col: value_col.to_owned(),
        groups: group_results,
        h_statistic,
        p_value,
        degrees_of_freedom,
    })
}

pub fn format_kruskal_wallis_result(result: &KruskalWallisAnalysisResult) -> String {
    let mut text = String::from("Kruskal-Wallis Test Results\n===========================\n\n");
    text.push_str(&format!(
        "Grouping by: '{}'\nValue column: '{}'\n\n---\n",
        result.group_col, result.value_col
    ));
    for group in &result.groups {
        text.push_str(&format!(
            "- Group {}: mean rank {:.4} (n={})\n",
            group.label, group.mean_rank, group.sample_size
        ));
    }
    text.push_str(&format!(
        "\nH-statistic: {:.4}\nDegrees of freedom: {}\np-value: {:.4}\n\n",
        result.h_statistic, result.degrees_of_freedom, result.p_value
    ));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: At least one group distribution differs significantly (p < 0.05).");
    } else {
        text.push_str("Conclusion: No significant distributional difference was detected (p >= 0.05).");
    }
    text
}

pub fn run_shapiro_wilk_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    group_col: &str,
    value_col: &str,
) -> Result<ShapiroAnalysisResult, String> {
    let group_index = table
        .headers
        .iter()
        .position(|header| header == group_col)
        .ok_or_else(|| format!("Unknown group column '{group_col}'"))?;
    let value_index = table
        .headers
        .iter()
        .position(|header| header == value_col)
        .ok_or_else(|| format!("Unknown value column '{value_col}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut grouped_values: HashMap<String, Vec<f64>> = HashMap::new();
    let mut order = Vec::new();
    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let group_label = normalize_label(row.get(group_index).map(String::as_str));
        let Some(value) = row.get(value_index) else {
            continue;
        };
        let Ok(value) = value.trim().parse::<f64>() else {
            continue;
        };
        if !grouped_values.contains_key(&group_label) {
            order.push(group_label.clone());
        }
        grouped_values.entry(group_label).or_default().push(value);
    }

    if order.is_empty() {
        return Err("Shapiro-Wilk test requires at least one populated group".to_owned());
    }

    let mut groups = Vec::new();
    for label in order {
        let Some(values) = grouped_values.get(&label) else {
            continue;
        };
        if values.len() < 3 {
            groups.push(ShapiroGroupResult {
                group_name: label,
                sample_size: values.len(),
                statistic: None,
                p_value: None,
                skipped: true,
            });
            continue;
        }

        let mut sorted_values = values.clone();
        sorted_values.sort_by(|left, right| {
            left.partial_cmp(right).unwrap_or(std::cmp::Ordering::Equal)
        });
        let statistic = shapiro_francia_w_statistic(&sorted_values);
        let p_value = shapiro_francia_p_value(statistic, sorted_values.len());
        groups.push(ShapiroGroupResult {
            group_name: label,
            sample_size: values.len(),
            statistic: Some(statistic),
            p_value: Some(p_value),
            skipped: false,
        });
    }

    Ok(ShapiroAnalysisResult {
        value_col: value_col.to_owned(),
        group_col: group_col.to_owned(),
        groups,
    })
}

pub fn format_shapiro_wilk_result(result: &ShapiroAnalysisResult) -> String {
    let mut text = String::from("Shapiro-Wilk Normality Test Results\n=========================================\n\n");
    text.push_str(&format!(
        "Value Column: {}\nGrouping by: {}\n\np > 0.05 suggests that the data is normally distributed.\n\n-----------------------------------------",
        result.value_col, result.group_col
    ));
    for group in &result.groups {
        text.push_str(&format!("\nGroup: {} (n={})\n", group.group_name, group.sample_size));
        if group.skipped {
            text.push_str("  -> Skipped (sample size < 3)\n");
        } else if let (Some(statistic), Some(p_value)) = (group.statistic, group.p_value) {
            text.push_str(&format!("  - W-statistic: {:.4}\n", statistic));
            text.push_str(&format!("  - p-value: {:.4}\n", p_value));
            if p_value > 0.05 {
                text.push_str("  - Conclusion: Data likely follows a normal distribution.\n");
            } else {
                text.push_str("  - Conclusion: Data likely does not follow a normal distribution.\n");
            }
        }
        text.push_str("-----------------------------------------");
    }
    text
}

pub fn run_two_proportion_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    rows_col: &str,
    cols_col: &str,
) -> Result<TwoProportionAnalysisResult, String> {
    let row_index = table
        .headers
        .iter()
        .position(|header| header == rows_col)
        .ok_or_else(|| format!("Unknown row column '{rows_col}'"))?;
    let col_index = table
        .headers
        .iter()
        .position(|header| header == cols_col)
        .ok_or_else(|| format!("Unknown column column '{cols_col}'"))?;
    let row_indices = resolved_row_indices(table, table_view);
    if row_indices.is_empty() {
        return Err("No visible rows available for analysis".to_owned());
    }

    let mut row_labels = Vec::new();
    let mut column_labels = Vec::new();
    let mut counts = HashMap::<(String, String), usize>::new();

    for row_idx in row_indices {
        let Some(row) = table.rows.get(row_idx) else {
            continue;
        };
        let row_label = normalize_label(row.get(row_index).map(String::as_str));
        let col_label = normalize_label(row.get(col_index).map(String::as_str));
        if !row_labels.contains(&row_label) {
            row_labels.push(row_label.clone());
        }
        if !column_labels.contains(&col_label) {
            column_labels.push(col_label.clone());
        }
        *counts.entry((row_label, col_label)).or_insert(0) += 1;
    }

    if row_labels.len() != 2 || column_labels.len() != 2 {
        return Err("2-proportion z-test requires a 2x2 contingency table".to_owned());
    }

    let contingency_table = row_labels
        .iter()
        .map(|row_label| {
            column_labels
                .iter()
                .map(|col_label| {
                    counts
                        .get(&(row_label.clone(), col_label.clone()))
                        .copied()
                        .unwrap_or(0)
                })
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();

    let success_label = column_labels[0].clone();
    let success_count_group1 = contingency_table[0][0];
    let success_count_group2 = contingency_table[1][0];
    let total_group1 = contingency_table[0].iter().sum::<usize>();
    let total_group2 = contingency_table[1].iter().sum::<usize>();
    let total = total_group1 + total_group2;
    if total == 0 || total_group1 == 0 || total_group2 == 0 {
        return Err("2-proportion z-test requires at least one observation in each group".to_owned());
    }

    let proportion_group1 = success_count_group1 as f64 / total_group1 as f64;
    let proportion_group2 = success_count_group2 as f64 / total_group2 as f64;
    let pooled = (success_count_group1 + success_count_group2) as f64 / total as f64;
    let standard_error =
        (pooled * (1.0 - pooled) * ((1.0 / total_group1 as f64) + (1.0 / total_group2 as f64)))
            .sqrt();
    let z_statistic = if standard_error <= f64::EPSILON {
        0.0
    } else {
        (proportion_group1 - proportion_group2) / standard_error
    };
    let p_value = 2.0 * (1.0 - normal_cdf(z_statistic.abs()));

    let (ci_low_group1, ci_high_group1) =
        wilson_score_interval(success_count_group1, total_group1);
    let (ci_low_group2, ci_high_group2) =
        wilson_score_interval(success_count_group2, total_group2);
    let difference_in_proportions = proportion_group1 - proportion_group2;
    let diff_standard_error = (
        proportion_group1 * (1.0 - proportion_group1) / total_group1 as f64
            + proportion_group2 * (1.0 - proportion_group2) / total_group2 as f64
    )
        .sqrt();
    let diff_margin = 1.96 * diff_standard_error;

    Ok(TwoProportionAnalysisResult {
        rows_col: rows_col.to_owned(),
        cols_col: cols_col.to_owned(),
        group1_label: row_labels[0].clone(),
        group2_label: row_labels[1].clone(),
        success_label,
        success_count_group1,
        success_count_group2,
        total_group1,
        total_group2,
        proportion_group1,
        proportion_group2,
        ci_low_group1,
        ci_high_group1,
        ci_low_group2,
        ci_high_group2,
        difference_in_proportions,
        ci_low_difference: difference_in_proportions - diff_margin,
        ci_high_difference: difference_in_proportions + diff_margin,
        z_statistic,
        p_value,
    })
}

pub fn format_two_proportion_result(result: &TwoProportionAnalysisResult) -> String {
    let mut text = String::from("2-Proportion z-test Results\n============================\n\n");
    text.push_str(&format!(
        "Comparing success rate for '{}' across '{}'.\nReference categorical column: '{}'\n\n",
        result.success_label, result.rows_col, result.cols_col
    ));
    text.push_str(&format!(
        "- Group 1: {} ({}/{}, {:.3}, 95% CI [{:.3}, {:.3}])\n",
        result.group1_label,
        result.success_count_group1,
        result.total_group1,
        result.proportion_group1,
        result.ci_low_group1,
        result.ci_high_group1
    ));
    text.push_str(&format!(
        "- Group 2: {} ({}/{}, {:.3}, 95% CI [{:.3}, {:.3}])\n\n",
        result.group2_label,
        result.success_count_group2,
        result.total_group2,
        result.proportion_group2,
        result.ci_low_group2,
        result.ci_high_group2
    ));
    text.push_str("---\n");
    text.push_str(&format!(
        "Difference in proportions: {:.3}\n",
        result.difference_in_proportions
    ));
    text.push_str(&format!(
        "95% CI for difference: [{:.3}, {:.3}]\n",
        result.ci_low_difference, result.ci_high_difference
    ));
    text.push_str(&format!("z-statistic: {:.4}\n", result.z_statistic));
    text.push_str(&format!("p-value: {:.4}\n\n", result.p_value));
    if result.p_value < 0.05 {
        text.push_str("Conclusion: The difference in proportions is statistically significant (p < 0.05).");
    } else {
        text.push_str("Conclusion: The difference in proportions is not statistically significant (p >= 0.05).");
    }
    text
}

pub fn run_chi_squared_analysis(
    table: &DataTable,
    table_view: &TableViewState,
    rows_col: &str,
    cols_col: &str,
) -> Result<ChiSquaredAnalysisResult, String> {
    let row_index = table
        .headers
        .iter()
        .position(|header| header == rows_col)
        .ok_or_else(|| format!("Unknown row column '{rows_col}'"))?;
    let col_index = table
        .headers
        .iter()
        .position(|header| header == cols_col)
        .ok_or_else(|| format!("Unknown column column '{cols_col}'"))?;
    let row_indices = resolved_row_indices(table, table_view);
    if row_indices.is_empty() {
        return Err("No visible rows available for analysis".to_owned());
    }

    let mut row_labels = Vec::new();
    let mut column_labels = Vec::new();
    let mut counts = HashMap::<(String, String), usize>::new();

    for row_idx in row_indices {
        let Some(row) = table.rows.get(row_idx) else {
            continue;
        };
        let row_label = normalize_label(row.get(row_index).map(String::as_str));
        let col_label = normalize_label(row.get(col_index).map(String::as_str));
        if !row_labels.contains(&row_label) {
            row_labels.push(row_label.clone());
        }
        if !column_labels.contains(&col_label) {
            column_labels.push(col_label.clone());
        }
        *counts.entry((row_label, col_label)).or_insert(0) += 1;
    }

    if row_labels.len() < 2 || column_labels.len() < 2 {
        return Err("Chi-squared analysis requires at least 2 rows and 2 columns".to_owned());
    }

    let contingency_table = row_labels
        .iter()
        .map(|row_label| {
            column_labels
                .iter()
                .map(|col_label| {
                    counts
                        .get(&(row_label.clone(), col_label.clone()))
                        .copied()
                        .unwrap_or(0)
                })
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();

    let row_totals = contingency_table
        .iter()
        .map(|row| row.iter().sum::<usize>())
        .collect::<Vec<_>>();
    let column_totals = (0..column_labels.len())
        .map(|col_index| contingency_table.iter().map(|row| row[col_index]).sum::<usize>())
        .collect::<Vec<_>>();
    let total: usize = row_totals.iter().sum();
    if total == 0 {
        return Err("Chi-squared analysis requires at least one observation".to_owned());
    }

    let total_f = total as f64;
    let expected_table = row_totals
        .iter()
        .map(|row_total| {
            column_totals
                .iter()
                .map(|col_total| (*row_total as f64 * *col_total as f64) / total_f)
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();

    let mut standardized_residuals = vec![vec![0.0; column_labels.len()]; row_labels.len()];
    let mut contribution_table = vec![vec![0.0; column_labels.len()]; row_labels.len()];
    let mut chi2 = 0.0;
    let use_yates_correction = row_labels.len() == 2 && column_labels.len() == 2;

    for row_index in 0..row_labels.len() {
        for col_index in 0..column_labels.len() {
            let observed = contingency_table[row_index][col_index] as f64;
            let expected = expected_table[row_index][col_index];
            if expected <= f64::EPSILON {
                continue;
            }
            let delta = observed - expected;
            let contribution = if use_yates_correction {
                let adjusted = (delta.abs() - 0.5).max(0.0);
                (adjusted * adjusted) / expected
            } else {
                (delta * delta) / expected
            };
            chi2 += contribution;
            contribution_table[row_index][col_index] = (delta * delta) / expected;
            standardized_residuals[row_index][col_index] = delta / expected.sqrt();
        }
    }

    let degrees_of_freedom = (row_labels.len() - 1) * (column_labels.len() - 1);
    let p_value = chi_square_p_value(chi2, degrees_of_freedom as f64);
    let min_dimension = (row_labels.len() - 1).min(column_labels.len() - 1).max(1) as f64;
    let cramers_v = (chi2 / (total_f * min_dimension)).sqrt();

    Ok(ChiSquaredAnalysisResult {
        rows_col: rows_col.to_owned(),
        cols_col: cols_col.to_owned(),
        contingency_table,
        row_labels,
        column_labels,
        expected_table,
        standardized_residuals,
        contribution_table,
        chi2,
        p_value,
        degrees_of_freedom,
        cramers_v,
    })
}

pub fn format_chi_squared_result(result: &ChiSquaredAnalysisResult) -> String {
    let mut text = String::from("Chi-squared Test Results\n==========================\n\n");
    text.push_str("Observed Frequencies:\n");
    text.push_str(&format_table(&result.contingency_table, &result.row_labels, &result.column_labels));
    text.push_str("\nExpected Frequencies:\n");
    text.push_str(&format_float_table(
        &result.expected_table,
        &result.row_labels,
        &result.column_labels,
        2,
    ));
    text.push_str("\nStandardized Residuals:\n");
    text.push_str(&format_float_table(
        &result.standardized_residuals,
        &result.row_labels,
        &result.column_labels,
        2,
    ));
    text.push_str("\nCell Contributions to Chi-squared:\n");
    text.push_str(&format_float_table(
        &result.contribution_table,
        &result.row_labels,
        &result.column_labels,
        2,
    ));
    text.push_str("\n---\n");
    text.push_str(&format!("Chi-squared statistic: {:.4}\n", result.chi2));
    text.push_str(&format!("Degrees of Freedom: {}\n", result.degrees_of_freedom));
    text.push_str(&format!("Cramer's V: {:.4}\n", result.cramers_v));
    text.push_str(&format!("p-value: {:.4}\n\n", result.p_value));
    if result.p_value < 0.05 {
        text.push_str(&format!(
            "Conclusion: There is a statistically significant association between '{}' and '{}' (p < 0.05).",
            result.rows_col, result.cols_col
        ));
    } else {
        text.push_str(&format!(
            "Conclusion: There is no statistically significant association between '{}' and '{}' (p >= 0.05).",
            result.rows_col, result.cols_col
        ));
    }
    text
}

fn normalize_label(value: Option<&str>) -> String {
    let value = value.unwrap_or("").trim();
    if value.is_empty() {
        "(empty)".to_owned()
    } else {
        value.to_owned()
    }
}

fn format_table(table: &[Vec<usize>], row_labels: &[String], column_labels: &[String]) -> String {
    let row_width = row_labels
        .iter()
        .map(|label| label.len())
        .max()
        .unwrap_or(5)
        .max("row".len());
    let col_widths = column_labels
        .iter()
        .enumerate()
        .map(|(index, label)| {
            let value_width = table
                .iter()
                .map(|row| row[index].to_string().len())
                .max()
                .unwrap_or(1);
            label.len().max(value_width).max(3)
        })
        .collect::<Vec<_>>();

    let mut lines = Vec::new();
    let mut header = format!("{:>width$} |", "row", width = row_width);
    for (label, width) in column_labels.iter().zip(col_widths.iter()) {
        header.push_str(&format!(" {:>width$}", label, width = width));
    }
    lines.push(header);

    for (row_label, row) in row_labels.iter().zip(table.iter()) {
        let mut line = format!("{:>width$} |", row_label, width = row_width);
        for (value, width) in row.iter().zip(col_widths.iter()) {
            line.push_str(&format!(" {:>width$}", value, width = width));
        }
        lines.push(line);
    }
    lines.join("\n")
}

fn format_float_table(
    table: &[Vec<f64>],
    row_labels: &[String],
    column_labels: &[String],
    precision: usize,
) -> String {
    let row_width = row_labels
        .iter()
        .map(|label| label.len())
        .max()
        .unwrap_or(5)
        .max("row".len());
    let col_widths = column_labels
        .iter()
        .enumerate()
        .map(|(index, label)| {
            let value_width = table
                .iter()
                .map(|row| format!("{:.precision$}", row[index], precision = precision).len())
                .max()
                .unwrap_or(precision + 2);
            label.len().max(value_width).max(3)
        })
        .collect::<Vec<_>>();

    let mut lines = Vec::new();
    let mut header = format!("{:>width$} |", "row", width = row_width);
    for (label, width) in column_labels.iter().zip(col_widths.iter()) {
        header.push_str(&format!(" {:>width$}", label, width = width));
    }
    lines.push(header);

    for (row_label, row) in row_labels.iter().zip(table.iter()) {
        let mut line = format!("{:>width$} |", row_label, width = row_width);
        for (value, width) in row.iter().zip(col_widths.iter()) {
            line.push_str(&format!(" {:>width$.precision$}", value, width = width, precision = precision));
        }
        lines.push(line);
    }
    lines.join("\n")
}

fn chi_square_p_value(chi2: f64, degrees_of_freedom: f64) -> f64 {
    if chi2 <= 0.0 || degrees_of_freedom <= 0.0 {
        return 1.0;
    }

    regularized_gamma_q(degrees_of_freedom / 2.0, chi2 / 2.0)
}

fn collect_numeric_column(
    table: &DataTable,
    table_view: &TableViewState,
    column: &str,
) -> Result<Vec<f64>, String> {
    let column_index = table
        .headers
        .iter()
        .position(|header| header == column)
        .ok_or_else(|| format!("Unknown column '{column}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut values = Vec::new();
    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let Some(value) = row.get(column_index) else {
            continue;
        };
        let Ok(value) = value.trim().parse::<f64>() else {
            continue;
        };
        values.push(value);
    }

    if values.is_empty() {
        return Err(format!("Column '{column}' does not contain any numeric values"));
    }

    Ok(values)
}

fn collect_paired_numeric_columns(
    table: &DataTable,
    table_view: &TableViewState,
    left_column: &str,
    right_column: &str,
) -> Result<Vec<(f64, f64)>, String> {
    let left_index = table
        .headers
        .iter()
        .position(|header| header == left_column)
        .ok_or_else(|| format!("Unknown column '{left_column}'"))?;
    let right_index = table
        .headers
        .iter()
        .position(|header| header == right_column)
        .ok_or_else(|| format!("Unknown column '{right_column}'"))?;
    let row_indices = resolved_row_indices(table, table_view);

    let mut pairs = Vec::new();
    for row_index in row_indices {
        let Some(row) = table.rows.get(row_index) else {
            continue;
        };
        let Some(left) = row.get(left_index) else {
            continue;
        };
        let Some(right) = row.get(right_index) else {
            continue;
        };
        let Ok(left) = left.trim().parse::<f64>() else {
            continue;
        };
        let Ok(right) = right.trim().parse::<f64>() else {
            continue;
        };
        pairs.push((left, right));
    }

    if pairs.is_empty() {
        return Err(format!(
            "Columns '{left_column}' and '{right_column}' do not contain any paired numeric values"
        ));
    }

    Ok(pairs)
}

fn rank_with_ties(values: &[f64]) -> Vec<f64> {
    let mut indexed_values = values
        .iter()
        .copied()
        .enumerate()
        .collect::<Vec<(usize, f64)>>();
    indexed_values.sort_by(|left, right| {
        left.1
            .partial_cmp(&right.1)
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    let mut ranks = vec![0.0; values.len()];
    let mut index = 0;
    while index < indexed_values.len() {
        let tie_start = index;
        let tie_value = indexed_values[index].1;
        index += 1;
        while index < indexed_values.len() && indexed_values[index].1 == tie_value {
            index += 1;
        }
        let rank_start = tie_start as f64 + 1.0;
        let rank_end = index as f64;
        let average_rank = (rank_start + rank_end) / 2.0;
        for tie_index in tie_start..index {
            ranks[indexed_values[tie_index].0] = average_rank;
        }
    }

    ranks
}

fn shapiro_francia_w_statistic(values: &[f64]) -> f64 {
    let n = values.len();
    if n < 3 {
        return f64::NAN;
    }
    let mean = values.iter().sum::<f64>() / n as f64;
    let sum_sq = values
        .iter()
        .map(|value| {
            let diff = *value - mean;
            diff * diff
        })
        .sum::<f64>();
    if sum_sq <= f64::EPSILON {
        return 1.0;
    }

    let normal_scores = (1..=n)
        .map(|index| {
            let probability = (index as f64 - 0.375) / (n as f64 + 0.25);
            inverse_normal_cdf(probability)
        })
        .collect::<Vec<_>>();
    let score_norm = normal_scores.iter().map(|value| value * value).sum::<f64>().sqrt();
    if score_norm <= f64::EPSILON {
        return 1.0;
    }
    let weights = normal_scores.iter().map(|value| value / score_norm).collect::<Vec<_>>();
    let numerator = values
        .iter()
        .zip(weights.iter())
        .map(|(value, weight)| value * weight)
        .sum::<f64>();
    (numerator * numerator / sum_sq).clamp(0.0, 1.0)
}

fn shapiro_francia_p_value(statistic: f64, sample_size: usize) -> f64 {
    if sample_size < 3 {
        return 1.0;
    }

    let n = sample_size as f64;
    let ln_n = n.ln();
    let mu = if sample_size <= 11 {
        -0.000_671_4 * n.powi(3) + 0.025_054 * n.powi(2) - 0.399_78 * n + 0.5440
    } else {
        0.003_891_5 * ln_n.powi(3) - 0.083_751 * ln_n.powi(2) - 0.310_82 * ln_n - 1.5861
    };
    let sigma = if sample_size <= 11 {
        (-0.002_032_2 * n.powi(3) + 0.062_767 * n.powi(2) - 0.778_57 * n + 1.382_2).exp()
    } else {
        (0.003_030_2 * ln_n.powi(2) - 0.082_676 * ln_n - 0.4803).exp()
    };

    if !statistic.is_finite() || statistic >= 1.0 {
        return 1.0;
    }
    let transformed = (1.0 - statistic).max(f64::MIN_POSITIVE).ln();
    let z = (transformed - mu) / sigma;
    normal_cdf(z).clamp(0.0, 1.0)
}

fn sigmoid_4pl(x: f64, bottom: f64, top: f64, hill_slope: f64, log_ec50: f64) -> f64 {
    bottom + (top - bottom) / (1.0 + 10_f64.powf((log_ec50 - x) * hill_slope))
}

fn fit_four_pl_parameters(x_values: &[f64], y_values: &[f64]) -> [f64; 4] {
    let mut bottom = y_values
        .iter()
        .copied()
        .fold(f64::INFINITY, f64::min);
    let mut top = y_values
        .iter()
        .copied()
        .fold(f64::NEG_INFINITY, f64::max);
    if !bottom.is_finite() || !top.is_finite() {
        return [f64::NAN; 4];
    }
    if (top - bottom).abs() <= f64::EPSILON {
        top = bottom + 1.0;
    }
    let mut hill_slope = 1.0;
    let mut log_ec50 = median(x_values);

    let mut params = [bottom, top, hill_slope, log_ec50];
    let mut step_sizes = [
        (top - bottom).abs().max(1.0) * 0.25,
        (top - bottom).abs().max(1.0) * 0.25,
        1.0,
        0.5,
    ];

    let mut best_error = four_pl_sum_squares(x_values, y_values, params);
    for _ in 0..200 {
        let mut improved = false;
        for index in 0..params.len() {
            let step = step_sizes[index];
            if step <= 1e-6 {
                continue;
            }
            for direction in [-1.0, 1.0] {
                let mut candidate = params;
                candidate[index] += direction * step;
                candidate[2] = candidate[2].clamp(-10.0, 10.0);
                candidate[3] = candidate[3].clamp(-12.0, 12.0);
                if index == 0 || index == 1 {
                    candidate[index] = candidate[index].clamp(-1.0e6, 1.0e6);
                }
                let error = four_pl_sum_squares(x_values, y_values, candidate);
                if error.is_finite() && error < best_error {
                    params = candidate;
                    best_error = error;
                    improved = true;
                }
            }
        }
        if !improved {
            for step in &mut step_sizes {
                *step *= 0.5;
            }
            if step_sizes.iter().all(|step| *step < 1e-5) {
                break;
            }
        }
    }

    bottom = params[0];
    top = params[1];
    hill_slope = params[2];
    log_ec50 = params[3];
    if top < bottom {
        std::mem::swap(&mut bottom, &mut top);
    }

    [bottom, top, hill_slope, log_ec50]
}

fn four_pl_sum_squares(x_values: &[f64], y_values: &[f64], params: [f64; 4]) -> f64 {
    x_values
        .iter()
        .zip(y_values.iter())
        .map(|(x, y)| {
            let prediction = sigmoid_4pl(*x, params[0], params[1], params[2], params[3]);
            if !prediction.is_finite() {
                return f64::INFINITY;
            }
            let residual = y - prediction;
            residual * residual
        })
        .sum()
}

fn median(values: &[f64]) -> f64 {
    let mut sorted = values.to_vec();
    sorted.sort_by(|left, right| left.partial_cmp(right).unwrap_or(std::cmp::Ordering::Equal));
    let mid = sorted.len() / 2;
    if sorted.len() % 2 == 0 {
        (sorted[mid - 1] + sorted[mid]) / 2.0
    } else {
        sorted[mid]
    }
}

fn inverse_normal_cdf(p: f64) -> f64 {
    if !(0.0..=1.0).contains(&p) {
        return f64::NAN;
    }
    if p <= 0.0 {
        return f64::NEG_INFINITY;
    }
    if p >= 1.0 {
        return f64::INFINITY;
    }

    // Acklam's inverse normal CDF approximation.
    const A: [f64; 6] = [
        -3.969_683_028_665_376e1,
        2.209_460_984_245_205e2,
        -2.759_285_104_469_687e2,
        1.383_577_518_672_69e2,
        -3.066_479_806_614_716e1,
        2.506_628_277_459_239,
    ];
    const B: [f64; 5] = [
        -5.447_609_879_822_406e1,
        1.615_858_368_580_409e2,
        -1.556_989_798_598_866e2,
        6.680_131_188_771_972e1,
        -1.328_068_155_288_572e1,
    ];
    const C: [f64; 6] = [
        -7.784_894_002_430_293e-3,
        -3.223_964_580_411_365e-1,
        -2.400_758_277_161_838,
        -2.549_732_539_343_734,
        4.374_664_141_464_968,
        2.938_163_982_698_783,
    ];
    const D: [f64; 4] = [
        7.784_695_709_041_462e-3,
        3.224_671_290_700_398e-1,
        2.445_134_137_142_996,
        3.754_408_661_907_416,
    ];
    const P_LOW: f64 = 0.024_25;
    const P_HIGH: f64 = 1.0 - P_LOW;

    let q;
    let r;
    if p < P_LOW {
        q = (-2.0 * p.ln()).sqrt();
        return (((((C[0] * q + C[1]) * q + C[2]) * q + C[3]) * q + C[4]) * q + C[5])
            / ((((D[0] * q + D[1]) * q + D[2]) * q + D[3]) * q + 1.0);
    }
    if p > P_HIGH {
        q = (-2.0 * (1.0 - p).ln()).sqrt();
        return -(((((C[0] * q + C[1]) * q + C[2]) * q + C[3]) * q + C[4]) * q + C[5])
            / ((((D[0] * q + D[1]) * q + D[2]) * q + D[3]) * q + 1.0);
    }

    q = p - 0.5;
    r = q * q;
    (((((A[0] * r + A[1]) * r + A[2]) * r + A[3]) * r + A[4]) * r + A[5]) * q
        / (((((B[0] * r + B[1]) * r + B[2]) * r + B[3]) * r + B[4]) * r + 1.0)
}

fn wilson_score_interval(successes: usize, total: usize) -> (f64, f64) {
    const Z: f64 = 1.959_963_984_540_054;
    let n = total as f64;
    if n <= 0.0 {
        return (0.0, 0.0);
    }
    let successes = successes as f64;
    let phat = successes / n;
    let z2 = Z * Z;
    let denominator = 1.0 + z2 / n;
    let center = (phat + z2 / (2.0 * n)) / denominator;
    let margin = Z
        * ((phat * (1.0 - phat) + z2 / (4.0 * n)) / n)
            .sqrt()
        / denominator;
    ((center - margin).clamp(0.0, 1.0), (center + margin).clamp(0.0, 1.0))
}

fn normal_cdf(x: f64) -> f64 {
    0.5 * (1.0 + erf_approx(x / std::f64::consts::SQRT_2))
}

fn erf_approx(x: f64) -> f64 {
    let sign = if x < 0.0 { -1.0 } else { 1.0 };
    let x = x.abs();
    let t = 1.0 / (1.0 + 0.327_591_1 * x);
    let y = (((((1.061_405_429 * t - 1.453_152_027) * t + 1.421_413_741) * t
        - 0.284_496_736)
        * t
        + 0.254_829_592)
        * t)
        * (-x * x).exp();
    sign * (1.0 - y)
}

fn student_t_cdf(t: f64, df: f64) -> f64 {
    if !t.is_finite() || !df.is_finite() || df <= 0.0 {
        return f64::NAN;
    }
    let x = df / (df + t * t);
    let ib = regularized_beta(x, df / 2.0, 0.5);
    if t >= 0.0 {
        1.0 - 0.5 * ib
    } else {
        0.5 * ib
    }
}

fn sample_variance(values: &[f64], mean: f64) -> f64 {
    if values.len() < 2 {
        return 0.0;
    }
    let sum_sq = values.iter().map(|value| {
        let diff = *value - mean;
        diff * diff
    });
    sum_sq.sum::<f64>() / (values.len() as f64 - 1.0)
}

fn f_distribution_p_value(f_stat: f64, dfn: f64, dfd: f64) -> f64 {
    if !f_stat.is_finite() || dfn <= 0.0 || dfd <= 0.0 {
        return f64::NAN;
    }
    if f_stat <= 0.0 {
        return 1.0;
    }
    let x = (dfn * f_stat) / (dfn * f_stat + dfd);
    1.0 - regularized_beta(x, dfn / 2.0, dfd / 2.0)
}

fn regularized_beta(x: f64, a: f64, b: f64) -> f64 {
    if x <= 0.0 {
        return 0.0;
    }
    if x >= 1.0 {
        return 1.0;
    }
    let bt = (ln_gamma(a + b) - ln_gamma(a) - ln_gamma(b) + a * x.ln() + b * (1.0 - x).ln())
        .exp();
    if x < (a + 1.0) / (a + b + 2.0) {
        bt * beta_continued_fraction(x, a, b) / a
    } else {
        1.0 - bt * beta_continued_fraction(1.0 - x, b, a) / b
    }
}

fn beta_continued_fraction(x: f64, a: f64, b: f64) -> f64 {
    const MAX_ITER: usize = 200;
    const EPS: f64 = 3.0e-14;
    const FPMIN: f64 = f64::MIN_POSITIVE / EPS;

    let qab = a + b;
    let qap = a + 1.0;
    let qam = a - 1.0;

    let mut c = 1.0;
    let mut d = 1.0 - qab * x / qap;
    if d.abs() < FPMIN {
        d = FPMIN;
    }
    d = 1.0 / d;
    let mut h = d;

    for m in 1..=MAX_ITER {
        let m2 = 2 * m;
        let mut aa = (m as f64) * (b - m as f64) * x / ((qam + m2 as f64) * (a + m2 as f64));
        d = 1.0 + aa * d;
        if d.abs() < FPMIN {
            d = FPMIN;
        }
        c = 1.0 + aa / c;
        if c.abs() < FPMIN {
            c = FPMIN;
        }
        d = 1.0 / d;
        h *= d * c;

        aa = -(a + m as f64) * (qab + m as f64) * x / ((a + m2 as f64) * (qap + m2 as f64));
        d = 1.0 + aa * d;
        if d.abs() < FPMIN {
            d = FPMIN;
        }
        c = 1.0 + aa / c;
        if c.abs() < FPMIN {
            c = FPMIN;
        }
        d = 1.0 / d;
        let del = d * c;
        h *= del;
        if (del - 1.0).abs() < EPS {
            break;
        }
    }

    h
}

fn regularized_gamma_q(a: f64, x: f64) -> f64 {
    if x < 0.0 || a <= 0.0 {
        return f64::NAN;
    }
    if x == 0.0 {
        return 1.0;
    }
    if x < a + 1.0 {
        1.0 - regularized_gamma_p_series(a, x)
    } else {
        regularized_gamma_q_continued_fraction(a, x)
    }
}

fn regularized_gamma_p_series(a: f64, x: f64) -> f64 {
    let gln = ln_gamma(a);
    let mut sum = 1.0 / a;
    let mut term = sum;
    let mut n = 1.0;
    while term.abs() > sum.abs() * 1e-14 {
        term *= x / (a + n);
        sum += term;
        n += 1.0;
        if n > 10_000.0 {
            break;
        }
    }
    sum * (-x + a * x.ln() - gln).exp()
}

fn regularized_gamma_q_continued_fraction(a: f64, x: f64) -> f64 {
    let gln = ln_gamma(a);
    let mut b = x + 1.0 - a;
    let mut c = 1.0 / f64::MIN_POSITIVE;
    let mut d = 1.0 / b;
    let mut h = d;
    for i in 1..=10_000 {
        let i_f = i as f64;
        let an = -i_f * (i_f - a);
        b += 2.0;
        d = an * d + b;
        if d.abs() < f64::MIN_POSITIVE {
            d = f64::MIN_POSITIVE;
        }
        c = b + an / c;
        if c.abs() < f64::MIN_POSITIVE {
            c = f64::MIN_POSITIVE;
        }
        d = 1.0 / d;
        let delta = d * c;
        h *= delta;
        if (delta - 1.0).abs() < 1e-14 {
            break;
        }
    }
    (-x + a * x.ln() - gln).exp() * h
}

fn ln_gamma(z: f64) -> f64 {
    const COEFFS: [f64; 9] = [
        0.999_999_999_999_809_9,
        676.520_368_121_885_1,
        -1_259.139_216_722_402_8,
        771.323_428_777_653_1,
        -176.615_029_162_140_6,
        12.507_343_278_686_905,
        -0.138_571_095_265_720_12,
        9.984_369_578_019_572e-6,
        1.505_632_735_149_311_6e-7,
    ];

    if z < 0.5 {
        return std::f64::consts::PI.ln()
            - (std::f64::consts::PI * z).sin().ln()
            - ln_gamma(1.0 - z);
    }

    let z = z - 1.0;
    let mut x = COEFFS[0];
    for (index, coeff) in COEFFS.iter().enumerate().skip(1) {
        x += coeff / (z + index as f64);
    }
    let t = z + 7.5;
    0.5 * (2.0 * std::f64::consts::PI).ln() + (z + 0.5) * t.ln() - t + x.ln()
}
