"""📂 قراءة CSV فقط مع استخراج Metadata ذكي"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console

console = Console()

class DataLoader:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"❌ الملف غير موجود: {file_path}")

        self.df = pd.read_csv(self.file_path, low_memory=False, encoding='utf-8')
        self.meta: Dict[str, Dict] = {}
        self._extract_meta()

        console.print(f"[green]✅ تم تحميل:[/green] {self.file_path.name} "
                      f"([cyan]{self.df.shape[0]:,}[/cyan] صف × [cyan]{self.df.shape[1]}[/cyan] عمود)")

    def _extract_meta(self):
        for col in self.df.columns:
            dtype = self.df[col].dtype
            unique = self.df[col].nunique(dropna=True)

            if pd.api.types.is_numeric_dtype(dtype):
                if unique <= 5:
                    measure = 'Nominal'
                elif unique <= 10:
                    measure = 'Ordinal'
                else:
                    measure = 'Scale'
            else:
                measure = 'Nominal'

            self.meta[col] = {
                'name': col,
                'label': col,
                'type': str(dtype),
                'measure': measure,
                'unique': unique,
                'missing': self.df[col].isna().sum()
            }

    def get_df(self) -> pd.DataFrame:
        return self.df.copy()

    def get_meta(self) -> Dict[str, Dict]:
        return self.meta.copy()

    def summary(self):
        console.print(f"\n[bold blue]📊 ملخص البيانات:[/bold blue]")
        console.print(f"  الصفوف: [cyan]{self.df.shape[0]:,}[/cyan]")
        console.print(f"  الأعمدة: [cyan]{self.df.shape[1]}[/cyan]")
        console.print(f"  Nominal: [yellow]{sum(1 for v in self.meta.values() if v['measure']=='Nominal')}[/yellow]")
        console.print(f"  Ordinal: [yellow]{sum(1 for v in self.meta.values() if v['measure']=='Ordinal')}[/yellow]")
        console.print(f"  Scale:   [yellow]{sum(1 for v in self.meta.values() if v['measure']=='Scale')}[/yellow]")
