"""
完整工作流程测试 - 滚动查看更多内容
"""
from playwright.sync_api import sync_playwright
import time

def test_full_workflow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        
        print("访问应用...")
        page.goto('http://localhost:8501')
        
        print("等待30秒让应用完全加载...")
        time.sleep(30)
        
        # 截图初始状态
        page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\test_1_initial.png', full_page=True)
        print("已截图: test_1_initial.png")
        
        # 直接查找文件输入框
        print("\n查找文件输入框...")
        file_input = page.locator('input[type="file"]').first
        if file_input.count() > 0:
            print("找到文件输入框，上传文件...")
            file_input.set_input_files('e:\\徐衡文档\\AI\\Trae EXCEL\\test_data.xlsx')
            print("文件已上传")
            time.sleep(10)  # 等待文件处理
            
            # 截图上传后状态（完整页面）
            page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\test_2_after_upload.png', full_page=True)
            print("已截图: test_2_after_upload.png")
            
            # 获取页面所有文本内容
            print("\n页面文本内容:")
            text_content = page.inner_text('body')
            
            # 检查是否包含批量清洗按钮文本
            if "开始批量智能清洗" in text_content:
                print("找到 '开始批量智能清洗' 文本!")
            else:
                print("未找到 '开始批量智能清洗' 文本")
            
            # 检查是否包含选择模式按钮
            if "表头行" in text_content:
                print("找到 '表头行' 按钮")
            
            # 列出所有按钮文本
            print("\n所有按钮:")
            all_buttons = page.locator('button').all()
            for i, btn in enumerate(all_buttons):
                try:
                    text = btn.inner_text()
                    visible = btn.is_visible()
                    if visible and text.strip():
                        print(f"  [{i}] '{text}'")
                except:
                    pass
            
            # 尝试查找批量清洗按钮（使用不同的选择器）
            print("\n尝试查找批量清洗按钮...")
            selectors = [
                'button:has-text("开始批量智能清洗")',
                'button:has-text("批量清洗")',
                'button:has-text("清洗")',
                '[data-testid="stButton"] button',
                'button[kind="primary"]'
            ]
            
            for selector in selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.count() > 0:
                        text = btn.inner_text()
                        visible = btn.is_visible()
                        print(f"  选择器 '{selector}': 找到 '{text}' (visible: {visible})")
                except Exception as e:
                    print(f"  选择器 '{selector}': 错误 {e}")
        else:
            print("未找到文件输入框")
        
        browser.close()
        print("\n测试完成")

if __name__ == "__main__":
    test_full_workflow()
