from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


def save_fig(path, dpi=180):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=dpi)
    plt.close()


def plot_metric_bar(df, x, y, hue, title, ylabel, path):
    plt.figure(figsize=(12, 5.5))
    sns.barplot(data=df, x=x, y=y, hue=hue)
    plt.title(title)
    plt.ylabel(ylabel)
    save_fig(path)
