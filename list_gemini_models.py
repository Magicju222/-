"""
列出所有可用的 Gemini 模型
运行此脚本查看您的 API Key 可以访问哪些模型
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 获取 API Key
api_key = os.getenv('LLM_API_KEY')

if not api_key or api_key == 'your-gemini-api-key-here':
    print("❌ 错误：请在 .env 文件中设置您的 Gemini API Key")
    print("   文件位置：e:\\徐衡文档\\AI\\Trae EXCEL\\.env")
    print("   修改这一行：LLM_API_KEY=\"your-gemini-api-key-here\"")
    print("   改为：LLM_API_KEY=\"AIzaSy...您的实际密钥...\"")
    exit(1)

# 配置 API
print("🔑 正在使用 API Key:", api_key[:20] + "..." if len(api_key) > 20 else api_key)
genai.configure(api_key=api_key)

print("\n📋 正在获取可用模型列表...\n")

try:
    # 列出所有模型
    models = list(genai.list_models())
    
    print(f"✅ 找到 {len(models)} 个模型\n")
    print("=" * 80)
    
    # 筛选出生成模型（支持 generateContent 的模型）
    generation_models = []
    
    for model in models:
        model_name = model.name
        display_name = getattr(model, 'display_name', 'N/A')
        description = getattr(model, 'description', 'N/A')
        
        # 检查是否支持生成内容
        supported_actions = []
        if 'generateContent' in str(model.supported_generation_methods):
            supported_actions.append('生成文本')
        if 'embedContent' in str(model.supported_generation_methods):
            supported_actions.append('生成嵌入')
        
        if 'generateContent' in str(model.supported_generation_methods):
            generation_models.append({
                'name': model_name,
                'display_name': display_name,
                'description': description[:100] + '...' if len(description) > 100 else description,
                'actions': supported_actions
            })
    
    print(f"🤖 支持文本生成的模型（共 {len(generation_models)} 个）：\n")
    
    for i, model in enumerate(generation_models, 1):
        print(f"{i}. 模型名称：{model['name']}")
        print(f"   显示名称：{model['display_name']}")
        print(f"   描述：{model['description']}")
        print(f"   支持功能：{', '.join(model['actions'])}")
        print()
    
    print("=" * 80)
    print("\n💡 推荐使用的模型名称：")
    print("   • gemini-2.0-flash（最新、最快）")
    print("   • gemini-2.0-flash-lite（轻量级）")
    print("   • gemini-1.5-flash（上一代）")
    print("\n📝 使用说明：")
    print("   在 .env 文件中设置：")
    print(f'   LLM_MODEL="gemini-2.0-flash"')
    
except Exception as e:
    print(f"❌ 错误：{str(e)}")
    print("\n可能的原因：")
    print("1. API Key 无效或已过期")
    print("2. 网络连接问题")
    print("3. API Key 没有访问 Gemini 的权限")
