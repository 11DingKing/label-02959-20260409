#!/bin/bash
# 初始化测试数据脚本

echo "🚀 正在生成测试数据..."

cd /app

# 生成示例数据
python3 data/sample_leads.py

echo ""
echo "✅ 初始化完成！"
echo ""
echo "📁 测试数据文件位于 /app/data/ 目录："
ls -la /app/data/*.xlsx /app/data/*.csv 2>/dev/null || echo "  (无数据文件)"
echo ""
