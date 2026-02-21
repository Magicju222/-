"""
测试DataFrame变量名访问修复
"""
import pandas as pd
from agent_analyzer import SecureCodeExecutor, ToolResult

def test_dataframe_variable_access():
    """测试DataFrame变量名访问"""
    print("="*80)
    print("测试DataFrame变量名访问")
    print("="*80)
    
    # 创建测试数据
    fleet_vehicle = pd.DataFrame({
        'vehicle_id': [1, 2, 3],
        'type': ['A', 'B', 'C'],
        'mileage': [1000, 2000, 3000]
    })
    dfs = {'fleet_vehicle': fleet_vehicle}
    
    executor = SecureCodeExecutor(dfs)
    
    # 测试1: DataFrame变量名访问（应该通过）
    code1 = "result = fleet_vehicle.sort_values('mileage')\nprint(result)"
    is_safe, msg = executor.validate_code(code1)
    print(f"\n1. DataFrame变量访问 fleet_vehicle.sort_values():")
    print(f"   验证结果: {'通过' if is_safe else '失败'}")
    print(f"   消息: {msg}")
    
    # 测试2: 执行代码
    if is_safe:
        result = executor.execute(code1)
        print(f"   执行结果: {'成功' if result.success else '失败'}")
        if not result.success:
            print(f"   错误: {result.error}")
    
    # 测试3: 危险模块访问（应该失败）
    code2 = "os.system('ls')"
    is_safe2, msg2 = executor.validate_code(code2)
    print(f"\n2. 危险模块访问 os.system():")
    print(f"   验证结果: {'通过（不安全）' if not is_safe2 else '失败（应该被拒绝）'}")
    print(f"   消息: {msg2}")
    
    # 测试4: 另一个DataFrame变量名
    sales_data = pd.DataFrame({
        'product': ['A', 'B'],
        'amount': [100, 200]
    })
    dfs2 = {'sales_data': sales_data}
    executor2 = SecureCodeExecutor(dfs2)
    
    code3 = "total = sales_data['amount'].sum()\nprint(total)"
    is_safe3, msg3 = executor2.validate_code(code3)
    print(f"\n3. DataFrame变量访问 sales_data['amount'].sum():")
    print(f"   验证结果: {'通过' if is_safe3 else '失败'}")
    print(f"   消息: {msg3}")
    
    if is_safe3:
        result3 = executor2.execute(code3)
        print(f"   执行结果: {'成功' if result3.success else '失败'}")
    
    print("\n" + "="*80)
    print("测试完成!")
    print("="*80)

if __name__ == '__main__':
    test_dataframe_variable_access()
