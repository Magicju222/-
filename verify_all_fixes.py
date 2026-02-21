"""
验证所有代码审查修复
"""
import os
import sys

def test_secure_code_executor():
    """测试安全代码执行器"""
    print("="*80)
    print("测试1: 安全代码执行器")
    print("="*80)
    
    from agent_analyzer import SecureCodeExecutor, ToolResult
    import pandas as pd
    
    # 创建测试数据
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6]
    })
    dfs = {'test': df}
    
    executor = SecureCodeExecutor(dfs)
    
    # 测试安全代码
    safe_code = "result = df['A'].sum()\nprint(result)"
    is_safe, msg = executor.validate_code(safe_code)
    print(f"✓ 安全代码验证: {'通过' if is_safe else '失败'} - {msg}")
    
    # 测试危险代码（导入os）
    dangerous_code = "import os\nos.system('ls')"
    is_safe, msg = executor.validate_code(dangerous_code)
    print(f"✓ 危险代码检测: {'通过' if not is_safe else '失败'} - {msg}")
    
    # 测试危险代码（使用eval）
    dangerous_code2 = "eval('1+1')"
    is_safe, msg = executor.validate_code(dangerous_code2)
    print(f"✓ eval检测: {'通过' if not is_safe else '失败'} - {msg}")
    
    # 测试执行安全代码
    result = executor.execute(safe_code)
    print(f"✓ 代码执行: {'成功' if result.success else '失败'}")
    
    print()

def test_backend_api():
    """测试后端API"""
    print("="*80)
    print("测试2: 后端API更新")
    print("="*80)
    
    # 检查后端API文件
    api_file = 'backend/app/api/v1/endpoints/users.py'
    if os.path.exists(api_file):
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'update_user_role' in content:
            print("✓ 后端API添加update_user_role端点")
        else:
            print("✗ 后端API缺少update_user_role端点")
        
        if 'role_data' in content:
            print("✓ API接收role_data参数")
        else:
            print("✗ API未正确接收参数")
    else:
        print(f"✗ API文件不存在: {api_file}")
    
    print()

def test_frontend_no_service_key():
    """测试前端不再使用Service Role Key"""
    print("="*80)
    print("测试3: 前端移除Service Role Key")
    print("="*80)
    
    user_mgmt_file = 'admin/user_management.py'
    if os.path.exists(user_mgmt_file):
        with open(user_mgmt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'SUPABASE_SERVICE_KEY' not in content:
            print("✓ 前端代码已移除SUPABASE_SERVICE_KEY")
        else:
            print("✗ 前端代码仍包含SUPABASE_SERVICE_KEY")
        
        if 'requests.put' in content and 'api_url' in content:
            print("✓ 前端使用后端API调用")
        else:
            print("✗ 前端未正确使用后端API")
    else:
        print(f"✗ 文件不存在: {user_mgmt_file}")
    
    print()

def test_large_file_handling():
    """测试大文件处理"""
    print("="*80)
    print("测试4: 大文件分块处理")
    print("="*80)
    
    cleaner_file = 'cleaner.py'
    if os.path.exists(cleaner_file):
        with open(cleaner_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'large_file_threshold' in content:
            print("✓ 添加大文件阈值设置")
        else:
            print("✗ 缺少大文件阈值设置")
        
        if 'csv_chunksize' in content:
            print("✓ 添加CSV分块大小设置")
        else:
            print("✗ 缺少CSV分块大小设置")
        
        if 'pd.read_csv' in content and 'chunksize' in content:
            print("✓ CSV使用分块读取")
        else:
            print("✗ CSV未使用分块读取")
    else:
        print(f"✗ 文件不存在: {cleaner_file}")
    
    print()

def test_requirements_locked():
    """测试依赖包版本锁定"""
    print("="*80)
    print("测试5: 依赖包版本锁定")
    print("="*80)
    
    req_file = 'requirements.txt'
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有版本号（==）
        lines = content.split('\n')
        versioned = [l for l in lines if '==' in l and not l.startswith('#')]
        unversioned = [l for l in lines if l.strip() and not l.startswith('#') and '==' not in l and l.strip() not in ['', '\n']]
        
        print(f"✓ 已锁定版本的包: {len(versioned)}个")
        for pkg in versioned[:5]:
            print(f"  - {pkg.strip()}")
        if len(versioned) > 5:
            print(f"  ... 还有{len(versioned)-5}个")
        
        if unversioned:
            print(f"✗ 未锁定版本的包: {len(unversioned)}个")
            for pkg in unversioned:
                print(f"  - {pkg.strip()}")
        else:
            print("✓ 所有包都已锁定版本")
    else:
        print(f"✗ 文件不存在: {req_file}")
    
    # 检查后端的requirements.txt
    backend_req = 'backend/requirements.txt'
    if os.path.exists(backend_req):
        with open(backend_req, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '==' in content:
            print("✓ 后端依赖包已锁定版本")
        else:
            print("✗ 后端依赖包未锁定版本")
    else:
        print(f"✗ 文件不存在: {backend_req}")
    
    print()

def main():
    """主函数"""
    print("\n" + "="*80)
    print("代码审查修复验证")
    print("="*80 + "\n")
    
    try:
        test_secure_code_executor()
    except Exception as e:
        print(f"安全代码执行器测试失败: {e}\n")
    
    try:
        test_backend_api()
    except Exception as e:
        print(f"后端API测试失败: {e}\n")
    
    try:
        test_frontend_no_service_key()
    except Exception as e:
        print(f"前端测试失败: {e}\n")
    
    try:
        test_large_file_handling()
    except Exception as e:
        print(f"大文件处理测试失败: {e}\n")
    
    try:
        test_requirements_locked()
    except Exception as e:
        print(f"依赖包测试失败: {e}\n")
    
    print("="*80)
    print("验证完成!")
    print("="*80)

if __name__ == '__main__':
    main()
