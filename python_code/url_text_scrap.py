import json
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def fetch_page_text_fast(page, url):
    try:
        # domcontentloaded 比 load 快得多，非常适合只读取 DOM 文本
        response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        
        if not response or not response.ok:
            print(f"    ⚠️ Load failed or non 200 code: {url}")
            return None

        page_text = await page.evaluate("() => document.body ? document.body.innerText.trim() : ''")
        return page_text

    except Exception as e:
        error_msg = str(e)
        if "Download is starting" in error_msg:
            print(f"    ⚠️ Skip download: {url}")
        elif "net::ERR_ABORTED" in error_msg:
            print(f"    ⚠️ Page stopped for Non-HTML: {url}")
        else:
            print(f"    ❌ Failed login in {url}: {e}")
        return None

async def main():
    # 路径配置
    input_urls_file = 'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\json_sitemap\\Company_urls_full.json'
    output_text_full = 'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\text_sitemap\\Company_text_full.json'
    
    # 动态生成本次运行的增量文件名
    current_date = datetime.now().strftime('%Y%m%d')
    output_text_new = f'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\text_sitemap\\text_update\\Company_new_text_{current_date}.json'
    
    # 1. 读取全量 URL 列表
    try:
        with open(input_urls_file, 'r', encoding='utf-8') as f:
            all_urls_data = json.load(f)
        print(f"📂 Successful in loading: {len(all_urls_data)} sites founded.")
    except Exception as e:
        print(f"❌ Fail in loading: {e}")
        return

    # 2. 读取历史文本全量库 (用于比对跳过)
    historical_text_data = {}
    if os.path.exists(output_text_full):
        try:
            with open(output_text_full, 'r', encoding='utf-8') as f:
                historical_text_data = json.load(f)
            print(f"📂 Loading History successful，and will skip current URL。")
        except Exception as e:
            print(f"⚠️ Loading History failed，rescrape and cover: {e}")
    else:
        print("📂 No History found，and will process scraping text for base [time demanding].")

    # 本月新增的文本结果
    new_text_results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 为提高速度，设置全局路由拦截，不加载无关资源
        await context.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "media", "font"] else route.continue_())

        for site_name, urls in all_urls_data.items():
            print(f"\n🚀 [Begin] {site_name} (Total urls count for processing: {len(urls)})")
            
            if site_name not in historical_text_data:
                historical_text_data[site_name] = {}
            if site_name not in new_text_results:
                new_text_results[site_name] = {}

            page = await context.new_page()
            
            new_count_this_site = 0
            skip_count_this_site = 0

            try:
                for url in urls:
                    # 核心逻辑：如果在历史库里已经有这个 URL 的文本了，直接跳过！
                    if url in historical_text_data[site_name]:
                        skip_count_this_site += 1
                        continue

                    # 如果没有，则发起请求
                    print(f"    --> Scraping currently: {url}")
                    page_text = await fetch_page_text_fast(page, url)
                    
                    if page_text:
                        # 存入历史全量库
                        historical_text_data[site_name][url] = page_text
                        # 存入本次增量库
                        new_text_results[site_name][url] = page_text
                        new_count_this_site += 1
                    
                    await asyncio.sleep(0.5)

            except Exception as e:
                print(f"❌ [Exception found] {site_name}: {e}")
            finally:
                await page.close()
                
            print(f"✅ [Finished] {site_name}: Newly found {new_count_this_site} pages，skipped {skip_count_this_site} pages already existed.")

            # （可选）为了防止意外中断导致数据全丢，可以在每个站点爬完后立刻保存一次全量库
            with open(output_text_full, 'w', encoding='utf-8') as f:
                json.dump(historical_text_data, f, ensure_ascii=False, indent=4)

        await browser.close()

    # 4. 保存本月增量文件
    with open(output_text_new, 'w', encoding='utf-8') as f:
        json.dump(new_text_results, f, ensure_ascii=False, indent=4)
    print(f"\n🎉 Job finished！")
    print(f"📁 History is updated: {output_text_full}")
    print(f"✨ Update founded！New adding of {sum(len(texts) for texts in new_text_results.values())} texts being stored to: {output_text_new}")

if __name__ == "__main__":
    asyncio.run(main())
