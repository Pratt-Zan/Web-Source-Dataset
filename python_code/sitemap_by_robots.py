import json
import asyncio
import os
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def get_sitemaps_from_robots(page, base_url):
    """尝试从 robots.txt 中读取所有的 Sitemap URL"""
    robots_url = f"{base_url.rstrip('/')}/robots.txt"
    sitemaps = []
    
    print(f"  --> 正在检查 robots.txt: {robots_url}")
    try:
        response = await page.goto(robots_url, timeout=15000)
        if response and response.ok:
            text = await response.text()
            for line in text.splitlines():
                if line.strip().lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    sitemaps.append(sitemap_url)
    except Exception as e:
        print(f"  ⚠️ 读取 robots.txt 失败或超时: {e}")

    # 没找到就用默认的
    if not sitemaps:
        sitemaps.append(f"{base_url.rstrip('/')}/sitemap.xml")
        print(f"  --> 未找到声明，使用默认: {sitemaps[0]}")

    return sitemaps

async def fetch_sitemap_urls(page, sitemap_url, collected_urls=None):
    """递归获取 sitemap 中的所有 URL"""
    if collected_urls is None:
        collected_urls = set()

    print(f"    --> 正在解析 XML: {sitemap_url}")
    try:
        response = await page.goto(sitemap_url, wait_until="domcontentloaded", timeout=20000)
        if not response or not response.ok:
            return collected_urls

        xml_content = await response.text()
        soup = BeautifulSoup(xml_content, 'xml')

        # 查找所有的子 sitemap，进行递归
        sitemaps = soup.find_all('sitemap')
        for sitemap in sitemaps:
            loc = sitemap.find('loc')
            if loc and loc.text:
                await fetch_sitemap_urls(page, loc.text.strip(), collected_urls)

        # 查找当前文件中的具体网页 url
        urls = soup.find_all('url')
        for url in urls:
            loc = url.find('loc')
            if loc and loc.text:
                collected_urls.add(loc.text.strip())

    except Exception as e:
        print(f"  ❌ 抓取异常 {sitemap_url}: {e}")

    return collected_urls

async def main():
    input_json_file = 'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\Company.json'
    output_json_file = 'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\json_sitemap\\Company_urls_full.json'
    
    # 动态生成增量文件名，例如：Company_new_urls_20260423.json
    current_date = datetime.now().strftime('%Y%m%d')
    new_urls_output_file = f'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\json_sitemap\\url_update\\Company_new_urls_{current_date}.json'
    
    try:
        with open(input_json_file, 'r', encoding='utf-8') as f:
            portals = json.load(f)
    except Exception as e:
        print(f"读取 json 失败: {e}")
        return

    # 1. 加载历史数据（如果存在）
    historical_data = {}
    if os.path.exists(output_json_file):
        try:
            with open(output_json_file, 'r', encoding='utf-8') as f:
                historical_data = json.load(f)
            print(f"📂 成功加载历史数据库: 包含 {len(historical_data)} 个站点的记录。")
        except Exception as e:
            print(f"⚠️ 读取历史全量库失败，将作为首次爬取执行: {e}")
    else:
        print("📂 未发现历史数据，本次将作为首次全量爬取。")

    # 用于存放结果的全集 { "SiteName": set() }
    # 先把历史数据放进去（并转为 set 方便后续去重求差集）
    final_results = {site: set(urls) for site, urls in historical_data.items()}
    
    # 仅仅用于存放“本次新增”的 URL { "SiteName": list() }
    new_results_only = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )

        for portal in portals:
            site_name = portal.get('name', 'Unknown')
            base_url = portal.get('url', '')
            if not base_url: continue

            print(f"\n🚀 [开始任务] {site_name} ({base_url})")

            # 确保全集里有这个站点的初始化
            if site_name not in final_results:
                final_results[site_name] = set()

            page = await context.new_page()
            
            # 用于收集当前爬取到的所有 URL
            current_scraped_urls = set()
            
            try:
                # 1. 找 sitemap 地址
                sitemap_urls = await get_sitemaps_from_robots(page, base_url)

                # 2. 遍历抓取
                for sm_url in sitemap_urls:
                    urls_from_this_sitemap = await fetch_sitemap_urls(page, sm_url)
                    current_scraped_urls.update(urls_from_this_sitemap)

                # 3. 对比：找出这次新爬到，但在历史数据中没有的 URL
                existing_urls = final_results[site_name]
                newly_discovered_urls = current_scraped_urls - existing_urls

                # 把新发现的加入到本次的全量库集合中
                final_results[site_name].update(newly_discovered_urls)

                # 如果有新增的，就记录到增量字典里
                if newly_discovered_urls:
                    new_results_only[site_name] = list(newly_discovered_urls)
                    print(f"✅ [完成] {site_name}: 发现 {len(newly_discovered_urls)} 个【新增】URL。(站点总数: {len(final_results[site_name])})")
                else:
                    print(f"✅ [完成] {site_name}: 没有发现新 URL。(站点总数保持为: {len(final_results[site_name])})")
            
            except Exception as e:
                print(f"❌ [整个站点处理失败] {site_name}: {e}")
            
            finally:
                # 爬完当前网站，立刻关掉标签页，释放内存
                await page.close()

        # 全部爬完后关掉浏览器
        await browser.close()

    # 准备保存：把全集 set 转回列表 list
    json_ready_results = {site: list(urls) for site, urls in final_results.items()}

    # 保存 1: 更新全量数据库 (供下个月对比使用)
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(json_ready_results, f, ensure_ascii=False, indent=4)
        
    # 保存 2: 单独保存一份本次新增的增量文件 (如果有新增的话)
    if new_results_only:
        with open(new_urls_output_file, 'w', encoding='utf-8') as f:
            json.dump(new_results_only, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 任务全部结束！")
        print(f"📁 历史全量库已更新: {output_json_file}")
        print(f"✨ 发现更新！新增的 URL 已单独保存至: {new_urls_output_file}")
    else:
        print(f"\n🎉 任务全部结束！所有站点都没有新增内容。全量库未发生本质变化。")

if __name__ == "__main__":
    asyncio.run(main())