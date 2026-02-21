"""
测试特定错误案例
"""
import pandas as pd
from agent_analyzer import SecureCodeExecutor, ToolResult

def test_specific_cases():
    """测试特定错误案例"""
    print("="*80)
    print("测试特定错误案例")
    print("="*80)
    
    # 创建测试数据
    fleet_distribution = pd.DataFrame({
        'type': ['A', 'B', 'A', 'C'],
        'count': [10, 20, 15, 5]
    })
    detail_data = pd.DataFrame({
        'category': ['X', 'Y', 'X', 'Z'],
        'value': [100, 200, 150, 50]
    })
    df_clean = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': [4, 5, 6]
    })
    
    dfs = {
        'fleet_distribution': fleet_distribution,
        'detail_data': detail_data,
        'df_clean': df_clean
    }
    
    executor = SecureCodeExecutor(dfs)
    
    # 测试1: to_string
    code1 = "result = fleet_distribution.to_string()\nprint(result)"
    is_safe, msg = executor.validate_code(code1)
    print(f"\n1. fleet_distribution.to_string():")
    print(f"   验证结果: {'通过' if is_safe else '失败'}")
    print(f"   消息: {msg}")
    if is_safe:
        result = executor.execute(code1)
        print(f"   执行结果: {'成功' if result.success else '失败'}")
        if not result.success:
            print(f"   错误: {result.error}")
    
    # 测试2: groupby
    code2 = "result = detail_data.groupby('category')['value'].sum()\nprint(result)"
    is_safe2, msg2 = executor.validate_code(code2)
    print(f"\n2. detail_data.groupby():")
    print(f"   验证结果: {'通过' if is_safe2 else '失败'}")
    print(f"   消息: {msg2}")
    if is_safe2:
        result2 = executor.execute(code2)
        print(f"   执行结果: {'成功' if result2.success else '失败'}")
        if not result2.success:
            print(f"   错误: {result2.error}")
    
    # 测试3: df_clean
    code3 = "result = df_clean['col1'].sum()\nprint(result)"
    is_safe3, msg3 = executor.validate_code(code3)
    print(f"\n3. df_clean['col1'].sum():")
    print(f"   验证结果: {'通过' if is_safe3 else '失败'}")
    print(f"   消息: {msg3}")
    if is_safe3:
        result3 = executor.execute(code3)
        print(f"   执行结果: {'成功' if result3.success else '失败'}")
        if not result3.success:
            print(f"   错误: {result3.error}")
    
    # 测试4: import语句
    code4 = "import pandas as pd\nprint(pd.__version__)"
    is_safe4, msg4 = executor.validate_code(code4)
    print(f"\n4. import pandas as pd:")
    print(f"   验证结果: {'通过' if is_safe4 else '失败'}")
    print(f"   消息: {msg4}")
    
    print("\n" + "="*80)
    print("测试完成!")
    print("="*80)

if __name__ == '__main__':
    test_specific_cases()
