import pandas as pd
from business_semantic_report import BusinessSemanticReportGenerator

# 创建测试数据
df = pd.DataFrame({
    '销售额': [100, 200, 150, 300],
    '销售量': [10, 20, 15, 30],
    '地区': ['华东', '华南', '华东', '华南'],
    '产品': ['A', 'B', 'A', 'B']
})

print("测试数据:")
print(df)
print()

# 创建生成器
gen = BusinessSemanticReportGenerator(df)

print("数值列:", gen.numeric_columns)
print("分类列:", gen.categorical_columns)
print()

# 测试业务指标分析
metrics = gen._analyze_business_metrics()
print(f"识别到 {len(metrics)} 个业务指标:")
for m in metrics[:5]:
    print(f"  - {m.name}: {m.value:.2f} {m.unit}")
