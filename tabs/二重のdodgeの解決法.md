# グラフ重ね描き時の「二重の`dodge`」問題とその解決策

## 発生する問題

- `seaborn`で異なる種類のグラフ（例: 棒グラフと散布図）を同じ軸に重ねて描くと、グループ間の位置がずれてしまうことがある。
- これは、各描画関数（例: `barplot`と`stripplot`）が**それぞれ独立して**、グループの位置を計算（`dodge`）してしまうために起こる。

## 解決策: 「Matplotlib-first」アーキテクチャ

この問題を根本的に解決するためには、`seaborn`に描画のすべてを任せるのではなく、**`matplotlib`と`seaborn`の役割を明確に分ける**ことが鍵となる。

- **Matplotlibの役割**: グラフの舞台となる**空の`Axes`オブジェクト**を準備する。
- **Seabornの役割**: 準備された`Axes`に、**順番に**グラフを描き加えていく。

この思想により、**先に描かれたグラフが`Axes`オブジェクトに「位置情報」を書き込み、次に描かれるグラフはその情報を利用して、正しい位置に描画する**というフローを確立する。

## 実装のポイント

1. **キャンバスを準備**
   - `matplotlib.pyplot.subplots()`で、描画する`Axes`オブジェクトを先に作成する。

2. **最初のグラフを描画**
   - `seaborn.barplot()`を呼び出し、`ax`引数に1で作成した`Axes`オブジェクトを渡す。
   - `seaborn`は、`x`と`hue`の組み合わせから各棒グラフの正確な位置を計算し、`Axes`に描き込む。

3. **重ねるグラフを描画**

   - `seaborn.stripplot()`を**同じ`Axes`オブジェクト**に対して呼び出す。
   - このとき、`dodge=False`を明示的に指定する。
   - これにより、`stripplot`は独自の**位置計算を行わず**、すでに`Axes`が持っている位置情報（`barplot`が書き込んだ情報）をそのまま利用して、データ点を正確に配置する。

## コード例

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Matplotlibでキャンバスを準備
fig, ax = plt.subplots(figsize=(8, 6))

# 2. 棒グラフを描画 (axesに位置情報を書き込む)
sns.barplot(
    data=df,
    x='category',
    y='value',
    hue='group',
    ax=ax
)

# 3. データ点を重ねて描画（dodge=Falseが重要！）
sns.stripplot(
    data=df,
    x='category',
    y='value',
    hue='group',
    jitter=True,
    dodge=False,  # <--- これが二重のdodgeを防ぐ
    ax=ax
)

# 凡例を統合的に管理
ax.legend(title='Group')
plt.show()
```
