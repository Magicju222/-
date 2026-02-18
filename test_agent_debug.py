"""
自动化测试 Agent 分析过程，检测并修复 bug
"""
import os
import sys
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

# 初始化 Agent 分析器
print("🤖 初始化 Agent 分析器...")
analyzer = AgentAnalyzer()
print(f"✅ Agent 分析器初始化完成，使用模型: {analyzer.model}")
print()

# 执行分析
print("🔍 开始 Agent 驱动的数据分析...")
print("=" * 70)

try:
    result = analyzer.analyze(
        df=df,
        context="这是一份销售数据，需要分析销售额、成本、利润之间的关系，以及地区和产品类别的表现。"
    )
    
    print("\n" + "=" * 70)
    print("✅ 分析完成！")
    print()
    
    # 显示执行步骤
    print(f"📊 执行了 {len(result.steps)} 个步骤:")
    for step in result.steps:
        status_icon = "✅" if step.tool_result and step.tool_result.success else "❌" if step.action == "error" else "ℹ️"
        print(f"\n  {status_icon} 步骤 {step.step_number}: {step.action}")
        if step.thought:
            print(f"     思考: {step.thought[:150]}...")
        if step.observation:
            obs = step.observation[:200] + "..." if len(step.observation) > 200 else step.observation
            print(f"     观察: {obs}")
    
    # 显示生成的代码
    if result.generated_code:
        print(f"\n📝 生成了 {len(result.generated_code)} 段代码")
    
    # 显示生成的图表
    if result.visualizations:
        print(f"\n📈 生成了 {len(result.visualizations)} 个图表")
    
    # 显示最终报告
    print("\n📄 最终分析报告:")
    print("=" * 70)
    print(result.final_report[:500] + "..." if len(result.final_report) > 500 else result.final_report)
    print("=" * 70)
    
    # 检查是否有错误步骤
    error_steps = [s for s in result.steps if s.action == "error"]
    if error_steps:
        print(f"\n⚠️  发现 {len(error_steps)} 个错误步骤")
        for step in error_steps:
            print(f"   - 步骤 {step.step_number}: {step.observation}")
        sys.exit(1)
    else:
        print("\n✅ 所有步骤执行成功，没有错误！")
        
except Exception as e:
    print(f"\n❌ 分析失败: {e}")
    print("\n详细错误信息:")
    traceback.print_exc()
    sys.exit(1)
