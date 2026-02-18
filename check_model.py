"""
检查当前使用的模型配置
"""
import os
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("🔍 当前模型配置检查")
print("=" * 60)

# 读取环境变量
provider = os.getenv('LLM_PROVIDER', '未设置')
model = os.getenv('LLM_MODEL', '未设置')
api_key = os.getenv('LLM_API_KEY', '未设置')
base_url = os.getenv('LLM_BASE_URL', '未设置')

print(f"\n📋 配置信息：")
print(f"   提供商 (LLM_PROVIDER): {provider}")
print(f"   模型 (LLM_MODEL): {model}")
print(f"   API地址 (LLM_BASE_URL): {base_url}")
print(f"   API Key: {api_key[:20]}..." if api_key != '未设置' else "   API Key: 未设置")

print(f"\n🤖 当前使用的模型: {model}")

if 'k2.5' in model.lower() or 'k2-5' in model.lower():
    print("\n⚠️  注意：Kimi K2.5 模型存在 Tool Use 兼容性问题")
    print("   错误信息: 'thinking is enabled but reasoning_content is missing'")
    print("   建议: 使用 moonshot-v1-8k 模型进行 Agent 分析")
elif 'moonshot-v1' in model.lower():
    print("\n✅ 使用的是 Moonshot v1 系列模型")
    print("   该模型支持 Tool Use (Function Calling) 功能")
    print("   Agent 分析功能可以正常工作")
else:
    print(f"\n⚠️  未知模型: {model}")

print("\n" + "=" * 60)
print("💡 如何切换到 Kimi K2.5？")
print("=" * 60)
print("""
目前 Kimi K2.5 的 Tool Use (Function Calling) 功能存在兼容性问题，
无法与 Agent 分析功能一起使用。

如果你需要使用 Kimi K2.5，可以：
1. 修改 .env 文件: LLM_MODEL="kimi-k2.5"
2. 但 Agent 分析功能会回退到普通对话模式（不使用工具）

或者等待 Moonshot 官方修复 Tool Use 的兼容性问题。
""")
