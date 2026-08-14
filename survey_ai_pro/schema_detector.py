"""🏗️ اكتشاف تلقائي ذكي لهيكل الاستبيان"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from rich.console import Console

console = Console()

@dataclass
class Axis:
    name: str
    variables: List[str]
    description: str = ""

@dataclass
class SurveySchema:
    title: str
    axes: List[Axis] = field(default_factory=list)
    demographics: List[str] = field(default_factory=list)
    group_var: Optional[str] = None
    likert_min: int = 1
    likert_max: int = 5
    likert_mid: float = 3.0

class SchemaDetector:
    """يكتشف هيكل الاستبيان تلقائياً من أي CSV"""

    def __init__(self, df: pd.DataFrame, meta: Dict):
        self.df = df
        self.meta = meta

    def detect(self, title: str = "دراسة ميدانية") -> SurveySchema:
        demo_vars = self._detect_demographics()
        axis_vars = self._detect_axis_variables()
        axes = self._group_into_axes(axis_vars)
        group_var = self._pick_group_var(demo_vars)

        schema = SurveySchema(
            title=title,
            axes=axes,
            demographics=demo_vars,
            group_var=group_var,
            likert_min=1,
            likert_max=5,
            likert_mid=3.0
        )

        console.print(f"[cyan]▪ المحاور المكتشفة: {len(axes)}[/cyan]")
        for ax in axes:
            console.print(f"  - {ax.name}: {len(ax.variables)} بنود")
        console.print(f"[cyan]▪ الديموغرافيات: {len(demo_vars)}[/cyan]")
        console.print(f"[cyan]▪ متغير التجميع: {group_var or 'لا يوجد'}[/cyan]")

        return schema

    def _detect_demographics(self) -> List[str]:
        """اكتشاف المتغيرات الديموغرافية"""
        candidates = []
        demo_keywords = ['gender', 'sex', 'age', 'education', 'experience', 
                        'job', 'work', 'income', 'marital', 'nationality',
                        'gender', 'الجنس', 'العمر', 'التعليم', 'الخبرة', 'الوظيفة']

        for col, info in self.meta.items():
            col_lower = col.lower()
            # 1. إذا كان الاسم يحتوي على كلمات ديموغرافية
            if any(k in col_lower for k in demo_keywords):
                candidates.append(col)
                continue
            # 2. فئوي مع 2-10 قيم
            if info['measure'] == 'Nominal' and 2 <= info['unique'] <= 10:
                candidates.append(col)

        return list(dict.fromkeys(candidates))[:6]  # إزالة التكرار + حد أقصى 6

    def _detect_axis_variables(self) -> List[str]:
        """اكتشاف بنود الاستبيان (ليكرت)"""
        candidates = []
        for col, info in self.meta.items():
            if info['measure'] in ['Ordinal', 'Scale']:
                # تحقق من نطاق ليكرت (1-5 أو 1-7)
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    vmin = self.df[col].min()
                    vmax = self.df[col].max()
                    if 1 <= vmin <= 2 and 3 <= vmax <= 7:
                        candidates.append(col)
        return candidates

    def _group_into_axes(self, variables: List[str]) -> List[Axis]:
        """تجميع البنود في محاور بناءً على البادئة"""
        from collections import defaultdict
        groups = defaultdict(list)

        for var in variables:
            # استخراج البادئة (Q1, Q2 → Q | Axis1, Axis2 → Axis)
            prefix = ''.join([c for c in var if not c.isdigit()]).rstrip('_').rstrip('-')
            if not prefix or prefix == var:
                prefix = var[:3] if len(var) > 3 else var
            groups[prefix].append(var)

        axes = []
        for prefix, vars_list in sorted(groups.items()):
            if len(vars_list) >= 2:
                axes.append(Axis(
                    name=f"المحور: {prefix}",
                    variables=sorted(vars_list, key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else x),
                    description=f"{len(vars_list)} بند"
                ))

        # إذا لم يُكتشف أي محور، ضع كل البنود في محور واحد
        if not axes and variables:
            axes.append(Axis(name="المحور الرئيسي", variables=variables))

        return axes

    def _pick_group_var(self, demo_vars: List[str]) -> Optional[str]:
        """اختيار أفضل متغير ديموغرافي للتجميع"""
        for var in demo_vars:
            if var in self.df.columns:
                unique = self.df[var].nunique()
                if 2 <= unique <= 5:  # 2-5 مجموعات مثالية
                    return var
        return demo_vars[0] if demo_vars else None
