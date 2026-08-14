"""🔬 محرك الإحصاء الوصفي والاستدلالي"""
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class AxisResult:
    name: str
    variables: List[str]
    overall_mean: float
    overall_std: float
    cronbach_alpha: Optional[float]
    item_stats: pd.DataFrame
    one_sample_tests: List[Dict]
    group_tests: List[Dict]
    correlation_matrix: Optional[pd.DataFrame]

class StatsEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.alpha = 0.05

    def analyze_axis(self, name: str, variables: List[str], 
                     group_var: Optional[str] = None, pop_mean: float = 3.0) -> AxisResult:
        valid_vars = [v for v in variables if v in self.df.columns]
        if not valid_vars:
            raise ValueError(f"لا يوجد متغيرات صالحة في المحور {name}")

        # إحصائيات المحور
        axis_data = self.df[valid_vars].mean(axis=1, skipna=True)
        overall_mean = round(axis_data.mean(), 3)
        overall_std = round(axis_data.std(), 3)

        # إحصائيات البنود
        item_stats = []
        for var in valid_vars:
            item_stats.append({
                'المتغير': var,
                'المتوسط': round(self.df[var].mean(), 3),
                'الانحراف المعياري': round(self.df[var].std(), 3),
                'الوسيط': round(self.df[var].median(), 3),
                'الحد الأدنى': self.df[var].min(),
                'الحد الأقصى': self.df[var].max(),
            })

        # Cronbach's Alpha
        alpha = self._cronbach_alpha(valid_vars)

        # One Sample T-Test
        one_sample_tests = []
        for var in valid_vars:
            try:
                ttest = self._one_sample_ttest(var, pop_mean)
                one_sample_tests.append(ttest)
            except:
                pass

        # Group Tests
        group_tests = []
        if group_var and group_var in self.df.columns:
            n_groups = self.df[group_var].nunique()
            for var in valid_vars:
                try:
                    if n_groups == 2:
                        test = self._independent_ttest(var, group_var)
                    else:
                        test = self._one_way_anova(var, group_var)
                    group_tests.append(test)
                except:
                    pass

        # Correlation Matrix
        corr_matrix = None
        if len(valid_vars) >= 2:
            corr_matrix = self.df[valid_vars].corr().round(3)

        return AxisResult(
            name=name,
            variables=valid_vars,
            overall_mean=overall_mean,
            overall_std=overall_std,
            cronbach_alpha=round(alpha, 3) if alpha else None,
            item_stats=pd.DataFrame(item_stats),
            one_sample_tests=one_sample_tests,
            group_tests=group_tests,
            correlation_matrix=corr_matrix
        )

    def _cronbach_alpha(self, variables: List[str]) -> Optional[float]:
        try:
            df_items = self.df[variables].dropna()
            if len(df_items) < 2:
                return None
            item_vars = df_items.var(axis=0, ddof=1)
            total_var = df_items.sum(axis=1).var(ddof=1)
            n = len(variables)
            alpha = (n / (n - 1)) * (1 - item_vars.sum() / total_var)
            return max(0, alpha)
        except:
            return None

    def _interpret_likert(self, mean: float) -> str:
        if mean >= 4.21: return "موافق بشدة"
        elif mean >= 3.41: return "موافق"
        elif mean >= 2.61: return "محايد"
        elif mean >= 1.81: return "غير موافق"
        else: return "غير موافق بشدة"

    def _one_sample_ttest(self, var: str, pop_mean: float) -> Dict:
        data = self.df[var].dropna()
        statistic, p_value = stats.ttest_1samp(data, pop_mean)
        mean = data.mean()
        return {
            'المتغير': var,
            'المتوسط': round(mean, 3),
            'الاتجاه': self._interpret_likert(mean),
            'الانحراف المعياري': round(data.std(), 3),
            'قيمة t': round(statistic, 4),
            'درجات الحرية': len(data) - 1,
            'قيمة p': round(p_value, 4),
            'حجم التأثير d': round((mean - pop_mean) / data.std(), 3),
            'النتيجة': 'معنوي' if p_value < self.alpha else 'غير معنوي',
            'التفسير': f"متوسط {var} = {mean:.2f} ({self._interpret_likert(mean)}), t={statistic:.3f}, p={p_value:.3f}"
        }

    def _independent_ttest(self, numeric_var: str, group_var: str) -> Dict:
        groups = self.df[group_var].dropna().unique()
        g1 = self.df[self.df[group_var] == groups[0]][numeric_var].dropna()
        g2 = self.df[self.df[group_var] == groups[1]][numeric_var].dropna()

        levene_stat, levene_p = stats.levene(g1, g2)
        equal_var = levene_p > self.alpha
        statistic, p_value = stats.ttest_ind(g1, g2, equal_var=equal_var)

        pooled = np.sqrt(((len(g1)-1)*g1.var() + (len(g2)-1)*g2.var()) / (len(g1)+len(g2)-2))
        cohens_d = (g1.mean() - g2.mean()) / pooled if pooled > 0 else 0

        return {
            'المتغير': numeric_var,
            'الاختبار': 'Independent T-Test',
            'المجموعة 1': str(groups[0]),
            'المجموعة 2': str(groups[1]),
            'متوسط 1': round(g1.mean(), 3),
            'متوسط 2': round(g2.mean(), 3),
            'قيمة t': round(statistic, 4),
            'قيمة p': round(p_value, 4),
            "Cohen's d": round(cohens_d, 3),
            'النتيجة': 'معنوي' if p_value < self.alpha else 'غير معنوي',
        }

    def _one_way_anova(self, numeric_var: str, group_var: str) -> Dict:
        groups = []
        group_names = self.df[group_var].dropna().unique()
        for name in group_names:
            groups.append(self.df[self.df[group_var] == name][numeric_var].dropna())

        statistic, p_value = stats.f_oneway(*groups)

        formula = f'{numeric_var} ~ C({group_var})'
        model = ols(formula, data=self.df).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)
        ss_between = anova_table['sum_sq'][0]
        ss_total = anova_table['sum_sq'].sum()
        eta_sq = ss_between / ss_total if ss_total > 0 else 0

        return {
            'المتغير': numeric_var,
            'الاختبار': 'One-Way ANOVA',
            'عدد المجموعات': len(group_names),
            'قيمة F': round(statistic, 4),
            'قيمة p': round(p_value, 4),
            'Eta squared': round(eta_sq, 3),
            'النتيجة': 'معنوي' if p_value < self.alpha else 'غير معنوي',
        }

    def frequency_table(self, var: str) -> pd.DataFrame:
        counts = self.df[var].value_counts(dropna=False).sort_index()
        percentages = (counts / counts.sum() * 100).round(2)
        cumulative = percentages.cumsum().round(2)
        return pd.DataFrame({
            'القيمة': counts.index,
            'التكرار': counts.values,
            'النسبة %': percentages.values,
            'النسبة التراكمية %': cumulative.values
        })

    def pearson_corr(self, var1: str, var2: str) -> Dict:
        combined = pd.DataFrame({var1: self.df[var1], var2: self.df[var2]}).dropna()
        r, p = stats.pearsonr(combined[var1], combined[var2])
        return {
            'المتغير 1': var1,
            'المتغير 2': var2,
            'r': round(r, 4),
            'p': round(p, 4),
            'قوة': 'قوي' if abs(r) >= 0.7 else 'متوسط' if abs(r) >= 0.5 else 'ضعيف',
            'الاتجاه': 'إيجابي' if r > 0 else 'سلبي',
            'معنوي': p < self.alpha
        }
