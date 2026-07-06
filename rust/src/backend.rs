use std::path::PathBuf;

use crate::core::AppCommand;
use crate::state::ProjectState;

#[derive(Debug, Default)]
pub struct AppBackend {
    project: ProjectState,
}

impl AppBackend {
    pub fn new() -> Self {
        Self {
            project: ProjectState::new(),
        }
    }

    pub fn project(&self) -> &ProjectState {
        &self.project
    }

    pub fn project_mut(&mut self) -> &mut ProjectState {
        &mut self.project
    }

    pub fn dispatch(&mut self, command: AppCommand) -> Result<(), String> {
        match command {
            AppCommand::LoadCsv { path } => self.load_csv(path),
            AppCommand::SetGraphType { graph_type } => {
                self.project.set_graph_type(graph_type);
                Ok(())
            }
            AppCommand::SetColumns {
                x_column,
                y_column,
                subgroup_column,
            } => {
                self.project.x_column = x_column;
                self.project.y_column = y_column;
                self.project.subgroup_column = subgroup_column;
                Ok(())
            }
        }
    }

    fn load_csv(&mut self, path: PathBuf) -> Result<(), String> {
        match self.project.open_csv_path(&path) {
            Ok(()) => {
                self.project.results_preview = format!(
                    "Loaded table\n\nRows: {}\nColumns: {}",
                    self.project.data_table.row_count(),
                    self.project.data_table.column_count()
                );
                Ok(())
            }
            Err(error) => {
                self.project.status_message = "CSV load failed".to_owned();
                self.project.results_preview = error;
                Err(self.project.results_preview.clone())
            }
        }
    }
}
