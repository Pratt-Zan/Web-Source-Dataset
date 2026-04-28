import json
import asyncio
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright

def get_domain(url):
    """获取 URL 的域名，用于同源判断"""
    return urlparse(url).netloc

def is_valid_link(link):
    """过滤掉不需要的链接类型"""
    if not link:
        return False
    if link.startswith(('javascript:', 'mailto:', '#', 'tel:')):
        return False
    # 这里加上了 .docx, .xlsx 等常见的文档格式，提前拦截一部分下载链接
    if any(link.lower().endswith(ext) for ext in ['.jpg', '.png', '.gif', '.pdf', '.mp4', '.zip', '.exe', '.css', '.doc', '.docx', '.xls', '.xlsx']):
        return False
    return True

async def crawl_site(browser, start_url, max_depth=2):
    target_domain = get_domain(start_url)
    visited = set()
    enqueued = set([start_url]) # 记录已经放入过队列的 URL，防止重复排队
    collected_data = [] # 用于存储最终的字典列表：[{"url": url, "text": text, "depth": depth}]
    
    queue = [(start_url, 0)] 

    context = await browser.new_context()
    page = await context.new_page()
    await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "media", "font"] else route.continue_())

    print(f"🚀 开始迭代爬取: {start_url} (最大深度限制: {max_depth} 层)")

    while queue:
        current_url, current_depth = queue.pop(0) 
        
        if current_depth > max_depth:
            continue
            
        if current_url in visited:
            continue
            
        print(f"正在抓取 [第 {current_depth} 层]: {current_url}")
        visited.add(current_url)

        try:
            await page.goto(current_url, wait_until="domcontentloaded", timeout=15000)
            
            # 🚀 新增：提取网页的纯文本内容 (过滤掉 HTML 标签，只保留页面上可见的文字)
            page_text = await page.evaluate("() => document.body ? document.body.innerText.trim() : ''")
            
            # 将抓取到的完整信息存入结果列表
            if page_text: # 只有当页面有文字内容时才保存（视你的需求而定，也可以不加这个 if）
                collected_data.append({
                    "url": current_url,
                    "depth": current_depth,
                    "text": page_text
                })
            else:
                collected_data.append({
                    "url": current_url,
                    "depth": current_depth,
                    "text": None
                })

            # 提取页面上的链接以进行下一层抓取
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
            # 🚀 修改：专门处理下载链接报错和其他意外错误
            error_msg = str(e)
            if "Download is starting" in error_msg:
                print(f"⚠️ 跳过下载文件 (不作为网页解析): {current_url}")
            elif "net::ERR_ABORTED" in error_msg:
                print(f"⚠️ 页面中止加载 (可能是非HTML资源或被服务器拦截): {current_url}")
            else:
                print(f"❌ 请求失败 {current_url}: {e}")

        await asyncio.sleep(0.5)

    await context.close()
    return collected_data

async def main():
    input_json_file = 'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\Company.json'
    output_json_file = 'C:\\Users\\Pratt\\Desktop\\HKUST-RA\\Database Construction\\json_iter_old\\Company_all_iter_full.json'
    final_results = {}

    try:
        with open(input_json_file, 'r', encoding='utf-8') as f:
            portals = json.load(f)
    except Exception as e:
        print(f"读取 JSON 失败: {e}")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for portal in portals:
            site_name = portal.get('name', 'Unknown')
            base_url = portal.get('url', '')

            if not base_url:
                continue

            # 开始抓取单个网站并返回包含文本数据的列表
            site_data = await crawl_site(browser, base_url, max_depth=2)
            
            print(f"✅ 网站 {site_name} 处理完成，共收集并解析了 {len(site_data)} 个内部页面\n")
            final_results[site_name] = site_data

        await browser.close()

    # 将带文本的数据写入 JSON 文件
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    
    print(f"🎉 所有数据已成功保存到 {output_json_file}")

if __name__ == "__main__":
    asyncio.run(main())