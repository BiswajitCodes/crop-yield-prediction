"""Matplotlib charts (static images rendered by Streamlit). All functions return a Figure."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config

C = config.CHART_COLORS
plt.rcParams.update({
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#9db3a7",
    "axes.labelcolor": "#26463a", "xtick.color": "#26463a", "ytick.color": "#26463a",
    "axes.titleweight": "bold", "axes.titlecolor": "#12352a", "figure.facecolor": "white",
    "axes.facecolor": "white", "axes.grid": True, "grid.color": "#edf3ef",
})


def _fig(w=6.4, h=3.8):
    fig, ax = plt.subplots(figsize=(w, h), dpi=110)
    ax.set_axisbelow(True)
    return fig, ax


def bar_by_category(series: pd.Series, title: str, ylabel: str, horizontal: bool = False, counts: pd.Series | None = None):
    fig, ax = _fig(6.8, max(3.6, 0.32 * len(series) + 1.2) if horizontal else 3.8)
    colors = [C[i % len(C)] for i in range(len(series))]
    if horizontal:
        bars = ax.barh(series.index.astype(str)[::-1], series.values[::-1], color=colors[::-1])
        ax.set_xlabel(ylabel)
        for b, v in zip(bars, series.values[::-1]):
            ax.text(b.get_width(), b.get_y() + b.get_height() / 2, f" {v:,.2f}", va="center", fontsize=8)
        ax.grid(axis="y", visible=False)
    else:
        bars = ax.bar(series.index.astype(str), series.values, color=colors)
        ax.set_ylabel(ylabel)
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        for b, v in zip(bars, series.values):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{v:,.2f}", ha="center", va="bottom", fontsize=8)
        ax.grid(axis="x", visible=False)
    ax.set_title(title)
    fig.tight_layout()
    return fig


def histogram(values: pd.Series, title: str, xlabel: str):
    fig, ax = _fig()
    bins = int(min(30, max(5, np.sqrt(len(values)))))
    ax.hist(values, bins=bins, color=C[0], edgecolor="white")
    ax.axvline(values.median(), color="#0b3d2e", ls="--", lw=1.2, label=f"median {values.median():,.2f}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of records")
    ax.set_title(title)
    ax.legend(frameon=False)
    fig.tight_layout()
    return fig


def boxplot(groups: dict[str, pd.Series], title: str, ylabel: str):
    fig, ax = _fig(6.8, 3.9)
    labels = [f"{k}\n(n={len(v)})" for k, v in groups.items()]
    bp = ax.boxplot(list(groups.values()), patch_artist=True, medianprops={"color": "#0b3d2e"})
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    for patch, col in zip(bp["boxes"], C * 3):
        patch.set_facecolor(col)
        patch.set_alpha(.75)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    return fig


def scatter(x: pd.Series, y: pd.Series, title: str, xlabel: str, ylabel: str):
    fig, ax = _fig()
    ax.scatter(x, y, s=14, alpha=.45, color=C[0], edgecolor="none")
    if len(x) >= 10 and x.nunique() > 3:
        try:
            m, b = np.polyfit(x, y, 1)
            xs = np.linspace(x.min(), x.max(), 50)
            ax.plot(xs, m * xs + b, color="#e8605d", lw=1.8, label="straight-line trend")
            ax.legend(frameon=False)
        except Exception:
            pass
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    return fig


def line(x, y, title: str, xlabel: str, ylabel: str):
    fig, ax = _fig()
    ax.plot(x, y, color=C[0], lw=2, marker="o", ms=4)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    return fig


def spearman(x: pd.Series, y: pd.Series) -> float | None:
    if len(x) < 10 or x.nunique() < 3 or y.nunique() < 3:
        return None
    v = x.rank().corr(y.rank())
    return None if pd.isna(v) else float(v)
