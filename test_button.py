"""
测试批量清洗按钮的 Playwright 脚本
"""
from playwright.sync_api import sync_playwright
import time

def test_button():
    with sync_playwright() as p:
        # 启动浏览器（非无头模式以便观察）
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # 访问应用
        print("访问应用...")
        page.goto('http://localhost:8501')
        page.wait_for_load_state('networkidle')
        
        # 等待页面加载
        time.sleep(3)
        
        # 截图查看初始状态
        page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\screenshot_1_initial.png', full_page=True)
        print("已截图: screenshot_1_initial.png")
        
        # 查找文件上传按钮
        try:
            file_input = page.locator('input[type="file"]').first
            if file_input.count() > 0:
                print("找到文件上传输入框")
                # 上传测试文件
                file_input.set_input_files('e:\\徐衡文档\\AI\\Trae EXCEL\\test_data.xlsx')
                print("已上传测试文件")
                time.sleep(3)
                
                # 截图查看上传后的状态
                page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\screenshot_2_after_upload.png', full_page=True)
                print("已截图: screenshot_2_after_upload.png")
                
                # 查找"开始批量智能清洗"按钮
                button_selectors = [
                    'button:has-text("开始批量智能清洗")',
                    'button:has-text("批量清洗")',
                    '[data-testid="stButton"] button',
                    'button[kind="primary"]'
                ]
                
                button = None
                for selector in button_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.count() > 0 and btn.is_visible():
                            button = btn
                            print(f"找到按钮使用选择器: {selector}")
                            break
                    except:
                        continue
                
                if button:
                    print("点击按钮...")
                    button.click()
                    time.sleep(2)
                    
                    # 截图查看点击后的状态
                    page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\screenshot_3_after_click.png', full_page=True)
                    print("已截图: screenshot_3_after_click.png")
                    
                    # 检查是否有调试信息
                    debug_text = page.locator('text=DEBUG').all()
                    print(f"找到 {len(debug_text)} 个 DEBUG 文本元素")
                    
                    # 检查是否有"Button clicked"文本
                    clicked_text = page.locator('text=Button clicked').all()
                    print(f"找到 {len(clicked_text)} 个 'Button clicked' 文本元素")
                else:
                    print("未找到按钮!")
                    # 截图查看页面结构
                    page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\screenshot_no_button.png', full_page=True)
                    
                    # 列出所有按钮
                    all_buttons = page.locator('button').all()
                    print(f"页面上的所有按钮 ({len(all_buttons)} 个):")
                    for i, btn in enumerate(all_buttons):
                        try:
                            text = btn.inner_text()
                            visible = btn.is_visible()
                            print(f"  按钮 {i}: '{text}' (visible: {visible})")
                        except:
                            print(f"  按钮 {i}: [无法获取文本]")
            else:
                print("未找到文件上传输入框")
                page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\screenshot_no_upload.png', full_page=True)
        except Exception as e:
            print(f"错误: {e}")
            page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\screenshot_error.png', full_page=True)
        
        browser.close()
        print("测试完成")

if __name__ == "__main__":
    test_button()
