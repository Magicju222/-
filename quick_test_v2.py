import pandas as pd
from business_semantic_report_v2 import BusinessSemanticReportGeneratorV2

# 创建测试数据
df = pd.DataFrame({
    '产品类别': ['电子产品', '服装', '食品'] * 4,
    '销售额': [150000, 80000, 45000, 200000, 95000, 52000, 180000, 72000, 48000, 220000, 85000, 50000],
    '销售量': [150, 400, 900, 200, 475, 1040, 180, 360, 960, 220, 425, 1000],
    '地区': ['华东', '华南', '华北'] * 4,
})

print("测试数据创建成功")
print(f"数据维度: {df.shape}")

# 创建生成器
gen = BusinessSemanticReportGeneratorV2(df)
print(f"数值列: {gen.numeric_columns}")
print(f"分类列: {gen.categorical_columns}")

# 测试业务指标分析
metrics = gen._analyze_business_metrics()
print(f"\n识别到 {len(metrics)} 个业务指标")
for m in metrics[:4]:
    print(f"  - {m.name}: {m.value:.2f} {m.unit}")

# 测试维度分析
dims = gen._analyze_by_dimensions()
print(f"\n识别到 {len(dims)} 个维度分析")
for d in dims[:2]:
    print(f"  - {d.dimension_name} x {d.metric_name}: {len(d.data)} 行")
    print(f"    总结: {d.summary}")

# 测试关键洞察
insights = gen._extract_key_insights()
print(f"\n提取到 {len(insights)} 个关键洞察")
for i in insights[:2]:
    print(f"  - {i.title}")

print("\n测试完成!")
