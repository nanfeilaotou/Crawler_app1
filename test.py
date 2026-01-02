import requests
from bs4 import BeautifulSoup
import time

def page_request(url, ua):
    """请求页面"""
    try:
        response = requests.get(url, headers=ua, timeout=10)
        response.raise_for_status() # 检查请求是否成功
        # 豆瓣页面编码通常是utf-8，这里指定一下避免乱码
        response.encoding = 'utf-8'
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"请求页面失败: {e}")
        return None

def page_parse(html_content):
    """解析主页面，提取电影信息和详情页链接"""
    soup = BeautifulSoup(html_content, 'lxml')
    # 查找页面中所有的电影项目
    movie_items = soup.find_all('div', class_='item')

    info_list = []
    href_list = []

    for item in movie_items:
        # 提取电影标题 (取第一个title属性的值)
        title_tag = item.find('span', class_='title')
        title = title_tag.get_text(strip=True) if title_tag else '无标题'

        # 提取评分
        rating_tag = item.find('span', class_='rating_num')
        rating = rating_tag.get_text(strip=True) if rating_tag else '无评分'

        # 提取一句话简介
        quote_tag = item.find('span', class_='inq')
        quote = quote_tag.get_text(strip=True) if quote_tag else '无简介'

        # 组合信息
        movie_info = f"{title} === 评分：{rating} === {quote}"
        info_list.append(movie_info)

        # 提取详情页链接
        link_tag = item.find('a')
        if link_tag and link_tag.has_attr('href'):
            href_list.append(link_tag['href'])

    return [href_list, info_list]

def save_txt(info_data, filename='douban_movies.txt'):
    """保存电影列表信息"""
    with open(filename, 'a', encoding='utf-8') as txt_file:
        for element in info_data[1]:
            txt_file.write(element + '\n\n')

def sub_page_request(info_data):
    """请求子页面（电影详情页）"""
    subpage_urls = info_data[0]
    ua_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    sub_html_list = []

    for url in subpage_urls[:3]: # 限制前3个，避免请求过多
        print(f"  正在抓取详情页: {url}")
        html = page_request(url, ua_header)
        if html:
            sub_html_list.append(html)
        time.sleep(2) # 对详情页增加请求延迟，更友好
    return sub_html_list

def sub_page_parse(sub_html_list):
    """解析详情页，提取更详细的信息（如剧情简介）"""
    detailed_list = []

    for html_content in sub_html_list:
        soup = BeautifulSoup(html_content, 'lxml')

        # 尝试查找剧情简介
        # 注意：豆瓣的简介可能有多种HTML结构，这里是一种常见情况
        summary_tag = soup.find('span', property='v:summary')
        if summary_tag:
            summary = summary_tag.get_text(strip=True)
            # 简化长文本
            if len(summary) > 100:
                summary = summary[:100] + '...'
        else:
            summary = "未找到剧情简介"

        detailed_list.append(summary)
        time.sleep(0.5) # 解析间隔

    return detailed_list

def sub_page_save(detailed_list, filename='douban_details.txt'):
    """保存详情信息"""
    with open(filename, 'a', encoding='utf-8') as txt_file:
        for element in detailed_list:
            txt_file.write("剧情简介: " + element + '\n\n')

if __name__ == '__main__':
    print("**************开始爬取豆瓣电影Top250**************")

    # 设置请求头，模拟浏览器访问
    ua_header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 豆瓣电影Top250共有10页，每页25部电影
    for page in range(0, 10): # 0-9页
        start = page * 25
        url = f'https://movie.douban.com/top250?start={start}&filter='
        print(f"开始解析第{page+1}页 (start={start})")

        html_content = page_request(url, ua_header)
        if not html_content:
            print(f"  第{page+1}页抓取失败，跳过")
            continue

        info_data = page_parse(html_content)
        save_txt(info_data)

        print(f"  第{page+1}页找到 {len(info_data[0])} 部电影")

        # 处理子网页（详情页）
        if info_data[0]: # 如果有详情页链接
            print(f"  开始解析第{page+1}页的详情页")
            sub_html_list = sub_page_request(info_data)
            detailed_list = sub_page_parse(sub_html_list)
            sub_page_save(detailed_list)

        time.sleep(3) # 页面间延迟，遵守爬虫礼仪

    print("**************数据提取完成**************")
    print("电影列表已保存到 douban_movies.txt")
    print("电影详情简介已保存到 douban_details.txt")