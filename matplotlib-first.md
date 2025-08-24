# 「Matplotlib-first」描画アーキテクチャの提案

このアプローチは、現在の`sns.catplot`をベースとした描画ロジックの非効率性や凡例制御の難しさを解決するため、**MatplotlibとSeabornの役割をより明確に分離する**ことを目的とします。

## 1\. 新しい設計思想の要点

- **Matplotlibでキャンバスを準備**: グラフを描画する「キャンバス」である`Figure`と`Axes`オブジェクトを、`matplotlib.pyplot.subplots()`を用いて明示的に作成します。これにより、描画領域の全体的な構造を完全にコントロール下に置きます。
- **Seabornで描画を委任**: `Seaborn`は、`ax`引数を介して、**事前に準備されたキャンバス上**にグラフを描画する役割に徹します。`catplot`のようなFigure-level関数は使用せず、`boxplot`や`barplot`といったAxes-level関数のみを利用します。
- **凡例を個別に制御**: `Seaborn`の描画関数で`legend=False`を指定して凡例の自動生成を抑制し、すべての描画が完了した後に`Matplotlib`の凡例機能で統一的に管理します。

## 2\. 変更のメリット

- **コードの簡素化**: `ax.clear()`でキャンバスを一度クリアするような無駄な処理が不要になり、コードがよりクリーンで直感的になります。
- **描画効率の向上**: `sns.catplot`が内部で実行する不要な描画計算がなくなります。
- **凡例の柔軟性向上**: 凡例の位置やタイトル、表示内容をコードで自由に設定できるようになります。
- **統一的な描画フロー**: 今後の新しいグラフタイプを追加する際も、この統一されたフローを適用できるため、拡張性が向上します。

## 3\. `statannotations`とファセット機能に関する懸念の解消

このアーキテクチャへの移行にあたり、「`statannotations`との連携」と「ファセット機能の実装」に関する懸念は、以下の設計によって解消されます。

### 3.1. `ax`オブジェクトの役割：生まれ（Origin）より育ち（State）

`statannotations`が正しく機能するのは、「Seaborn生まれの`ax`」だからではありません。より正確には、\*\*「まっさらな`ax`オブジェクトに、Seabornの描画関数が情報を『描き込む』ことで、`statannotations`が必要とする文脈が完成する」\*\*ためです。

- **① キャンバスの準備 (`plt.subplots`)**: `matplotlib`が、座標軸だけを持つ**真っ白なキャンバス (`ax`)** を用意します。
- **② 描画 (`sns.boxplot(ax=ax, ...)`):** `seaborn`がそのキャンバスに、与えられたデータに基づいて箱ひげ図などを描き込みます。このプロセスを通じて、`ax`オブジェクトは初めて「X座標0 = 'Control'」のような**文脈情報**をプロパティとして保持します。
- **③ アノテーション (`Annotator(ax, ...)`):** `statannotations`は、**描画後の`ax`オブジェクト**を受け取り、そこに書き込まれた文脈情報（軸ラベルと座標の対応など）を読み取って、正しい位置にアノテーションを描画します。

つまり、`ax`オブジェクトの生まれは常に同じ`Matplotlib`です。重要なのは、`statannotations`が呼ばれる前に、`seaborn`によって適切に「育てられている」ことであり、本アーキテクチャはそのプロセスをより明示的にコントロールするものです。

### 3.2. ファセット戦略：「分割統治（Divide and Conquer）」

`sns.catplot`が内部で作るファセットと`plt.subplots`で作るファセットが「寸分も狂わない」ことを保証する必要はありません。なぜなら、本アーキテクチャは**各ファセットを完全に独立した世界として扱う**からです。

具体的には、`plt.subplots`で作成した`axes`配列をループ処理します。

```python
# fig, axes = plt.subplots(...)
for ax, category in zip(axes, categories):
    # 1. ファセット一つ分のデータを抽出
    subset_df = df[df['Treatment'] == category]

    # 2. そのaxに、そのデータだけでグラフを描画
    sns.boxplot(data=subset_df, ..., ax=ax)

    # 3. そのaxに、そのデータだけでアノテーション
    annotator = Annotator(ax, ..., data=subset_df)
    annotator.annotate()
```

このループの中で、`annotator`は**一つの`ax`と、それに対応するデータ（`subset_df`）しか認識しません。** これにより、`catplot`のように複雑な全体像の中から対応関係を探す必要がなくなり、各ファセット内で描画とアノテーションが完結するため、構造的に間違いようがなく、非常に堅牢な実装が可能になります。

## 4\. 実装の概念図 (`handlers/graph_manager.py`内)

```mermaid
graph TD
    A[update_graph()の開始] --> B{グラフタイプの判定};
    B -- paired_scatter --> C[draw_paired_scatter()];
    B -- histogram --> D[draw_histogram()];
    B -- その他 --> E[draw_categorical_plot()];

    subgraph draw_categorical_plot()
        F[fig, axes = plt.subplots() を呼び出し];
        F --> G["for ax in axes.flat: ループ"];
        G --> H{ベースとなるグラフを描画};
        H -- boxplot --> I[sns.boxplot(..., ax=ax)];
        H -- barplot --> J[sns.barplot(..., ax=ax)];
        I --> K[sns.stripplot(..., ax=ax, legend=False)];
        J --> K;
        K --> L[apply_annotations(ax, ...)];
        L --> G;
        G -- ループ終了 --> M[fig.legend() で凡例を管理];
        M --> N[最終的な描画プロパティを適用];
    end
```
