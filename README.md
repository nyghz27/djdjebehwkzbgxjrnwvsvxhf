# Master Pipeline Extractor

## 🎮 بايبلاين استخراج موارد لعبة Unity الشامل

هذا المشروع يجمع بين عدة أدوات قوية لاستخراج وتحليل موارد لعبة Unity:

### ✨ المميزات:
- **AssetRipper.CLI** - استخراج الموارد من ملفات اللعبة
- **Ghidra** - فك تشفير وتحليل الكود الأصلي IL2CPP
- **dnfile** - تحليل ملفات .NET DLL
- **PyYAML** - معالجة ملفات الإعدادات

### 📁 الملفات الرئيسية:

#### 1. `master_pipeline_colab.py`
البايبلاين الشامل المُحسّن لـ Google Colab:
- تثبيت تلقائي للمكتبات والأدوات
- استخراج موارد اللعبة باستخدام AssetRipper
- تفكيك هرمي لملفات .prefab و .asset
- تحليل ملفات IL2CPP Dump
- تصنيف منظم للملفات

#### 2. `Program.cs`
ملف C# لـ AssetRipper.CLI:
- يقبل مجلد كامل كمدخل
- يستخرج كل الملفات بشكل متكرر
- يُصدّر مشروع Unity منظم

### 🚀 التشغيل السريع (Colab):

```python
# 1. في خلية أولى:
from google.colab import drive
drive.mount('/content/drive')

# 2. في خلية ثانية:
!git clone https://github.com/nyghz27/djdjebehwkzbgxjrnwvsvxhf.git
%cd djdjebehwkzbgxjrnwvsvxhf
!python master_pipeline_colab.py
```

### 📊 النتيجة المتوقعة:

```
ORGANIZED_MASTER_PROJECT/
├── 01_Logic_Configs/          # ملفات الكود والإعدادات
├── 02_Assets_Media/           # الموارد الوسائط (صور، صوتيات)
├── 03_CSV_Data/               # ملفات البيانات
├── 04_Network_Backend/        # كود الشبكة
├── 05_Unclassified/           # ملفات غير مصنفة
├── 06_DLLs_Raw_Original/      # ملفات DLL الأصلية
└── manifest.json              # تقرير الاستخراج
```

### 🔧 المتطلبات:

- Python 3.8+
- .NET 9 SDK (يتم تثبيته تلقائياً)
- Java 21+ (لـ Ghidra)
- 50GB+ مساحة تخزين (حسب حجم اللعبة)

### ⚠️ ملاحظات مهمة:

1. **وقت التنفيذ:** قد يأخذ ساعات حسب حجم اللعبة
2. **Google Drive:** يجب ربط Drive قبل التشغيل
3. **الأخطاء غير الحرجة:** البايبلاين يستمر حتى لو فشلت مرحلة معينة
4. **الملفات الكبيرة:** يتم تقسيم تلقائياً للملفات > 50MB

### 📝 الإخراج:

ملف `manifest.json` يحتوي على:
- عدد الملفات المستخرجة في كل فئة
- عدد الأرشيفات المفكوكة
- عدد الفئات المحللة (Meshes، Classes، Methods)
- الأخطاء التي حدثت

---

**Model:** Claude 3.5 Sonnet (GitHub Copilot)
