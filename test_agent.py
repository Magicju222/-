"""
测试 Agent 驱动的数据分析
"""
import os
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import numpy as np
from agent_analyzer import AgentAnalyzer
import traceback

# 创建测试数据
print("📊 创建测试数据...")
np.random.seed(42)
n = 100

data = {
    '销售额': np.random.randint(1000, 50000, n),
    '成本': np.random.randint(500, 30000, n),
    '客户满意度': np.random.uniform(3.0, 5.0, n).round(2),
    '地区': np.random.choice(['北京', '上海', '广州', '深圳'], n),
    '产品类别': np.random.choice(['电子产品', '服装', '食品', '家居'], n),
}

df = pd.DataFrame(data)
df['利润'] = df['销售额'] - df['成本']

print(f"✅ 测试数据创建完成: {df.shape}")
print(f"📋 列名: {list(df.columns)}")
print()

# 初始化 Agent 分析器 - 使用 moonshot-v1-8k 模型测试
print("🤖 初始化 Agent 分析器 (使用 moonshot-v1-8k)...")
analyzer = AgentAnalyzer(model="moonshot-v1-8k")
print("✅ Agent 分析器初始化完成")
print()

# 执行分析
print("🔍 开始 Agent 驱动的数据分析...")
print("=" * 60)

try:
    result = analyzer.analyze(
        df=df,
        context="这是一份销售数据，需要分析销售额、成本、利润之间的关系，以及地区和产品类别的表现。"
    )
    
    print("\n" + "=" * 60)
    print("✅ 分析完成！")
    print()
    
    # 显示执行步骤
    print(f"📊 执行了 {len(result.steps)} 个步骤:")
    for step in result.steps:
        print(f"\n  步骤 {step.step_number}: {step.action}")
        if step.thought:
            print(f"    思考: {step.thought[:200]}...")
        if step.observation:
            print(f"    观察: {step.observation[:200]}...")
        if step.tool_result:
            if step.tool_result.success:
                print(f"    ✅ 成功")
            else:
                print(f"    ❌ 错误: {step.tool_result.error[:200]}...")
    
    # 显示生成的代码
    if result.generated_code:
        print(f"\n📝 生成了 {len(result.generated_code)} 段代码")
        for i, code in enumerate(result.generated_code[:3], 1):
            print(f"\n  代码片段 {i}:")
            print(f"    {code[:200]}...")
    
    # 显示生成的图表
    if result.visualizations:
        print(f"\n📈 生成了 {len(result.visualizations)} 个图表:")
        for path in result.visualizations:
            print(f"    - {path}")
    
    # 显示最终报告
    print("\n📄 最终分析报告:")
    print("=" * 60)
    print(result.final_report)
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 分析失败: {e}")
    print("\n详细错误信息:")
    traceback.print_exc()
