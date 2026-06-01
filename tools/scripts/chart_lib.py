#!/usr/bin/env python3
"""Chart Library — factory of all chart types using matplotlib/seaborn/networkx."""

import os, re, json, time, math
from datetime import datetime as dt

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

_seaborn_ok = False
try:
    import seaborn as sns
    _seaborn_ok = True
except ImportError:
    pass

_networkx_ok = False
try:
    import networkx as nx
    _networkx_ok = True
except ImportError:
    pass

_scipy_ok = False
try:
    import scipy.cluster.hierarchy as sch
    import scipy.stats as stats
    _scipy_ok = True
except ImportError:
    pass

try:
    from matplotlib_venn import venn2, venn3
    _venn_ok = True
except ImportError:
    _venn_ok = False

try:
    import squarify
    _squarify_ok = True
except ImportError:
    _squarify_ok = False

try:
    from wordcloud import WordCloud
    _wordcloud_ok = True
except ImportError:
    _wordcloud_ok = False

# ─── helpers ────────────────────────────────────────────────────

_DARK = "#1a1a2e"
_LIGHT = "#e0e0e0"
_GREEN = "#16a34a"
_RED = "#dc2626"
_PURPLE = "#9333ea"
_GRAY = "#888"


def _setup_ax(ax, title="", xlabel="", ylabel="", dark=True):
    if dark:
        ax.set_facecolor(_DARK)
        ax.tick_params(colors=_GRAY, labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#444")
        ax.spines["bottom"].set_color("#444")
        ax.grid(True, color="#333", linewidth=0.5, alpha=0.5)
    ax.set_title(title, color=_LIGHT, fontsize=11, pad=10)
    ax.set_xlabel(xlabel, color=_GRAY, fontsize=9)
    ax.set_ylabel(ylabel, color=_GRAY, fontsize=9)


def _fig(wide=False):
    w, h = (10, 5) if wide else (7, 4)
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(_DARK)
    return fig, ax


def _save(fig, path, dpi=130):
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=_DARK)
    plt.close(fig)
    return path


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


def _len(x):
    return len(x) if hasattr(x, '__len__') else 0


# ═══════════════════════════════════════════════════════════════════
# CHART GENERATORS
# ═══════════════════════════════════════════════════════════════════

def line(data: dict, output_path: str, **kw) -> str:
    """Line chart with conditional color segments."""
    points = data.get("chart", [])
    s = data.get("summary", {})
    if _len(points) == 0:
        return _placeholder(output_path, "No data")
    dates = [p["date"] for p in points]
    vals = [p["deviation_percent"] for p in points]
    prof = [p.get("profitable", False) for p in points]
    fig, ax = _fig()
    for i in range(1, len(points)):
        c = _GREEN if prof[i] else _RED
        ax.plot(dates[i - 1 : i + 1], vals[i - 1 : i + 1], color=c, lw=2)
    for i in range(len(points)):
        c = _GREEN if prof[i] else _RED
        ax.scatter(dates[i], vals[i], color=c, s=18, zorder=5)
    ax.axhline(0, color=_PURPLE, ls="--", lw=1)
    ax.text(dates[0], 0, " Entry", color=_PURPLE, fontsize=8, va="bottom")
    _setup_ax(ax,
        title=f"{s.get('symbol','?')}  |  Entry: {s.get('entry_price','?')} → {s.get('current_price','?')}",
        ylabel="%")
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    _auto_ylim(ax, vals)
    return _save(fig, output_path)


def bar(data: dict, output_path: str, **kw) -> str:
    """Bar chart — values per category."""
    cats = data.get("categories", [])
    vals = data.get("values", [])
    if _len(cats) == 0:
        return _placeholder(output_path, "No categories")
    fig, ax = _fig()
    colors = [_GREEN if v >= 0 else _RED for v in vals]
    bars = ax.bar(range(len(cats)), vals, color=colors, width=0.6)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels(cats, rotation=30, ha="right", fontsize=8, color=_GRAY)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + (0.5 if v >= 0 else -1),
                f"{v:.2f}", ha="center", va="bottom" if v >= 0 else "top",
                fontsize=7, color=_GRAY)
    _setup_ax(ax, title=data.get("title", "Bar Chart"), ylabel=data.get("ylabel", ""))
    return _save(fig, output_path)


def grouped_bar(data: dict, output_path: str, **kw) -> str:
    """Grouped bar chart."""
    groups = data.get("groups", [])
    subgroups = data.get("subgroups", [])
    values = data.get("values", [])
    if _len(groups) == 0 or _len(subgroups) == 0:
        return _placeholder(output_path, "No data")
    x = np.arange(len(groups))
    n = len(subgroups)
    w = 0.8 / n
    fig, ax = _fig(wide=True)
    pal = plt.cm.Set2(np.linspace(0, 1, n))
    for i, sg in enumerate(subgroups):
        ax.bar(x + i * w - 0.4 + w / 2, [v[i] for v in values], w, label=sg, color=pal[i])
    ax.set_xticks(x)
    ax.set_xticklabels(groups, rotation=30, ha="right", fontsize=8, color=_GRAY)
    ax.legend(fontsize=8, labelcolor=_GRAY)
    _setup_ax(ax, title=data.get("title", "Grouped Bar Chart"))
    return _save(fig, output_path)


def stacked_bar(data: dict, output_path: str, **kw) -> str:
    """Stacked bar chart."""
    cats = data.get("categories", [])
    groups = data.get("groups", [])
    values = data.get("values", [])
    if _len(cats) == 0 or _len(groups) == 0:
        return _placeholder(output_path, "No data")
    x = np.arange(len(cats))
    fig, ax = _fig(wide=True)
    pal = plt.cm.Set2(np.linspace(0, 1, len(groups)))
    bottom = np.zeros(len(cats))
    for i, g in enumerate(groups):
        ax.bar(x, [v[i] for v in values], 0.6, bottom=bottom, label=g, color=pal[i])
        bottom += np.array([v[i] for v in values])
    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=30, ha="right", fontsize=8, color=_GRAY)
    ax.legend(fontsize=8, labelcolor=_GRAY)
    _setup_ax(ax, title=data.get("title", "Stacked Bar Chart"))
    return _save(fig, output_path)


def boxplot(data: dict, output_path: str, **kw) -> str:
    """Box plot."""
    groups = data.get("groups", {})
    if _len(groups) == 0:
        return _placeholder(output_path, "No data")
    fig, ax = _fig()
    labels, datasets = list(groups.keys()), list(groups.values())
    bp = ax.boxplot(datasets, tick_labels=labels, patch_artist=True, widths=0.5)
    pal = plt.cm.Set2(np.linspace(0, 1, len(labels)))
    for patch, color in zip(bp["boxes"], pal):
        patch.set_facecolor(color)
    for flier in bp["fliers"]:
        flier.set(marker="o", markersize=4, alpha=0.5)
    _setup_ax(ax, title=data.get("title", "Box Plot"), ylabel=data.get("ylabel", ""))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=20, ha="right")
    return _save(fig, output_path)


def violin(data: dict, output_path: str, **kw) -> str:
    """Violin plot."""
    groups = data.get("groups", {})
    if _len(groups) == 0:
        return _placeholder(output_path, "No data")
    if _seaborn_ok:
        df = pd.DataFrame({k: pd.Series(v) for k, v in groups.items()})
        melted = df.melt(var_name="group", value_name="value")
        fig, ax = _fig()
        sns.violinplot(data=melted, x="group", y="value", ax=ax, palette="Set2", inner="box")
        _setup_ax(ax, title=data.get("title", "Violin Plot"), ylabel=data.get("ylabel", ""))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=20, ha="right")
        return _save(fig, output_path)
    labels, datasets = list(groups.keys()), list(groups.values())
    fig, ax = _fig()
    parts = ax.violinplot(datasets, positions=range(1, len(labels) + 1), showmedians=True)
    for pc in parts["bodies"]:
        pc.set_facecolor(_PURPLE)
        pc.set_alpha(0.6)
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8, color=_GRAY)
    _setup_ax(ax, title=data.get("title", "Violin Plot"), ylabel=data.get("ylabel", ""))
    return _save(fig, output_path)


def bubble(data: dict, output_path: str, **kw) -> str:
    """Bubble chart: x, y, size, optional color."""
    x = data.get("x", [])
    y = data.get("y", [])
    s = data.get("size", [30] * len(x))
    c = data.get("color", None)
    labels = data.get("labels", [])
    if _len(x) == 0:
        return _placeholder(output_path, "No data")
    fig, ax = _fig(wide=True)
    sizes = [_clamp(v * 80 / max(s), 10, 800) if max(s) > 0 else 30 for v in s]
    sc = ax.scatter(x, y, s=sizes, c=c if c else _PURPLE, alpha=0.7, edgecolors="white", linewidth=0.5)
    if labels:
        for xi, yi, li in zip(x, y, labels):
            ax.text(xi, yi, li, fontsize=6, ha="center", va="center", color="white")
    _setup_ax(ax, title=data.get("title", "Bubble Chart"), xlabel=data.get("xlabel", ""), ylabel=data.get("ylabel", ""))
    return _save(fig, output_path)


def scatter(data: dict, output_path: str, **kw) -> str:
    """Scatter plot."""
    x = data.get("x", [])
    y = data.get("y", [])
    c = data.get("color", None)
    labels = data.get("labels", [])
    if _len(x) == 0:
        return _placeholder(output_path, "No data")
    fig, ax = _fig()
    ax.scatter(x, y, c=c if c else _PURPLE, s=20, alpha=0.7)
    if labels:
        for xi, yi, li in zip(x, y, labels):
            ax.text(xi, yi, li, fontsize=7, ha="left", va="bottom", color=_GRAY)
    _setup_ax(ax, title=data.get("title", "Scatter Plot"), xlabel=data.get("xlabel", ""), ylabel=data.get("ylabel", ""))
    return _save(fig, output_path)


def histogram(data: dict, output_path: str, **kw) -> str:
    """Histogram."""
    values = data.get("values", [])
    if values is None or len(values) == 0:
        return _placeholder(output_path, "No data")
    bins = data.get("bins", "auto")
    fig, ax = _fig()
    n, bins_edges, patches = ax.hist(values, bins=bins, color=_PURPLE, alpha=0.7, edgecolor="white", linewidth=0.5)
    _setup_ax(ax, title=data.get("title", "Histogram"), xlabel=data.get("xlabel", "Value"), ylabel="Frequency")
    return _save(fig, output_path)


def density(data: dict, output_path: str, **kw) -> str:
    """Density plot (KDE)."""
    groups = data.get("groups", {})
    if _len(groups) == 0:
        return _placeholder(output_path, "No data")
    fig, ax = _fig()
    if _seaborn_ok:
        df = pd.DataFrame({k: pd.Series(v) for k, v in groups.items()})
        melted = df.melt(var_name="group", value_name="value")
        sns.kdeplot(data=melted, x="value", hue="group", ax=ax, palette="Set2", fill=True, alpha=0.3)
    else:
        pal = plt.cm.Set2(np.linspace(0, 1, len(groups)))
        for (label, vals), color in zip(groups.items(), pal):
            kde = stats.gaussian_kde(vals)
            xs = np.linspace(min(vals), max(vals), 200)
            ax.plot(xs, kde(xs), label=label, color=color, lw=2)
            ax.fill_between(xs, kde(xs), alpha=0.2, color=color)
        ax.legend(fontsize=8, labelcolor=_GRAY)
    _setup_ax(ax, title=data.get("title", "Density Plot"), xlabel=data.get("xlabel", "Value"), ylabel="Density")
    return _save(fig, output_path)


def heatmap(data: dict, output_path: str, **kw) -> str:
    """Heatmap from 2D array."""
    matrix = data.get("matrix", [])
    row_labels = data.get("row_labels", [])
    col_labels = data.get("col_labels", [])
    if not matrix:
        return _placeholder(output_path, "No data")
    arr = np.array(matrix)
    fig, ax = _fig(wide=True)
    im = ax.imshow(arr, cmap=data.get("cmap", "RdBu_r"), aspect="auto")
    fig.colorbar(im, ax=ax, shrink=0.7)
    if row_labels:
        ax.set_yticks(range(len(row_labels)))
        ax.set_yticklabels(row_labels, fontsize=7, color=_GRAY)
    if col_labels:
        ax.set_xticks(range(len(col_labels)))
        ax.set_xticklabels(col_labels, rotation=30, ha="right", fontsize=7, color=_GRAY)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            v = arr[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6, color="white" if abs(v) > 0.5 else "black")
    _setup_ax(ax, title=data.get("title", "Heatmap"))
    return _save(fig, output_path)


def correlogram(data: dict, output_path: str, **kw) -> str:
    """Correlation matrix plot."""
    return heatmap(data, output_path, **kw)


def pie(data: dict, output_path: str, **kw) -> str:
    """Pie / Donut chart."""
    labels = data.get("labels", [])
    values = data.get("values", [])
    if _len(labels) == 0:
        return _placeholder(output_path, "No data")
    donut = data.get("donut", True)
    fig, ax = _fig()
    colors = [plt.cm.Set2(i % 10) for i in range(len(labels))]
    wedges, texts, autotexts = ax.pie(values, labels=labels, autopct="%1.1f%%",
                                        colors=colors, startangle=90,
                                        wedgeprops=dict(width=0.4) if donut else None)
    for t in texts + autotexts:
        t.set_fontsize(8)
        t.set_color(_GRAY)
    _setup_ax(ax, title=data.get("title", "Pie Chart"))
    return _save(fig, output_path)


def circular_bar(data: dict, output_path: str, **kw) -> str:
    """Circular (polar) bar chart."""
    labels = data.get("labels", [])
    values = data.get("values", [])
    if _len(labels) == 0:
        return _placeholder(output_path, "No data")
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    values_norm = np.array(values)
    if values_norm.max() > 0:
        values_norm = values_norm / values_norm.max() * 100
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(_DARK)
    ax.set_facecolor(_DARK)
    colors = [_GREEN if v >= 0 else _RED for v in values]
    bars = ax.bar(angles, values_norm, width=2 * np.pi / n * 0.8, bottom=0, color=colors, alpha=0.8)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=7, color=_GRAY)
    ax.tick_params(colors=_GRAY)
    ax.set_title(data.get("title", "Circular Bar Chart"), color=_LIGHT, fontsize=11, pad=15)
    ax.spines["polar"].set_color("#444")
    return _save(fig, output_path)


def radar(data: dict, output_path: str, **kw) -> str:
    """Radar / Spider chart."""
    categories = data.get("categories", [])
    series = data.get("series", [])
    if _len(categories) == 0 or _len(series) == 0:
        return _placeholder(output_path, "No data")
    n = len(categories)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(_DARK)
    ax.set_facecolor(_DARK)
    pal = plt.cm.tab10(np.linspace(0, 1, len(series)))
    for i, s in enumerate(series):
        vals = s.get("values", [])
        vals += vals[:1]
        ax.plot(angles, vals, "o-", color=pal[i], lw=2, label=s.get("name", f"Series {i}"))
        ax.fill(angles, vals, alpha=0.1, color=pal[i])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=8, color=_GRAY)
    ax.tick_params(colors=_GRAY, labelsize=7)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8, labelcolor=_GRAY)
    ax.set_title(data.get("title", "Radar Chart"), color=_LIGHT, fontsize=11, pad=15)
    ax.spines["polar"].set_color("#444")
    return _save(fig, output_path)


def lollipop(data: dict, output_path: str, **kw) -> str:
    """Lollipop chart."""
    cats = data.get("categories", [])
    vals = data.get("values", [])
    if _len(cats) == 0:
        return _placeholder(output_path, "No data")
    fig, ax = _fig()
    colors = [_GREEN if v >= 0 else _RED for v in vals]
    ax.stem(range(len(cats)), vals, basefmt=" ", linefmt="gray", markerfmt=" ")
    ax.scatter(range(len(cats)), vals, color=colors, s=40, zorder=5)
    ax.axhline(0, color=_PURPLE, ls="--", lw=0.8)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels(cats, rotation=30, ha="right", fontsize=8, color=_GRAY)
    _setup_ax(ax, title=data.get("title", "Lollipop Chart"), ylabel=data.get("ylabel", ""))
    return _save(fig, output_path)


def histogram2d(data: dict, output_path: str, **kw) -> str:
    """2D Histogram / Hexbin."""
    x = data.get("x", [])
    y = data.get("y", [])
    if _len(x) == 0:
        return _placeholder(output_path, "No data")
    kind = data.get("kind", "hexbin")
    fig, ax = _fig()
    if kind == "hexbin":
        ax.hexbin(x, y, gridsize=data.get("gridsize", 20), cmap="viridis", mincnt=1)
        fig.colorbar(ax.collections[0], ax=ax, shrink=0.7)
    else:
        ax.hist2d(x, y, bins=data.get("bins", 20), cmap="viridis")
        fig.colorbar(ax.collections[0], ax=ax, shrink=0.7)
    _setup_ax(ax, title=data.get("title", "2D Histogram"), xlabel=data.get("xlabel", ""), ylabel=data.get("ylabel", ""))
    return _save(fig, output_path)


def dendrogram(data: dict, output_path: str, **kw) -> str:
    """Hierarchical clustering dendrogram."""
    matrix = data.get("matrix", [])
    labels = data.get("labels", [])
    if _len(matrix) == 0 or not _scipy_ok:
        return _placeholder(output_path, "No data / scipy not available")
    arr = np.array(matrix)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    linkage = sch.linkage(arr, method=data.get("method", "ward"))
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(_DARK)
    ax.set_facecolor(_DARK)
    sch.dendrogram(linkage, labels=labels, ax=ax, leaf_font_size=8,
                   color_threshold=0.7 * max(linkage[:, 2]))
    ax.tick_params(colors=_GRAY, labelsize=8)
    ax.set_title(data.get("title", "Dendrogram"), color=_LIGHT, fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#444")
    ax.spines["bottom"].set_color("#444")
    ax.set_ylabel("Distance", color=_GRAY, fontsize=9)
    return _save(fig, output_path)


def network(data: dict, output_path: str, **kw) -> str:
    """Network graph."""
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    if not nodes or not _networkx_ok:
        return _placeholder(output_path, "No data / networkx not available")
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor(_DARK)
    ax.set_facecolor(_DARK)
    pos = nx.spring_layout(G, seed=42, k=0.5)
    node_sizes = data.get("node_sizes", [300] * len(nodes))
    node_colors = data.get("node_colors", [_PURPLE] * len(nodes))
    nx.draw(G, pos, ax=ax, with_labels=True, font_size=7, font_color=_GRAY,
            node_size=node_sizes, node_color=node_colors,
            edge_color="#555", width=0.5, alpha=0.8)
    ax.set_title(data.get("title", "Network Graph"), color=_LIGHT, fontsize=11)
    ax.axis("off")
    return _save(fig, output_path)


def parallel_coords(data: dict, output_path: str, **kw) -> str:
    """Parallel coordinates."""
    df = data.get("dataframe", None)
    class_col = data.get("class_column", None)
    if df is not None:
        fig, ax = _fig(wide=True)
        pd.plotting.parallel_coordinates(df, class_column=class_col or df.columns[0], ax=ax, color=plt.cm.Set2)
    else:
        values = data.get("values", [])
        cats = data.get("categories", [])
        if not values:
            return _placeholder(output_path, "No data")
        fig, ax = _fig(wide=True)
        arr = np.array(values)
        for row in arr:
            ax.plot(range(len(cats)), row, alpha=0.3, color=_PURPLE, lw=0.8)
        ax.set_xticks(range(len(cats)))
        ax.set_xticklabels(cats, fontsize=7, color=_GRAY)
    _setup_ax(ax, title=data.get("title", "Parallel Coordinates"))
    return _save(fig, output_path)


def ridgeline(data: dict, output_path: str, **kw) -> str:
    """Ridgeline plot (joyplot)."""
    groups = data.get("groups", {})
    if _len(groups) == 0:
        return _placeholder(output_path, "No data")
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(_DARK)
    ax.set_facecolor(_DARK)
    pal = plt.cm.Set2(np.linspace(0, 1, len(groups)))
    labels = list(groups.keys())
    offset = 0
    gap = data.get("gap", 0.5)
    for i, (label, vals) in enumerate(reversed(list(groups.items()))):
        if _scipy_ok:
            kde = stats.gaussian_kde(vals)
            xs = np.linspace(min(vals), max(vals), 200)
            ys = kde(xs)
        else:
            ys, bin_edges = np.histogram(vals, bins=30, density=True)
            xs = (bin_edges[:-1] + bin_edges[1:]) / 2
        ax.fill_between(xs, ys + offset, offset, alpha=0.7, color=pal[len(labels) - 1 - i])
        ax.plot(xs, ys + offset, color=pal[len(labels) - 1 - i], lw=1)
        ax.text(xs[0], offset + max(ys) * 0.5, label, fontsize=8, color=_GRAY, va="center")
        offset += gap + max(ys)
    ax.set_yticks([])
    _setup_ax(ax, title=data.get("title", "Ridgeline Plot"), xlabel=data.get("xlabel", "Value"))
    return _save(fig, output_path)


def stream(data: dict, output_path: str, **kw) -> str:
    """Stream chart / stacked area."""
    x = data.get("x", [])
    layers = data.get("layers", [])
    if _len(x) == 0 or _len(layers) == 0:
        return _placeholder(output_path, "No data")
    fig, ax = _fig(wide=True)
    pal = plt.cm.Set2(np.linspace(0, 1, len(layers)))
    arr = np.array(layers)
    ax.stackplot(x, arr, labels=data.get("labels", []), colors=pal, alpha=0.8)
    if data.get("labels"):
        ax.legend(fontsize=8, labelcolor=_GRAY, loc="upper left")
    _setup_ax(ax, title=data.get("title", "Stream Chart"), xlabel=data.get("xlabel", ""), ylabel=data.get("ylabel", ""))
    return _save(fig, output_path)


def treemap(data: dict, output_path: str, **kw) -> str:
    """Treemap."""
    labels = data.get("labels", [])
    sizes = data.get("sizes", [])
    if not labels or not _squarify_ok:
        return _placeholder(output_path, "No data / squarify not available")
    colors = [plt.cm.Set2(i % 10) for i in range(len(labels))]
    fig, ax = _fig(wide=True)
    squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.8, ax=ax)
    ax.axis("off")
    ax.set_title(data.get("title", "Treemap"), color=_LIGHT, fontsize=11)
    return _save(fig, output_path)


def venn(data: dict, output_path: str, **kw) -> str:
    """Venn diagram (2 or 3 sets)."""
    sets = data.get("sets", ())
    labels = data.get("labels", ())
    if not _venn_ok or _len(sets) < 2:
        return _placeholder(output_path, "Venn not available")
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor(_DARK)
    ax.set_facecolor(_DARK)
    if _len(sets) <= 3:
        v = venn2(subsets=sets, set_labels=labels, ax=ax)
    elif _len(sets) <= 7:
        v = venn3(subsets=sets, set_labels=labels, ax=ax)
    else:
        return _placeholder(output_path, "Venn needs 2 or 3 sets")
    for text in ax.texts:
        text.set_color(_LIGHT)
        text.set_fontsize(8)
    ax.set_title(data.get("title", "Venn Diagram"), color=_LIGHT, fontsize=11)
    return _save(fig, output_path)


def wordcloud(data: dict, output_path: str, **kw) -> str:
    """Word cloud."""
    text = data.get("text", "")
    if not text or not _wordcloud_ok:
        return _placeholder(output_path, "No text / wordcloud not available")
    wc = WordCloud(width=800, height=400, background_color=_DARK,
                   colormap="Set2", max_words=data.get("max_words", 100))
    wc.generate(text)
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(_DARK)
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(data.get("title", "Word Cloud"), color=_LIGHT, fontsize=11)
    return _save(fig, output_path)


def scatter3d(data: dict, output_path: str, **kw) -> str:
    """3D Scatter plot."""
    x = data.get("x", [])
    y = data.get("y", [])
    z = data.get("z", [])
    if _len(x) == 0:
        return _placeholder(output_path, "No data")
    fig = plt.figure(figsize=(8, 6))
    fig.patch.set_facecolor(_DARK)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(_DARK)
    ax.scatter(x, y, z, c=data.get("color", _PURPLE), s=20, alpha=0.7)
    ax.set_title(data.get("title", "3D Scatter"), color=_LIGHT, fontsize=11)
    ax.tick_params(colors=_GRAY, labelsize=7)
    ax.xaxis.pane.set_facecolor(_DARK)
    ax.yaxis.pane.set_facecolor(_DARK)
    ax.zaxis.pane.set_facecolor(_DARK)
    ax.xaxis.pane.set_edgecolor("#444")
    ax.yaxis.pane.set_edgecolor("#444")
    ax.zaxis.pane.set_edgecolor("#444")
    return _save(fig, output_path)


def scatter_matrix(data: dict, output_path: str, **kw) -> str:
    """Scatter plot matrix (pairs plot)."""
    df = data.get("dataframe", None)
    if df is not None:
        fig, ax = _fig(wide=True)
        pd.plotting.scatter_matrix(df, ax=ax, alpha=0.5, figsize=(8, 8), diagonal="hist")
        return _save(fig, output_path)
    columns = data.get("columns", [])
    values = data.get("values", [])
    if _len(columns) == 0 or _len(values) == 0:
        return _placeholder(output_path, "No data")
    df = pd.DataFrame(values, columns=columns)
    fig, axes = plt.subplots(len(columns), len(columns), figsize=(9, 9))
    fig.patch.set_facecolor(_DARK)
    for i, ci in enumerate(columns):
        for j, cj in enumerate(columns):
            ax = axes[i, j]
            ax.set_facecolor(_DARK)
            if i == j:
                ax.hist(df[ci], color=_PURPLE, alpha=0.6)
            else:
                ax.scatter(df[cj], df[ci], color=_PURPLE, s=5, alpha=0.5)
            if i == len(columns) - 1:
                ax.set_xlabel(cj, fontsize=6, color=_GRAY)
            if j == 0:
                ax.set_ylabel(ci, fontsize=6, color=_GRAY)
            ax.tick_params(colors=_GRAY, labelsize=5)
    fig.suptitle(data.get("title", "Scatter Matrix"), color=_LIGHT, fontsize=12)
    return _save(fig, output_path)


# ─── helpers ────────────────────────────────────────────────────

def _auto_ylim(ax, vals, margin=0.15):
    lo, hi = min(vals), max(vals)
    if hi - lo < 1:
        lo, hi = -1, 1
    rng = hi - lo
    ax.set_ylim(lo - rng * margin, hi + rng * margin)


def _placeholder(path, msg="No data"):
    fig, ax = _fig()
    ax.text(0.5, 0.5, msg, ha="center", va="center", color=_GRAY, fontsize=14,
            transform=ax.transAxes)
    _setup_ax(ax, title="Placeholder")
    return _save(fig, path)


# ─── factory ────────────────────────────────────────────────────

CHART_TYPES = {
    "line": line,
    "bar": bar,
    "grouped_bar": grouped_bar,
    "stacked_bar": stacked_bar,
    "boxplot": boxplot,
    "violin": violin,
    "bubble": bubble,
    "scatter": scatter,
    "histogram": histogram,
    "density": density,
    "heatmap": heatmap,
    "correlogram": correlogram,
    "pie": pie,
    "circular_bar": circular_bar,
    "radar": radar,
    "lollipop": lollipop,
    "histogram2d": histogram2d,
    "dendrogram": dendrogram,
    "network": network,
    "parallel_coords": parallel_coords,
    "ridgeline": ridgeline,
    "stream": stream,
    "treemap": treemap,
    "venn": venn,
    "wordcloud": wordcloud,
    "scatter3d": scatter3d,
    "scatter_matrix": scatter_matrix,
}


def list_types() -> list[str]:
    return sorted(CHART_TYPES.keys())


def generate(chart_type: str, data: dict, output_path: str, **kw) -> str:
    """Generate a chart. Returns path to PNG."""
    fn = CHART_TYPES.get(chart_type)
    if not fn:
        available = ", ".join(list_types())
        raise ValueError(f"Unknown chart type: {chart_type}. Available: {available}")
    return fn(data, output_path, **kw)


def test_all(output_dir: str = "/tmp/chart_tests"):
    """Generate test images for all chart types."""
    os.makedirs(output_dir, exist_ok=True)
    results = {}
    for ct in list_types():
        data = _test_data(ct)
        path = os.path.join(output_dir, f"{ct}.png")
        try:
            generate(ct, data, path)
            results[ct] = "OK"
        except Exception as e:
            results[ct] = f"FAIL: {e}"
    return results


def _test_data(ct: str) -> dict:
    """Return test data for a chart type."""
    base = {"title": f"Test {ct}"}
    if ct == "line":
        base.update({
            "chart": [
                {"date": "2026-01-01", "deviation_percent": -2.3, "profitable": False},
                {"date": "2026-01-02", "deviation_percent": -1.1, "profitable": False},
                {"date": "2026-01-03", "deviation_percent": 0.5, "profitable": True},
                {"date": "2026-01-04", "deviation_percent": 3.2, "profitable": True},
                {"date": "2026-01-05", "deviation_percent": 1.8, "profitable": True},
                {"date": "2026-01-06", "deviation_percent": -0.7, "profitable": False},
            ],
            "summary": {"symbol": "BTC", "entry_price": 50000, "current_price": 51000}
        })
    elif ct in ("bar", "lollipop"):
        base.update({"categories": ["BTC", "ETH", "SOL", "ADA", "XRP"], "values": [5.2, -2.1, 3.8, -1.5, 4.0], "ylabel": "PnL %"})
    elif ct in ("grouped_bar",):
        base.update({"groups": ["Q1", "Q2", "Q3"], "subgroups": ["BTC", "ETH", "SOL"], "values": [[10, 5, 3], [8, 6, 4], [12, 7, 2]]})
    elif ct in ("stacked_bar",):
        base.update({"categories": ["Jan", "Feb", "Mar"], "groups": ["A", "B", "C"], "values": [[3, 5, 2], [4, 3, 6], [2, 7, 4]]})
    elif ct in ("boxplot", "violin"):
        base.update({"groups": {"BTC": [1, 2, 3, 4, 5, -1, -2, 3], "ETH": [2, 3, 4, -1, -3, 2, 5], "SOL": [-1, 0, 1, 2, 3, -2]}, "ylabel": "Return %"})
    elif ct in ("bubble",):
        base.update({"x": [1, 2, 3, 4, 5], "y": [10, 20, 15, 30, 25], "size": [10, 40, 20, 60, 35], "labels": ["A", "B", "C", "D", "E"], "xlabel": "Risk", "ylabel": "Return"})
    elif ct in ("scatter", "histogram2d"):
        np.random.seed(42)
        base.update({"x": np.random.randn(50).tolist(), "y": (np.random.randn(50) * 1.5 + 0.5).tolist(), "xlabel": "X", "ylabel": "Y"})
    elif ct in ("histogram",):
        np.random.seed(42)
        base.update({"values": (np.random.randn(200) * 2 + 1).tolist(), "bins": 25, "xlabel": "Value"})
    elif ct in ("density", "ridgeline"):
        np.random.seed(42)
        base.update({"groups": {"A": np.random.randn(100).tolist(), "B": (np.random.randn(100) + 1).tolist(), "C": (np.random.randn(100) - 0.5).tolist()}, "xlabel": "Value"})
    elif ct in ("heatmap", "correlogram"):
        np.random.seed(42)
        mat = np.random.randn(5, 5)
        mat = (mat + mat.T) / 2
        np.fill_diagonal(mat, 1)
        base.update({"matrix": mat.tolist(), "row_labels": ["A", "B", "C", "D", "E"], "col_labels": ["A", "B", "C", "D", "E"]})
    elif ct in ("pie", "circular_bar"):
        base.update({"labels": ["BTC", "ETH", "SOL", "ADA", "XRP"], "values": [40, 25, 15, 12, 8]})
    elif ct in ("radar",):
        base.update({"categories": ["Speed", "Power", "Agility", "Defense", "Luck"],
                     "series": [{"name": "Char A", "values": [80, 60, 70, 50, 90]},
                                {"name": "Char B", "values": [50, 90, 60, 80, 40]}]})
    elif ct in ("dendrogram",):
        base.update({"matrix": [[1, 2], [2, 3], [3, 1], [5, 4], [6, 5], [7, 6]], "labels": ["A", "B", "C", "D", "E", "F"]})
    elif ct in ("network",):
        base.update({"nodes": ["A", "B", "C", "D", "E"], "edges": [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("A", "C"), ("B", "E")]})
    elif ct in ("parallel_coords",):
        base.update({"values": [[1, 2, 3], [4, 5, 6], [7, 8, 9], [2, 3, 1], [5, 4, 6]], "categories": ["X", "Y", "Z"]})
    elif ct in ("stream",):
        np.random.seed(42)
        x = list(range(10))
        layers = [np.random.rand(10) * 10 + i * 5 for i in range(4)]
        base.update({"x": x, "layers": layers, "labels": ["A", "B", "C", "D"]})
    elif ct in ("treemap",):
        base.update({"labels": ["BTC", "ETH", "SOL", "ADA", "XRP", "DOT"], "sizes": [45, 25, 15, 8, 5, 2]})
    elif ct in ("venn",):
        base.update({"sets": (10, 15, 5), "labels": ("A", "B", "AB")})
    elif ct in ("wordcloud",):
        base.update({"text": "python data science machine learning AI neural network deep learning chart visualization matplotlib seaborn plotly pandas numpy scipy", "max_words": 30})
    elif ct in ("scatter3d",):
        np.random.seed(42)
        base.update({"x": np.random.randn(30), "y": np.random.randn(30), "z": np.random.randn(30)})
    elif ct in ("scatter_matrix",):
        np.random.seed(42)
        cols, rows = 3, 50
        data_arr = np.random.randn(rows, cols) * 2 + np.arange(cols)
        base.update({"columns": ["A", "B", "C"],
                     "values": data_arr.tolist()})
    return base


if __name__ == "__main__":
    results = test_all()
    for k, v in results.items():
        status = "✅" if v == "OK" else "❌"
        print(f"{status} {k}: {v}")
