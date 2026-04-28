import json
import asyncio
import os
from datetime import datetime
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright

def get_domain(url):
    """获取 URL 的域名，用于同源判断"""
    return urlparse(url).netloc

def is_valid_link(link):
    """过滤掉不需要的链接类型 (保留你原有的过滤逻辑)"""
    if not link:
        return False
    if link.startswith(('javascript:', 'mailto:', '#', 'tel:')):
        return False
    if any(link.lower().endswith(ext) for ext in ['.jpg', '.png', '.gif', '.pdf', '.mp4', '.zip', '.exe', '.css', '.doc', '.docx', '.xls', '.xlsx']):
        return False
    return True

async def crawl_site(browser, start_url, site_name, max_depth, history_db, new_db):
    target_domain = get_domain(start_url)
    visited = set()
    enqueued = set([start_url]) # 记录已经放入过队列的 URL，防止重复排队
    
    queue = [(start_url, 0)] 

    context = await browser.new_context()
    page = await context.new_page()
    await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "media", "font"] else route.continue_())

    print(f"\n🚀 开始迭代爬取: {site_name} - {start_url} (最大深度限制: {max_depth} 层)")

    new_count = 0
    skip_save_count = 0

    while queue:
        current_url, current_depth = queue.pop(0) 
        
        if current_depth > max_depth:
            continue
            
        if current_url in visited:
            continue
            
        visited.add(current_url)

        # 判断是否已存在于历史库
        is_known = current_url in history_db
        if is_known:
            print(f"    ⏩ [跳过存储] 第 {current_depth} 层 - 已在历史库中，仅提取内部链接: {current_url}")
            skip_save_count += 1
        else:
            print(f"    🌟 [新页面] 第 {current_depth} 层 - 正在抓取并保存文本: {current_url}")

        try:
            await page.goto(current_url, wait_until="domcontentloaded", timeout=15000)
            
            # 如果是新页面，则提取并保存纯文本内容
            if not is_known:
                page_text = await page.evaluate("() => document.body ? document.body.innerText.trim() : ''")
                # 按照架构二的字典格式存储 { "url": "text" }
                history_db[current_url] = page_text
                new_db[current_url] = page_text
                new_count += 1

            # 无论页面是否已知，都需要提取页面上的链接，保证爬虫能继续往下走 (BFS核心)
            hrefs = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a')).map(a => a.href);
            }""")

            for href in hrefs:
                if not is_valid_link(href):
                    continue

                full_url = urljoin(current_url, href)

                if get_domain(full_url) == target_domain:
                    clean_url = full_url.split('#')[0]
                    # 如果这个链接之前没有排过队，就加入队列
                    if clean_url not in enqueued:
                        enqueued.add(clean_url)
                        queue.append((clean_url, current_depth + 1))
                        
        except Exception as e:
            error_msg = str(e)
            if "Download is starting" in error_msg:
                print(f"    ⚠️ 跳过下载文件 (不作为网页解析): {current_url}")
            elif "net::ERR_ABORTED" in error_msg:
                print(f"    ⚠️ 页面中止加载 (可能是非HTML资源或被服务器拦截): {current_url}")
            else:
                print(f"    ❌ 请求失败 {current_url}: {e}")

        await asyncio.sleep(0.5)

    await context.close()
    return new_count, skip_save_count

async def main():
    # 路径配置
    input_json_file = 'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\Company.json'
    output_text_full = 'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\json_iter\\Company_iter_full.json'
    
    # 动态生成本次运行的增量文件名
    current_date = datetime.now().strftime('%Y%m%d')
    output_text_new = f'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\json_iter\\text_update\\Company_new_iter_{current_date}.json'

    # 1. 读取入口公司列表
    try:
        with open(input_json_file, 'r', encoding='utf-8') as f:
            portals = json.load(f)
        print(f"📂 成功加载公司入口列表: 包含 {len(portals)} 个站点。")
    except Exception as e:
        print(f"❌ 读取公司入口列表失败: {e}")
        return

    # 2. 读取历史文本全量库 (用于比对跳过)
    # 数据结构: { "SiteName": { "https://...": "text content", ... } }
    historical_text_data = {}
    if os.path.exists(output_text_full):
        try:
            with open(output_text_full, 'r', encoding='utf-8') as f:
                historical_text_data = json.load(f)
            print(f"📂 成功加载历史全量数据库，将自动跳过已知页面的文本存储。")
        except Exception as e:
            print(f"⚠️ 读取历史数据失败，本次将重新抓取并覆盖: {e}")
    else:
        print("📂 未发现历史文本数据，本次将进行【全量初始化抓取】。")

    # 3. 本月新增的文本结果
    new_text_results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for portal in portals:
            site_name = portal.get('name', 'Unknown')
            base_url = portal.get('url', '')

            if not base_url:
                continue

            # 初始化当前公司的字典层级
            if site_name not in historical_text_data:
                historical_text_data[site_name] = {}
            if site_name not in new_text_results:
                new_text_results[site_name] = {}

            # 开始抓取，传入历史库和增量库的引用，在函数内直接更新
            new_count, skip_count = await crawl_site(
                browser, 
                base_url, 
                site_name, 
                max_depth=2, 
                history_db=historical_text_data[site_name], 
                new_db=new_text_results[site_name]
            )
            
            print(f"✅ [{site_name}] 处理完成: 新发现并存储了 {new_count} 个页面，跳过存储 {skip_count} 个已知页面。")

            # （可选安全措施）每个站点爬完后立刻保存一次全量库，防止程序中途崩溃导致数据丢失
            with open(output_text_full, 'w', encoding='utf-8') as f:
                json.dump(historical_text_data, f, ensure_ascii=False, indent=4)

        await browser.close()

    # 4. 剔除没有新内容的空字典，保持增量文件整洁
    new_text_results_clean = {k: v for k, v in new_text_results.items() if v}

    # 5. 保存本月增量文件
    with open(output_text_new, 'w', encoding='utf-8') as f:
        json.dump(new_text_results_clean, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 任务全部结束！")
    print(f"📁 历史全量库已更新: {output_text_full}")
    total_new_pages = sum(len(texts) for texts in new_text_results_clean.values())
    print(f"✨ 发现更新！本月新增了 {total_new_pages} 个页面文本，已单独保存至: {output_text_new}")

if __name__ == "__main__":
    asyncio.run(main())