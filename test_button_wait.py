"""
测试按钮 - 等待更长时间
"""
from playwright.sync_api import sync_playwright
import time

def test_button():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        
        print("访问应用...")
        page.goto('http://localhost:8501')
        
        print("等待30秒让应用完全加载...")
        time.sleep(30)
        
        # 截图
        page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\screenshot_wait.png', full_page=True)
        print("已截图: screenshot_wait.png")
        
        # 查找测试按钮
        buttons = page.locator('button').all()
        print(f"\n找到 {len(buttons)} 个按钮:")
        for i, btn in enumerate(buttons):
            try:
                text = btn.inner_text()
                visible = btn.is_visible()
                print(f"  按钮 {i}: '{text}' (visible: {visible})")
            except:
                print(f"  按钮 {i}: [无法获取]")
        
        # 尝试点击测试按钮
        test_btn = page.locator('button:has-text("TEST BUTTON")').first
        if test_btn.count() > 0 and test_btn.is_visible():
            print("\n找到测试按钮，点击...")
            test_btn.click()
            time.sleep(3)
            
            # 截图查看结果
            page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\screenshot_after_click.png', full_page=True)
            print("已截图: screenshot_after_click.png")
            
            # 检查是否有成功消息
            success_text = page.locator('text=TEST BUTTON WAS CLICKED').all()
            print(f"找到 {len(success_text)} 个成功消息")
        else:
            print("\n未找到测试按钮")
        
        browser.close()
        print("测试完成")

if __name__ == "__main__":
    test_button()
