#!/bin/bash

# Master Pipeline Runner Script
# استخدام: bash run.sh

echo "==============================================="
echo "🚀 Master Pipeline Extractor"
echo "==============================================="
echo ""
echo "تأكد من:"
echo "✓ Google Drive مربوط"
echo "✓ الملفات المراد استخراجها موجودة في Drive"
echo ""
read -p "هل تريد المتابعة؟ (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "✗ تم الإلغاء"
    exit 1
fi

echo ""
echo "🔧 بدء البايبلاين..."
python3 master_pipeline_colab.py

echo ""
echo "✅ انتهى البايبلاين!"
echo "النتيجة موجودة في: /content/drive/MyDrive/ORGANIZED_MASTER_PROJECT"
