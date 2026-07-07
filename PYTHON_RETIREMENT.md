# Python Retirement Checklist

## Purpose

This document tracks the retirement history of the Python implementation.

The runtime Python code under `calcite/` has been removed. The remaining Python test harness and parity bridge have also been removed, so the repository no longer ships Python sources for runtime or verification.

## Keep For Now

No runtime Python modules remain under `calcite/`, and no Python test harness remains in the repo.

## Retirement Candidates

None.

## Retirement Order

1. Freeze Rust parity for the supported workflows.
2. Remove UI-specific Python entry points.
3. Remove dialog and handler modules that no longer back a reference workflow.
4. Remove persistence and table-interaction helpers once Rust state handling is trusted.
5. Remove remaining reference-only code after fixtures and golden outputs are updated.

## Verification Before Removal

- Rust tests continue to pass.
- Tauri frontend build continues to pass.
- Migration notes reflect the retired workflow.
- Fixture-based parity checks have been replaced with Rust-native coverage.

## Current Status

- Rust now covers the core table, graph, transform, and statistics slices needed for the migration.
- The Python reference stack is fully retired from the repository.
- Remaining work is now entirely on Rust UI polish, coverage gaps, and product behavior.
- Historical retirement notes below are preserved for context.
