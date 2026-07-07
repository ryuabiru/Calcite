use calcite_rust::graph_data::{
    BarChartData, CorrelationHeatmapData, HeatmapChartData, HistogramChartData, MosaicChartData,
    ProportionPlotData, StackedBarChartData, build_bar_chart_data, build_correlation_heatmap_data,
    build_heatmap_chart_data, build_histogram_chart_data, build_mosaic_chart_data,
    build_proportion_plot_data, build_stacked_bar_chart_data,
};
use calcite_rust::analysis::{
    ChiSquaredAnalysisResult, format_independent_t_test_result, format_linear_regression_result,
    format_four_pl_regression_result, format_kruskal_wallis_result, format_mann_whitney_u_result,
    format_one_way_anova_result, format_paired_t_test_result, format_pearson_correlation_result,
    format_shapiro_wilk_result, format_spearman_correlation_result, format_two_proportion_result,
    format_wilcoxon_signed_rank_result,
    run_independent_t_test_analysis, run_linear_regression_analysis, run_one_way_anova_analysis,
    run_mann_whitney_u_analysis, run_paired_t_test_analysis, run_pearson_correlation_analysis,
    run_four_pl_regression_analysis, run_kruskal_wallis_analysis, run_shapiro_wilk_analysis,
    run_spearman_correlation_analysis, run_two_proportion_analysis, run_wilcoxon_signed_rank_analysis,
};
use calcite_rust::{backend::AppBackend, core::AppCommand, state::HeatmapNormalizationMode};
use eframe::egui;
use rfd::FileDialog;

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("Calcite Rust")
            .with_inner_size([1440.0, 920.0])
            .with_min_inner_size([1180.0, 760.0]),
        ..Default::default()
    };

    eframe::run_native(
        "Calcite Rust",
        options,
        Box::new(|_cc| Ok(Box::new(CalciteRustApp::default()))),
    )
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum LeftTab {
    DataFrame,
    Properties,
}

struct CalciteRustApp {
    left_tab: LeftTab,
    backend: AppBackend,
    csv_path_input: String,
    row_filter_input: String,
    x_column_input: String,
    y_column_input: String,
    subgroup_column_input: String,
}

impl Default for CalciteRustApp {
    fn default() -> Self {
        Self {
            left_tab: LeftTab::DataFrame,
            backend: AppBackend::new(),
            csv_path_input: String::new(),
            row_filter_input: String::new(),
            x_column_input: String::new(),
            y_column_input: String::new(),
            subgroup_column_input: String::new(),
        }
    }
}

impl eframe::App for CalciteRustApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.apply_theme(ctx);

        egui::TopBottomPanel::top("toolbar")
            .frame(
                egui::Frame::default()
                    .fill(egui::Color32::from_rgb(232, 220, 199))
                    .inner_margin(egui::Margin::symmetric(12, 10)),
            )
            .show(ctx, |ui| {
                ui.horizontal_wrapped(|ui| {
                    ui.heading("Calcite");
                    ui.separator();
                    for label in [
                        "Scatter Plot",
                        "Bar Chart",
                        "Count Plot",
                        "Stacked Bar",
                        "Correlation Heatmap",
                        "Heatmap",
                        "Proportion Plot",
                        "Histogram",
                    ] {
                        let selected = self.backend.project().current_graph_type == label;
                        if ui.selectable_label(selected, label).clicked() {
                            let _ = self.backend.dispatch(AppCommand::SetGraphType {
                                graph_type: label.to_owned(),
                            });
                        }
                    }
                    ui.separator();
                    ui.label(&self.backend.project().status_message);
                });
            });

        egui::SidePanel::left("left_sidebar")
            .resizable(true)
            .default_width(420.0)
            .frame(self.panel_frame())
            .show(ctx, |ui| {
                ui.horizontal(|ui| {
                    ui.selectable_value(&mut self.left_tab, LeftTab::DataFrame, "DataFrame");
                    ui.selectable_value(&mut self.left_tab, LeftTab::Properties, "Properties");
                });
                ui.add_space(10.0);

                match self.left_tab {
                    LeftTab::DataFrame => self.show_dataframe_panel(ui),
                    LeftTab::Properties => self.show_properties_panel(ui),
                }
            });

        egui::TopBottomPanel::bottom("graph_area")
            .resizable(true)
            .default_height(420.0)
            .frame(self.panel_frame())
            .show(ctx, |ui| {
                ui.horizontal(|ui| {
                    ui.heading("Graph");
                    ui.separator();
                    ui.label(format!(
                        "Current type: {}",
                        self.backend.project().current_graph_type
                    ));
                });
                ui.add_space(8.0);
                self.show_graph_panel(ui);
            });

        egui::CentralPanel::default()
            .frame(self.panel_frame())
            .show(ctx, |ui| {
                let total_width = ui.available_width().max(1.0);
                let gap = 16.0;
                if total_width < 700.0 {
                    self.show_data_controls(ui);
                    ui.add_space(gap);
                    self.show_results_panel(ui);
                } else {
                    let usable_width = (total_width - gap).max(1.0);
                    let left_width = (usable_width * 0.62).clamp(220.0, usable_width - 220.0);
                    let right_width = (usable_width - left_width).max(1.0);

                    ui.horizontal(|ui| {
                        ui.allocate_ui_with_layout(
                            egui::vec2(left_width, ui.available_height()),
                            egui::Layout::top_down(egui::Align::Min),
                            |ui| {
                                self.show_data_controls(ui);
                            },
                        );
                        ui.add_space(gap);
                        ui.allocate_ui_with_layout(
                            egui::vec2(right_width, ui.available_height()),
                            egui::Layout::top_down(egui::Align::Min),
                            |ui| {
                                self.show_results_panel(ui);
                            },
                        );
                    });
                }
            });
    }
}

impl CalciteRustApp {
    fn apply_theme(&self, ctx: &egui::Context) {
        let mut visuals = egui::Visuals::light();
        visuals.override_text_color = Some(egui::Color32::from_rgb(31, 26, 23));
        visuals.widgets.noninteractive.bg_fill = egui::Color32::from_rgb(251, 247, 240);
        visuals.widgets.inactive.bg_fill = egui::Color32::from_rgb(255, 253, 249);
        visuals.widgets.hovered.bg_fill = egui::Color32::from_rgb(245, 236, 223);
        visuals.widgets.active.bg_fill = egui::Color32::from_rgb(223, 207, 187);
        visuals.widgets.open.bg_fill = egui::Color32::from_rgb(237, 226, 211);
        visuals.selection.bg_fill = egui::Color32::from_rgb(217, 143, 61);
        visuals.panel_fill = egui::Color32::from_rgb(244, 239, 230);
        visuals.window_fill = egui::Color32::from_rgb(251, 247, 240);
        ctx.set_visuals(visuals);
    }

    fn panel_frame(&self) -> egui::Frame {
        egui::Frame::default()
            .fill(egui::Color32::from_rgb(251, 247, 240))
            .stroke(egui::Stroke::new(
                1.0,
                egui::Color32::from_rgb(220, 202, 179),
            ))
            .corner_radius(14.0)
            .inner_margin(egui::Margin::same(14))
    }

    fn placeholder_surface(&self, ui: &mut egui::Ui, title: &str, body: &str, size: [f32; 2]) {
        egui::Frame::default()
            .fill(egui::Color32::from_rgb(255, 250, 243))
            .stroke(egui::Stroke::new(
                1.0,
                egui::Color32::from_rgb(224, 210, 192),
            ))
            .corner_radius(12.0)
            .show(ui, |ui| {
                ui.set_min_size(egui::vec2(size[0].max(120.0), size[1].max(90.0)));
                ui.vertical_centered(|ui| {
                    ui.add_space(12.0);
                    ui.strong(title);
                    ui.add_space(6.0);
                    ui.label(body);
                    ui.add_space(12.0);
                });
            });
    }

    fn show_graph_panel(&self, ui: &mut egui::Ui) {
        let project = self.backend.project();
        let current_graph_type = project.current_graph_type.as_str();
        if current_graph_type != "Bar Chart"
            && current_graph_type != "Count Plot"
            && current_graph_type != "Stacked Bar"
            && current_graph_type != "Correlation Heatmap"
            && current_graph_type != "Heatmap"
            && current_graph_type != "Proportion Plot"
            && current_graph_type != "Mosaic Plot"
            && current_graph_type != "Histogram"
        {
            self.placeholder_surface(
                ui,
                "Rust graph renderer bootstrap",
                "This region will host the new Rust-native plotting pipeline.",
                [
                    ui.available_width().max(1.0),
                    (ui.available_height() - 8.0).max(1.0),
                ],
            );
            return;
        }

        match current_graph_type {
            "Correlation Heatmap" => {
                let Some(heatmap_data) = build_correlation_heatmap_data(&project.data_table) else {
                    self.placeholder_surface(
                        ui,
                        "No graph data",
                        "Load a CSV with at least two numeric columns to render the correlation heatmap.",
                        [ui.available_width().max(1.0), (ui.available_height() - 8.0).max(1.0)],
                    );
                    return;
                };

                self.draw_correlation_heatmap(ui, &heatmap_data);
            }
            "Heatmap" => {
                let Some(row_name) =
                    (!project.y_column.trim().is_empty()).then(|| project.y_column.as_str())
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph yet",
                        "Set X and Y columns to render the heatmap.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                let Some(column_name) =
                    (!project.x_column.trim().is_empty()).then(|| project.x_column.as_str())
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph yet",
                        "Set X and Y columns to render the heatmap.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                let Some(chart_data) = build_heatmap_chart_data(
                    &project.data_table,
                    &project.table_view,
                    row_name,
                    column_name,
                    project.heatmap_normalization_mode,
                ) else {
                    self.placeholder_surface(
                        ui,
                        "No graph data",
                        "Load a CSV and choose X and Y columns to render the heatmap.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                self.draw_heatmap_chart(ui, &chart_data, project.chi_squared_result.as_ref());
            }
            "Stacked Bar" => {
                let Some(category_name) =
                    (!project.x_column.trim().is_empty()).then(|| project.x_column.as_str())
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph yet",
                        "Set an X column and subgroup column to render the stacked bar chart.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                let Some(subgroup_name) = (!project.subgroup_column.trim().is_empty())
                    .then(|| project.subgroup_column.as_str())
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph yet",
                        "Set an X column and subgroup column to render the stacked bar chart.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                let Some(chart_data) = build_stacked_bar_chart_data(
                    &project.data_table,
                    &project.table_view,
                    category_name,
                    subgroup_name,
                ) else {
                    self.placeholder_surface(
                        ui,
                        "No graph data",
                        "Load a CSV and choose X and subgroup columns to render the stacked bar chart.",
                        [ui.available_width().max(1.0), (ui.available_height() - 8.0).max(1.0)],
                    );
                    return;
                };

                self.draw_stacked_bar_chart(ui, &chart_data);
            }
            "Proportion Plot" => {
                let Some(column_name) =
                    (!project.x_column.trim().is_empty()).then(|| project.x_column.as_str())
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph yet",
                        "Set an X column to render the proportion plot.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                let Some(chart_data) =
                    build_proportion_plot_data(&project.data_table, &project.table_view, column_name)
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph data",
                        "Load a CSV and choose an X column to render the proportion plot.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                self.draw_proportion_plot(ui, &chart_data, project.two_proportion_result.as_ref());
            }
            "Mosaic Plot" => {
                let Some(row_name) =
                    (!project.y_column.trim().is_empty()).then(|| project.y_column.as_str())
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph yet",
                        "Set X and Y columns to render the mosaic plot.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                let Some(column_name) =
                    (!project.x_column.trim().is_empty()).then(|| project.x_column.as_str())
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph yet",
                        "Set X and Y columns to render the mosaic plot.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                let Some(chart_data) =
                    build_mosaic_chart_data(&project.data_table, &project.table_view, row_name, column_name)
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph data",
                        "Load a CSV and choose X and Y columns to render the mosaic plot.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                self.draw_mosaic_chart(ui, &chart_data, project.chi_squared_result.as_ref());
            }
            "Histogram" => {
                let Some(column_name) =
                    (!project.x_column.trim().is_empty()).then(|| project.x_column.as_str())
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph yet",
                        "Set an X column to render the histogram.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                let Some(chart_data) =
                    build_histogram_chart_data(&project.data_table, &project.table_view, column_name)
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph data",
                        "Load a CSV with numeric values in the X column to render the histogram.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                self.draw_histogram_chart(ui, &chart_data);
            }
            _ => {
                let Some(column_name) =
                    (!project.x_column.trim().is_empty()).then(|| project.x_column.as_str())
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph yet",
                        "Set an X column to render the bar chart.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                let Some(chart_data) =
                    build_bar_chart_data(&project.data_table, &project.table_view, column_name)
                else {
                    self.placeholder_surface(
                        ui,
                        "No graph data",
                        "Load a CSV and choose an X column to render the bar chart.",
                        [
                            ui.available_width().max(1.0),
                            (ui.available_height() - 8.0).max(1.0),
                        ],
                    );
                    return;
                };

                self.draw_bar_chart(ui, &chart_data);
            }
        }
    }

    fn draw_bar_chart(&self, ui: &mut egui::Ui, chart_data: &BarChartData) {
        let desired_size = egui::vec2(
            ui.available_width().max(1.0),
            ui.available_height().max(260.0),
        );
        let (rect, _) = ui.allocate_exact_size(desired_size, egui::Sense::hover());
        let painter = ui.painter_at(rect);
        let bg = egui::Color32::from_rgb(255, 250, 243);
        let border = egui::Color32::from_rgb(224, 210, 192);
        painter.rect_filled(rect, 12.0, bg);
        painter.rect_stroke(
            rect,
            12.0,
            egui::Stroke::new(1.0, border),
            egui::StrokeKind::Outside,
        );

        let inner = rect.shrink2(egui::vec2(18.0, 18.0));
        let max_count = chart_data
            .segments
            .iter()
            .map(|segment| segment.count)
            .max()
            .unwrap_or(1) as f32;
        let bar_count = chart_data.segments.len().max(1) as f32;
        let bar_gap = 10.0;
        let bar_width = ((inner.width() - ((bar_count - 1.0) * bar_gap)) / bar_count).max(24.0);
        let plot_bottom = inner.bottom() - 28.0;
        let plot_top = inner.top() + 26.0;
        let plot_height = (plot_bottom - plot_top).max(1.0);
        let axis_color = egui::Color32::from_rgb(116, 95, 73);

        painter.line_segment(
            [
                egui::pos2(inner.left(), plot_bottom),
                egui::pos2(inner.right(), plot_bottom),
            ],
            egui::Stroke::new(1.5, axis_color),
        );
        painter.line_segment(
            [
                egui::pos2(inner.left(), plot_top),
                egui::pos2(inner.left(), plot_bottom),
            ],
            egui::Stroke::new(1.5, axis_color),
        );

        painter.text(
            egui::pos2(inner.left(), inner.top()),
            egui::Align2::LEFT_TOP,
            format!(
                "{}  |  {} visible rows",
                chart_data.column_name, chart_data.visible_row_count
            ),
            egui::FontId::proportional(16.0),
            egui::Color32::from_rgb(58, 45, 32),
        );

        for (index, segment) in chart_data.segments.iter().enumerate() {
            let x = inner.left() + (index as f32 * (bar_width + bar_gap));
            let height_ratio = if max_count <= 0.0 {
                0.0
            } else {
                segment.count as f32 / max_count
            };
            let bar_height = plot_height * height_ratio;
            let bar_rect = egui::Rect::from_min_size(
                egui::pos2(x, plot_bottom - bar_height),
                egui::vec2(bar_width, bar_height),
            );
            painter.rect_filled(bar_rect, 8.0, egui::Color32::from_rgb(217, 143, 61));
            painter.rect_stroke(
                bar_rect,
                8.0,
                egui::Stroke::new(1.0, egui::Color32::from_rgb(140, 63, 22)),
                egui::StrokeKind::Outside,
            );
            painter.text(
                egui::pos2(bar_rect.center().x, bar_rect.top() - 4.0),
                egui::Align2::CENTER_BOTTOM,
                segment.count.to_string(),
                egui::FontId::proportional(14.0),
                egui::Color32::from_rgb(58, 45, 32),
            );
            painter.text(
                egui::pos2(bar_rect.center().x, plot_bottom + 6.0),
                egui::Align2::CENTER_TOP,
                &segment.label,
                egui::FontId::proportional(13.0),
                egui::Color32::from_rgb(58, 45, 32),
            );
        }
    }

    fn draw_stacked_bar_chart(&self, ui: &mut egui::Ui, chart_data: &StackedBarChartData) {
        let desired_size = egui::vec2(
            ui.available_width().max(1.0),
            ui.available_height().max(260.0),
        );
        let (rect, _) = ui.allocate_exact_size(desired_size, egui::Sense::hover());
        let painter = ui.painter_at(rect);
        let bg = egui::Color32::from_rgb(255, 250, 243);
        let border = egui::Color32::from_rgb(224, 210, 192);
        painter.rect_filled(rect, 12.0, bg);
        painter.rect_stroke(
            rect,
            12.0,
            egui::Stroke::new(1.0, border),
            egui::StrokeKind::Outside,
        );

        let palette = [
            egui::Color32::from_rgb(217, 143, 61),
            egui::Color32::from_rgb(196, 108, 41),
            egui::Color32::from_rgb(160, 88, 35),
            egui::Color32::from_rgb(130, 67, 28),
        ];
        let inner = rect.shrink2(egui::vec2(18.0, 18.0));
        let max_total = chart_data
            .categories
            .iter()
            .map(|category| category.total_count)
            .max()
            .unwrap_or(1) as f32;
        let category_count = chart_data.categories.len().max(1) as f32;
        let bar_gap = 12.0;
        let bar_width =
            ((inner.width() - ((category_count - 1.0) * bar_gap)) / category_count).max(24.0);
        let plot_bottom = inner.bottom() - 28.0;
        let plot_top = inner.top() + 26.0;
        let plot_height = (plot_bottom - plot_top).max(1.0);
        let axis_color = egui::Color32::from_rgb(116, 95, 73);

        painter.line_segment(
            [
                egui::pos2(inner.left(), plot_bottom),
                egui::pos2(inner.right(), plot_bottom),
            ],
            egui::Stroke::new(1.5, axis_color),
        );
        painter.line_segment(
            [
                egui::pos2(inner.left(), plot_top),
                egui::pos2(inner.left(), plot_bottom),
            ],
            egui::Stroke::new(1.5, axis_color),
        );

        painter.text(
            egui::pos2(inner.left(), inner.top()),
            egui::Align2::LEFT_TOP,
            format!(
                "{} by {}  |  {} visible rows",
                chart_data.category_column_name,
                chart_data.subgroup_column_name,
                chart_data.visible_row_count
            ),
            egui::FontId::proportional(16.0),
            egui::Color32::from_rgb(58, 45, 32),
        );

        for (index, category) in chart_data.categories.iter().enumerate() {
            let x = inner.left() + (index as f32 * (bar_width + bar_gap));
            let total_ratio = if max_total <= 0.0 {
                0.0
            } else {
                category.total_count as f32 / max_total
            };
            let bar_height = plot_height * total_ratio;
            let bar_top = plot_bottom - bar_height;
            let bar_rect = egui::Rect::from_min_size(
                egui::pos2(x, bar_top),
                egui::vec2(bar_width, bar_height),
            );

            painter.rect_stroke(
                bar_rect,
                8.0,
                egui::Stroke::new(1.0, egui::Color32::from_rgb(140, 63, 22)),
                egui::StrokeKind::Outside,
            );

            let mut segment_bottom = plot_bottom;
            for (segment_index, segment) in category.segments.iter().enumerate() {
                if segment.count == 0 {
                    continue;
                }
                let segment_ratio = if category.total_count == 0 {
                    0.0
                } else {
                    segment.count as f32 / category.total_count as f32
                };
                let segment_height = bar_height * segment_ratio;
                let segment_top = segment_bottom - segment_height;
                let segment_rect = egui::Rect::from_min_max(
                    egui::pos2(x, segment_top),
                    egui::pos2(x + bar_width, segment_bottom),
                );
                let color = palette[segment_index % palette.len()];
                painter.rect_filled(segment_rect, 8.0, color);
                painter.rect_stroke(
                    segment_rect,
                    8.0,
                    egui::Stroke::new(1.0, egui::Color32::from_rgb(140, 63, 22)),
                    egui::StrokeKind::Outside,
                );
                segment_bottom = segment_top;
            }

            painter.text(
                egui::pos2(bar_rect.center().x, bar_rect.top() - 4.0),
                egui::Align2::CENTER_BOTTOM,
                category.total_count.to_string(),
                egui::FontId::proportional(14.0),
                egui::Color32::from_rgb(58, 45, 32),
            );
            painter.text(
                egui::pos2(bar_rect.center().x, plot_bottom + 6.0),
                egui::Align2::CENTER_TOP,
                &category.label,
                egui::FontId::proportional(13.0),
                egui::Color32::from_rgb(58, 45, 32),
            );
        }
    }

    fn draw_proportion_plot(
        &self,
        ui: &mut egui::Ui,
        chart_data: &ProportionPlotData,
        highlight: Option<&calcite_rust::analysis::TwoProportionAnalysisResult>,
    ) {
        let desired_size = egui::vec2(
            ui.available_width().max(1.0),
            ui.available_height().max(260.0),
        );
        let (rect, _) = ui.allocate_exact_size(desired_size, egui::Sense::hover());
        let painter = ui.painter_at(rect);
        let bg = egui::Color32::from_rgb(255, 250, 243);
        let border = egui::Color32::from_rgb(224, 210, 192);
        painter.rect_filled(rect, 12.0, bg);
        painter.rect_stroke(
            rect,
            12.0,
            egui::Stroke::new(1.0, border),
            egui::StrokeKind::Outside,
        );

        let inner = rect.shrink2(egui::vec2(18.0, 18.0));
        let bar_count = chart_data.segments.len().max(1) as f32;
        let bar_gap = 10.0;
        let bar_width = ((inner.width() - ((bar_count - 1.0) * bar_gap)) / bar_count).max(24.0);
        let plot_bottom = inner.bottom() - 28.0;
        let plot_top = inner.top() + 26.0;
        let plot_height = (plot_bottom - plot_top).max(1.0);
        let axis_color = egui::Color32::from_rgb(116, 95, 73);

        painter.line_segment(
            [
                egui::pos2(inner.left(), plot_bottom),
                egui::pos2(inner.right(), plot_bottom),
            ],
            egui::Stroke::new(1.5, axis_color),
        );
        painter.line_segment(
            [
                egui::pos2(inner.left(), plot_top),
                egui::pos2(inner.left(), plot_bottom),
            ],
            egui::Stroke::new(1.5, axis_color),
        );

        painter.text(
            egui::pos2(inner.left(), inner.top()),
            egui::Align2::LEFT_TOP,
            format!(
                "{}  |  {} visible rows",
                chart_data.column_name, chart_data.visible_row_count
            ),
            egui::FontId::proportional(16.0),
            egui::Color32::from_rgb(58, 45, 32),
        );

        if let Some(result) = highlight {
            if result.rows_col == chart_data.column_name {
                let callout_rect = egui::Rect::from_min_size(
                    egui::pos2(inner.right() - 246.0, inner.top() + 4.0),
                    egui::vec2(236.0, 72.0),
                );
                painter.rect_filled(callout_rect, 8.0, egui::Color32::from_rgb(248, 236, 224));
                painter.rect_stroke(
                    callout_rect,
                    8.0,
                    egui::Stroke::new(1.0, egui::Color32::from_rgb(186, 120, 73)),
                    egui::StrokeKind::Outside,
                );
                painter.text(
                    callout_rect.left_top() + egui::vec2(10.0, 10.0),
                    egui::Align2::LEFT_TOP,
                    format!("2-Proportion: {}", result.success_label),
                    egui::FontId::proportional(12.0),
                    egui::Color32::from_rgb(92, 57, 34),
                );
                painter.text(
                    callout_rect.left_top() + egui::vec2(10.0, 28.0),
                    egui::Align2::LEFT_TOP,
                    format!(
                        "{}: {:.3}  |  {}: {:.3}",
                        result.group1_label,
                        result.proportion_group1,
                        result.group2_label,
                        result.proportion_group2
                    ),
                    egui::FontId::proportional(12.0),
                    egui::Color32::from_rgb(92, 57, 34),
                );
                painter.text(
                    callout_rect.left_top() + egui::vec2(10.0, 46.0),
                    egui::Align2::LEFT_TOP,
                    format!("Diff {:.3}  p={:.4}", result.difference_in_proportions, result.p_value),
                    egui::FontId::proportional(12.0),
                    egui::Color32::from_rgb(92, 57, 34),
                );
            }
        }

        for (index, segment) in chart_data.segments.iter().enumerate() {
            let x = inner.left() + (index as f32 * (bar_width + bar_gap));
            let bar_height = plot_height * (segment.proportion as f32).clamp(0.0, 1.0);
            let bar_rect = egui::Rect::from_min_size(
                egui::pos2(x, plot_bottom - bar_height),
                egui::vec2(bar_width, bar_height),
            );
            let mut fill_color = egui::Color32::from_rgb(217, 143, 61);
            let mut stroke_color = egui::Color32::from_rgb(140, 63, 22);
            let mut stroke_width = 1.0;
            if let Some(result) = highlight {
                if result.rows_col == chart_data.column_name
                    && (segment.label == result.group1_label || segment.label == result.group2_label)
                {
                    fill_color = egui::Color32::from_rgb(234, 173, 104);
                    stroke_color = egui::Color32::from_rgb(170, 75, 35);
                    stroke_width = 2.5;
                }
            }
            painter.rect_filled(bar_rect, 8.0, fill_color);
            painter.rect_stroke(
                bar_rect,
                8.0,
                egui::Stroke::new(stroke_width, stroke_color),
                egui::StrokeKind::Outside,
            );
            painter.text(
                egui::pos2(bar_rect.center().x, bar_rect.top() - 4.0),
                egui::Align2::CENTER_BOTTOM,
                format!("{:.0}%", segment.proportion * 100.0),
                egui::FontId::proportional(14.0),
                egui::Color32::from_rgb(58, 45, 32),
            );
            painter.text(
                egui::pos2(bar_rect.center().x, bar_rect.bottom() - 4.0),
                egui::Align2::CENTER_BOTTOM,
                segment.count.to_string(),
                egui::FontId::proportional(12.0),
                egui::Color32::from_rgb(58, 45, 32),
            );
            painter.text(
                egui::pos2(bar_rect.center().x, plot_bottom + 6.0),
                egui::Align2::CENTER_TOP,
                &segment.label,
                egui::FontId::proportional(13.0),
                egui::Color32::from_rgb(58, 45, 32),
            );
        }
    }

    fn draw_mosaic_chart(
        &self,
        ui: &mut egui::Ui,
        chart_data: &MosaicChartData,
        highlight: Option<&ChiSquaredAnalysisResult>,
    ) {
        let desired_size = egui::vec2(
            ui.available_width().max(1.0),
            ui.available_height().max(280.0),
        );
        let (rect, _) = ui.allocate_exact_size(desired_size, egui::Sense::hover());
        let painter = ui.painter_at(rect);
        let bg = egui::Color32::from_rgb(255, 250, 243);
        let border = egui::Color32::from_rgb(224, 210, 192);
        painter.rect_filled(rect, 12.0, bg);
        painter.rect_stroke(
            rect,
            12.0,
            egui::Stroke::new(1.0, border),
            egui::StrokeKind::Outside,
        );

        let inner = rect.shrink2(egui::vec2(18.0, 18.0));
        let row_count = chart_data.row_labels.len().max(1) as f32;
        let column_count = chart_data.column_labels.len().max(1) as f32;
        let cell_size = ((inner.width().min(inner.height()) - 56.0) / row_count.max(column_count))
            .max(28.0);
        let grid_width = cell_size * column_count;
        let grid_left = inner.left() + 110.0;
        let grid_top = inner.top() + 34.0;
        let axis_color = egui::Color32::from_rgb(116, 95, 73);
        let max_count = chart_data
            .counts
            .iter()
            .flat_map(|row| row.iter())
            .copied()
            .max()
            .unwrap_or(1) as f32;

        painter.text(
            egui::pos2(inner.left(), inner.top()),
            egui::Align2::LEFT_TOP,
            format!(
                "Mosaic Plot: {} vs {}",
                chart_data.row_column_name, chart_data.column_column_name
            ),
            egui::FontId::proportional(16.0),
            egui::Color32::from_rgb(58, 45, 32),
        );

        for (index, label) in chart_data.column_labels.iter().enumerate() {
            let x = grid_left + (index as f32 * cell_size) + (cell_size / 2.0);
            painter.text(
                egui::pos2(x, grid_top - 6.0),
                egui::Align2::CENTER_BOTTOM,
                label,
                egui::FontId::proportional(12.0),
                axis_color,
            );
        }

        for (index, label) in chart_data.row_labels.iter().enumerate() {
            let y = grid_top + (index as f32 * cell_size) + (cell_size / 2.0);
            painter.text(
                egui::pos2(grid_left - 6.0, y),
                egui::Align2::RIGHT_CENTER,
                label,
                egui::FontId::proportional(12.0),
                axis_color,
            );
        }

        for (row_index, row) in chart_data.counts.iter().enumerate() {
            for (col_index, count) in row.iter().enumerate() {
                let intensity = (*count as f32 / max_count).clamp(0.0, 1.0);
                let red = (248.0 - (80.0 * intensity)) as u8;
                let green = (238.0 - (90.0 * intensity)) as u8;
                let blue = (231.0 + (18.0 * intensity)) as u8;
                let cell_rect = egui::Rect::from_min_size(
                    egui::pos2(
                        grid_left + (col_index as f32 * cell_size),
                        grid_top + (row_index as f32 * cell_size),
                    ),
                    egui::vec2(cell_size, cell_size),
                );
                let mut fill_color = egui::Color32::from_rgb(red, green, blue);
                let mut stroke_color = border;
                let mut stroke_width = 1.0;
                let residual = highlight.and_then(|result| {
                    if result.rows_col == chart_data.row_column_name
                        && result.cols_col == chart_data.column_column_name
                    {
                        Self::chi_squared_residual(
                            result,
                            &chart_data.row_labels[row_index],
                            &chart_data.column_labels[col_index],
                        )
                    } else {
                        None
                    }
                });
                if let Some(residual) = residual {
                    let strength = (residual.abs() / 3.0).clamp(0.0, 1.0);
                    let tint = if residual >= 0.0 {
                        egui::Color32::from_rgb(244, 188, 176)
                    } else {
                        egui::Color32::from_rgb(178, 206, 242)
                    };
                    fill_color = Self::blend_colors(fill_color, tint, (strength * 0.45) as f32);
                    stroke_color = if residual >= 0.0 {
                        egui::Color32::from_rgb(171, 78, 58)
                    } else {
                        egui::Color32::from_rgb(72, 104, 170)
                    };
                    stroke_width = if residual.abs() >= 2.0 { 2.5 } else { 1.5 };
                }
                painter.rect_filled(cell_rect, 4.0, fill_color);
                painter.rect_stroke(
                    cell_rect,
                    4.0,
                    egui::Stroke::new(stroke_width, stroke_color),
                    egui::StrokeKind::Outside,
                );
                painter.text(
                    cell_rect.center(),
                    egui::Align2::CENTER_CENTER,
                    count.to_string(),
                    egui::FontId::proportional(12.0),
                    egui::Color32::from_rgb(58, 45, 32),
                );
                if let Some(residual) = residual {
                    painter.text(
                        cell_rect.right_top() - egui::vec2(4.0, 4.0),
                        egui::Align2::RIGHT_TOP,
                        format!("{residual:+.1}"),
                        egui::FontId::proportional(10.0),
                        stroke_color,
                    );
                }
            }
        }

        let legend_x = grid_left + grid_width + 18.0;
        for (offset, label, intensity) in [(0.0, "low", 0.0), (1.0, "mid", 0.5), (2.0, "high", 1.0)]
        {
            let y = grid_top + (offset * 22.0);
            let red = (248.0 - (80.0 * intensity)) as u8;
            let green = (238.0 - (90.0 * intensity)) as u8;
            let blue = (231.0 + (18.0 * intensity)) as u8;
            let swatch = egui::Rect::from_min_size(egui::pos2(legend_x, y), egui::vec2(14.0, 14.0));
            painter.rect_filled(swatch, 3.0, egui::Color32::from_rgb(red, green, blue));
            painter.rect_stroke(
                swatch,
                3.0,
                egui::Stroke::new(1.0, border),
                egui::StrokeKind::Outside,
            );
            painter.text(
                egui::pos2(legend_x + 20.0, y + 7.0),
                egui::Align2::LEFT_CENTER,
                label,
                egui::FontId::proportional(12.0),
                axis_color,
            );
        }
    }

    fn draw_histogram_chart(&self, ui: &mut egui::Ui, chart_data: &HistogramChartData) {
        let desired_size = egui::vec2(
            ui.available_width().max(1.0),
            ui.available_height().max(260.0),
        );
        let (rect, _) = ui.allocate_exact_size(desired_size, egui::Sense::hover());
        let painter = ui.painter_at(rect);
        let bg = egui::Color32::from_rgb(255, 250, 243);
        let border = egui::Color32::from_rgb(224, 210, 192);
        painter.rect_filled(rect, 12.0, bg);
        painter.rect_stroke(
            rect,
            12.0,
            egui::Stroke::new(1.0, border),
            egui::StrokeKind::Outside,
        );

        let inner = rect.shrink2(egui::vec2(18.0, 18.0));
        let bin_count = chart_data.bins.len().max(1) as f32;
        let bar_gap = 10.0;
        let bar_width = ((inner.width() - ((bin_count - 1.0) * bar_gap)) / bin_count).max(24.0);
        let plot_bottom = inner.bottom() - 28.0;
        let plot_top = inner.top() + 26.0;
        let plot_height = (plot_bottom - plot_top).max(1.0);
        let axis_color = egui::Color32::from_rgb(116, 95, 73);
        let max_count = chart_data
            .bins
            .iter()
            .map(|bin| bin.count)
            .max()
            .unwrap_or(1) as f32;

        painter.line_segment(
            [
                egui::pos2(inner.left(), plot_bottom),
                egui::pos2(inner.right(), plot_bottom),
            ],
            egui::Stroke::new(1.5, axis_color),
        );
        painter.line_segment(
            [
                egui::pos2(inner.left(), plot_top),
                egui::pos2(inner.left(), plot_bottom),
            ],
            egui::Stroke::new(1.5, axis_color),
        );

        painter.text(
            egui::pos2(inner.left(), inner.top()),
            egui::Align2::LEFT_TOP,
            format!(
                "{}  |  {} visible rows",
                chart_data.column_name, chart_data.visible_row_count
            ),
            egui::FontId::proportional(16.0),
            egui::Color32::from_rgb(58, 45, 32),
        );

        for (index, bin) in chart_data.bins.iter().enumerate() {
            let x = inner.left() + (index as f32 * (bar_width + bar_gap));
            let height_ratio = if max_count <= 0.0 {
                0.0
            } else {
                bin.count as f32 / max_count
            };
            let bar_height = plot_height * height_ratio;
            let bar_rect = egui::Rect::from_min_size(
                egui::pos2(x, plot_bottom - bar_height),
                egui::vec2(bar_width, bar_height),
            );
            painter.rect_filled(bar_rect, 8.0, egui::Color32::from_rgb(217, 143, 61));
            painter.rect_stroke(
                bar_rect,
                8.0,
                egui::Stroke::new(1.0, egui::Color32::from_rgb(140, 63, 22)),
                egui::StrokeKind::Outside,
            );
            painter.text(
                egui::pos2(bar_rect.center().x, bar_rect.top() - 4.0),
                egui::Align2::CENTER_BOTTOM,
                bin.count.to_string(),
                egui::FontId::proportional(14.0),
                egui::Color32::from_rgb(58, 45, 32),
            );
            painter.text(
                egui::pos2(bar_rect.center().x, plot_bottom + 6.0),
                egui::Align2::CENTER_TOP,
                &bin.label,
                egui::FontId::proportional(13.0),
                egui::Color32::from_rgb(58, 45, 32),
            );
        }
    }

    fn draw_correlation_heatmap(&self, ui: &mut egui::Ui, heatmap_data: &CorrelationHeatmapData) {
        let desired_size = egui::vec2(
            ui.available_width().max(1.0),
            ui.available_height().max(280.0),
        );
        let (rect, _) = ui.allocate_exact_size(desired_size, egui::Sense::hover());
        let painter = ui.painter_at(rect);
        let bg = egui::Color32::from_rgb(255, 250, 243);
        let border = egui::Color32::from_rgb(224, 210, 192);
        painter.rect_filled(rect, 12.0, bg);
        painter.rect_stroke(
            rect,
            12.0,
            egui::Stroke::new(1.0, border),
            egui::StrokeKind::Outside,
        );

        let inner = rect.shrink2(egui::vec2(18.0, 18.0));
        let n = heatmap_data.column_names.len().max(1) as f32;
        let cell_size = ((inner.width().min(inner.height()) - 42.0) / n).max(28.0);
        let grid_width = cell_size * n;
        let grid_left = inner.left() + 110.0;
        let grid_top = inner.top() + 34.0;
        let axis_color = egui::Color32::from_rgb(116, 95, 73);

        painter.text(
            egui::pos2(inner.left(), inner.top()),
            egui::Align2::LEFT_TOP,
            "Correlation Heatmap",
            egui::FontId::proportional(16.0),
            egui::Color32::from_rgb(58, 45, 32),
        );

        for (index, name) in heatmap_data.column_names.iter().enumerate() {
            let x = grid_left + (index as f32 * cell_size) + (cell_size / 2.0);
            painter.text(
                egui::pos2(x, grid_top - 6.0),
                egui::Align2::CENTER_BOTTOM,
                name,
                egui::FontId::proportional(12.0),
                axis_color,
            );
            let y = grid_top + (index as f32 * cell_size) + (cell_size / 2.0);
            painter.text(
                egui::pos2(grid_left - 6.0, y),
                egui::Align2::RIGHT_CENTER,
                name,
                egui::FontId::proportional(12.0),
                axis_color,
            );
        }

        for row_index in 0..heatmap_data.column_names.len() {
            for col_index in 0..heatmap_data.column_names.len() {
                let correlation = heatmap_data.values[row_index][col_index].unwrap_or(0.0);
                let heat = ((((correlation as f32) + 1.0) / 2.0).clamp(0.0, 1.0)) as f32;
                let red = (248.0 - (90.0 * heat)) as u8;
                let green = (238.0 - (120.0 * heat)) as u8;
                let blue = (231.0 + (14.0 * heat)) as u8;
                let cell_rect = egui::Rect::from_min_size(
                    egui::pos2(
                        grid_left + (col_index as f32 * cell_size),
                        grid_top + (row_index as f32 * cell_size),
                    ),
                    egui::vec2(cell_size, cell_size),
                );
                painter.rect_filled(cell_rect, 4.0, egui::Color32::from_rgb(red, green, blue));
                painter.rect_stroke(
                    cell_rect,
                    4.0,
                    egui::Stroke::new(1.0, border),
                    egui::StrokeKind::Outside,
                );
                painter.text(
                    cell_rect.center(),
                    egui::Align2::CENTER_CENTER,
                    format!("{correlation:.2}"),
                    egui::FontId::proportional(12.0),
                    egui::Color32::from_rgb(58, 45, 32),
                );
            }
        }

        let legend_x = grid_left + grid_width + 18.0;
        for (offset, label, correlation) in
            [(-1.0, "-1.0", -1.0), (0.0, "0.0", 0.0), (1.0, "1.0", 1.0)]
        {
            let y = grid_top + ((offset + 1.0) * 22.0);
            let heat = ((((correlation as f32) + 1.0) / 2.0).clamp(0.0, 1.0)) as f32;
            let red = (248.0 - (90.0 * heat)) as u8;
            let green = (238.0 - (120.0 * heat)) as u8;
            let blue = (231.0 + (14.0 * heat)) as u8;
            let swatch = egui::Rect::from_min_size(egui::pos2(legend_x, y), egui::vec2(14.0, 14.0));
            painter.rect_filled(swatch, 3.0, egui::Color32::from_rgb(red, green, blue));
            painter.rect_stroke(
                swatch,
                3.0,
                egui::Stroke::new(1.0, border),
                egui::StrokeKind::Outside,
            );
            painter.text(
                egui::pos2(legend_x + 20.0, y + 7.0),
                egui::Align2::LEFT_CENTER,
                label,
                egui::FontId::proportional(12.0),
                axis_color,
            );
        }
    }

    fn draw_heatmap_chart(
        &self,
        ui: &mut egui::Ui,
        heatmap_data: &HeatmapChartData,
        highlight: Option<&ChiSquaredAnalysisResult>,
    ) {
        let desired_size = egui::vec2(
            ui.available_width().max(1.0),
            ui.available_height().max(280.0),
        );
        let (rect, _) = ui.allocate_exact_size(desired_size, egui::Sense::hover());
        let painter = ui.painter_at(rect);
        let bg = egui::Color32::from_rgb(255, 250, 243);
        let border = egui::Color32::from_rgb(224, 210, 192);
        painter.rect_filled(rect, 12.0, bg);
        painter.rect_stroke(
            rect,
            12.0,
            egui::Stroke::new(1.0, border),
            egui::StrokeKind::Outside,
        );

        let inner = rect.shrink2(egui::vec2(18.0, 18.0));
        let row_count = heatmap_data.row_labels.len().max(1) as f32;
        let column_count = heatmap_data.column_labels.len().max(1) as f32;
        let cell_size =
            ((inner.width().min(inner.height()) - 56.0) / row_count.max(column_count)).max(28.0);
        let grid_width = cell_size * column_count;
        let grid_left = inner.left() + 110.0;
        let grid_top = inner.top() + 34.0;
        let axis_color = egui::Color32::from_rgb(116, 95, 73);

        painter.text(
            egui::pos2(inner.left(), inner.top()),
            egui::Align2::LEFT_TOP,
            format!(
                "Heatmap: {} vs {}",
                heatmap_data.row_column_name, heatmap_data.column_column_name
            ),
            egui::FontId::proportional(16.0),
            egui::Color32::from_rgb(58, 45, 32),
        );

        for (index, label) in heatmap_data.column_labels.iter().enumerate() {
            let x = grid_left + (index as f32 * cell_size) + (cell_size / 2.0);
            painter.text(
                egui::pos2(x, grid_top - 6.0),
                egui::Align2::CENTER_BOTTOM,
                label,
                egui::FontId::proportional(12.0),
                axis_color,
            );
        }

        for (index, label) in heatmap_data.row_labels.iter().enumerate() {
            let y = grid_top + (index as f32 * cell_size) + (cell_size / 2.0);
            painter.text(
                egui::pos2(grid_left - 6.0, y),
                egui::Align2::RIGHT_CENTER,
                label,
                egui::FontId::proportional(12.0),
                axis_color,
            );
        }

        let max_count = heatmap_data
            .values
            .iter()
            .flat_map(|row| row.iter())
            .copied()
            .fold(0.0_f64, f64::max)
            .max(1.0) as f32;

        for (row_index, row) in heatmap_data.values.iter().enumerate() {
            for (col_index, value) in row.iter().enumerate() {
                let intensity = (*value as f32 / max_count).clamp(0.0, 1.0);
                let red = (248.0 - (80.0 * intensity)) as u8;
                let green = (238.0 - (90.0 * intensity)) as u8;
                let blue = (231.0 + (18.0 * intensity)) as u8;
                let cell_rect = egui::Rect::from_min_size(
                    egui::pos2(
                        grid_left + (col_index as f32 * cell_size),
                        grid_top + (row_index as f32 * cell_size),
                    ),
                    egui::vec2(cell_size, cell_size),
                );
                let mut fill_color = egui::Color32::from_rgb(red, green, blue);
                let mut stroke_color = border;
                let mut stroke_width = 1.0;
                let residual = highlight.and_then(|result| {
                    if result.rows_col == heatmap_data.row_column_name
                        && result.cols_col == heatmap_data.column_column_name
                    {
                        Self::chi_squared_residual(
                            result,
                            &heatmap_data.row_labels[row_index],
                            &heatmap_data.column_labels[col_index],
                        )
                    } else {
                        None
                    }
                });
                if let Some(residual) = residual {
                    let strength = (residual.abs() / 3.0).clamp(0.0, 1.0);
                    let tint = if residual >= 0.0 {
                        egui::Color32::from_rgb(244, 188, 176)
                    } else {
                        egui::Color32::from_rgb(178, 206, 242)
                    };
                    fill_color = Self::blend_colors(fill_color, tint, (strength * 0.45) as f32);
                    stroke_color = if residual >= 0.0 {
                        egui::Color32::from_rgb(171, 78, 58)
                    } else {
                        egui::Color32::from_rgb(72, 104, 170)
                    };
                    stroke_width = if residual.abs() >= 2.0 { 2.5 } else { 1.5 };
                }
                painter.rect_filled(cell_rect, 4.0, fill_color);
                painter.rect_stroke(
                    cell_rect,
                    4.0,
                    egui::Stroke::new(stroke_width, stroke_color),
                    egui::StrokeKind::Outside,
                );
                painter.text(
                    cell_rect.center(),
                    egui::Align2::CENTER_CENTER,
                    if heatmap_data.normalization_mode == HeatmapNormalizationMode::Count {
                        heatmap_data.counts[row_index][col_index].to_string()
                    } else {
                        format!("{value:.2}")
                    },
                    egui::FontId::proportional(12.0),
                    egui::Color32::from_rgb(58, 45, 32),
                );
                if let Some(residual) = residual {
                    painter.text(
                        cell_rect.right_top() - egui::vec2(4.0, 4.0),
                        egui::Align2::RIGHT_TOP,
                        format!("{residual:+.1}"),
                        egui::FontId::proportional(10.0),
                        stroke_color,
                    );
                }
            }
        }

        let legend_x = grid_left + grid_width + 18.0;
        for (offset, label, intensity) in [(0.0, "low", 0.0), (1.0, "mid", 0.5), (2.0, "high", 1.0)]
        {
            let y = grid_top + (offset * 22.0);
            let red = (248.0 - (80.0 * intensity)) as u8;
            let green = (238.0 - (90.0 * intensity)) as u8;
            let blue = (231.0 + (18.0 * intensity)) as u8;
            let swatch = egui::Rect::from_min_size(egui::pos2(legend_x, y), egui::vec2(14.0, 14.0));
            painter.rect_filled(swatch, 3.0, egui::Color32::from_rgb(red, green, blue));
            painter.rect_stroke(
                swatch,
                3.0,
                egui::Stroke::new(1.0, border),
                egui::StrokeKind::Outside,
            );
            painter.text(
                egui::pos2(legend_x + 20.0, y + 7.0),
                egui::Align2::LEFT_CENTER,
                label,
                egui::FontId::proportional(12.0),
                axis_color,
            );
        }
    }

    fn chi_squared_residual(
        result: &ChiSquaredAnalysisResult,
        row_label: &str,
        column_label: &str,
    ) -> Option<f64> {
        let row_index = result.row_labels.iter().position(|label| label == row_label)?;
        let column_index = result
            .column_labels
            .iter()
            .position(|label| label == column_label)?;
        Some(result.standardized_residuals[row_index][column_index])
    }

    fn blend_colors(
        base: egui::Color32,
        overlay: egui::Color32,
        amount: f32,
    ) -> egui::Color32 {
        let amount = amount.clamp(0.0, 1.0);
        let inverse = 1.0 - amount;
        egui::Color32::from_rgba_unmultiplied(
            (base.r() as f32 * inverse + overlay.r() as f32 * amount) as u8,
            (base.g() as f32 * inverse + overlay.g() as f32 * amount) as u8,
            (base.b() as f32 * inverse + overlay.b() as f32 * amount) as u8,
            255,
        )
    }

    fn show_dataframe_panel(&mut self, ui: &mut egui::Ui) {
        ui.heading("DataFrame");
        ui.label(
            self.backend
                .project()
                .loaded_file_name()
                .as_deref()
                .map_or("No file loaded yet.", |name| name),
        );
        ui.add_space(8.0);
        self.placeholder_surface(
            ui,
            "Table view bootstrap",
            "CSV loading, table rendering, sorting, filtering, and selection state will move here first.",
            [ui.available_width().max(1.0), 120.0],
        );
        ui.add_space(10.0);
        self.show_csv_loader(ui);
        ui.add_space(10.0);
        self.show_table_preview(ui);
        ui.add_space(10.0);
        self.show_column_metadata(ui);
    }

    fn show_properties_panel(&mut self, ui: &mut egui::Ui) {
        ui.heading("Properties");
        ui.label("The Rust version will reintroduce plot properties incrementally.");
        ui.add_space(8.0);
            egui::Grid::new("properties_grid")
            .num_columns(2)
            .spacing([12.0, 10.0])
            .show(ui, |ui| {
                ui.label("Theme");
                ui.label("Warm light bootstrap");
                ui.end_row();

                ui.label("Legend");
                ui.label("Planned");
                ui.end_row();

                ui.label("Axes");
                ui.label("Planned");
                ui.end_row();

                ui.label("Heatmap");
                egui::ComboBox::from_id_salt("heatmap_normalization_mode")
                    .selected_text(self.backend.project().heatmap_normalization_mode.label())
                    .show_ui(ui, |ui| {
                        let project = self.backend.project_mut();
                        for mode in HeatmapNormalizationMode::ALL {
                            ui.selectable_value(
                                &mut project.heatmap_normalization_mode,
                                mode,
                                mode.label(),
                            );
                        }
                    });
                ui.end_row();

                ui.label("Analysis");
                ui.vertical(|ui| {
                    if ui
                        .button("Run One-way ANOVA")
                        .on_hover_text("Uses X as group labels and Y as numeric values.")
                        .clicked()
                    {
                        let group_col = self.backend.project().x_column.clone();
                        let value_col = self.backend.project().y_column.clone();
                        match run_one_way_anova_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &group_col,
                            &value_col,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "One-way ANOVA completed for {} vs {}",
                                    group_col, value_col
                                );
                                self.backend.project_mut().results_preview =
                                    format_one_way_anova_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Shapiro-Wilk")
                        .on_hover_text("Uses X as group labels and Y as numeric values.")
                        .clicked()
                    {
                        let group_col = self.backend.project().x_column.clone();
                        let value_col = self.backend.project().y_column.clone();
                        match run_shapiro_wilk_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &group_col,
                            &value_col,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "Shapiro-Wilk test completed for {} vs {}",
                                    group_col, value_col
                                );
                                self.backend.project_mut().results_preview =
                                    format_shapiro_wilk_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Mann-Whitney U")
                        .on_hover_text("Compares X and Y as independent numeric samples.")
                        .clicked()
                    {
                        let col1 = self.backend.project().x_column.clone();
                        let col2 = self.backend.project().y_column.clone();
                        match run_mann_whitney_u_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &col1,
                            &col2,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "Mann-Whitney U test completed for {} vs {}",
                                    col1, col2
                                );
                                self.backend.project_mut().results_preview =
                                    format_mann_whitney_u_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Independent t-test")
                        .on_hover_text("Compares X and Y as independent numeric samples.")
                        .clicked()
                    {
                        let col1 = self.backend.project().x_column.clone();
                        let col2 = self.backend.project().y_column.clone();
                        match run_independent_t_test_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &col1,
                            &col2,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "Independent t-test completed for {} vs {}",
                                    col1, col2
                                );
                                self.backend.project_mut().results_preview =
                                    format_independent_t_test_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Wilcoxon signed-rank")
                        .on_hover_text("Compares X and Y as paired numeric samples.")
                        .clicked()
                    {
                        let col1 = self.backend.project().x_column.clone();
                        let col2 = self.backend.project().y_column.clone();
                        match run_wilcoxon_signed_rank_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &col1,
                            &col2,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "Wilcoxon signed-rank test completed for {} vs {}",
                                    col1, col2
                                );
                                self.backend.project_mut().results_preview =
                                    format_wilcoxon_signed_rank_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Paired t-test")
                        .on_hover_text("Compares X and Y as paired numeric samples.")
                        .clicked()
                    {
                        let col1 = self.backend.project().x_column.clone();
                        let col2 = self.backend.project().y_column.clone();
                        match run_paired_t_test_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &col1,
                            &col2,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "Paired t-test completed for {} vs {}",
                                    col1, col2
                                );
                                self.backend.project_mut().results_preview =
                                    format_paired_t_test_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Kruskal-Wallis")
                        .on_hover_text("Uses X as group labels and Y as numeric values.")
                        .clicked()
                    {
                        let group_col = self.backend.project().x_column.clone();
                        let value_col = self.backend.project().y_column.clone();
                        match run_kruskal_wallis_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &group_col,
                            &value_col,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "Kruskal-Wallis test completed for {} vs {}",
                                    group_col, value_col
                                );
                                self.backend.project_mut().results_preview =
                                    format_kruskal_wallis_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Linear Regression")
                        .on_hover_text("Fits Y as a linear function of X.")
                        .clicked()
                    {
                        let col1 = self.backend.project().x_column.clone();
                        let col2 = self.backend.project().y_column.clone();
                        match run_linear_regression_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &col1,
                            &col2,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "Linear regression completed for {} vs {}",
                                    col1, col2
                                );
                                self.backend.project_mut().results_preview =
                                    format_linear_regression_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run 4PL Regression")
                        .on_hover_text("Fits Y with a sigmoidal 4-parameter logistic model.")
                        .clicked()
                    {
                        let col1 = self.backend.project().x_column.clone();
                        let col2 = self.backend.project().y_column.clone();
                        match run_four_pl_regression_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &col1,
                            &col2,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "4PL regression completed for {} vs {}",
                                    col1, col2
                                );
                                self.backend.project_mut().results_preview =
                                    format_four_pl_regression_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Pearson Correlation")
                        .on_hover_text("Uses X and Y as paired numeric columns.")
                        .clicked()
                    {
                        let col1 = self.backend.project().x_column.clone();
                        let col2 = self.backend.project().y_column.clone();
                        match run_pearson_correlation_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &col1,
                            &col2,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "Pearson correlation completed for {} vs {}",
                                    col1, col2
                                );
                                self.backend.project_mut().results_preview =
                                    format_pearson_correlation_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Spearman Correlation")
                        .on_hover_text("Uses X and Y as paired numeric columns.")
                        .clicked()
                    {
                        let col1 = self.backend.project().x_column.clone();
                        let col2 = self.backend.project().y_column.clone();
                        match run_spearman_correlation_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &col1,
                            &col2,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "Spearman correlation completed for {} vs {}",
                                    col1, col2
                                );
                                self.backend.project_mut().results_preview =
                                    format_spearman_correlation_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run 2-Proportion")
                        .on_hover_text("Uses X as row groups and Y as outcome categories.")
                        .clicked()
                    {
                        let rows_col = self.backend.project().x_column.clone();
                        let cols_col = self.backend.project().y_column.clone();
                        match run_two_proportion_analysis(
                            &self.backend.project().data_table,
                            &self.backend.project().table_view,
                            &rows_col,
                            &cols_col,
                        ) {
                            Ok(result) => {
                                self.backend.project_mut().status_message = format!(
                                    "2-proportion z-test completed for {} vs {}",
                                    rows_col, cols_col
                                );
                                self.backend.project_mut().results_preview =
                                    format_two_proportion_result(&result);
                            }
                            Err(error) => {
                                self.backend.project_mut().status_message = error.clone();
                                self.backend.project_mut().results_preview = error;
                            }
                        }
                    }
                    if ui
                        .button("Run Chi-squared")
                        .on_hover_text("Uses X as rows and Y as columns.")
                        .clicked()
                    {
                        let rows_col = self.backend.project().x_column.clone();
                        let cols_col = self.backend.project().y_column.clone();
                        let _ = self.backend.dispatch(AppCommand::RunChiSquaredAnalysis {
                            rows_col,
                            cols_col,
                        });
                    }
                    ui.label("Uses X as row labels and Y as column labels.");
                });
                ui.end_row();
            });
    }

    fn show_csv_loader(&mut self, ui: &mut egui::Ui) {
        ui.heading("CSV Loader");
        ui.label("Select a CSV file or enter a path manually.");
        ui.add_space(6.0);

        ui.horizontal(|ui| {
            ui.add(
                egui::TextEdit::singleline(&mut self.csv_path_input)
                    .hint_text("/path/to/data.csv")
                    .desired_width(f32::INFINITY),
            );
        });

        ui.add_space(8.0);
        ui.horizontal(|ui| {
            let select_clicked = ui
                .add_sized(
                    [(ui.available_width() * 0.48).max(1.0), 36.0],
                    egui::Button::new("Select CSV...")
                        .fill(egui::Color32::from_rgb(164, 74, 27))
                        .stroke(egui::Stroke::new(1.0, egui::Color32::from_rgb(140, 63, 22))),
                )
                .clicked();

            let load_clicked = ui
                .add_sized(
                    [ui.available_width().max(1.0), 36.0],
                    egui::Button::new("Load CSV")
                        .fill(egui::Color32::from_rgb(164, 74, 27))
                        .stroke(egui::Stroke::new(1.0, egui::Color32::from_rgb(140, 63, 22))),
                )
                .clicked();

            if select_clicked
                && let Some(path) = FileDialog::new().add_filter("CSV", &["csv"]).pick_file()
            {
                self.csv_path_input = path.display().to_string();
                self.load_csv_path(path);
            }

            if load_clicked {
                let path = self.csv_path_input.trim().to_owned();
                let path = std::path::PathBuf::from(path);
                if path.as_os_str().is_empty() {
                    self.backend.project_mut().status_message = "CSV path is empty".to_owned();
                    return;
                }

                self.load_csv_path(path);
            }
        });
    }

    fn load_csv_path(&mut self, path: std::path::PathBuf) {
        if let Err(error) = self
            .backend
            .dispatch(AppCommand::LoadCsv { path: path.clone() })
        {
            self.backend.project_mut().status_message = error.clone();
            self.backend.project_mut().results_preview = error;
        } else {
            self.row_filter_input.clear();
        }
    }

    fn show_table_preview(&mut self, ui: &mut egui::Ui) {
        ui.heading("Table Preview");
        ui.add_space(6.0);
        let table = &self.backend.project().data_table;
        if table.is_empty() {
            ui.label("No table data loaded.");
            return;
        }

        let headers = table.headers.clone();
        let table_view = self.backend.project().table_view.clone();
        let preview_row_indices: Vec<usize> = table_view
            .visible_row_indices
            .iter()
            .copied()
            .take(20)
            .collect();
        let preview_rows: Vec<Vec<String>> = preview_row_indices
            .iter()
            .filter_map(|row_index| table.rows.get(*row_index).cloned())
            .collect();
        ui.label(format!(
            "{} rows, {} columns",
            table.row_count(),
            table.column_count()
        ));
        ui.label(format!(
            "Visible rows: {}",
            table_view.visible_row_indices.len()
        ));
        if !table_view.row_filter_query.is_empty() && table_view.visible_row_indices.is_empty() {
            ui.label(format!(
                "No rows matched filter '{}'.",
                table_view.row_filter_query
            ));
        }
        ui.label(format!(
            "Sort: {} | Selected rows: {}",
            table_view
                .sort_column
                .and_then(|column_index| headers.get(column_index).map(String::as_str))
                .map(|header| {
                    let direction = if table_view.sort_ascending {
                        "ascending"
                    } else {
                        "descending"
                    };
                    format!("{header} ({direction})")
                })
                .unwrap_or_else(|| "none".to_owned()),
            table_view.selected_rows.len()
        ));
        ui.add_space(6.0);

        egui::ScrollArea::both().max_height(260.0).show(ui, |ui| {
            egui::Grid::new("table_preview_grid")
                .striped(true)
                .spacing([12.0, 8.0])
                .show(ui, |ui| {
                    ui.strong("#");
                    for (column_index, header) in headers.iter().enumerate() {
                        let label = if table_view.sort_column == Some(column_index) {
                            let direction = if table_view.sort_ascending { "^" } else { "v" };
                            format!("{header} {direction}")
                        } else {
                            header.clone()
                        };

                        if ui.button(label).clicked() {
                            let _ = self
                                .backend
                                .dispatch(AppCommand::ToggleSortByColumn { column_index });
                        }
                    }
                    ui.end_row();

                    for (preview_index, row) in preview_rows.iter().enumerate() {
                        let row_index = preview_row_indices[preview_index];
                        let selected = table_view.selected_rows.contains(&row_index);
                        if ui
                            .selectable_label(selected, (row_index + 1).to_string())
                            .clicked()
                        {
                            let _ = self
                                .backend
                                .dispatch(AppCommand::ToggleRowSelection { row_index });
                        }
                        for cell in row {
                            ui.label(cell);
                        }
                        ui.end_row();
                    }
                });
        });
    }

    fn show_column_metadata(&self, ui: &mut egui::Ui) {
        let table = &self.backend.project().data_table;
        if table.column_metadata().is_empty() {
            return;
        }

        ui.heading("Column Metadata");
        ui.add_space(6.0);
        egui::ScrollArea::both().max_height(180.0).show(ui, |ui| {
            egui::Grid::new("column_metadata_grid")
                .striped(true)
                .spacing([12.0, 8.0])
                .show(ui, |ui| {
                    ui.strong("Column");
                    ui.strong("Type");
                    ui.strong("Non-empty");
                    ui.strong("Distinct");
                    ui.end_row();

                    for meta in table.column_metadata() {
                        ui.label(format!("{} ({})", meta.name, meta.index + 1));
                        ui.label(match meta.kind {
                            calcite_rust::state::ColumnKind::Empty => "empty",
                            calcite_rust::state::ColumnKind::Numeric => "numeric",
                            calcite_rust::state::ColumnKind::Text => "text",
                            calcite_rust::state::ColumnKind::Mixed => "mixed",
                        });
                        ui.label(meta.non_empty_count.to_string());
                        ui.label(meta.distinct_count.to_string());
                        ui.end_row();
                    }
                });
        });
    }

    fn show_data_controls(&mut self, ui: &mut egui::Ui) {
        ui.heading("Data");
        ui.add_space(8.0);
        egui::Grid::new("data_controls")
            .num_columns(2)
            .spacing([12.0, 10.0])
            .show(ui, |ui| {
                ui.label("Graph Type");
                ui.label(&self.backend.project().current_graph_type);
                ui.end_row();

                ui.label("Filter");
                let filter_changed = ui
                    .text_edit_singleline(&mut self.row_filter_input)
                    .changed();
                ui.end_row();

                ui.label("X Column");
                let x_changed = ui.text_edit_singleline(&mut self.x_column_input).changed();
                ui.end_row();

                ui.label("Y Column");
                let y_changed = ui.text_edit_singleline(&mut self.y_column_input).changed();
                ui.end_row();

                ui.label("Sub-group");
                let subgroup_changed = ui
                    .text_edit_singleline(&mut self.subgroup_column_input)
                    .changed();
                ui.end_row();

                if filter_changed {
                    let _ = self.backend.dispatch(AppCommand::SetRowFilter {
                        query: self.row_filter_input.clone(),
                    });
                }

                if x_changed || y_changed || subgroup_changed {
                    let _ = self.backend.dispatch(AppCommand::SetColumns {
                        x_column: self.x_column_input.clone(),
                        y_column: self.y_column_input.clone(),
                        subgroup_column: self.subgroup_column_input.clone(),
                    });
                }
            });

        ui.add_space(12.0);
        let button = egui::Button::new("Update Graph")
            .fill(egui::Color32::from_rgb(164, 74, 27))
            .stroke(egui::Stroke::new(1.0, egui::Color32::from_rgb(140, 63, 22)));
        ui.add_sized([ui.available_width().max(1.0), 40.0], button);
    }

    fn show_results_panel(&mut self, ui: &mut egui::Ui) {
        ui.heading("Analysis Results");
        ui.add_space(8.0);
        egui::ScrollArea::vertical().show(ui, |ui| {
            ui.monospace(&self.backend.project().results_preview);
        });
    }
}
