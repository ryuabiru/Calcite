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

初期 bootstrap では `eframe/egui` を採用する。

理由:

- Node.js や web bundler への依存が不要
- 同一リポジトリで最小 app shell を素早く立ち上げられる
- Rust 単体で window / panel / state bootstrap を進めやすい
- Tauri よりも「まず Rust 化を始める」目的に対して初動が軽い

見直し条件:

- 配布戦略上 web UI の方が明確に有利になった場合
- 複雑なデザイン要件が `egui` で厳しくなった場合
- app shell の段階を抜けた後に Tauri へ再評価する必要が出た場合

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

1. Rust app shell を起動できるようにする
2. 画面構造を既存 Calcite に寄せる
3. CSV と table を実装する
4. simple graph を 1 つずつ置き換える
5. data transforms を移す
6. simple statistics を移す
7. advanced statistics を最後に扱う

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

1. Table sorting and selection state を Rust 側に追加する
2. CSV import を file dialog から起動できるようにする
3. Project persistence の Rust schema を定義する
4. Graph type との接続を state model 経由に寄せる
