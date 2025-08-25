# Calcite

**Calcite**は、GraphPad Prismにインスパイアされた、直感的な操作が可能なデータ分析・グラフ作成アプリケーションです。プログラミングの知識がなくても、GUI操作だけでデータのインポートから統計解析、論文品質のグラフ作成までをシームレスに行うことを目指しています。

## 💎 プロジェクト名の由来

「Calcite（方解石）」は、光を多方向に屈折させる性質を持つ鉱物です。また、その名称は「Calculation（計算）」の`cal`と語源を共有しています。このプロジェクトは、方解石が光を多角的に見せるように、一つのデータから様々な側面を分析し、洞察を得られるように、という願いを込めて名付けられました。

## ✨ 主な機能

- **データハンドリング**

  - CSVファイルのインポート、クリップボードからのデータ貼り付け（Excelなどに対応）
  - スプレッドシート形式のインタラクティブなテーブル表示と直接編集
  - `pandas.eval`を利用した数式による新しい列の動的作成
  - データ形式の変換（ワイド形式 ⇔ ロング形式）

- **グラフ描画**

  - **描画エンジンの統一**: グラフ描画のコアエンジンを`seaborn`に統一し、論文品質のグラフを少ないコードで描画できるようにしました。
  - **Matplotlib-firstアーキテクチャ**: グラフの描画をより柔軟に制御するため、`matplotlib`で明示的にキャンバス（`Figure`と`Axes`）を準備し、`seaborn`は描画に徹するという新しいアーキテクチャを確立しました。これにより、凡例の制御や重ね描きがより堅牢になりました。
  - **動的UI**: グラフタイプ（散布図、棒グラフ、ペアード散布図）に応じて、データ選択UIが最適な形式に自動で切り替わります。
  - **詳細なカスタマイズ**: タイトルや軸ラベルのフォントサイズ、軸範囲、対数スケール、グリッド線などをGUIから細かく設定可能。
  - **Prism風スタイル**: グラフの上と右の枠線を非表示にするオプションを搭載。

- **統計解析**

  - **自動アノテーション**: 統計検定結果のp値をグラフ上にブラケットとアスタリスク(\*)で自動描画します。専門ライブラリ`statannotations`を導入することで、重なりを自動回避しながら堅牢に行われます。
  - **Independent t-test**: 複数条件でのフィルタリングが可能なUIを実装し、複雑なTidy Dataにも対応します。
  - **Paired t-test / Wilcoxon Signed-rank test**: 対応のある2群間の比較検定。
  - **One-way ANOVA / Kruskal-Wallis Test**: 3群以上の比較と、Tukey's HSDまたはDunn's Post-hocによる多重比較検定に対応。
  - **Chi-squared Test**: カテゴリカル変数間の関連を検定。
  - **Spearman's Correlation**: 2つの列間の順位相関を検定。
  - **回帰分析**: 線形回帰および非線形回帰（シグモイド曲線、4PL）に対応し、R²値をグラフに表示します。

## 🛠️ セットアップ

本アプリケーションはクロスプラットフォーム（Windows, macOS, Linux）で動作します。

1. **リポジトリをクローン**

    ```bash
    git clone https://github.com/ryuki-abiru/calcite.git
    cd calcite
    ```

2. **仮想環境の作成と有効化**

    ```bash
    # Python 3.10以降を推奨
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS / Linux
    source venv/bin/activate
    ```

3. **依存ライブラリのインストール**
    以下の内容で`requirements.txt`ファイルを作成し、インストールを実行してください。

    **`requirements.txt`**:

    ``` txt
    PySide6
    pandas
    numpy
    scipy
    statsmodels
    matplotlib
    scikit-posthocs
    statannotations
    ```

    ```bash
    pip install -r requirements.txt
    ```

4. **アプリケーションの実行**

    ```bash
    python main.py
    ```

## 🚀 使い方

1. **`File > Open CSV...`** または **`Edit > Paste`** でデータを読み込みます。
2. ツールバーから**グラフタイプ**（Scatter, Barなど）を選択します。
3. 画面下部の\*\*「データ」タブ\*\*で、X軸・Y軸などに使用するカラムを選択します。
4. 「フォーマット」「テキストと凡例」「軸」タブでグラフの見た目を調整します。
5. **`Analysis`** メニューから実行したい統計解析を選択し、ダイアログの指示に従います。
6. 完成したグラフは **`File > Save Graph As...`** から保存できます。
