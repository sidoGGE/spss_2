"""📈 رسوم بيانية احترافية"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['figure.facecolor'] = 'white'

COLORS = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B", 
          "#6A994E", "#BC4B51", "#5D4E6D", "#8B5A3C", "#4A7C59"]

class Visualizer:
    def __init__(self, df: pd.DataFrame, output_dir: str = "output/figures"):
        self.df = df
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)

    def _save(self, fig, name: str) -> str:
        path = self.out / name
        fig.savefig(path, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        return str(path)

    def bar(self, var: str, title: str = None, name: str = "bar.png") -> str:
        counts = self.df[var].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(counts)), counts.values, color=COLORS[:len(counts)], edgecolor='white')
        ax.set_xticks(range(len(counts)))
        ax.set_xticklabels([str(l)[:25] for l in counts.index], rotation=30, ha='right')
        ax.set_ylabel('التكرار')
        ax.set_title(title or f'توزيع {var}', fontsize=14, fontweight='bold')
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h, f'{int(h)}', ha='center', va='bottom')
        plt.tight_layout()
        return self._save(fig, name)

    def pie(self, var: str, title: str = None, name: str = "pie.png") -> str:
        counts = self.df[var].value_counts()
        if len(counts) > 8:
            counts = counts.head(8)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(counts.values, labels=[str(l)[:20] for l in counts.index],
               autopct='%1.1f%%', colors=COLORS[:len(counts)], startangle=90)
        ax.set_title(title or f'توزيع {var}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        return self._save(fig, name)

    def hist(self, var: str, bins: int = 20, name: str = "hist.png") -> str:
        fig, ax = plt.subplots(figsize=(10, 6))
        data = self.df[var].dropna()
        ax.hist(data, bins=bins, color=COLORS[0], edgecolor='white', alpha=0.8, density=True)
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(data)
        x = np.linspace(data.min(), data.max(), 200)
        ax.plot(x, kde(x), color=COLORS[1], lw=2.5, label='KDE')
        ax.axvline(data.mean(), color='red', ls='--', lw=2, label=f'Mean={data.mean():.2f}')
        ax.set_xlabel(var)
        ax.set_ylabel('الكثافة')
        ax.set_title(f'توزيع {var}', fontsize=14, fontweight='bold')
        ax.legend()
        plt.tight_layout()
        return self._save(fig, name)

    def box(self, num_var: str, group_var: str = None, name: str = "box.png") -> str:
        fig, ax = plt.subplots(figsize=(10, 6))
        if group_var and group_var in self.df.columns:
            sns.boxplot(data=self.df, x=group_var, y=num_var, 
                       palette=COLORS[:self.df[group_var].nunique()], ax=ax)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')
        else:
            sns.boxplot(data=self.df, y=num_var, color=COLORS[0], ax=ax)
        ax.set_title(f'Box Plot: {num_var}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        return self._save(fig, name)

    def corr_heatmap(self, vars_list: List[str], name: str = "corr.png") -> str:
        valid = [v for v in vars_list if v in self.df.columns]
        corr = self.df[valid].corr()
        fig, ax = plt.subplots(figsize=(max(8, len(valid)), max(6, len(valid))))
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlBu_r', 
                   center=0, square=True, linewidths=1, ax=ax)
        ax.set_title('مصفوفة الارتباطات', fontsize=14, fontweight='bold')
        plt.tight_layout()
        return self._save(fig, name)

    def axes_compare(self, axes_data: Dict[str, Dict], name: str = "axes_compare.png") -> str:
        fig, ax = plt.subplots(figsize=(10, 6))
        names = list(axes_data.keys())
        means = [axes_data[k]['mean'] for k in names]
        stds = [axes_data[k]['std'] for k in names]
        bars = ax.barh(names, means, xerr=stds, color=COLORS[:len(names)], 
                      edgecolor='white', capsize=5)
        ax.axvline(3.0, color='red', ls='--', lw=2, label='μ = 3')
        ax.set_xlabel('المتوسط')
        ax.set_title('مقارنة متوسطات المحاور', fontsize=14, fontweight='bold')
        ax.legend()
        for i, (bar, m) in enumerate(zip(bars, means)):
            ax.text(m, i, f'  {m:.2f}', va='center', fontsize=11)
        plt.tight_layout()
        return self._save(fig, name)
