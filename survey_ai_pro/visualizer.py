"""📈 رسوم بيانية احترافية مع دعم RTL للعربية"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict
import arabic_reshaper
from bidi.algorithm import get_display
import warnings

warnings.filterwarnings('ignore')

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['figure.facecolor'] = 'white'

COLORS = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B",
          "#6A994E", "#BC4B51", "#5D4E6D", "#8B5A3C", "#4A7C59"]


def reshape_arabic(text: str) -> str:
    """إعادة تشكيل النص العربي وعكس اتجاهه للعرض الصحيح"""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)


def get_arabic_font():
    """البحث عن خط عربي في النظام"""
    font_paths = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\times.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/GeezaPro.ttc",
        "/Library/Fonts/Arial.ttf",
    ]

    for fp in font_paths:
        if Path(fp).exists():
            try:
                return fm.FontProperties(fname=fp)
            except:
                continue

    # تحميل خط Amiri
    font_dir = Path("fonts")
    font_file = font_dir / "Amiri-Regular.ttf"
    if font_file.exists():
        try:
            return fm.FontProperties(fname=str(font_file))
        except:
            pass

    return None


class Visualizer:
    def __init__(self, df: pd.DataFrame, output_dir: str = "output/figures"):
        self.df = df
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.arabic_font = get_arabic_font()

    def _arabic_text(self, text: str) -> str:
        """تحويل النص العربي للعرض الصحيح"""
        if self.arabic_font:
            return reshape_arabic(str(text))
        return str(text)

    def _save(self, fig, name: str) -> str:
        path = self.out / name
        fig.savefig(path, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        return str(path)

    def _set_arabic_labels(self, ax, title=None, xlabel=None, ylabel=None):
        """ضبط التسميات العربية"""
        if title:
            ax.set_title(self._arabic_text(title), fontsize=14, fontweight='bold',
                        fontproperties=self.arabic_font)
        if xlabel:
            ax.set_xlabel(self._arabic_text(xlabel), fontsize=11,
                         fontproperties=self.arabic_font)
        if ylabel:
            ax.set_ylabel(self._arabic_text(ylabel), fontsize=11,
                         fontproperties=self.arabic_font)

    def bar(self, var: str, title: str = None, name: str = "bar.png") -> str:
        counts = self.df[var].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(counts)), counts.values, color=COLORS[:len(counts)], edgecolor='white')
        ax.set_xticks(range(len(counts)))

        labels = [self._arabic_text(str(l)[:25]) for l in counts.index]
        ax.set_xticklabels(labels, rotation=30, ha='right', fontproperties=self.arabic_font)

        self._set_arabic_labels(ax, title=title or f'توزيع {var}', ylabel='التكرار')

        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h, f'{int(h)}',
                   ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        return self._save(fig, name)

    def pie(self, var: str, title: str = None, name: str = "pie.png") -> str:
        counts = self.df[var].value_counts()
        if len(counts) > 8:
            counts = counts.head(8)

        fig, ax = plt.subplots(figsize=(8, 8))
        labels = [self._arabic_text(str(l)[:20]) for l in counts.index]

        wedges, texts, autotexts = ax.pie(
            counts.values, labels=labels, autopct='%1.1f%%',
            colors=COLORS[:len(counts)], startangle=90,
            textprops={'fontproperties': self.arabic_font, 'fontsize': 10}
        )

        self._set_arabic_labels(ax, title=title or f'توزيع {var}')
        plt.tight_layout()
        return self._save(fig, name)

    def hist(self, var: str, bins: int = 20, name: str = "hist.png") -> str:
        fig, ax = plt.subplots(figsize=(10, 6))
        data = self.df[var].dropna()
        ax.hist(data, bins=bins, color=COLORS[0], edgecolor='white', alpha=0.8, density=True)

        from scipy.stats import gaussian_kde
        kde = gaussian_kde(data)
        x = np.linspace(data.min(), data.max(), 200)
        ax.plot(x, kde(x), color=COLORS[1], lw=2.5, label=self._arabic_text('KDE'))
        ax.axvline(data.mean(), color='red', ls='--', lw=2,
                  label=self._arabic_text(f'المتوسط={data.mean():.2f}'))

        self._set_arabic_labels(ax, title=f'توزيع {var}', xlabel=var, ylabel='الكثافة')
        ax.legend(prop=self.arabic_font)
        plt.tight_layout()
        return self._save(fig, name)

    def box(self, num_var: str, group_var: str = None, name: str = "box.png") -> str:
        fig, ax = plt.subplots(figsize=(10, 6))
        if group_var and group_var in self.df.columns:
            n_groups = self.df[group_var].nunique()
            sns.boxplot(data=self.df, x=group_var, y=num_var,
                       palette=COLORS[:n_groups], ax=ax)

            labels = [self._arabic_text(str(l)[:20]) for l in ax.get_xticklabels()]
            ax.set_xticklabels(labels, rotation=30, ha='right',
                             fontproperties=self.arabic_font)
        else:
            sns.boxplot(data=self.df, y=num_var, color=COLORS[0], ax=ax)

        self._set_arabic_labels(ax, title=f'Box Plot: {num_var}')
        plt.tight_layout()
        return self._save(fig, name)

    def corr_heatmap(self, vars_list: List[str], name: str = "corr.png") -> str:
        valid = [v for v in vars_list if v in self.df.columns]
        corr = self.df[valid].corr()

        fig, ax = plt.subplots(figsize=(max(8, len(valid)), max(6, len(valid))))
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

        sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlBu_r',
                   center=0, square=True, linewidths=1, ax=ax)

        self._set_arabic_labels(ax, title='مصفوفة الارتباطات')
        plt.tight_layout()
        return self._save(fig, name)

    def axes_compare(self, axes_data: Dict[str, Dict], name: str = "axes_compare.png") -> str:
        fig, ax = plt.subplots(figsize=(10, 6))
        names = list(axes_data.keys())
        means = [axes_data[k]['mean'] for k in names]
        stds = [axes_data[k]['std'] for k in names]

        # عكس الترتيب لعرض من الأعلى إلى الأسفل
        names = names[::-1]
        means = means[::-1]
        stds = stds[::-1]

        arabic_names = [self._arabic_text(n) for n in names]

        bars = ax.barh(arabic_names, means, xerr=stds, color=COLORS[:len(names)],
                      edgecolor='white', capsize=5)
        ax.axvline(3.0, color='red', ls='--', lw=2, label=self._arabic_text('μ = 3'))

        self._set_arabic_labels(ax, title='مقارنة متوسطات المحاور', xlabel='المتوسط')
        ax.legend(prop=self.arabic_font)

        for i, (bar, m) in enumerate(zip(bars, means)):
            ax.text(m, i, f' {m:.2f}', va='center', fontsize=11)

        plt.tight_layout()
        return self._save(fig, name)

    def item_analysis_chart(self, axis_name: str, item_stats: pd.DataFrame, name: str = None) -> str:
        """رسم بياني لتحليل البنود داخل محور"""
        if item_stats is None or item_stats.empty or 'المتوسط' not in item_stats.columns:
            return None

        if name is None:
            name = f"item_analysis_{axis_name}.png"

        fig, ax = plt.subplots(figsize=(12, 6))

        items = item_stats.index.astype(str).tolist()
        means = item_stats['المتوسط'].values

        arabic_items = [self._arabic_text(str(item)[:30]) for item in items]

        bars = ax.barh(arabic_items, means, color=COLORS[0], edgecolor='white')
        ax.axvline(3.0, color='red', ls='--', lw=2, label=self._arabic_text('μ = 3'))

        # تلوين البنود حسب المستوى
        for i, (bar, m) in enumerate(zip(bars, means)):
            if m >= 4.21:
                bar.set_color('#2E86AB')  # موافق بشدة
            elif m >= 3.41:
                bar.set_color('#6A994E')  # موافق
            elif m >= 2.61:
                bar.set_color('#F18F01')  # محايد
            elif m >= 1.81:
                bar.set_color('#C73E1D')  # غير موافق
            else:
                bar.set_color('#3B1F2B')  # غير موافق بشدة

            ax.text(m, i, f' {m:.2f}', va='center', fontsize=9)

        self._set_arabic_labels(ax, title=f'تحليل بنود محور {axis_name}', xlabel='المتوسط')
        ax.legend(prop=self.arabic_font)
        ax.set_xlim(1, 5)

        plt.tight_layout()
        return self._save(fig, name)

    def demographic_cross_tab(self, var1: str, var2: str, name: str = None) -> str:
        """رسم بياني للتقاطع الديموغرافي"""
        if name is None:
            name = f"crosstab_{var1}_{var2}.png"

        crosstab = pd.crosstab(self.df[var1], self.df[var2], normalize='index') * 100

        fig, ax = plt.subplots(figsize=(10, 6))
        crosstab.plot(kind='bar', ax=ax, color=COLORS[:len(crosstab.columns)],
                     edgecolor='white')

        labels = [self._arabic_text(str(l)[:20]) for l in ax.get_xticklabels()]
        ax.set_xticklabels(labels, rotation=30, ha='right', fontproperties=self.arabic_font)

        legend_labels = [self._arabic_text(str(l)[:20]) for l in crosstab.columns]
        ax.legend(legend_labels, prop=self.arabic_font, title=self._arabic_text(var2))

        self._set_arabic_labels(ax, title=f'التقاطع بين {var1} و {var2}', xlabel=var1, ylabel='النسبة %')

        plt.tight_layout()
        return self._save(fig, name)

    def likert_distribution(self, axis_name: str, variables: List[str], name: str = None) -> str:
        """رسم توزيع درجات ليكرت لبنود محور"""
        if name is None:
            name = f"likert_dist_{axis_name}.png"

        valid_vars = [v for v in variables if v in self.df.columns]
        if not valid_vars:
            return None

        fig, axes = plt.subplots(1, len(valid_vars), figsize=(4 * len(valid_vars), 5))
        if len(valid_vars) == 1:
            axes = [axes]

        for ax, var in zip(axes, valid_vars):
            counts = self.df[var].value_counts().sort_index()
            bars = ax.bar(range(len(counts)), counts.values, color=COLORS[:len(counts)])
            ax.set_xticks(range(len(counts)))
            ax.set_xticklabels([str(i) for i in counts.index], fontsize=9)
            ax.set_title(self._arabic_text(var[:30]), fontsize=10, fontproperties=self.arabic_font)
            ax.set_ylabel(self._arabic_text('التكرار'), fontproperties=self.arabic_font)

            for bar in bars:
                h = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., h, f'{int(h)}',
                       ha='center', va='bottom', fontsize=8)

        plt.suptitle(self._arabic_text(f'توزيع درجات ليكرت - {axis_name}'),
                    fontsize=14, fontweight='bold', fontproperties=self.arabic_font)
        plt.tight_layout()
        return self._save(fig, name)
