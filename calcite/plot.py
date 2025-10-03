import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# (ここに以前作成した set_plot_style と plot_bar 関数の定義を記述)
# --- 関数の定義 ここから ---
def set_plot_style():
    """
    グラフ描画のための推奨グローバルスタイルを設定する。(フォント設定更新版)
    - seabornテーマ: 'ticks'
    - フォント: Arial, サイズ指定 (軸ラベル 15, 目盛り 12)
    - 背景色: 白
    """
    sns.set_theme(style='ticks')
    
    # matplotlibのパラメータを更新
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': 'Arial', # デフォルトのサンセリフフォントをArialに設定
        'axes.labelsize': 15,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
    })
    
    # Paul Tol氏の "Bright" 質的カラーパレット
    paul_tol_bright = [
        '#332288',  # Indigo
        '#88CCEE',  # Cyan
        '#44AA99',  # Teal
        '#999933',  # Olive
        '#DDCC77',  # Sand
        '#CC6677',  # Rose
        '#AA4499',  # Purple
        '#DDDDDD'   # Pale gray
    ]
    
        # Paul Tol氏の "Bright" 質的カラーパレット
    paul_tol_light = [
    '#BBBBBB',  '#AA4499', '#332288','#CC6677',
    '#882255', '#DDCC77', '#999933','#88CCEE',
    '#44AA99', '#117733', '#EEEEEE',
    ]
    # このパレットをデフォルトとしてseabornに登録
    sns.set_palette(paul_tol_light)
    print("Plot style with Arial font has been set.")

def plot_bar(data, x, y, hue=None, facet=None, individual_points=False, 
             stripplot_kws=None, despine_plot=True, legend_loc='upper left',
             facet_title_size=16, **kwargs):
    """
    (Spine描画タイミング修正版)
    """
    # ... (前半のコードは変更なし) ...
    x_order = sorted(data[x].unique())
    hue_order = sorted(data[hue].unique()) if hue else None

    kwargs.setdefault('edgecolor', 'black'); kwargs.setdefault('linewidth', 1.5)
    kwargs.setdefault('errorbar', 'sd'); kwargs.setdefault('capsize', 0)
    
    if stripplot_kws is None: stripplot_kws = {}
    stripplot_kws.setdefault('edgecolor', 'black'); stripplot_kws.setdefault('linewidth', 1.5)

    if facet:
        n_facets = len(facet_values)
        nrows, ncols = 1, n_facets
    else:
        facet_values = [None]; n_facets = 1; nrows, ncols = 1, 1

    fig, axes = plt.subplots(
        nrows, ncols, figsize=(6 * ncols, 5 * nrows), 
        squeeze=False, sharex=True, sharey=True
    )
    axes_flat = axes.flatten()

    # --- ループ 1: グラフ要素の描画 ---
    for i, facet_value in enumerate(facet_values):
        ax = axes_flat[i]
        plot_data = data[data[facet] == facet_value] if facet_value is not None else data
        if facet_value is not None: ax.set_title(f'{facet_value}', fontsize=facet_title_size)

        sns.barplot(data=plot_data, x=x, y=y, hue=hue, ax=ax, order=x_order, hue_order=hue_order, **kwargs)
        if individual_points:
            sns.stripplot(data=plot_data, x=x, y=y, hue=hue, dodge=True, ax=ax, order=x_order, hue_order=hue_order, **stripplot_kws)
        
        if hue:
            if ax.get_legend() is not None: ax.get_legend().remove()
            handles, labels = ax.get_legend_handles_labels()
            if individual_points:
                n_hue = len(hue_order) if hue_order else len(plot_data[hue].unique())
                handles, labels = handles[:n_hue], labels[:n_hue]
            ax.legend(handles, labels, loc=legend_loc, title=hue)
        
        # Spine延長のロジックをここから削除
        if facet and n_facets >= 4:
            ax.set_xlabel('')

    for i in range(n_facets, len(axes_flat)): axes_flat[i].set_visible(False)

    # --- ループ 2: 最終的なスタイリング調整 ---
    # 全グラフ描画後に、確定したy軸の高さを使ってSpineを延長する
    for ax in axes_flat:
        if not ax.get_visible(): continue # 非表示のaxはスキップ
            
        if despine_plot: sns.despine(ax=ax)
        
        ymin, ymax = ax.get_ylim()
        extension = (ymax - ymin) * 0.1
        ax.spines['left'].set_bounds(ymin - extension, ymax)
    
    if facet and n_facets >= 4:
        fig.supxlabel(x, y=0.04, fontsize=plt.rcParams['axes.labelsize'])
    
    fig.tight_layout()

    return (fig, axes[0, 0]) if nrows * ncols == 1 else (fig, axes)


'''
import pandas as pd
import numpy as np
import itertools

def create_symmetrical_data(samples_per_group=10):
    """
    カテゴリの組み合わせが均等な「左右対称」のサンプルデータを生成する。

    Parameters
    ----------
    samples_per_group : int, optional
        各カテゴリの組み合わせごとに生成するサンプル数 (default is 10)。

    Returns
    -------
    pd.DataFrame
        生成されたサンプルデータフレーム。
    """
    # 各変数のカテゴリを定義
    times = ['Lunch', 'Dinner']
    days = ['Thur', 'Fri', 'Sat', 'Sun']
    sexes = ['Male', 'Female']
    
    # カテゴリのすべての組み合わせを生成
    all_combinations = list(itertools.product(times, days, sexes))
    
    # データフレームを格納するリスト
    data_list = []
    
    # 各組み合わせに対してダミーデータを生成
    for time, day, sex in all_combinations:
        # 平均値に少し差をつけて、もっともらしいグラフになるように調整
        mean_value = 15  # 基礎となる平均値
        if time == 'Dinner': mean_value += 5
        if day in ['Sat', 'Sun']: mean_value += 8
        if sex == 'Male': mean_value += 2
            
        # 平均値周りの正規分布に従うランダムな値を生成
        values = np.random.normal(loc=mean_value, scale=4, size=samples_per_group)
        
        # 生成したデータをリストに追加
        for value in values:
            data_list.append({
                'time': time,
                'day': day,
                'sex': sex,
                'value': value
            })
            
    return pd.DataFrame(data_list)

# --- データの生成 ---
symmetrical_df = create_symmetrical_data(samples_per_group=15)
print("--- Symmetrical Data Head ---")
print(symmetrical_df.head())
print("\n--- Value counts for each category combination ---")
print(symmetrical_df.groupby(['time', 'day', 'sex']).size())

set_plot_style()
symmetrical_df = create_symmetrical_data()
# "time" でファセット (Lunch, Dinner の2つ)
fig, axes = plot_bar(data=symmetrical_df, x='day', y='value', hue='sex', individual_points=True)

plt.show()


# "day" でファセット (Thur, Fri, Sat, Sun の4つ)
fig, axes = plot_bar(data=symmetrical_df, x='sex', y='value', facet='day')
plt.show()
'''