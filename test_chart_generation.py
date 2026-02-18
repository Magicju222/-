"""
测试图表生成功能的 Playwright 脚本
"""
from playwright.sync_api import sync_playwright
import time
import os

def test_chart_generation():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        
        print("🌐 正在访问应用...")
        page.goto('http://localhost:8502')
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        
        # 截图查看初始状态
        print("📸 截图：初始页面")
        page.screenshot(path='debug_01_initial.png', full_page=True)
        
        # 上传测试文件
        print("\n📁 上传测试文件...")
        file_input = page.locator('input[type="file"]').first
        if file_input.count() > 0:
            file_path = os.path.abspath('test_data.xlsx')
            file_input.set_input_files(file_path)
            print(f"✅ 已上传文件: {file_path}")
            time.sleep(3)
        else:
            print("❌ 未找到文件上传输入框")
            browser.close()
            return
        
        # 点击"开始批量智能清洗"按钮
        print("\n🔍 查找开始批量智能清洗按钮...")
        clean_button = page.get_by_text("开始批量智能清洗").first
        if clean_button.count() > 0:
            print("🖱️ 点击开始批量智能清洗")
            clean_button.click()
            time.sleep(8)  # 等待清洗完成
            page.screenshot(path='debug_02_after_clean.png', full_page=True)
            print("✅ 清洗完成")
        else:
            print("❌ 未找到开始批量智能清洗按钮")
        
        # 查找并点击 AI数据分析 按钮
        print("\n🔍 查找 AI数据分析 按钮...")
        # 滚动到页面底部查找按钮
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        
        ai_button = page.get_by_text("🔮 AI数据分析").first
        if ai_button.count() > 0:
            print("🖱️ 点击 🔮 AI数据分析")
            ai_button.click()
            time.sleep(3)
            
            # 继续滚动到分析界面
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            page.screenshot(path='debug_03_after_ai_click.png', full_page=True)
            print("✅ 进入AI分析界面")
            
            # 查找"🚀 开始AI分析"按钮（可能需要滚动）
            print("\n🔍 查找 🚀 开始AI分析 按钮...")
            
            # 尝试多次滚动查找按钮
            for scroll_attempt in range(3):
                start_button = page.get_by_text("🚀 开始AI分析").first
                if start_button.count() > 0:
                    print("🖱️ 点击 🚀 开始AI分析")
                    start_button.click()
                    
                    # 等待分析完成（最多90秒）
                    print("⏳ 等待AI分析完成...")
                    for i in range(90):
                        time.sleep(1)
                        content = page.content()
                        if "分析完成" in content or "AI 分析完成" in content:
                            print("✅ AI分析完成！")
                            break
                        if i % 10 == 0:
                            print(f"   等待中... {i}秒")
                    
                    time.sleep(2)
                    page.screenshot(path='debug_04_after_analysis.png', full_page=True)
                    
                    # 滚动到图表生成部分
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    
                    # 查找"生成可视化图表"按钮
                    print("\n🔍 查找 生成可视化图表 按钮...")
                    chart_button = page.get_by_text("生成可视化图表").first
                    if chart_button.count() > 0:
                        print("🖱️ 点击 生成可视化图表")
                        chart_button.click()
                        
                        # 等待图表生成
                        print("⏳ 等待图表生成...")
                        time.sleep(15)
                        page.screenshot(path='debug_05_after_chart.png', full_page=True)
                        
                        # 检查结果
                        content = page.content()
                        if "成功生成" in content:
                            print("✅ 图表生成成功！")
                        elif "没有生成" in content:
                            print("❌ 图表生成失败：没有生成任何图表")
                        else:
                            print("⚠️ 图表生成状态未知，请查看截图")
                    else:
                        print("❌ 未找到 生成可视化图表 按钮")
                    
                    break  # 成功找到按钮并执行，退出循环
                else:
                    print(f"   滚动尝试 {scroll_attempt + 1}/3...")
                    page.evaluate("window.scrollBy(0, 500)")
                    time.sleep(1)
            else:
                print("❌ 未找到 🚀 开始AI分析 按钮")
                # 列出所有按钮帮助调试
                print("\n📋 当前页面所有按钮：")
                buttons = page.locator('button').all()
                for i, btn in enumerate(buttons):
                    text = btn.text_content().strip()
                    if text and len(text) < 50:
                        print(f"  - '{text}'")
        else:
            print("❌ 未找到 🔮 AI数据分析 按钮")
        
        print("\n📸 截图已保存")
        
        browser.close()
        print("\n✅ 测试完成")

if __name__ == "__main__":
    test_chart_generation()
