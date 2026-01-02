# check_scores.py - 验证前10部电影的原始评分
import requests
from bs4 import BeautifulSoup
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
url = 'https://movie.douban.com/top250?start=0&filter='
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

items = soup.find_all('div', class_='item')[:10]  # 只看前10个

print("前10部电影评分检查：")
print("-" * 50)
for i, item in enumerate(items, 1):
    # 方法1：从 property="v:average" 提取（这是豆瓣的结构化数据，最可靠）
    rating_elem = item.find('span', {'property': 'v:average'})
    rating_1 = rating_elem.get_text(strip=True) if rating_elem else "未找到(v:average)"

    # 方法2：从 class="rating_num" 提取（备用）
    rating_elem2 = item.find('span', class_='rating_num')
    rating_2 = rating_elem2.get_text(strip=True) if rating_elem2 else "未找到(rating_num)"

    # 获取标题
    title_elem = item.find('span', class_='title')
    title = title_elem.get_text(strip=True) if title_elem else "无标题"

    print(f"{i:2d}. 《{title[:10]}...》")
    print(f"    评分(v:average): {rating_1}")
    print(f"    评分(rating_num): {rating_2}")
    print("-" * 50)