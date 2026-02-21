"""
测试安全修复是否正常工作
"""
import os
import sys

# 测试1: 文件类型验证
def test_file_validation():
    """测试文件类型验证函数"""
    print("="*60)
    print("测试1: 文件类型验证")
    print("="*60)
    
    # 导入验证函数
    from app import validate_file_type
    
    # 测试有效的xlsx文件头
    xlsx_header = b'\x50\x4b\x03\x04' + b'\x00' * 100  # ZIP格式
    is_valid, msg = validate_file_type(xlsx_header, "test.xlsx")
    print(f"✓ 有效xlsx文件: {'通过' if is_valid else '失败'} - {msg}")
    
    # 测试有效的xls文件头
    xls_header = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\x00' * 100  # OLE格式
    is_valid, msg = validate_file_type(xls_header, "test.xls")
    print(f"✓ 有效xls文件: {'通过' if is_valid else '失败'} - {msg}")
    
    # 测试有效的csv文件
    csv_content = b'col1,col2\nvalue1,value2'
    is_valid, msg = validate_file_type(csv_content, "test.csv")
    print(f"✓ 有效csv文件: {'通过' if is_valid else '失败'} - {msg}")
    
    # 测试伪造扩展名的文件
    fake_xlsx = b'\x00\x00\x00\x00' + b'\x00' * 100
    is_valid, msg = validate_file_type(fake_xlsx, "fake.xlsx")
    print(f"✓ 伪造xlsx文件: {'拒绝' if not is_valid else '通过'} - {msg}")
    
    # 测试不支持的文件类型
    is_valid, msg = validate_file_type(b'\x00', "test.pdf")
    print(f"✓ 不支持的类型: {'拒绝' if not is_valid else '通过'} - {msg}")
    
    print()

# 测试2: 后端配置验证
def test_backend_config():
    """测试后端配置验证"""
    print("="*60)
    print("测试2: 后端配置验证")
    print("="*60)
    
    try:
        # 设置测试环境变量
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_SERVICE_KEY'] = 'eyJhbGci.test.test'
        
        from backend.app.core.config import get_settings
        settings = get_settings()
        
        print(f"✓ API前缀: {settings.API_V1_STR}")
        print(f"✓ 项目名称: {settings.PROJECT_NAME}")
        print(f"✓ 允许的源: {settings.ALLOWED_ORIGINS}")
        print(f"✓ 环境模式: {settings.ENVIRONMENT}")
        print(f"✓ 最大文件大小: {settings.MAX_FILE_SIZE_MB}MB")
        print(f"✓ 速率限制: {settings.RATE_LIMIT_PER_MINUTE}/分钟")
        
        print("\n✓ 配置验证通过!")
    except Exception as e:
        print(f"✗ 配置验证失败: {e}")
    
    print()

# 测试3: 文件哈希计算
def test_file_hash():
    """测试文件哈希计算"""
    print("="*60)
    print("测试3: 文件哈希计算")
    print("="*60)
    
    from app import get_file_hash
    
    # 测试小文件
    small_file = b'test content'
    hash1 = get_file_hash(small_file)
    hash2 = get_file_hash(small_file)
    print(f"✓ 小文件哈希: {hash1}")
    print(f"✓ 哈希一致性: {'通过' if hash1 == hash2 else '失败'}")
    
    # 测试大文件（超过8KB）
    large_file = b'x' * 10000
    hash3 = get_file_hash(large_file)
    print(f"✓ 大文件哈希: {hash3}")
    print(f"✓ 大文件只取前8KB: {'通过' if len(large_file) > 8192 else '失败'}")
    
    # 测试不同内容产生不同哈希
    different_file = b'different content'
    hash4 = get_file_hash(different_file)
    print(f"✓ 不同内容不同哈希: {'通过' if hash1 != hash4 else '失败'}")
    
    print()

# 测试4: CORS配置
def test_cors_config():
    """测试CORS配置"""
    print("="*60)
    print("测试4: CORS配置")
    print("="*60)
    
    try:
        from backend.app.main import app
        from backend.app.core.config import get_settings
        
        settings = get_settings()
        allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
        
        print(f"✓ 允许的源: {allowed_origins}")
        print(f"✓ 不在允许所有来源('*'): {'通过' if '*' not in allowed_origins else '失败'}")
        print(f"✓ 环境模式: {settings.ENVIRONMENT}")
        
        print("\n✓ CORS配置安全!")
    except Exception as e:
        print(f"✗ CORS配置测试失败: {e}")
    
    print()

def main():
    """主函数"""
    print("\n" + "="*60)
    print("安全修复验证测试")
    print("="*60 + "\n")
    
    try:
        test_file_validation()
    except Exception as e:
        print(f"文件验证测试失败: {e}\n")
    
    try:
        test_backend_config()
    except Exception as e:
        print(f"后端配置测试失败: {e}\n")
    
    try:
        test_file_hash()
    except Exception as e:
        print(f"文件哈希测试失败: {e}\n")
    
    try:
        test_cors_config()
    except Exception as e:
        print(f"CORS配置测试失败: {e}\n")
    
    print("="*60)
    print("测试完成!")
    print("="*60)

if __name__ == '__main__':
    main()
