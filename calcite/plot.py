from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns


def set_plot_style() -> None:
    sns.set_theme(style="ticks")
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": "Arial",
            "axes.labelsize": 15,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    sns.set_palette(
        [
            "#BBBBBB",
            "#AA4499",
            "#332288",
            "#CC6677",
            "#882255",
            "#DDCC77",
            "#999933",
            "#88CCEE",
            "#44AA99",
            "#117733",
            "#EEEEEE",
        ]
    )
