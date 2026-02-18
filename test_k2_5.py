"""
测试 Kimi K2.5 模型 API - 尝试不同的模型名称
"""
from openai import OpenAI

api_key = "sk-f34Brzt6NSbS3MIKlWB5G9ZuCCt554alGh5tHE0x1PWpq5QJ"
base_url = "https://api.moonshot.cn/v1"

# 尝试不同的模型名称
model_names = [
    "kimi-k2-5",
    "kimi-k2.5",
    "kimi-k2.5-latest",
    "kimi-k2.5-202501",
    "moonshot-v1-8k",  # 回退到默认模型
]

client = OpenAI(api_key=api_key, base_url=base_url)

print("🧪 测试不同的 Kimi K2.5 模型名称")
print("=" * 50)

for model in model_names:
    print(f"\n🔍 尝试模型: {model}")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "你好"}
            ],
            max_tokens=50
        )
        print(f"   ✅ 成功！模型: {response.model}")
        print(f"   📝 回复: {response.choices[0].message.content[:50]}...")
        print(f"\n🎯 正确的模型名称是: {model}")
        break
    except Exception as e:
        error_msg = str(e)
        if "Not found" in error_msg:
            print(f"   ❌ 模型不存在")
        elif "Permission" in error_msg:
            print(f"   ❌ 没有权限访问此模型")
        else:
            print(f"   ❌ 错误: {error_msg[:100]}")

print("\n" + "=" * 50)
print("💡 说明：")
print("   Kimi K2.5 可能需要特殊的 API 权限或不同的调用方式")
print("   建议访问 https://platform.moonshot.cn/docs 查看最新文档")
