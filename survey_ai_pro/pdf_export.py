"""📄 تصدير PDF بخط عربي - يعمل على Windows و Linux"""
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from fpdf import FPDF
from rich.console import Console
import urllib.request
import os

console = Console()

class PDFExporter(FPDF):
    def __init__(self, path: str = "output/report.pdf"):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.out_path = Path(path)
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self._font_ready = False
        self._setup_fonts()
        self.set_auto_page_break(auto=True, margin=20)
        self.add_page()

    def _setup_fonts(self):
        """إعداد الخطوط العربية - يعمل على أي نظام"""
        # 1. محاولة إيجاد خط عربي في النظام
        system_fonts = [
            # Windows
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\times.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            # macOS
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ]

        for fp in system_fonts:
            if Path(fp).exists():
                try:
                    self.add_font('Arabic', '', fp, uni=True)
                    self.add_font('Arabic', 'B', fp, uni=True)
                    self.set_font('Arabic', '', 12)
                    self._font_ready = True
                    return
                except Exception as e:
                    continue

        # 2. تحميل خط Amiri من الإنترنت إذا لم يُوجد
        font_dir = Path("fonts")
        font_dir.mkdir(exist_ok=True)
        font_file = font_dir / "Amiri-Regular.ttf"

        if not font_file.exists():
            try:
                console.print("[yellow]⚠️ جاري تحميل خط عربي...[/yellow]")
                url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
                urllib.request.urlretrieve(url, str(font_file))
            except Exception as e:
                console.print(f"[red]⚠️ تعذر تحميل الخط: {e}[/red]")

        if font_file.exists():
            try:
                self.add_font('Arabic', '', str(font_file), uni=True)
                self.add_font('Arabic', 'B', str(font_file), uni=True)
                self.set_font('Arabic', '', 12)
                self._font_ready = True
                return
            except:
                pass

        # 3. Fallback - Helvetica بدون عربي
        console.print("[yellow]⚠️ لم يُوجد خط عربي. سيتم استخدام Helvetica (بدون عربية).[/yellow]")
        self.set_font('Helvetica', '', 12)
        self._font_ready = False

    def _safe_text(self, text: str) -> str:
        """تأمين النص للـ PDF"""
        if not text:
            return ""
        if self._font_ready:
            return text
        # إذا لم يكن هناك خط عربي، نحول إلى ASCII
        return text.encode('ascii', 'ignore').decode('ascii') if text else ""

    def header(self):
        if self._font_ready:
            self.set_font('Arabic', '', 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, 'SurveyAI Pro - التقرير الإحصائي', 0, 0, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        if self._font_ready:
            self.set_font('Arabic', '', 10)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'صفحة {self.page_no()}', 0, 0, 'C')

    def add_title(self, text: str):
        if self._font_ready:
            self.set_font('Arabic', 'B', 18)
            self.set_text_color(46, 134, 171)
            self.cell(0, 15, self._safe_text(text), 0, 1, 'C')
        else:
            self.set_font('Helvetica', 'B', 18)
            self.cell(0, 15, "SURVEY REPORT", 0, 1, 'C')
        self.ln(5)

    def add_heading(self, text: str):
        if self._font_ready:
            self.set_font('Arabic', 'B', 14)
            self.set_text_color(162, 59, 114)
            self.cell(0, 12, self._safe_text(text), 0, 1, 'R')
        else:
            self.set_font('Helvetica', 'B', 14)
            self.cell(0, 12, text.encode('ascii','ignore').decode(), 0, 1, 'L')
        self.ln(3)

    def add_paragraph(self, text: str):
        if self._font_ready:
            self.set_font('Arabic', '', 11)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 7, self._safe_text(text), align='R')
        else:
            self.set_font('Helvetica', '', 11)
            self.multi_cell(0, 7, text.encode('ascii','ignore').decode(), align='L')
        self.ln(3)

    def add_caption(self, text: str):
        """شرح/تسمية توضيحية للصور والجداول"""
        if self._font_ready:
            self.set_font('Arabic', 'I', 10)
            self.set_text_color(80, 80, 80)
            self.multi_cell(0, 6, self._safe_text(text), align='R')
        self.ln(2)

    def add_table(self, df: pd.DataFrame, title: str = None):
        if title and self._font_ready:
            self.add_heading(title)

        self.set_font('Arabic' if self._font_ready else 'Helvetica', 'B', 9)

        col_widths = []
        for col in df.columns:
            max_len = max(len(str(v)) for v in df[col]) if not df.empty else len(str(col))
            max_len = max(max_len, len(str(col)))
            col_widths.append(min(max_len * 3 + 5, 50))

        total = sum(col_widths)
        if total > 190:
            scale = 190 / total
            col_widths = [w * scale for w in col_widths]

        # رأس الجدول
        self.set_fill_color(46, 134, 171)
        self.set_text_color(255, 255, 255)
        for i, col in enumerate(df.columns):
            txt = self._safe_text(str(col)) if self._font_ready else str(col)[:20]
            self.cell(col_widths[i], 8, txt, 1, 0, 'C', True)
        self.ln()

        # البيانات
        self.set_font('Arabic' if self._font_ready else 'Helvetica', '', 9)
        self.set_text_color(0, 0, 0)
        fill = False
        for _, row in df.iterrows():
            if fill:
                self.set_fill_color(240, 240, 240)
            else:
                self.set_fill_color(255, 255, 255)
            for i, val in enumerate(row):
                text = f"{val:.3f}" if isinstance(val, float) else str(val)
                if not self._font_ready:
                    text = text.encode('ascii', 'ignore').decode()[:20]
                self.cell(col_widths[i], 7, text[:25], 1, 0, 'C', True)
            self.ln()
            fill = not fill
        self.ln(5)

    def add_image(self, path: str, width: float = 180, caption: str = None):
        if Path(path).exists():
            self.image(str(path), x=(210-width)/2, w=width)
            self.ln(2)
            if caption:
                self.add_caption(caption)
            self.ln(3)

    def save(self) -> str:
        self.output(str(self.out_path))
        console.print(f"[green]✅ PDF: {self.out_path}[/green]")
        return str(self.out_path)
