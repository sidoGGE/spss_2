"""مراسل التحليل الإحصائي - تقارير أكاديمية مفصلة"""
import pandas as pd
from typing import Dict, List
from rich.console import Console

console = Console()

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


class AIReporter:
    def __init__(self, model="llama3.1", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.client = None
        if HAS_OLLAMA:
            try:
                self.client = ollama.Client(host=base_url)
            except Exception as e:
                console.print(f"[yellow]تحذير: {e}[/yellow]")

    def available(self):
        if not HAS_OLLAMA or self.client is None:
            return False
        try:
            self.client.list()
            return True
        except:
            return False

    def generate(self, title, demographics, axes_results, group_var, n):
        if not self.available():
            console.print("[red]خدمة التحليل غير متاحة. شغّل: ollama serve[/red]")
            return self._fallback(title, axes_results, demographics, group_var, n)

        console.print("[cyan]جاري إعداد التحليل الأكاديمي...[/cyan]")
        prompt = self._build_prompt(title, demographics, axes_results, group_var, n)

        try:
            resp = self.client.generate(
                model=self.model,
                prompt=prompt,
                system=self._system_prompt(),
                options={
                    "temperature": 0.3,
                    "num_ctx": 8192,
                    "num_predict": 6000,
                }
            )
            text = resp.get("response", "")
            if not text or len(text) < 1000:
                return self._retry_lighter(title, demographics, axes_results, group_var, n)
            console.print(f"[green]تم الاستلام ({len(text)} حرف)[/green]")
            return text
        except Exception as e:
            console.print(f"[red]خطأ: {e}[/red]")
            return self._fallback(title, axes_results, demographics, group_var, n)

    def _retry_lighter(self, title, demographics, axes_results, group_var, n):
        try:
            console.print("[cyan]محاولة بنموذج أخف...[/cyan]")
            prompt = self._build_prompt(title, demographics, axes_results, group_var, n)
            resp = self.client.generate(
                model="llama3.2:3b",
                prompt=prompt,
                system=self._system_prompt(),
                options={"temperature": 0.3, "num_ctx": 4096, "num_predict": 4000}
            )
            text = resp.get("response", "")
            console.print(f"[green]تم الاستلام ({len(text)} حرف)[/green]")
            return text
        except Exception as e:
            return self._fallback(title, axes_results, demographics, group_var, n)

    def _system_prompt(self):
        return """أنت أستاذ جامعي متخصص في الإحصاء والبحث العلمي. تكتب فصول نتائج رسائل الماجستير والدكتوراه بالعربية الفصحى الأكاديمية الرصينة.

قواعد صارمة:
1. استخدم فقط الأرقام والبيانات المقدمة في الطلب - لا تخترع أي أرقام.
2. صنّف مقياس ليكرت 1-5 كالتالي:
   - 4.21 - 5.00: موافق بشدة
   - 3.41 - 4.20: موافق
   - 2.61 - 3.40: محايد
   - 1.81 - 2.60: غير موافق
   - 1.00 - 1.80: غير موافق بشدة
3. اذكر قيم t و p و d بشكل دقيق.
4. اكتب تقريراً شاملاً ومفصلاً (2000-3000 كلمة على الأقل).
5. اختتم بخلاصة مفصلة (300-400 كلمة) + توصيات عملية (200-300 كلمة).
6. أسلوب أكاديمي رصين، استخدم المصطلحات الإحصائية بشكل صحيح.
7. قسّم التقرير إلى أقسام واضحة مع عناوين فرعية.
8. اربط النتائج بالأدبيات النظرية.
9. ناقش النتائج غير المتوقعة والمحدودات.
10. اكتب النص جاهزاً للنسخ المباشر في الرسالة الأكاديمية.
11. لا تذكر أبداً أن النص مولد آلياً أو بواسطة أي برنامج أو ذكاء اصطناعي.
12. اكتب كأنك باحث أكاديمي حقيقي كتب هذا الفصل بنفسه."""

    def _build_prompt(self, title, demographics, axes_results, group_var, n):
        lines = [
            f"اكتب فصل نتائج شاملاً ومفصلاً (2000-3000 كلمة) لرسالة ماجستير.",
            f"",
            f"عنوان الدراسة: {title}",
            f"حجم العينة: {n} فرد",
            f"",
            f"{'='*60}",
            f"القسم الأول: الخصائص الديموغرافية للعينة",
            f"{'='*60}",
        ]

        for var_name, freq_table in demographics.items():
            lines.append(f"\n▪ {var_name}:")
            lines.append(freq_table.to_string(index=False))

        lines.extend([
            "",
            "=" * 60,
            "القسم الثاني: تحليل محاور الاستبيان (مقياس ليكرت 1-5، المتوسط الفرضي μ=3)",
            "=" * 60,
        ])

        for axis in axes_results:
            lines.append(f"\n▪ المحور: {axis.name}")
            lines.append(f"  المتوسط العام: M={axis.overall_mean}, الانحراف المعياري: SD={axis.overall_std}")
            lines.append(f"  معامل الثبات (Cronbach's Alpha): α={axis.cronbach_alpha or 'غير محسوب'}")

            if axis.item_stats is not None and not axis.item_stats.empty:
                lines.append("  إحصائيات البنود:")
                lines.append(axis.item_stats.to_string(index=False))

            lines.append("  نتائج One Sample T-Test (مقارنة بالمتوسط الفرضي 3):")
            for t in axis.one_sample_tests:
                lines.append(f"    • {t['المتغير']}: M={t['المتوسط']}, t={t['قيمة t']}, p={t['قيمة p']}, d={t['حجم التأثير d']}, الاتجاه={t['الاتجاه']}")

        all_group_tests = []
        for axis in axes_results:
            all_group_tests.extend(axis.group_tests)

        if all_group_tests:
            lines.extend(["", "=" * 60, f"القسم الثالث: الفروق الديموغرافية (متغير التجميع: {group_var})", "=" * 60])
            for t in all_group_tests:
                lines.append(f"\n▪ {t['الاختبار']} - المتغير: {t['المتغير']}")
                for k, v in t.items():
                    if k not in ['الاختبار', 'التفسير']:
                        lines.append(f"    {k}: {v}")

        lines.extend([
            "",
            "=" * 60,
            "المطلوب: اكتب فصل نتائج أكاديمي شاملاً يتضمن:",
            "=" * 60,
            "",
            "1. مقدمة (10-15 سطر): تقدم سياق الدراسة وأهمية النتائج.",
            "2. الخصائص الديموغرافية (200-300 كلمة): وصف تفصيلي لتوزيع العينة مع تفسير دلالة كل متغير.",
            "3. لكل محور (200-300 كلمة لكل محور):",
            "   - وصف المتوسط العام وتصنيفه على مقياس ليكرت.",
            "   - تحليل البنود الأعلى والأدنى مع تفسير الدلالة.",
            "   - تحليل نتائج One Sample T-Test مع ذكر القيم الإحصائية.",
            "   - تفسير معامل الثبات (Cronbach's Alpha).",
            "4. الفروق الديموغرافية (200-300 كلمة): تحليل الفروق المعنوية وتفسيرها نظرياً.",
            "5. المناقشة (400-500 كلمة): مقارنة النتائج بالدراسات السابقة وربطها بالإطار النظري.",
            "6. الخلاصة (300-400 كلمة): ملخص النتائج الرئيسية والإجابة عن أسئلة الدراسة.",
            "7. التوصيات (200-300 كلمة): توصيات عملية للباحثين والممارسين.",
            "8. محدودات الدراسة (100-150 كلمة).",
            "",
            "اكتب النص جاهزاً للنسخ المباشر. لا تختصر. استخدم أسلوباً أكاديمياً رصيناً.",
            "لا تذكر أبداً أن النص مولد آلياً أو بواسطة أي برنامج.",
            "",
        ])

        return "\n".join(lines)

    def _fallback(self, title, axes_results, demographics, group_var, n):
        lines = [
            f"فصل نتائج الدراسة: {title}",
            "",
            "=" * 60,
            "1. مقدمة",
            "=" * 60,
            f"تناولت هذه الدراسة موضوع '{title}' بعينة قوامها {n} فرد. وتهدف الدراسة إلى تحليل البيانات الإحصائية المستخلصة من الاستبيان واستخلاص النتائج ذات الدلالة الإحصائية.",
            "",
            "=" * 60,
            "2. الخصائص الديموغرافية للعينة",
            "=" * 60,
        ]

        for var_name, freq_table in demographics.items():
            lines.append(f"\n▪ {var_name}:")
            lines.append(freq_table.to_string(index=False))
            lines.append(f"\nيوضح الجدول أعلاه توزيع المستجيبين على متغير {var_name}.")

        lines.extend([
            "",
            "=" * 60,
            "3. تحليل محاور الاستبيان",
            "=" * 60,
        ])

        for axis in axes_results:
            lines.append(f"\n▪ المحور: {axis.name}")
            lines.append(f"المتوسط العام: {axis.overall_mean} (μ=3)")
            lines.append(f"الانحراف المعياري: {axis.overall_std}")
            lines.append(f"معامل الثبات: {axis.cronbach_alpha or 'غير محسوب'}")

            if axis.item_stats is not None and not axis.item_stats.empty:
                lines.append("إحصائيات البنود:")
                lines.append(axis.item_stats.to_string(index=False))

            lines.append("\nنتائج One Sample T-Test:")
            for t in axis.one_sample_tests:
                lines.append(f"  • {t['المتغير']}: M={t['المتوسط']}, t={t['قيمة t']}, p={t['قيمة p']}, d={t['حجم التأثير d']}")

            if axis.overall_mean >= 4.21:
                level = "موافق بشدة"
            elif axis.overall_mean >= 3.41:
                level = "موافق"
            elif axis.overall_mean >= 2.61:
                level = "محايد"
            elif axis.overall_mean >= 1.81:
                level = "غير موافق"
            else:
                level = "غير موافق بشدة"

            lines.append(f"\nتصنيف المحور: {level}")

        all_group_tests = []
        for axis in axes_results:
            all_group_tests.extend(axis.group_tests)

        if all_group_tests:
            lines.extend(["", "=" * 60, f"4. الفروق الديموغرافية", "=" * 60])
            for t in all_group_tests:
                lines.append(f"\n▪ {t['الاختبار']} - {t['المتغير']}: {t['النتيجة']}")

        lines.extend([
            "",
            "=" * 60,
            "5. الخلاصة والتوصيات",
            "=" * 60,
            "",
            "خلاصة:",
            "أظهرت نتائج الدراسة مجموعة من النتائج الإحصائية المهمة التي تساهم في فهم الظاهرة المدروسة. يُوصى بإجراء دراسات مستقبلية تتناول عينات أكبر وأكثر تنوعاً.",
            "",
            "توصيات:",
            "1. تطبيق نتائج الدراسة في الممارسة العملية.",
            "2. إجراء دراسات مقارنة في بيئات مختلفة.",
            "3. تطوير أدوات قياس أكثر دقة.",
            "4. دراسة المتغيرات الوسيطة والمعدلة.",
            "",
            "نصيحة: لتشغيل خدمة التحليل على GPU 8GB:",
            "  1. ollama pull llama3.2:3b",
            '  2. غيّر في main.py: ollama_model="llama3.2:3b"',
        ])

        return "\n".join(lines)
