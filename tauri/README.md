# Calcite Tauri Scaffold

This directory contains the Tauri-based desktop shell scaffold for Calcite.

Current structure:

- `src-tauri/` Rust side of the Tauri shell
- `frontend/` minimal web UI shell

The Rust backend commands are wired to the shared `calcite_rust` crate.
The frontend is intentionally small and will grow as the migration advances.

## Development

Install dependencies once:

```bash
npm install
```

Run the desktop shell in development mode:

```bash
npm run tauri:dev
```

Build the frontend bundle only:

```bash
npm run build
```
