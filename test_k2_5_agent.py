"""
测试 Kimi K2.5 的 Agent (Tool Use) 能力
尝试不同的参数组合
"""
import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import json

api_key = os.getenv('LLM_API_KEY')
base_url = "https://api.moonshot.cn/v1"

# 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_data_info",
            "description": "获取数据集的基本信息",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "执行 Python 代码",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python代码"}
                },
                "required": ["code"]
            }
        }
    }
]

# 测试不同的模型名称和参数
model_names = [
    "kimi-k2.5",
    "kimi-k2-turbo-preview",
    "kimi-k2-turbo",
    "moonshot-v1-8k"
]

print("=" * 70)
print("🧪 测试 Kimi K2.5 Agent (Tool Use) 能力")
print("=" * 70)

for model in model_names:
    print(f"\n{'='*70}")
    print(f"🔍 测试模型: {model}")
    print('='*70)
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    messages = [
        {"role": "system", "content": "你是一个数据分析助手，可以使用工具帮助用户分析数据。"},
        {"role": "user", "content": "请帮我计算 2 的 10 次方是多少？使用 execute_python 工具执行 Python 代码来计算。"}
    ]
    
    try:
        # 尝试 1: 基本调用
        print("\n  尝试 1: 基本 Tool Use 调用...")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=1,  # K2.5 只支持 temperature=1
            max_tokens=1000
        )
        
        message = response.choices[0].message
        print(f"    ✅ 成功！模型: {response.model}")
        
        if message.tool_calls:
            print(f"    🛠️  模型调用了工具:")
            for tc in message.tool_calls:
                print(f"       - {tc.function.name}: {tc.function.arguments}")
        else:
            print(f"    💬 模型回复: {message.content[:100]}...")
            
    except Exception as e:
        error_msg = str(e)
        print(f"    ❌ 失败: {error_msg[:150]}")
        
        # 尝试 2: 禁用思考模式
        if "thinking" in error_msg.lower() or "reasoning" in error_msg.lower():
            try:
                print("\n  尝试 2: 禁用思考模式...")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=1,
                    max_tokens=1000,
                    extra_body={"enable_thinking": False}
                )
                print(f"    ✅ 成功（禁用思考模式）！")
            except Exception as e2:
                print(f"    ❌ 仍然失败: {str(e2)[:150]}")
        
        # 尝试 3: 不使用 tools，测试普通对话
        try:
            print("\n  尝试 3: 普通对话模式（不使用 tools）...")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=1,
                max_tokens=1000
            )
            print(f"    ✅ 普通对话成功！")
            print(f"    💬 回复: {response.choices[0].message.content[:100]}...")
        except Exception as e3:
            print(f"    ❌ 普通对话也失败: {str(e3)[:150]}")

print("\n" + "=" * 70)
print("📊 测试完成")
print("=" * 70)
