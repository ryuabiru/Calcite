# 「Matplotlib-first」描画アーキテクチャの提案

このアプローチは、現在の`sns.catplot`をベースとした描画ロジックの非効率性や凡例制御の難しさを解決するため、**MatplotlibとSeabornの役割をより明確に分離する**ことを目的とします。

## 1\. 新しい設計思想の要点

- **Matplotlibでキャンバスを準備**: グラフを描画する「キャンバス」である`Figure`と`Axes`オブジェクトを、`matplotlib.pyplot.subplots()`を用いて明示的に作成します。
- **Seabornで描画を委任**: `Seaborn`は、`ax`引数を介して、**事前に準備されたキャンバス上**にグラフを描画する役割に徹します。
- **凡例を個別に制御**: `Seaborn`の描画関数で`legend=False`を指定して凡例の自動生成を抑制し、すべての描画が完了した後に`Matplotlib`の凡例機能で統一的に管理します。

## 2\. 変更のメリット

- **コードの簡素化**: `ax.clear()`でキャンバスを一度クリアするような無駄な処理が不要になり、コードがよりクリーンで直感的になります。
- **描画効率の向上**: `sns.catplot`が内部で実行する不要な描画計算がなくなります。
- **凡例の柔軟性向上**: 凡例の位置やタイトル、表示内容をコードで自由に設定できるようになります。
- **統一的な描画フロー**: 今後の新しいグラフタイプ（例：時系列プロットなど）を追加する際も、この統一されたフローを適用できるため、拡張性が向上します。

## 3\. 実装の概念図 (`handlers/graph_manager.py`内)

```mermaid
graph TD
    A[update_graph()の開始] --> B{グラフタイプの判定};
    B -- paired_scatter --> C[draw_paired_scatter()];
    B -- histogram --> D[draw_histogram()];
    B -- その他 --> E[draw_categorical_plot()];
    
    subgraph draw_categorical_plot()
        F[fig, ax = plt.subplots() を呼び出し];
        F --> G{ベースとなるグラフの描写};
        G -- boxplot --> H[sns.boxplot(..., ax=ax)];
        G -- barplot --> I[sns.barplot(..., ax=ax)];
        H --> J[sns.stripplot(..., ax=ax, legend=False)];
        I --> J;
        J --> K[fig.legend() で凡例を管理];
        K --> L[apply_annotations(ax, ...)];
        L --> M[最終的な描画プロパティを適用];
    end
```

## 4\. 実装における注意点

- **`statannotations`との連携**: この方法でも、描画に`seaborn`を使用するため、`statannotations`は問題なく機能します。`Annotator`インスタンスに渡す`x`、`y`、`data`、`ax`などの情報は、この新しいフローでも同じように利用できます。
- **ファセットへの対応**: `subplots`でファセットに対応するには、`sharex=True`や`sharey=True`といった引数を適切に設定する必要があります。各サブプロットに対する描画は、`for ax in axes.flat:`といったループで行います。
