"""
测试可视化库导入
"""
import pandas as pd
from agent_analyzer import SecureCodeExecutor, ToolResult

def test_visualization_import():
    """测试可视化库导入"""
    print("="*80)
    print("测试可视化库导入")
    print("="*80)
    
    # 创建测试数据
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 15, 25, 30]
    })
    dfs = {'data': df}
    
    executor = SecureCodeExecutor(dfs)
    
    # 测试1: 导入matplotlib
    code1 = """
import matplotlib.pyplot as plt
plt.figure(figsize=(8, 6))
plt.plot([1, 2, 3], [1, 4, 9])
plt.title('Test Plot')
print("matplotlib导入成功")
"""
    is_safe, msg = executor.validate_code(code1)
    print(f"\n1. 导入matplotlib.pyplot:")
    print(f"   验证结果: {'通过' if is_safe else '失败'}")
    print(f"   消息: {msg}")
    if is_safe:
        result = executor.execute(code1)
        print(f"   执行结果: {'成功' if result.success else '失败'}")
        if not result.success:
            print(f"   错误: {result.error}")
    
    # 测试2: 导入seaborn
    code2 = """
import seaborn as sns
print("seaborn版本:", sns.__version__)
print("seaborn导入成功")
"""
    is_safe2, msg2 = executor.validate_code(code2)
    print(f"\n2. 导入seaborn:")
    print(f"   验证结果: {'通过' if is_safe2 else '失败'}")
    print(f"   消息: {msg2}")
    if is_safe2:
        result2 = executor.execute(code2)
        print(f"   执行结果: {'成功' if result2.success else '失败'}")
        if not result2.success:
            print(f"   错误: {result2.error}")
    
    # 测试3: 使用sns创建图表
    code3 = """
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# 使用DataFrame创建图表
df_plot = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
sns.barplot(data=df_plot, x='x', y='y')
plt.title('Test Bar Plot')
print("图表创建成功")
"""
    is_safe3, msg3 = executor.validate_code(code3)
    print(f"\n3. 使用seaborn创建图表:")
    print(f"   验证结果: {'通过' if is_safe3 else '失败'}")
    print(f"   消息: {msg3}")
    if is_safe3:
        result3 = executor.execute(code3)
        print(f"   执行结果: {'成功' if result3.success else '失败'}")
        if not result3.success:
            print(f"   错误: {result3.error}")
    
    print("\n" + "="*80)
    print("测试完成!")
    print("="*80)

if __name__ == '__main__':
    test_visualization_import()
