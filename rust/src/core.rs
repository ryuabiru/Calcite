use std::path::PathBuf;

#[derive(Clone, Debug)]
pub enum AppCommand {
    LoadCsv {
        path: PathBuf,
    },
    SetGraphType {
        graph_type: String,
    },
    SetColumns {
        x_column: String,
        y_column: String,
        subgroup_column: String,
    },
}
