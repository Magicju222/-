"""
完整工作流程测试 - 上传文件并测试批量清洗按钮
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
        
        # 查找并点击文件上传
        print("\n查找文件上传区域...")
        # 尝试多种方式找到上传区域
        upload_area = page.locator('text=/上传 Excel|Browse files|Drag and drop/i').first
        if upload_area.count() > 0:
            print("找到上传区域，点击...")
            upload_area.click()
            time.sleep(2)
        
        # 查找文件输入框
        file_input = page.locator('input[type="file"]').first
        if file_input.count() > 0:
            print("找到文件输入框，上传文件...")
            file_input.set_input_files('e:\\徐衡文档\\AI\\Trae EXCEL\\test_data.xlsx')
            print("文件已上传")
            time.sleep(5)  # 等待文件处理
            
            # 截图上传后状态
            page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\test_2_after_upload.png', full_page=True)
            print("已截图: test_2_after_upload.png")
            
            # 查找"开始批量智能清洗"按钮
            print("\n查找批量清洗按钮...")
            batch_button = page.locator('button:has-text("开始批量智能清洗")').first
            if batch_button.count() > 0 and batch_button.is_visible():
                print("找到批量清洗按钮，点击...")
                batch_button.click()
                time.sleep(5)
                
                # 截图点击后状态
                page.screenshot(path='e:\\徐衡文档\\AI\\Trae EXCEL\\test_3_after_batch_click.png', full_page=True)
                print("已截图: test_3_after_batch_click.png")
                
                # 检查是否有处理中的消息
                processing = page.locator('text=/处理|Processing|cleaning/i').all()
                print(f"找到 {len(processing)} 个处理相关文本")
                
                # 检查是否有成功消息
                success = page.locator('text=/成功|success|完成|completed/i').all()
                print(f"找到 {len(success)} 个成功相关文本")
                
                # 检查是否有错误消息
                error = page.locator('text=/错误|error|失败|failed/i').all()
                print(f"找到 {len(error)} 个错误相关文本")
            else:
                print("未找到批量清洗按钮!")
                # 列出所有可见按钮
                all_buttons = page.locator('button').all()
                print(f"\n所有按钮 ({len(all_buttons)} 个):")
                for i, btn in enumerate(all_buttons):
                    try:
                        text = btn.inner_text()
                        visible = btn.is_visible()
                        if visible:
                            print(f"  可见按钮: '{text}'")
                    except:
                        pass
        else:
            print("未找到文件输入框")
        
        browser.close()
        print("\n测试完成")

if __name__ == "__main__":
    test_full_workflow()
