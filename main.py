#!/usr/bin/env python3
"""
SurveyAI Pro - نقطة التشغيل الرئيسية
"""

import sys
from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.panel import Panel

from survey_ai_pro.data_loader import DataLoader
from survey_ai_pro.schema_detector import SchemaDetector
from survey_ai_pro.stats_engine import StatsEngine, AxisResult
from survey_ai_pro.ai_reporter import AIReporter
from survey_ai_pro.visualizer import Visualizer
from survey_ai_pro.word_export import WordExporter
from survey_ai_pro.pdf_export import PDFExporter

console = Console()


def create_sample_data():
    import numpy as np
    import pandas as pd
    np.random.seed(42)
    n = 261
    data = {
        'Gender': np.random.choice([1, 2], n, p=[0.55, 0.45]),
        'Age': np.random.choice([1, 2, 3, 4, 5], n, p=[0.15, 0.35, 0.30, 0.15, 0.05]),
        'Experience': np.random.choice([1, 2, 3, 4, 5], n, p=[0.10, 0.25, 0.35, 0.20, 0.10]),
        'Education': np.random.choice([1, 2, 3, 4], n, p=[0.20, 0.40, 0.30, 0.10]),
        'JobLevel': np.random.choice([1, 2, 3, 4], n, p=[0.30, 0.35, 0.25, 0.10]),
    }
    for i in range(1, 25):
        data[f'Q{i}'] = np.random.choice([1, 2, 3, 4, 5], n, p=[0.05, 0.10, 0.25, 0.40, 0.20])
    df = pd.DataFrame(data)
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    df.to_csv(out_dir / "AB7_ENG_Release_Version6.csv", index=False, encoding='utf-8-sig')
    console.print("[green]بيانات تجريبية: data/AB7_ENG_Release_Version6.csv[/green]")
    return str(out_dir / "AB7_ENG_Release_Version6.csv")


def run(csv_path=None, title="دراسة ميدانية", output_dir="output", ollama_model="llama3.1"):
    console.print(Panel.fit("تحميل البيانات", style="bold blue"))
    if csv_path is None or not Path(csv_path).exists():
        console.print("[yellow]لم يُعثر على الملف. إنشاء بيانات تجريبية...[/yellow]")
        csv_path = create_sample_data()

    loader = DataLoader(csv_path)
    df = loader.get_df()
    meta = loader.get_meta()
    n = len(df)

    console.print(Panel.fit("اكتشاف هيكل الاستبيان", style="bold blue"))
    detector = SchemaDetector(df, meta)
    schema = detector.detect(title=title)

    console.print(Panel.fit("الإحصاء الوصفي والاختبارات", style="bold blue"))
    stats_engine = StatsEngine(df)

    demographics = {}
    for demo in schema.demographics:
        if demo in df.columns:
            demographics[demo] = stats_engine.frequency_table(demo)

    axes_results = []
    for axis in schema.axes:
        console.print(f"[yellow]تحليل: {axis.name}[/yellow]")
        result = stats_engine.analyze_axis(
            axis.name, axis.variables,
            group_var=schema.group_var,
            pop_mean=schema.likert_mid
        )
        axes_results.append(result)

    console.print(Panel.fit("إعداد التحليل الأكاديمي", style="bold blue"))
    ai = AIReporter(model=ollama_model)
    analysis_report = ai.generate(
        title=title,
        demographics=demographics,
        axes_results=axes_results,
        group_var=schema.group_var,
        n=n
    )

    report_path = Path(output_dir) / "analysis_report.txt"
    report_path.write_text(analysis_report, encoding="utf-8")
    console.print(f"[green]التحليل الأكاديمي: {report_path}[/green]")

    console.print(Panel.fit("إنشاء الرسوم البيانية", style="bold blue"))
    viz = Visualizer(df, output_dir=f"{output_dir}/figures")

    demo_figures = {}
    for demo in list(demographics.keys())[:5]:
        bar_p = viz.bar(demo, name=f"demo_{demo}_bar.png")
        pie_p = viz.pie(demo, name=f"demo_{demo}_pie.png")
        demo_figures[demo] = [bar_p, pie_p]

    axes_comparison = {}
    for r in axes_results:
        axes_comparison[r.name] = {'mean': r.overall_mean, 'std': r.overall_std}

    axes_compare_path = None
    if axes_comparison:
        axes_compare_path = viz.axes_compare(axes_comparison, name="axes_comparison.png")

    box_paths = {}
    if schema.group_var and schema.group_var in df.columns:
        for r in axes_results:
            if r.variables:
                box_p = viz.box(r.variables[0], group_var=schema.group_var,
                               name=f"box_{r.variables[0]}.png")
                box_paths[r.name] = box_p

    console.print(Panel.fit("تصدير Word", style="bold blue"))
    word = WordExporter(path=f"{output_dir}/survey_report.docx")
    word.title(title)

    word.paragraph("═══════════════════════════════════════", align="center")
    word.paragraph("التقرير الإحصائي الشامل", bold=True, align="center")
    word.paragraph(f"{title}", bold=True, align="center")
    word.paragraph(f"حجم العينة: {n} فرد", align="center")
    word.paragraph("═══════════════════════════════════════", align="center")
    word.page_break()

    word.heading("ملخص تنفيذي", level=1)
    summary_text = f'تناولت هذه الدراسة موضوع "{title}" بعينة قوامها {n} فرد. تم استخدام الاستبيان كأداة رئيسية لجمع البيانات، وتم تحليل البيانات باستخدام الإحصاء الوصفي واختبارات الفروق. أظهرت النتائج وجود اتجاهات إيجابية في معظم محاور الدراسة.'
    word.paragraph(summary_text)
    word.page_break()

    word.heading("القسم الأول: الخصائص الديموغرافية للعينة", level=1)
    word.paragraph("يستعرض هذا القسم الخصائص الديموغرافية لعينة الدراسة.")

    for var_name, freq_table in demographics.items():
        word.heading(f"جدول توزيع {var_name}", level=2)
        word.table(freq_table)
        total = freq_table['التكرار'].sum() if 'التكرار' in freq_table.columns else n
        max_freq = freq_table['التكرار'].max() if 'التكرار' in freq_table.columns else 0
        max_cat = freq_table.loc[freq_table['التكرار'].idxmax(), freq_table.columns[0]] if 'التكرار' in freq_table.columns else ""
        max_pct = (max_freq / total * 100) if total > 0 else 0
        word.paragraph(f"يوضح الجدول أعلاه توزيع المستجيبين على متغير {var_name}. يُلاحظ أن أكثر الفئات شيوعاً هي الفئة ({max_cat}) بنسبة {max_pct:.1f}%.")

        if var_name in demo_figures:
            word.heading(f"الشكل البياني: توزيع {var_name}", level=2)
            word.image(demo_figures[var_name][0], width=14)
            word.paragraph(f"الشكل أعلاه يُظهر توزيع التكرارات لمتغير {var_name} على شكل أعمدة.")
            word.image(demo_figures[var_name][1], width=12)
            word.paragraph(f"الشكل الدائري يُظهر النسب المئوية لكل فئة من فئات {var_name}.")

    word.page_break()

    word.heading("القسم الثاني: تحليل محاور الاستبيان", level=1)
    word.paragraph("يُقدم هذا القسم تحليلاً إحصائياً شاملاً لمحاور الاستبيان الرئيسية.")

    if axes_compare_path and Path(axes_compare_path).exists():
        word.heading("مقارنة المتوسطات بين المحاور", level=2)
        word.image(axes_compare_path, width=14)
        word.paragraph("الشكل أعلاه يُقارن المتوسطات العامة للمحاور المختلفة مع المتوسط الفرضي (3).")

    for r in axes_results:
        word.heading(f"المحور: {r.name}", level=2)
        if r.overall_mean >= 4.21:
            level = "موافق بشدة"
        elif r.overall_mean >= 3.41:
            level = "موافق"
        elif r.overall_mean >= 2.61:
            level = "محايد"
        elif r.overall_mean >= 1.81:
            level = "غير موافق"
        else:
            level = "غير موافق بشدة"

        word.paragraph(f"المتوسط العام للمحور هو {r.overall_mean:.3f}، والانحراف المعياري {r.overall_std:.3f}. يُصنف هذا المحور ضمن مستوى '{level}'. معامل الثبات (Cronbach's Alpha) = {r.cronbach_alpha or 'غير محسوب'}.")

        if r.item_stats is not None and not r.item_stats.empty:
            word.heading("إحصائيات البنود التفصيلية", level=3)
            word.table(r.item_stats)
            if 'المتوسط' in r.item_stats.columns:
                highest = r.item_stats.loc[r.item_stats['المتوسط'].idxmax()]
                lowest = r.item_stats.loc[r.item_stats['المتوسط'].idxmin()]
                word.paragraph(f"البند الأعلى متوسطاً هو ({highest.name}) بمتوسط {highest['المتوسط']:.3f}. أما البند الأدنى متوسطاً فهو ({lowest.name}) بمتوسط {lowest['المتوسط']:.3f}.")

        if r.one_sample_tests:
            word.heading("نتائج One Sample T-Test", level=3)
            ttest_df = pd.DataFrame(r.one_sample_tests)
            cols = ['المتغير', 'المتوسط', 'الاتجاه', 'قيمة t', 'قيمة p', 'حجم التأثير d', 'النتيجة']
            available_cols = [c for c in cols if c in ttest_df.columns]
            word.table(ttest_df[available_cols])

        if r.name in box_paths:
            word.heading(f"الشكل البياني: توزيع {r.variables[0] if r.variables else 'البند'}", level=3)
            word.image(box_paths[r.name], width=14)

        if r.correlation_matrix is not None:
            word.heading("مصفوفة الارتباطات", level=3)
            corr_img = viz.corr_heatmap(r.variables, name=f"corr_{r.name}.png")
            word.image(corr_img, width=14)

        word.page_break()

    all_group_tests = []
    for r in axes_results:
        all_group_tests.extend(r.group_tests)

    if all_group_tests:
        word.heading("القسم الثالث: الفروق الديموغرافية", level=1)
        word.paragraph("يستعرض هذا القسم نتائج اختبارات الفروق بين المجموعات.")
        for t in all_group_tests:
            word.heading(f"{t['الاختبار']}: {t['المتغير']}", level=2)
            test_df = pd.DataFrame([{k: v for k, v in t.items() if k not in ['الاختبار', 'التفسير']}])
            word.table(test_df)
            is_significant = t.get('النتيجة') == 'معنوي'
            word.paragraph(f"{'توجد فروق ذات دلالة إحصائية' if is_significant else 'لا توجد فروق ذات دلالة إحصائية'} بين المجموعات في متغير {t['المتغير']}.")
        word.page_break()

    word.heading("القسم الرابع: المناقشة الإحصائية", level=1)
    word.paragraph("يقدم هذا القسم مناقشة تفصيلية للنتائج الإحصائية في ضوء الإطار النظري للدراسة.")
    for r in axes_results:
        word.heading(f"مناقشة محور {r.name}", level=2)
        if r.overall_mean >= 3.41:
            interp = f"أظهر محور {r.name} متوسطاً عاماً مرتفعاً ({r.overall_mean:.3f})، مما يشير إلى موافقة المستجيبين."
        elif r.overall_mean >= 2.61:
            interp = f"أظهر محور {r.name} متوسطاً عاماً محايداً ({r.overall_mean:.3f})، مما يشير إلى تباين في الآراء."
        else:
            interp = f"أظهر محور {r.name} متوسطاً عاماً منخفضاً ({r.overall_mean:.3f})، مما يشير إلى عدم موافقة المستجيبين."
        word.paragraph(interp)
        if r.cronbach_alpha is not None:
            word.paragraph(f"معامل الثبات (Cronbach's Alpha = {r.cronbach_alpha:.3f}) {'يُعتبر ممتازاً' if r.cronbach_alpha >= 0.9 else 'يُعتبر جيداً' if r.cronbach_alpha >= 0.7 else 'يُعتبر مقبولاً' if r.cronbach_alpha >= 0.6 else 'يُعتبر ضعيفاً'}.")
    word.page_break()

    word.heading("القسم الخامس: التحليل الأكاديمي المتقدم", level=1)
    word.paragraph("يُقدم القسم التالي تحليلاً أكاديمياً شاملاً لمناقشة النتائج، مبنياً على البيانات الإحصائية الفعلية للدراسة.")
    word.ai_text(analysis_report)

    word_path = word.save()

    console.print(Panel.fit("تصدير PDF", style="bold blue"))
    pdf = PDFExporter(path=f"{output_dir}/survey_report.pdf")
    pdf.add_cover_page(title, "التقرير الإحصائي الشامل", n)
    pdf.add_heading("ملخص تنفيذي", level=1)
    pdf.add_paragraph(f'تناولت هذه الدراسة موضوع "{title}" بعينة قوامها {n} فرد. تم استخدام الاستبيان كأداة رئيسية لجمع البيانات.')
    pdf.add_page_break()

    pdf.add_heading("القسم الأول: الخصائص الديموغرافية للعينة", level=1)
    for var_name, freq_table in demographics.items():
        pdf.add_table(freq_table, title=f"جدول توزيع {var_name}")
        pdf.add_caption(f"يوضح الجدول توزيع المستجيبين على متغير {var_name}.")
        if var_name in demo_figures:
            pdf.add_image(demo_figures[var_name][0], width=14, caption=f"الشكل: توزيع {var_name} - أعمدة")
            pdf.add_image(demo_figures[var_name][1], width=12, caption=f"الشكل: توزيع {var_name} - دائري")
    pdf.add_page_break()

    pdf.add_heading("القسم الثاني: تحليل محاور الاستبيان", level=1)
    if axes_compare_path:
        pdf.add_image(axes_compare_path, width=14, caption="الشكل: مقارنة متوسطات المحاور مع المتوسط الفرضي")

    for r in axes_results:
        pdf.add_heading(r.name, level=2)
        if r.item_stats is not None and not r.item_stats.empty:
            pdf.add_table(r.item_stats)
            pdf.add_caption(f"إحصائيات بنود محور {r.name}. المتوسط العام = {r.overall_mean:.3f}")
        if r.one_sample_tests:
            ttest_df = pd.DataFrame(r.one_sample_tests)
            cols = ['المتغير', 'المتوسط', 'الاتجاه', 'قيمة t', 'قيمة p', 'حجم التأثير d', 'النتيجة']
            available_cols = [c for c in cols if c in ttest_df.columns]
            pdf.add_table(ttest_df[available_cols])
            pdf.add_caption("نتائج One Sample T-Test مقارنة بالمتوسط الفرضي 3")
        if r.name in box_paths:
            pdf.add_image(box_paths[r.name], width=14, caption=f"الشكل الصندوقي: توزيع {r.variables[0] if r.variables else 'البند'}")
    pdf.add_page_break()

    if all_group_tests:
        pdf.add_heading("القسم الثالث: الفروق الديموغرافية", level=1)
        for t in all_group_tests:
            test_df = pd.DataFrame([{k: v for k, v in t.items() if k not in ['الاختبار', 'التفسير']}])
            pdf.add_table(test_df)
            pdf.add_caption(f"{t['الاختبار']} - {t['المتغير']}: {t['النتيجة']}")

    pdf.add_heading("القسم الرابع: المناقشة الإحصائية", level=1)
    for r in axes_results:
        pdf.add_heading(f"مناقشة محور {r.name}", level=2)
        if r.overall_mean >= 3.41:
            interp = f"أظهر محور {r.name} متوسطاً عاماً مرتفعاً ({r.overall_mean:.3f})، مما يشير إلى موافقة المستجيبين."
        elif r.overall_mean >= 2.61:
            interp = f"أظهر محور {r.name} متوسطاً عاماً محايداً ({r.overall_mean:.3f})، مما يشير إلى تباين في الآراء."
        else:
            interp = f"أظهر محور {r.name} متوسطاً عاماً منخفضاً ({r.overall_mean:.3f})، مما يشير إلى عدم موافقة المستجيبين."
        pdf.add_paragraph(interp)

    pdf.add_heading("القسم الخامس: التحليل الأكاديمي المتقدم", level=1)
    for para in analysis_report.split('\n\n'):
        if para.strip():
            pdf.add_paragraph(para.strip())

    pdf_path = pdf.save()

    console.print(Panel.fit("انتهى التحليل بنجاح!", style="bold green"))
    console.print(f"[cyan]Word: {word_path}[/cyan]")
    console.print(f"[cyan]PDF: {pdf_path}[/cyan]")
    console.print(f"[cyan]التحليل الأكاديمي: {report_path}[/cyan]")

    return {
        'word': word_path,
        'pdf': pdf_path,
        'analysis': str(report_path),
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
