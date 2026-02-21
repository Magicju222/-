"""
测试执行上下文保留
验证多次执行时代码中创建的变量可以被后续代码访问
"""
import pandas as pd
from agent_analyzer import DataAnalysisTools, ToolResult

def test_context_preservation():
    """测试执行上下文保留"""
    print("="*80)
    print("测试执行上下文保留")
    print("="*80)
    
    # 创建测试数据
    df1 = pd.DataFrame({
        'id': [1, 2, 3],
        'value': [10, 20, 30]
    })
    df2 = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['A', 'B', 'C']
    })
    
    dfs = {
        'raw_data': df1,
        'ref_data': df2
    }
    
    # 使用 DataAnalysisTools（它会保持 SecureCodeExecutor 单例）
    tools = DataAnalysisTools(dfs)
    
    # 测试1: 第一次执行，创建新变量
    code1 = """
# 数据清洗
df_clean = raw_data.copy()
df_clean['value_doubled'] = df_clean['value'] * 2
print("步骤1: 创建了 df_clean")
print(df_clean)
"""
    print("\n1. 第一次执行（创建 df_clean）:")
    result1 = tools.execute_python(code1)
    print(f"   执行结果: {'成功' if result1.success else '失败'}")
    if result1.success:
        print(f"   输出: {result1.result}")
    else:
        print(f"   错误: {result1.error}")
    
    # 测试2: 第二次执行，访问第一次创建的变量
    code2 = """
# 使用第一次创建的变量
print("步骤2: 访问 df_clean")
print(df_clean.head())
total = df_clean['value_doubled'].sum()
print(f"总和: {total}")
"""
    print("\n2. 第二次执行（访问 df_clean）:")
    result2 = tools.execute_python(code2)
    print(f"   执行结果: {'成功' if result2.success else '失败'}")
    if result2.success:
        print(f"   输出: {result2.result}")
    else:
        print(f"   错误: {result2.error}")
    
    # 测试3: 第三次执行，合并数据
    code3 = """
# 合并数据
df_merged = df_clean.merge(ref_data, on='id')
print("步骤3: 创建了 df_merged")
print(df_merged)
"""
    print("\n3. 第三次执行（创建 df_merged）:")
    result3 = tools.execute_python(code3)
    print(f"   执行结果: {'成功' if result3.success else '失败'}")
    if result3.success:
        print(f"   输出: {result3.result}")
    else:
        print(f"   错误: {result3.error}")
    
    # 测试4: 第四次执行，访问之前创建的所有变量
    code4 = """
# 访问所有之前创建的变量
print("步骤4: 访问所有变量")
print("df_clean 行数:", len(df_clean))
print("df_merged 行数:", len(df_merged))
print("分析完成!")
"""
    print("\n4. 第四次执行（访问所有变量）:")
    result4 = tools.execute_python(code4)
    print(f"   执行结果: {'成功' if result4.success else '失败'}")
    if result4.success:
        print(f"   输出: {result4.result}")
    else:
        print(f"   错误: {result4.error}")
    
    # 测试5: 定义函数
    code5 = """
# 定义辅助函数
def calculate_ratio(a, b):
    return a / b if b != 0 else 0

ratio = calculate_ratio(100, 200)
print(f"步骤5: 函数计算结果 = {ratio}")
"""
    print("\n5. 第五次执行（定义函数）:")
    result5 = tools.execute_python(code5)
    print(f"   执行结果: {'成功' if result5.success else '失败'}")
    if result5.success:
        print(f"   输出: {result5.result}")
    else:
        print(f"   错误: {result5.error}")
    
    print("\n" + "="*80)
    print("测试完成!")
    print("="*80)

if __name__ == '__main__':
    test_context_preservation()
