"""
完整工作流程测试 - 直接上传文件并测试批量清洗按钮
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
        
        # 直接查找文件输入框（可能隐藏但可操作）
        print("\n查找文件输入框...")
        file_input = page.locator('input[type="file"]').first
        if file_input.count() > 0:
            print("找到文件输入框，上传文件...")
            file_input.set_input_files('e:\\徐衡文档\\AI\\Trae EXCEL\\test_data.xlsx')
            print("文件已上传")
            time.sleep(8)  # 等待文件处理
            
            # 截图上传后状态
            page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\test_2_after_upload.png', full_page=True)
            print("已截图: test_2_after_upload.png")
            
            # 滚动到页面底部查找批量清洗按钮
            print("\n滚动页面查找批量清洗按钮...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            # 查找"开始批量智能清洗"按钮
            print("查找批量清洗按钮...")
            batch_button = page.locator('button:has-text("开始批量智能清洗")').first
            if batch_button.count() > 0:
                visible = batch_button.is_visible()
                print(f"找到按钮，可见性: {visible}")
                
                if visible:
                    print("点击批量清洗按钮...")
                    batch_button.click()
                    time.sleep(5)
                    
                    # 截图点击后状态
                    page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\test_3_after_batch_click.png', full_page=True)
                    print("已截图: test_3_after_batch_click.png")
                    
                    # 检查页面内容
                    content = page.content()
                    if "DEBUG" in content:
                        print("找到 DEBUG 文本")
                    if "Button clicked" in content:
                        print("找到 'Button clicked' 文本")
                    if "processing" in content.lower():
                        print("找到 processing 文本")
                else:
                    print("按钮存在但不可见")
            else:
                print("未找到批量清洗按钮!")
                # 列出所有可见按钮
                all_buttons = page.locator('button').all()
                print(f"\n所有按钮 ({len(all_buttons)} 个):")
                for i, btn in enumerate(all_buttons):
                    try:
                        text = btn.inner_text()
                        visible = btn.is_visible()
                        print(f"  按钮 {i}: '{text}' (visible: {visible})")
                    except:
                        pass
        else:
            print("未找到文件输入框")
        
        browser.close()
        print("\n测试完成")

if __name__ == "__main__":
    test_full_workflow()
