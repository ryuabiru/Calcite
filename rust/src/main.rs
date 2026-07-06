mod backend;
mod core;
mod project_persistence;
mod state;

use backend::AppBackend;
use core::AppCommand;
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
                self.placeholder_surface(
                    ui,
                    "Rust graph renderer bootstrap",
                    "This region will host the new Rust-native plotting pipeline.",
                    [ui.available_width(), ui.available_height() - 8.0],
                );
            });

        egui::CentralPanel::default()
            .frame(self.panel_frame())
            .show(ctx, |ui| {
                ui.columns(2, |columns| {
                    self.show_data_controls(&mut columns[0]);
                    self.show_results_panel(&mut columns[1]);
                });
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
            "CSV loading, table rendering, sorting, and selection state will move here first.",
            [ui.available_width(), 120.0],
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
                    [ui.available_width() * 0.48, 36.0],
                    egui::Button::new("Select CSV...")
                        .fill(egui::Color32::from_rgb(164, 74, 27))
                        .stroke(egui::Stroke::new(1.0, egui::Color32::from_rgb(140, 63, 22))),
                )
                .clicked();

            let load_clicked = ui
                .add_sized(
                    [ui.available_width(), 36.0],
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
        let preview_rows: Vec<Vec<String>> =
            table.preview_rows(20).map(|row| row.to_owned()).collect();
        let table_view = self.backend.project().table_view.clone();
        ui.label(format!(
            "{} rows, {} columns",
            table.row_count(),
            table.column_count()
        ));
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

                    for (row_index, row) in preview_rows.iter().enumerate() {
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
                            crate::state::ColumnKind::Empty => "empty",
                            crate::state::ColumnKind::Numeric => "numeric",
                            crate::state::ColumnKind::Text => "text",
                            crate::state::ColumnKind::Mixed => "mixed",
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
        ui.add_sized([ui.available_width(), 40.0], button);
    }

    fn show_results_panel(&mut self, ui: &mut egui::Ui) {
        ui.heading("Analysis Results");
        ui.add_space(8.0);
        egui::ScrollArea::vertical().show(ui, |ui| {
            ui.monospace(&self.backend.project().results_preview);
        });
    }
}
