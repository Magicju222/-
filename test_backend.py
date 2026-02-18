"""
测试后端服务和数据库连接
"""
import requests
import sys

def test_backend():
    base_url = "http://localhost:8000"
    
    print("🔍 测试后端服务...")
    print(f"   地址: {base_url}")
    
    # 测试根路径
    try:
        print("\n1️⃣ 测试根路径 /")
        r = requests.get(f"{base_url}/", timeout=5)
        print(f"   状态码: {r.status_code}")
        print(f"   响应: {r.text[:200]}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试健康检查
    try:
        print("\n2️⃣ 测试健康检查 /health")
        r = requests.get(f"{base_url}/health", timeout=5)
        print(f"   状态码: {r.status_code}")
        print(f"   响应: {r.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试 API 文档
    try:
        print("\n3️⃣ 测试 API 文档 /docs")
        r = requests.get(f"{base_url}/docs", timeout=5)
        print(f"   状态码: {r.status_code}")
        if r.status_code == 200:
            print("   ✅ API 文档可访问")
        else:
            print(f"   ⚠️ 状态码: {r.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    test_backend()
