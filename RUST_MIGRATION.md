# Rust Migration Plan

## Objective

Calcite を長期的に Rust ベースのデスクトップアプリへ移行する。

当面は Python 実装と Rust 実装を同一リポジトリで共存させる。ただし移行の目的は単なる技術実験ではなく、最終的に Python GUI 依存を取り除き、配布・保守・UI 品質・状態管理を一本化することにある。

## Non-Goals

- 初期段階で `pandas` / `scipy` / `statsmodels` の完全代替を作ること
- 全統計機能を短期間で Rust に移植すること
- 既存 Python 実装の UI と Rust UI を長期的に二重保守すること

## Core Principles

1. 先に UI とアプリ骨格を Rust に寄せる。
2. 統計実装は最後に移す。最初から完全移植を狙わない。
3. 移行期間中は Python を参照実装として扱う。
4. 各フェーズで「ユーザーが使えるもの」を残す。
5. リポジトリ分離は後回しにし、まずは移行速度を優先する。

## Temporary Monorepo Structure

現時点では同一リポジトリ共存を前提にする。

想定構成:

- `calcite/`
  既存 Python 実装
- `rust/` or `calcite-rs/`
  新しい Rust アプリ本体
- `fixtures/`
  Python と Rust で共有する CSV / project fixtures
- `docs/` or top-level `*.md`
  移行設計・進捗メモ

Rust 側の実装が進んでも、Python 側はしばらく削除しない。Rust 側で feature parity が取れた単位ごとに Python 実装を retirement 候補へ移す。

## Selected GUI Stack

GUI の本線は `Tauri` を採用する。

理由:

- 既存 Calcite の GUI 要件は Web ベースのレイアウトで再現しやすい
- 表、ダイアログ、タブ、複数ビューの構造を柔軟に組める
- Rust 側の state / data / analysis を command bridge で分離しやすい
- 最終配布形態を見据えたときに、UI の本線として整合しやすい

補助的な位置づけ:

- いまある `eframe/egui` の Rust 画面は、Rust コアと state model を検証するためのプロトタイプとして扱う
- 本番 GUI は Tauri 側へ段階的に移す
- 移行完了後は `egui` shell を退役候補にする

## Target Architecture

最終像は以下。

- Rust:
  - desktop shell
  - UI
  - state management
  - project persistence
  - table interaction
  - graph orchestration
  - data transformation
  - basic statistics
- Python:
  - 移行完了後は不要

初期～中期は以下の形を許容する。

- Rust:
  - desktop shell
  - UI
  - app state
  - file/project lifecycle
- Python:
  - graph/statistics/data engine

## Boundary Design

Rust / React / Tauri の責務を明確に分離する。

### Rust Responsibilities

- domain model
- data transformation
- project persistence
- validation
- statistics and graph orchestration
- command / query execution

Rust は UI コンポーネントや画面レイアウトの知識を持たない。

### React Responsibilities

- panel layout
- temporary input state
- async request lifecycle
- user interaction
- presentation-specific formatting

React は CSV 実装詳細や project format の内部仕様を直接持たない。

### Tauri Responsibilities

- command bridge
- query bridge
- desktop shell lifecycle

Tauri 側には業務ロジックを置かず、Rust core と React UI の橋渡しだけに留める。

### Coupling Rules

1. React は Rust の内部 state 構造を前提にしない
2. Rust は React の画面都合の flag を持ち込まない
3. 読み取りは `query`、変更は `command` に分離する
4. frontend は Tauri invoke を薄い API wrapper 経由で呼ぶ
5. frontend に返すデータは内部 state の直露出ではなく DTO とする

## Frontend / Backend Contract

当面の API 境界は command / query 分離で整理する。

### Query Examples

- `get_app_snapshot`
- `get_table_view`
- `get_graph_config`
- `get_results_view`

### Command Examples

- `load_csv`
- `set_columns`
- `set_graph_type`
- `edit_cell`
- `restructure_data`
- `pivot_data`
- `save_project`

この contract を先に固定してから、React 側の画面実装を広げる。

## Migration Phases

### Phase 0: Bootstrap

Goal:

- Rust アプリの土台を作る
- 同一リポジトリで開発できる状態にする

Tasks:

- Rust app directory を追加
- GUI 技術を確定する
- 開発起動手順を README に追記
- Python 実装を参照実装として固定

Exit Criteria:

- 空でも起動する Rust アプリがある
- リポジトリから Python と Rust の両方を起動できる

### Phase 1: App Shell and Project Model

Goal:

- Calcite の基本的な画面骨格と状態モデルを Rust で持つ

Tasks:

- main window
- panel layout
- graph area placeholder
- data panel placeholder
- results panel placeholder
- project state schema の Rust 定義

Exit Criteria:

- Python を呼ばなくても Rust 側の画面骨格が成立する
- project settings 相当の状態を Rust で保持できる

Current Status:

- Rust app shell is bootstrapped in `rust/`
- `ProjectState` and `DataTable` live in Rust
- CSV loading and table previews are wired into the UI
- Table sorting and row selection are wired into the Rust table preview
- Column metadata is inferred from loaded CSV files and displayed in the UI
- CSV import now reports concise status text and detailed error summaries
- Rust project persistence schema now mirrors manifest, settings, table, and analysis buckets

### Phase 1.5: Tauri GUI Bootstrap

Goal:

- Rust コアを再利用しつつ、Tauri ベースの本番 GUI を立ち上げる

Tasks:

- Tauri app shell
- frontend 画面の skeleton
- Rust command bridge
- state と UI の接続
- table / graph / results の主要レイアウト

Exit Criteria:

- Tauri で Calcite の主要レイアウトが起動する
- Rust backend と frontend の境界が確立する

Current Status:

- Tauri scaffold is added under `tauri/`
- Rust backend commands are exposed through a Tauri command bridge
- A minimal web frontend shell has been created for the desktop UI direction
- Tauri frontend build and desktop launch are verified locally
- Tauri development startup is now standardized around the official `tauri dev` flow
- The temporary `cargo run` / manual window bootstrap workaround has been removed
- `npm run tauri:dev` now reaches the desktop shell and launches `target/debug/calcite-tauri`
- Frontend is being reshaped into the Calcite 4-pane workspace
- Load CSV / Save Project / Export CSV controls are wired into the Tauri frontend
- Table editing commands are wired into the Tauri frontend and backend

### Phase 2: Data Loading and Table UX

Goal:

- CSV 読み込みと表表示を Rust 側へ移す

Tasks:

- CSV import
- table model
- column metadata
- selection state
- sort/filter の最小機能

Exit Criteria:

- CSV を読み込み、表で閲覧・選択・並べ替えできる

Current Status:

- Rust 側で CSV 読み込みと table preview は動作している
- Sorting と row selection は Rust 側で連動している
- Column metadata は Rust 側で表示している
- Case-insensitive row filtering が Rust preview に追加された

### Phase 3: Graph Pipeline Migration

Goal:

- 低難度グラフから Rust 側へ移す

Tasks:

- bar
- countplot
- stacked_bar
- stacked_bar_100
- proportion_plot
- heatmap

Exit Criteria:

- 現在のカテゴリ系可視化が Rust で再現できる
- Python 側描画に依存しなくても主要な探索が可能

Current Status:

- Rust graph area now renders a native categorical bar chart from the loaded table
- Rust graph area now also renders a native stacked bar chart from the loaded table and subgroup column
- Rust graph area now also renders a native correlation heatmap from numeric columns
- Rust graph area now also renders a native categorical heatmap from the loaded table's X/Y columns
- The first graph pipeline slice is in place and can be extended toward countplot and other categorical views
- Remaining graph types will be prioritized after the Tauri shell is in place

### Phase 4: Data Transformation Migration

Goal:

- 日常操作で必要なデータ加工を Rust に寄せる

Tasks:

- filter
- wide/long reshape
- pivot
- export/import の再構築
- project persistence の再設計

Exit Criteria:

- Python GUI が担っていた日常データ操作を Rust 単体で実行できる

Current Status:

- Rust backend now exposes pure DataTable reshape and pivot helpers
- Backend commands can restructure long-form tables and pivot them back into wide form
- CSV-backed table state is rebuilt after transformations so metadata stays in sync
- Rust backend can persist and restore project snapshots from a project directory
- Project save/load round-trips keep table, filters, and graph settings in sync
- Rust backend can import clipboard-style delimited text and export the current table as CSV

### Phase 5: Basic Analysis Migration

Goal:

- 利用頻度が高く、依存が浅い統計機能を Rust 化する

Tasks:

- correlation
- chi-squared
- 2-proportion
- simple linear regression
- result formatting
- graph-statistics linkage

Exit Criteria:

- 現在のカテゴリ解析フローを Rust 単体で完結できる

Current Status:

- 未着手

### Phase 6: Advanced Statistics Migration

Goal:

- 高度な検定と回帰を段階的に置き換える

Tasks:

- t-tests
- ANOVA
- non-parametric tests
- Shapiro-Wilk
- 4PL

Exit Criteria:

- Python 参照なしでも必要機能が満たせる

Current Status:

- 未着手

### Phase 7: Python Retirement

Goal:

- Python GUI と依存を段階的に整理する

Tasks:

- 不要モジュールの削除
- fixtures と golden outputs の見直し
- packaging の一本化
- migration notes の整理

Exit Criteria:

- 配布物が Rust アプリに一本化される

## Recommended Weekly Order

毎日少しずつ進める前提では、以下の順序を崩さない。

1. Rust / React / Tauri の責務境界を先に固定する
2. Rust コアの state / persistence / transform を固める
3. Tauri shell と frontend contract を安定させる
4. 画面構造を既存 Calcite に寄せる
5. CSV と table を接続する
6. graph を 1 つずつ置き換える
7. data transforms を UI に接続する
8. simple statistics を移す
9. advanced statistics を最後に扱う

## Long-Term Execution Strategy

長期移行は「1 回の大移植」ではなく、「1 画面操作が最後まで通る小さな縦スライス」の積み上げで進める。

### Recommended Slice Order

1. CSV 読み込み -> table 表示
2. 列選択 -> graph settings 反映
3. filter / sort -> table 再描画
4. reshape / pivot -> table 更新
5. save / load project -> state 復元
6. graph type ごとの parity 取得
7. analysis ごとの parity 取得

### Daily Rule

1. 1 日 1 スライスだけ進める
2. 各スライスで Rust テストを通す
3. 各スライスで frontend の操作確認を行う
4. 各スライスで Python 実装との parity を 1 点確認する

### Verification Policy

- Rust: domain / application をユニットテスト中心に固める
- Tauri: command / query contract の結合確認を行う
- frontend: 表示ロジックと API 呼び出しの整合を確認する
- Python parity: fixture ベースで結果比較を継続する

## Branch Strategy

当面の基準ブランチ:

- 現在作業の起点: `rust-migration-bootstrap`

以後のサブブランチ例:

- `rust-shell`
- `rust-table-model`
- `rust-categorical-plots`
- `rust-project-format`
- `rust-basic-stats`

原則:

- Python 側の通常開発と Rust 移行は分ける
- ただし Python 側で参照実装を直す必要がある場合は同一リポジトリ内で許容する
- 大きい移行は必ずフェーズ単位で branch を切る

## Immediate Next Steps

1. command / query と DTO の境界を Rust 側で明文化する
2. 最初の縦スライスを `CSV 読み込み -> table 表示` に固定する
3. reshape / pivot / export / project 操作を GUI 上の導線として整理する
4. graph の残り種別を優先度順に Rust 側へ移す

## Next Slice

次回の作業は以下の 1 スライスに固定する。

### Slice Goal

- `CSV 読み込み -> table 表示` を React UI 上で最後まで通す

### Done Criteria

- React の DataFrame ペインで CSV path を指定して読み込める
- Rust backend から table headers と row data を query として取得できる
- frontend 側で table preview が描画される
- 読み込み後に row count / column count / loaded file name が UI に反映される
- 読み込み失敗時にエラーが Results または Status に表示される

### Files Expected To Change

- `rust/src/backend.rs`
- `rust/src/state.rs`
- `tauri/src-tauri/src/main.rs`
- `tauri/frontend/src/api.js`
- `tauri/frontend/src/App.jsx`

### Verification

- `cd rust && cargo test`
- `cd tauri && npm run build`
- `cd tauri && npm run tauri:dev`
- 実機確認: CSV 読み込み後に table preview が表示される

## After Next Slice

次の優先順位は以下。

1. `sort / filter -> table 再描画`
2. `列選択 -> graph settings 反映`
3. `reshape / pivot -> table 更新`
4. `save / load project -> state 復元`

## Working Rule

毎回の作業開始時は以下だけ見ればよい。

1. `Immediate Next Steps`
2. `Next Slice`
3. `After Next Slice`

その日の作業が終わったら、完了した slice をこのファイルへ反映し、次の slice を 1 つだけ明示する。
