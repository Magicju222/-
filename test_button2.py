"""
测试批量清洗按钮的 Playwright 脚本 - 改进版
"""
from playwright.sync_api import sync_playwright
import time

def test_button():
    with sync_playwright() as p:
        # 启动浏览器（非无头模式以便观察）
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        
        # 访问应用
        print("访问应用...")
        page.goto('http://localhost:8501')
        
        # 等待更长时间让应用加载
        print("等待应用加载...")
        time.sleep(5)
        
        # 截图查看初始状态
        page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\screenshot_1_initial.png', full_page=True)
        print("已截图: screenshot_1_initial.png")
        
        # 获取页面内容
        content = page.content()
        print(f"页面内容长度: {len(content)}")
        
        # 查找所有按钮
        all_buttons = page.locator('button').all()
        print(f"页面上的所有按钮 ({len(all_buttons)} 个):")
        for i, btn in enumerate(all_buttons):
            try:
                text = btn.inner_text()
                visible = btn.is_visible()
                print(f"  按钮 {i}: '{text}' (visible: {visible})")
            except Exception as e:
                print(f"  按钮 {i}: [错误: {e}]")
        
        # 查找文件上传区域
        file_inputs = page.locator('input[type="file"]').all()
        print(f"\n找到 {len(file_inputs)} 个文件上传输入框")
        
        # 查找包含"上传"或"选择文件"的文本
        upload_texts = page.locator('text=/上传|选择文件|Upload|Drag|Drop/i').all()
        print(f"找到 {len(upload_texts)} 个上传相关文本元素")
        for i, elem in enumerate(upload_texts[:5]):
            try:
                text = elem.inner_text()
                print(f"  文本 {i}: '{text}'")
            except:
                pass
        
        browser.close()
        print("测试完成")

if __name__ == "__main__":
    test_button()
