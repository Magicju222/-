"""
检查 Moonshot API 配置和连接状态
"""
import os
from dotenv import load_dotenv
load_dotenv()

import requests

print("=" * 70)
print("🔍 Moonshot API 配置检查")
print("=" * 70)

# 读取配置
api_key = os.getenv('LLM_API_KEY')
base_url = os.getenv('LLM_BASE_URL')
model = os.getenv('LLM_MODEL')

print(f"\n📋 当前配置：")
print(f"   Base URL: {base_url}")
print(f"   Model: {model}")
print(f"   API Key: {api_key[:20]}..." if api_key else "   API Key: 未设置")

# 检查 Base URL 格式
print(f"\n🔍 Base URL 检查：")
if base_url == "https://api.moonshot.cn/v1":
    print("   ✅ 标准 Moonshot API 地址")
elif base_url == "https://api.moonshot.cn":
    print("   ⚠️  缺少 /v1 路径，建议改为: https://api.moonshot.cn/v1")
elif "moonshot" in base_url.lower():
    print(f"   ℹ️  自定义 Moonshot 地址: {base_url}")
else:
    print(f"   ❓ 非标准地址: {base_url}")

# 测试 API 连接
print(f"\n🌐 测试 API 连接：")
try:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 测试模型列表接口
    response = requests.get(
        f"{base_url}/models",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        print("   ✅ API 连接成功！")
        models = response.json().get('data', [])
        print(f"   📊 可用模型数量: {len(models)}")
        
        # 检查当前模型是否在列表中
        model_ids = [m.get('id') for m in models]
        if model in model_ids:
            print(f"   ✅ 当前模型 '{model}' 可用")
        else:
            print(f"   ⚠️  当前模型 '{model}' 不在可用列表中")
            print(f"   💡 可用模型: {', '.join(model_ids[:5])}...")
    else:
        print(f"   ❌ API 连接失败: HTTP {response.status_code}")
        print(f"   错误信息: {response.text[:200]}")
        
except Exception as e:
    print(f"   ❌ 连接错误: {e}")

# 测试聊天接口
print(f"\n💬 测试聊天接口：")
try:
    from openai import OpenAI
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "你好"}],
        max_tokens=50
    )
    
    print("   ✅ 聊天接口正常！")
    print(f"   📝 响应: {response.choices[0].message.content[:50]}...")
    print(f"   🤖 实际使用模型: {response.model}")
    
except Exception as e:
    print(f"   ❌ 聊天接口错误: {e}")

print("\n" + "=" * 70)
print("📚 Moonshot API 文档")
print("=" * 70)
print("""
官方文档: https://platform.moonshot.cn/docs
API 地址: https://api.moonshot.cn/v1
支持模型:
  - moonshot-v1-8k
  - moonshot-v1-32k
  - moonshot-v1-128k
  - kimi-k2.5
  - kimi-k2-turbo-preview
""")
