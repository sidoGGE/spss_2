# SurveyAI Pro 🤖📊

برنامج تحليل استبيانات احترافي بالذكاء الاصطناعي - للجامعات والأعمال.

## المميزات
- ✅ يقرأ أي ملف CSV
- ✅ اكتشاف تلقائي ذكي للمحاور والديموغرافيات
- ✅ إحصاء وصفي + One Sample T-Test + ANOVA + T-Test + ارتباطات
- ✅ Cronbach's Alpha لكل محور
- ✅ تكامل Ollama لكتابة فصول النتائج بالعربية
- ✅ تصدير Word + PDF بخط عربي صحيح
- ✅ رسوم بيانية احترافية (Bar, Pie, Histogram, Box, Correlation Heatmap)

## التثبيت
```bash
pip install -r requirements.txt
```

## تشغيل Ollama
```bash
ollama pull llama3.1
ollama serve
```

## الاستخدام
1. ضع ملف CSV في مجلد `data/`
2. عدل `main.py`:
```python
run(
    csv_path="data/ملفك.csv",
    title="عنوان دراستك",
    output_dir="output",
    ollama_model="llama3.1"
)
```
3. شغّل:
```bash
python main.py
```

## هيكل CSV المتوقع
| العمود | الوصف |
|--------|-------|
| Q1, Q2, Q3... | بنود الاستبيان (ليكرت 1-5) |
| Gender, Age... | متغيرات ديموغرافية فئوية |

المشروع **مطاطي** - يكتشف تلقائياً أي هيكل.
