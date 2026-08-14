"""🤖 مراسل Ollama - محسّن لـ GPU 8GB"""
import pandas as pd
from typing import Dict, List, Optional
from rich.console import Console

console = Console()

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


class AIReporter:
    """مراسل Ollama - يقبل model و base_url"""

    def __init__(self, model="llama3.1", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.client = None
        if HAS_OLLAMA:
            try:
                self.client = ollama.Client(host=base_url)
            except Exception as e:
                console.print(f"[yellow]⚠️ Ollama: {e}[/yellow]")

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
            console.print("[red]❌ Ollama غير متاح. شغّل: ollama serve[/red]")
            return self._fallback(title, axes_results)

        console.print("[cyan]🤖 جاري طلب التقرير من Ollama...[/cyan]")
        console.print("[yellow]⚠️ إذا تجمد البرنامج، غيّر num_ctx في الكود أو استخدم llama3.2:3b[/yellow]")

        prompt = self._build_prompt(title, demographics, axes_results, group_var, n)

        try:
            resp = self.client.generate(
                model=self.model,
                prompt=prompt,
                system=self._system_prompt(),
                options={
                    "temperature": 0.25,
                    "num_ctx": 4096,
                    "num_predict": 3000,
                }
            )
            text = resp.get("response", "")

            if not text or len(text) < 500:
                console.print("[yellow]⚠️ التقرير قصير - ربما نفد VRAM. محاولة بنموذج أخف...[/yellow]")
                return self._retry_lighter(title, demographics, axes_results, group_var, n)

            console.print(f"[green]✅ تم استلام تقرير ({len(text)} حرف)[/green]")
            return text

        except Exception as e:
            console.print(f"[red]❌ خطأ Ollama: {e}[/red]")
            return self._fallback(title, axes_results)

    def _retry_lighter(self, title, demographics, axes_results, group_var, n):
        try:
            console.print("[cyan]🔄 محاولة بـ llama3.2:3b...[/cyan]")
            resp = self.client.generate(
                model="llama3.2:3b",
                prompt=self._build_prompt(title, demographics, axes_results, group_var, n),
                system=self._system_prompt(),
                options={"temperature": 0.25, "num_ctx": 4096, "num_predict": 3000}
            )
            text = resp.get("response", "")
            console.print(f"[green]✅ تم الاستلام ({len(text)} حرف)[/green]")
            return text
        except Exception as e:
            console.print(f"[red]❌ فشل: {e}[/red]")
            return self._fallback(title, axes_results)

    def _system_prompt(self):
        return """أنت أستاذ جامعي متخصص في الإحصاء. تكتب فصول نتائج رسائل الماجستير بالعربية الفصحى.

قواعد:
1. استخدم فقط الأرقام المقدمة.
2. صنّف ليكرت 1-5: 4.21-5.00 موافق بشدة | 3.41-4.20 موافق | 2.61-3.40 محايد | 1.81-2.60 غير موافق | 1.00-1.80 غير موافق بشدة.
3. اذكر t و p و d.
4. اكتب 1200-2000 كلمة.
5. اختتم بخلاصة + توصيات.
6. أسلوب أكاديمي رصين."""

    def _build_prompt(self, title, demographics, axes_results, group_var, n):
        lines = [
            f"اكتب فصل نتائج شاملاً (1200-2000 كلمة) لرسالة ماجستير.",
            f"عنوان: {title}",
            f"العينة: {n} فرد",
            "",
            "=" * 50,
            "القسم الأول: الديموغرافيات",
            "=" * 50,
        ]

        for var_name, freq_table in demographics.items():
            lines.append(f"\n▪ {var_name}:")
            lines.append(freq_table.to_string(index=False))

        lines.extend([
            "",
            "=" * 50,
            "القسم الثاني: المحاور (ليكرت 1-5، μ=3)",
            "=" * 50,
        ])

        for axis in axes_results:
            lines.append(f"\n▪ {axis.name}: M={axis.overall_mean}, SD={axis.overall_std}, α={axis.cronbach_alpha or 'N/A'}")
            if axis.item_stats is not None and not axis.item_stats.empty:
                lines.append(axis.item_stats.to_string(index=False))
            lines.append("\nOne Sample T-Test:")
            for t in axis.one_sample_tests:
                lines.append(f"  • {t['المتغير']}: M={t['المتوسط']}, t={t['قيمة t']}, p={t['قيمة p']}, d={t['حجم التأثير d']}, {t['الاتجاه']}")

        all_group_tests = []
        for axis in axes_results:
            all_group_tests.extend(axis.group_tests)

        if all_group_tests:
            lines.extend(["", "=" * 50, f"القسم الثالث: الفروق ({group_var})", "=" * 50])
            for t in all_group_tests:
                lines.append(f"\n▪ {t['الاختبار']} - {t['المتغير']}: p={t['قيمة p']}, {t['النتيجة']}")

        lines.extend([
            "",
            "المطلوب:",
            "1. مقدمة (5-7 أسطر).",
            "2. ديموغرافيات (150-200 كلمة).",
            "3. لكل محور (100-150 كلمة): المتوسط، البنود العالية/المنخفضة، T-Test.",
            "4. الفروق إن وجدت.",
            "5. خلاصة + توصيات.",
            "",
            "اكتب النص جاهزاً للنسخ. لا تختصر.",
        ])

        return "\n".join(lines)

    def _fallback(self, title, axes_results):
        lines = [f"فصل نتائج: {title}\n", "⚠️ Ollama غير متاح أو نفد VRAM.\n"]
        for axis in axes_results:
            lines.append(f"\n▪ {axis.name}: M={axis.overall_mean}, SD={axis.overall_std}, α={axis.cronbach_alpha}")
        lines.append("\n\n💡 نصيحة: لتشغيل Ollama على GPU 8GB:")
        lines.append("   1. ollama pull llama3.2:3b")
        lines.append('   2. غيّر في main.py: ollama_model="llama3.2:3b"')
        return "\n".join(lines)
