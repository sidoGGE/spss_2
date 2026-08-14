"""تصدير PDF بخط عربي ودعم RTL كامل"""
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from rich.console import Console
import re

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False

console = Console()


def is_arabic_word(word):
    return bool(re.search(r'[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]', word))


def reshape_arabic(text):
    if not text or not HAS_ARABIC:
        return text or ""
    words = text.split(' ')
    fixed_words = []
    for word in words:
        if is_arabic_word(word):
            reshaped = arabic_reshaper.reshape(word)
            fixed = get_display(reshaped)
            fixed_words.append(fixed)
        else:
            fixed_words.append(word)
    fixed_words.reverse()
    return ' '.join(fixed_words)


class PDFExporter:
    def __init__(self, path="output/report.pdf"):
        self.out_path = Path(path)
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self._font_ready = False
        self._font_name = "ArabicFont"
        self._setup_fonts()

        self.doc = SimpleDocTemplate(
            str(self.out_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        self.story = []
        self._setup_styles()
        self._page_width = A4[0] - 4*cm

    def _setup_fonts(self):
        system_fonts = [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\tahoma.ttf",
            r"C:\Windows\Fonts\times.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
            "/System/Library/Fonts/GeezaPro.ttc",
        ]

        for fp in system_fonts:
            if Path(fp).exists():
                try:
                    pdfmetrics.registerFont(TTFont(self._font_name, fp))
                    self._font_ready = True
                    return
                except:
                    continue

        import urllib.request
        font_dir = Path("fonts")
        font_dir.mkdir(exist_ok=True)
        font_file = font_dir / "Amiri-Regular.ttf"

        if not font_file.exists():
            try:
                url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
                urllib.request.urlretrieve(url, str(font_file))
            except:
                pass

        if font_file.exists():
            try:
                pdfmetrics.registerFont(TTFont(self._font_name, str(font_file)))
                self._font_ready = True
                return
            except:
                pass

        self._font_name = "Helvetica"
        self._font_ready = False

    def _setup_styles(self):
        self.styles = getSampleStyleSheet()

        self.styles.add(ParagraphStyle(
            name='ArabicTitle',
            fontName=self._font_name,
            fontSize=20,
            textColor=HexColor('#2E86AB'),
            alignment=TA_CENTER,
            spaceAfter=20,
            leading=28,
        ))

        self.styles.add(ParagraphStyle(
            name='ArabicHeading1',
            fontName=self._font_name,
            fontSize=16,
            textColor=HexColor('#A23B72'),
            alignment=TA_RIGHT,
            spaceAfter=12,
            spaceBefore=16,
            leading=24,
        ))

        self.styles.add(ParagraphStyle(
            name='ArabicHeading2',
            fontName=self._font_name,
            fontSize=13,
            textColor=HexColor('#2E86AB'),
            alignment=TA_RIGHT,
            spaceAfter=10,
            spaceBefore=12,
            leading=20,
        ))

        self.styles.add(ParagraphStyle(
            name='ArabicBody',
            fontName=self._font_name,
            fontSize=11,
            textColor=black,
            alignment=TA_RIGHT,
            spaceAfter=10,
            leading=18,
        ))

        self.styles.add(ParagraphStyle(
            name='ArabicCaption',
            fontName=self._font_name,
            fontSize=9,
            textColor=HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=12,
            leading=14,
        ))

        self.styles.add(ParagraphStyle(
            name='CoverText',
            fontName=self._font_name,
            fontSize=14,
            textColor=HexColor('#333333'),
            alignment=TA_CENTER,
            spaceAfter=8,
            leading=20,
        ))

    def _rtext(self, text):
        if not text:
            return ""
        if self._font_ready and HAS_ARABIC:
            return reshape_arabic(str(text))
        return str(text)

    def add_title(self, text):
        self.story.append(Paragraph(self._rtext(text), self.styles['ArabicTitle']))
        self.story.append(Spacer(1, 0.5*cm))

    def add_cover_page(self, title, subtitle, n):
        self.story.append(Spacer(1, 4*cm))
        self.story.append(Paragraph(self._rtext("═══════════════════════════════════════"), self.styles['CoverText']))
        self.story.append(Paragraph(self._rtext("التقرير الإحصائي الشامل"), self.styles['CoverText']))
        self.story.append(Paragraph(self._rtext(title), self.styles['ArabicTitle']))
        self.story.append(Paragraph(self._rtext(f"حجم العينة: {n} فرد"), self.styles['CoverText']))
        self.story.append(Paragraph(self._rtext("═══════════════════════════════════════"), self.styles['CoverText']))
        self.story.append(PageBreak())

    def add_heading(self, text, level=1):
        style_name = 'ArabicHeading1' if level == 1 else 'ArabicHeading2'
        self.story.append(Paragraph(self._rtext(text), self.styles[style_name]))

    def add_paragraph(self, text):
        if not text or not text.strip():
            return
        self.story.append(Paragraph(self._rtext(text), self.styles['ArabicBody']))

    def add_caption(self, text):
        self.story.append(Paragraph(self._rtext(text), self.styles['ArabicCaption']))

    def add_table(self, df, title=None):
        if title:
            self.add_heading(title, level=2)

        if df.empty:
            return

        headers = [self._rtext(str(col)) for col in df.columns]
        data = [headers]

        for _, row in df.iterrows():
            row_data = []
            for val in row:
                text = f"{val:.3f}" if isinstance(val, float) else str(val)
                row_data.append(self._rtext(text))
            data.append(row_data)

        n_cols = len(df.columns)
        available_width = self._page_width
        col_width = available_width / n_cols
        col_widths = [col_width] * n_cols

        table = Table(data, colWidths=col_widths, repeatRows=1)

        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self._font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('TEXTCOLOR', (0, 1), (-1, -1), black),
            ('FONTNAME', (0, 1), (-1, -1), self._font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]

        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), HexColor('#F5F5F5')))

        table.setStyle(TableStyle(style_commands))
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*cm))

    def add_image(self, path, width=14, caption=None):
        if not Path(path).exists():
            return

        max_width = self._page_width
        img_width = min(width * cm, max_width)

        img = RLImage(str(path), width=img_width)
        img.hAlign = 'CENTER'
        self.story.append(img)
        self.story.append(Spacer(1, 0.2*cm))

        if caption:
            self.add_caption(caption)

    def add_page_break(self):
        self.story.append(PageBreak())

    def add_spacer(self, height=0.5):
        self.story.append(Spacer(1, height*cm))

    def save(self):
        try:
            self.doc.build(self.story)
            console.print(f"[green]PDF: {self.out_path}[/green]")
            return str(self.out_path)
        except Exception as e:
            console.print(f"[red]خطأ PDF: {e}[/red]")
            raise
