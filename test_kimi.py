"""
测试 Kimi API 连接
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

print("=" * 60)
print("测试 Kimi API 连接")
print("=" * 60)

# 检查配置
provider = os.getenv('LLM_PROVIDER')
api_key = os.getenv('LLM_API_KEY')
base_url = os.getenv('LLM_BASE_URL')
model = os.getenv('LLM_MODEL')

print(f"\n📋 配置信息：")
print(f"   提供商: {provider}")
print(f"   API Key: {api_key[:20]}..." if api_key else "   API Key: 未设置")
print(f"   Base URL: {base_url}")
print(f"   模型: {model}")

if provider != 'moonshot':
    print(f"\n❌ 错误：提供商不是 moonshot，当前是 {provider}")
    exit(1)

if not api_key or api_key == 'your-moonshot-api-key-here':
    print("\n❌ 错误：API Key 未设置")
    exit(1)

print("\n🔄 正在测试 API 连接...")

try:
    from llm_client import LLMClient
    
    client = LLMClient()
    print(f"✅ 客户端初始化成功")
    print(f"   实际使用模型: {client.config.model}")
    print(f"   实际使用 Base URL: {client.config.base_url}")
    
    # 发送测试请求
    print("\n🔄 发送测试请求...")
    response = client.analyze(
        prompt="你好，请用一句话确认你能正常工作。",
        system_message="你是一个 helpful 的助手。",
        temperature=0.7,
        max_tokens=100
    )
    
    print(f"✅ API 测试成功！")
    print(f"\n📝 响应内容：")
    print(f"   {response}")
    
except Exception as e:
    print(f"\n❌ 错误：{str(e)}")
    import traceback
    print(f"\n详细错误：")
    traceback.print_exc()
