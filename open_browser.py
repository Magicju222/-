"""
打开浏览器访问项目主页
"""
import webbrowser
import time

print("🌐 正在打开项目主页...")
print("   前端地址: http://localhost:8502")
print("   后端地址: http://localhost:8000")
print("   API文档:  http://localhost:8000/docs")
print()

# 打开前端页面
webbrowser.open("http://localhost:8502")
time.sleep(1)

print("✅ 浏览器已打开！")
print()
print("📋 服务状态:")
print("   - 前端 (Streamlit): http://localhost:8502")
print("   - 后端 (FastAPI):   http://localhost:8000")
print("   - API 文档:         http://localhost:8000/docs")
