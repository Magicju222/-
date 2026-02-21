"""
生成业务语义分析报告 V2
"""
import pandas as pd
from business_semantic_report_v2 import generate_business_semantic_report

# 创建测试数据
df = pd.DataFrame({
    '产品类别': ['电子产品', '服装', '食品'] * 4,
    '销售额': [150000, 80000, 45000, 200000, 95000, 52000, 180000, 72000, 48000, 220000, 85000, 50000],
    '销售量': [150, 400, 900, 200, 475, 1040, 180, 360, 960, 220, 425, 1000],
    '地区': ['华东', '华南', '华北'] * 4,
})

print("生成业务分析报告 V2...")

# 生成报告
md_report, word_report = generate_business_semantic_report(df, title="销售业务分析报告V2")

# 保存报告
with open('business_report_v2.md', 'w', encoding='utf-8') as f:
    f.write(md_report)
print("✓ 已保存: business_report_v2.md")

with open('business_report_v2.docx', 'wb') as f:
    f.write(word_report)
print("✓ 已保存: business_report_v2.docx")

print(f"\n报告生成完成!")
print(f"Markdown报告: {len(md_report)} 字符")
print(f"Word报告: {len(word_report)} 字节")

# 显示报告预览
print("\n" + "="*80)
print("报告预览（前1500字符）:")
print("="*80)
print(md_report[:1500])
