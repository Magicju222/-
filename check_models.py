"""
使用新版 google-genai 检查可用模型
"""

from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 获取 API Key
api_key = os.getenv('LLM_API_KEY')

if not api_key or api_key == 'your-gemini-api-key-here':
    print("❌ 错误：请在 .env 文件中设置您的 Gemini API Key")
    exit(1)

print("🔑 正在使用 API Key:", api_key[:20] + "...")
print("\n📋 正在获取可用模型列表...\n")

try:
    # 创建客户端
    client = genai.Client(api_key=api_key)
    
    # 列出模型
    models = list(client.models.list())
    
    print(f"✅ 找到 {len(models)} 个模型\n")
    print("=" * 80)
    
    # 筛选支持生成内容的模型
    generation_models = []
    
    for model in models:
        model_id = model.name  # 格式: models/gemini-xxx
        display_name = getattr(model, 'display_name', 'N/A')
        
        # 检查支持的操作
        supported_actions = []
        if hasattr(model, 'supported_actions'):
            supported_actions = model.supported_actions
        
        # 只显示支持生成内容的模型
        if 'generateContent' in str(supported_actions) or 'generateContent' in str(model):
            generation_models.append({
                'id': model_id,
                'display_name': display_name,
                'actions': supported_actions
            })
    
    print(f"\n🤖 支持文本生成的模型（共 {len(generation_models)} 个）：\n")
    
    for i, model in enumerate(generation_models, 1):
        print(f"{i}. 模型 ID：{model['id']}")
        print(f"   显示名称：{model['display_name']}")
        print(f"   支持功能：{model['actions']}")
        print()
    
    print("=" * 80)
    print("\n💡 推荐使用的模型名称（复制到 .env 文件）：")
    
    # 推荐模型
    recommended = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash', 'gemini-1.5-pro']
    found_recommended = []
    
    for model in generation_models:
        model_name = model['id'].replace('models/', '')
        for rec in recommended:
            if rec in model_name:
                found_recommended.append(model_name)
                break
    
    if found_recommended:
        for name in found_recommended[:3]:
            print(f'   LLM_MODEL="{name}"')
    else:
        # 如果没有找到推荐的，显示前3个
        for model in generation_models[:3]:
            name = model['id'].replace('models/', '')
            print(f'   LLM_MODEL="{name}"')
    
    print("\n📝 使用说明：")
    print("   1. 复制上面的模型名称")
    print("   2. 粘贴到 .env 文件的 LLM_MODEL 行")
    print("   3. 重启 Streamlit 服务")
    
except Exception as e:
    print(f"❌ 错误：{str(e)}")
    print("\n可能的原因：")
    print("1. API Key 无效或已过期")
    print("2. 网络连接问题（需要能访问 Google 服务）")
    print("3. API Key 没有访问 Gemini 的权限")
    print("\n💡 建议：")
    print("   由于网络问题，您可以直接使用以下常用模型名称：")
    print('   LLM_MODEL="gemini-2.0-flash"')
