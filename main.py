#!/usr/bin/env python3
"""
🚀 SurveyAI Pro - نقطة التشغيل الرئيسية
"""

import sys
from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.panel import Panel

from survey_ai_pro.data_loader import DataLoader
from survey_ai_pro.schema_detector import SchemaDetector, SurveySchema
from survey_ai_pro.stats_engine import StatsEngine, AxisResult
from survey_ai_pro.ai_reporter import AIReporter
from survey_ai_pro.visualizer import Visualizer
from survey_ai_pro.word_export import WordExporter
from survey_ai_pro.pdf_export import PDFExporter

console = Console()


def create_sample_data():
    """إنشاء بيانات تجريبية"""
    import numpy as np
    import pandas as pd

    np.random.seed(42)
    n = 150

    data = {
        'Gender': np.random.choice([1, 2], n, p=[0.6, 0.4]),
        'Age': np.random.choice([1, 2, 3, 4], n, p=[0.2, 0.4, 0.3, 0.1]),
        'Experience': np.random.choice([1, 2, 3, 4, 5], n),
        'Education': np.random.choice([1, 2, 3], n, p=[0.3, 0.5, 0.2]),
    }

    for i in range(1, 16):
        data[f'Q{i}'] = np.random.choice([1, 2, 3, 4, 5], n, p=[0.05, 0.1, 0.25, 0.4, 0.2])

    df = pd.DataFrame(data)
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    df.to_csv(out_dir / "AB7_ENG_Release_Version6.csv", index=False, encoding='utf-8-sig')
    console.print("[green]✅ بيانات تجريبية: data/AB7_ENG_Release_Version6.csv[/green]")
    return str(out_dir / "AB7_ENG_Release_Version6.csv")


def run(csv_path: str = None, title: str = "دراسة ميدانية", 
        output_dir: str = "output", ollama_model: str = "llama3.1"):
    """تشغيل التحليل الكامل"""

    # ─── 1. تحميل البيانات ───
    console.print(Panel.fit("📂 تحميل البيانات", style="bold blue"))

    if csv_path is None or not Path(csv_path).exists():
        console.print("[yellow]⚠️ لم يُعثر على الملف. إنشاء بيانات تجريبية...[/yellow]")
        csv_path = create_sample_data()

    loader = DataLoader(csv_path)
    df = loader.get_df()
    meta = loader.get_meta()

    # ─── 2. اكتشاف هيكل الاستبيان ───
    console.print(Panel.fit("🏗️ اكتشاف هيكل الاستبيان", style="bold blue"))
    detector = SchemaDetector(df, meta)
    schema = detector.detect(title=title)

    # ─── 3. الإحصاء الوصفي ───
    console.print(Panel.fit("📊 الإحصاء الوصفي والاختبارات", style="bold blue"))
    stats_engine = StatsEngine(df)

    demographics = {}
    for demo in schema.demographics:
        if demo in df.columns:
            demographics[demo] = stats_engine.frequency_table(demo)

    axes_results: List[AxisResult] = []
    for axis in schema.axes:
        console.print(f"[yellow]▪ تحليل: {axis.name}[/yellow]")
        result = stats_engine.analyze_axis(
            axis.name, axis.variables,
            group_var=schema.group_var,
            pop_mean=schema.likert_mid
        )
        axes_results.append(result)

    # ─── 4. التقرير الذكي (Ollama) ───
    console.print(Panel.fit("🤖 توليد التقرير الذكي", style="bold blue"))
    ai = AIReporter(model=ollama_model)
    ai_report = ai.generate(
        title=title,
        demographics=demographics,
        axes_results=axes_results,
        group_var=schema.group_var,
        n=len(df)
    )

    ai_path = Path(output_dir) / "ai_report.txt"
    ai_path.write_text(ai_report, encoding="utf-8")
    console.print(f"[green]✅ تقرير AI: {ai_path}[/green]")

    # ─── 5. الرسوم البيانية ───
    console.print(Panel.fit("📈 إنشاء الرسوم البيانية", style="bold blue"))
    viz = Visualizer(df, output_dir=f"{output_dir}/figures")

    demo_figures = {}  # {var: [bar_path, pie_path]}
    for demo in list(demographics.keys())[:4]:
        bar_p = viz.bar(demo, name=f"demo_{demo}_bar.png")
        pie_p = viz.pie(demo, name=f"demo_{demo}_pie.png")
        demo_figures[demo] = [bar_p, pie_p]

    # رسوم المحاور
    axes_comparison = {}
    for r in axes_results:
        axes_comparison[r.name] = {'mean': r.overall_mean, 'std': r.overall_std}

    axes_compare_path = None
    if axes_comparison:
        axes_compare_path = viz.axes_compare(axes_comparison, name="axes_comparison.png")

    # رسوم Box Plot لكل محور
    box_paths = {}
    if schema.group_var and schema.group_var in df.columns:
        for r in axes_results:
            if r.variables:
                box_p = viz.box(r.variables[0], group_var=schema.group_var, 
                               name=f"box_{r.variables[0]}.png")
                box_paths[r.name] = box_p

    # ─── 6. تصدير Word (مع رسوم + شرح) ───
    console.print(Panel.fit("📝 تصدير Word مع الرسوم والشروح", style="bold blue"))
    word = WordExporter(path=f"{output_dir}/survey_report.docx")
    word.title(title)

    # صفحة الغلاف
    word.paragraph("═══════════════════════════════════════", align="center")
    word.paragraph("التقرير الإحصائي الشامل", bold=True, align="center")
    word.paragraph(f"{title}", bold=True, align="center")
    word.paragraph(f"حجم العينة: {len(df)} فرد", align="center")
    word.paragraph("═══════════════════════════════════════", align="center")
    word.page_break()

    # ── الخصائص الديموغرافية ──
    word.heading("القسم الأول: الخصائص الديموغرافية", level=1)
    word.paragraph(
        "يستعرض هذا القسم الخصائص الديموغرافية لعينة الدراسة، "
        "والتي تُعد أساساً لفهم تركيبة المستجيبين وتوزيعهم على المتغيرات الفئوية. "
        "تُعرض البيانات في جداول تكرارية ورسوم بيانية توضيحية."
    )

    for var_name, freq_table in demographics.items():
        word.heading(f"جدول توزيع {var_name}", level=2)
        word.table(freq_table)
        word.paragraph(
            f"يوضح الجدول أعلاه توزيع المستجيبين على متغير {var_name}. "
            f"يُلاحظ أن أكثر الفئات شيوعاً هي الفئة ذات التكرار الأعلى، "
            f"مما يعكس طبيعة العينة المدروسة."
        )

        # إضافة الرسوم
        if var_name in demo_figures:
            bar_p, pie_p = demo_figures[var_name]
            word.heading(f"الشكل البياني: توزيع {var_name}", level=2)
            word.image(bar_p, width=14)
            word.paragraph(
                f"الشكل أعلاه يُظهر توزيع التكرارات لمتغير {var_name} على شكل أعمدة، "
                f"مما يسهل مقارنة الفئات المختلفة من حيث الحجم."
            )
            word.image(pie_p, width=12)
            word.paragraph(
                f"الشكل الدائري يُظهر النسب المئوية لكل فئة من فئات {var_name}، "
                f"ويوضح مساهمة كل فئة في العينة الكلية."
            )

    word.page_break()

    # ── تحليل المحاور ──
    word.heading("القسم الثاني: تحليل محاور الاستبيان", level=1)
    word.paragraph(
        "يُقدم هذا القسم تحليلاً إحصائياً شاملاً لمحاور الاستبيان الرئيسية، "
        "بما في ذلك الإحصاء الوصفي، واختبارات One Sample T-Test، "
        "ومعامل الثبات (Cronbach's Alpha)، والرسوم البيانية التوضيحية."
    )

    if axes_compare_path and Path(axes_compare_path).exists():
        word.heading("مقارنة المتوسطات بين المحاور", level=2)
        word.image(axes_compare_path, width=15)
        word.paragraph(
            "الشكل أعلاه يُقارن المتوسطات العامة للمحاور المختلفة مع المتوسط الفرضي (3). "
            "المحاور التي يتجاوز متوسطها 3 تشير إلى اتجاه إيجابي، "
            "بينما المحاور دون 3 تشير إلى اتجاه سلبي أو محايد."
        )

    for r in axes_results:
        word.heading(f"المحور: {r.name}", level=2)

        # إحصائيات البنود
        if r.item_stats is not None and not r.item_stats.empty:
            word.heading("إحصائيات البنود", level=3)
            word.table(r.item_stats)
            word.paragraph(
                f"يُظهر الجدول إحصائيات وصفية لبنود محور {r.name}. "
                f"المتوسط العام للمحور هو {r.overall_mean}، والانحراف المعياري {r.overall_std}. "
                f"معامل الثبات (Cronbach's Alpha) = {r.cronbach_alpha or 'غير محسوب'}، "
                f"مما يدل على {'درجة ثبات جيدة' if r.cronbach_alpha and r.cronbach_alpha >= 0.7 else 'درجة ثبات مقبولة' if r.cronbach_alpha and r.cronbach_alpha >= 0.6 else 'ثبات ضعيف يحتاج مراجعة'}."
            )

        # One Sample T-Test
        if r.one_sample_tests:
            word.heading("نتائج One Sample T-Test", level=3)
            ttest_df = pd.DataFrame(r.one_sample_tests)
            cols = ['المتغير', 'المتوسط', 'الاتجاه', 'قيمة t', 'قيمة p', 'حجم التأثير d', 'النتيجة']
            available_cols = [c for c in cols if c in ttest_df.columns]
            word.table(ttest_df[available_cols])
            word.paragraph(
                f"يُظهر الجدول نتائج اختبار T للعينة الواحدة لمقارنة متوسطات بنود {r.name} "
                f"بالمتوسط الفرضي (3). القيم ذات الدلالة الإحصائية (p < 0.05) "
                f"تُشير إلى وجود اختلاف معنوي عن المتوسط الفرضي."
            )

        # Box Plot
        if r.name in box_paths:
            word.heading(f"الشكل البياني: توزيع {r.variables[0]}", level=3)
            word.image(box_paths[r.name], width=14)
            word.paragraph(
                f"الشكل الصندوقي أعلاه يُظهر توزيع بند {r.variables[0]} عبر فئات {schema.group_var}، "
                f"ويوضح الوسيط والربيعين والقيم الشاذة لكل فئة."
            )

        # Correlation Matrix
        if r.correlation_matrix is not None:
            word.heading("مصفوفة الارتباطات", level=3)
            corr_img = viz.corr_heatmap(r.variables, name=f"corr_{r.name}.png")
            word.image(corr_img, width=14)
            word.paragraph(
                f"الخريطة الحرارية تُظهر معاملات الارتباط بين بنود محور {r.name}. "
                f"الارتباطات القوية (r > 0.7) تُشير إلى تجانس عالٍ بين البنود."
            )

    word.page_break()

    # ── الفروق الديموغرافية ──
    all_group_tests = []
    for r in axes_results:
        all_group_tests.extend(r.group_tests)

    if all_group_tests:
        word.heading("القسم الثالث: الفروق الديموغرافية", level=1)
        word.paragraph(
            "يستعرض هذا القسم نتائج اختبارات الفروق بين المجموعات، "
            "والتي تُساعد في تحديد ما إذا كانت المتغيرات الديموغرافية تؤثر "
            "في استجابات المستجيبين."
        )

        for t in all_group_tests:
            word.heading(f"{t['الاختبار']}: {t['المتغير']}", level=2)
            test_df = pd.DataFrame([{k: v for k, v in t.items() if k not in ['الاختبار', 'التفسير']}])
            word.table(test_df)
            word.paragraph(
                f"نتيجة الاختبار: {t['النتيجة']}. "
                f"{'توجد فروق ذات دلالة إحصائية' if t['النتيجة'] == 'معنوي' else 'لا توجد فروق ذات دلالة إحصائية'} "
                f"بين المجموعات في متغير {t['المتغير']}."
            )

    word.page_break()

    # ── تقرير AI ──
    word.heading("القسم الرابع: فصل نتائج الدراسة (مولد بالذكاء الاصطناعي)", level=1)
    word.paragraph(
        "يُقدم القسم التالي تحليلاً أكاديمياً شاملاً لمناقشة النتائج، "
        "مولداً بالذكاء الاصطناعي بناءً على البيانات الإحصائية الفعلية."
    )
    word.ai_text(ai_report)

    word_path = word.save()

    # ─── 7. تصدير PDF (مع رسوم + شرح) ───
    console.print(Panel.fit("📄 تصدير PDF مع الرسوم والشروح", style="bold blue"))
    pdf = PDFExporter(path=f"{output_dir}/survey_report.pdf")
    pdf.add_title(title)

    pdf.add_heading("القسم الأول: الخصائص الديموغرافية")
    pdf.add_paragraph(
        "يستعرض هذا القسم الخصائص الديموغرافية لعينة الدراسة."
    )

    for var_name, freq_table in demographics.items():
        pdf.add_table(freq_table, title=f"جدول توزيع {var_name}")
        pdf.add_caption(
            f"يوضح الجدول توزيع المستجيبين على متغير {var_name} مع النسب المئوية."
        )
        if var_name in demo_figures:
            bar_p, pie_p = demo_figures[var_name]
            pdf.add_image(bar_p, width=170, caption=f"الشكل: توزيع {var_name} - أعمدة")
            pdf.add_image(pie_p, width=150, caption=f"الشكل: توزيع {var_name} - دائري")

    pdf.add_heading("القسم الثاني: تحليل المحاور")

    if axes_compare_path:
        pdf.add_image(axes_compare_path, width=170, 
                     caption="الشكل: مقارنة متوسطات المحاور مع المتوسط الفرضي")

    for r in axes_results:
        pdf.add_heading(r.name)
        if r.item_stats is not None and not r.item_stats.empty:
            pdf.add_table(r.item_stats)
            pdf.add_caption(f"إحصائيات بنود محور {r.name}. المتوسط العام = {r.overall_mean}")

        if r.one_sample_tests:
            ttest_df = pd.DataFrame(r.one_sample_tests)
            cols = ['المتغير', 'المتوسط', 'الاتجاه', 'قيمة t', 'قيمة p', 'حجم التأثير d', 'النتيجة']
            available_cols = [c for c in cols if c in ttest_df.columns]
            pdf.add_table(ttest_df[available_cols])
            pdf.add_caption("نتائج One Sample T-Test مقارنة بالمتوسط الفرضي 3")

        if r.name in box_paths:
            pdf.add_image(box_paths[r.name], width=170,
                         caption=f"الشكل الصندوقي: توزيع {r.variables[0]}")

    if all_group_tests:
        pdf.add_heading("القسم الثالث: الفروق الديموغرافية")
        for t in all_group_tests:
            test_df = pd.DataFrame([{k: v for k, v in t.items() if k not in ['الاختبار', 'التفسير']}])
            pdf.add_table(test_df)

    pdf.add_heading("القسم الرابع: فصل نتائج الدراسة")
    for para in ai_report.split('\n\n'):
        if para.strip():
            pdf.add_paragraph(para.strip())

    pdf_path = pdf.save()

    # ─── الخلاصة ───
    console.print(Panel.fit("✅ انتهى التحليل بنجاح!", style="bold green"))
    console.print(f"[cyan]📄 Word:[/cyan] {word_path}")
    console.print(f"[cyan]📄 PDF:[/cyan] {pdf_path}")
    console.print(f"[cyan]🤖 AI Report:[/cyan] {ai_path}")
    console.print(f"[cyan]📊 Figures:[/cyan] {output_dir}/figures/")

    return {
        'word': word_path,
        'pdf': pdf_path,
        'ai': str(ai_path),
        'schema': schema,
        'axes_results': axes_results
    }


if __name__ == "__main__":
    RESULTS = run(
        csv_path="data/AB7_ENG_Release_Version6.csv",
        title="تأثير نظم ERP على جودة المعلومة المحاسبية",
        output_dir="output",
        ollama_model="llama3.1"
    )
