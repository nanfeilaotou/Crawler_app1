"""
豆瓣电影Top250数据分析系统 v2.0
功能：爬取 -> 清洗 -> 存储 -> 分析 -> 可视化
"""

# ========== 【第一部分】MATPLOTLIB 配置 - 必须放在最最开头！ ==========
# 注意：matplotlib的配置需要在导入其他matplotlib模块之前完成
import matplotlib

# 方案1: 使用 'Agg' 后端（最稳定，直接生成图片文件，不弹窗）
# Agg后端用于非交互式环境，将图形渲染为图像文件
matplotlib.use('Agg')

# 方案2: 如果想尝试弹窗显示，但在PyCharm中可能有问题
# matplotlib.use('TkAgg')

# 设置中文字体
# 指定中文字体列表，程序会按顺序尝试使用这些字体
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
# 解决负号显示问题
matplotlib.rcParams['axes.unicode_minus'] = False
# ================================================================

# ========== 【第二部分】其他第三方库导入 ==========
import requests  # 用于发送HTTP请求获取网页内容
from bs4 import BeautifulSoup  # 用于解析HTML文档
import pandas as pd  # 数据处理库，用于数据清洗和分析
import sqlite3  # SQLite数据库操作
# 注意：这里导入的是 plt，它已经继承了上方的全部配置
import matplotlib.pyplot as plt  # 数据可视化库
from wordcloud import WordCloud, STOPWORDS  # 词云生成库
import numpy as np  # 科学计算库
from datetime import datetime  # 日期时间处理
import time  # 时间相关功能，用于延迟
# ================================================

# ========== 【第三部分】配置类 ==========
class Config:
    """项目配置类，存储所有配置参数"""
    BASE_URL = 'https://movie.douban.com/top250'  # 豆瓣电影Top250基础URL
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',  # 模拟浏览器请求
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',  # 接受中文语言
    }
    DB_NAME = 'douban_movies.db'  # SQLite数据库文件名
    REQUEST_DELAY = 2  # 请求延迟时间（秒），防止被封IP
    MAX_PAGES = 2  # 测试用2页，完整爬取改为10（每页25部电影，10页=250部）
# =======================================

# ==================== 爬虫模块 ====================
class DoubanSpider:
    """豆瓣爬虫核心类，负责爬取和解析豆瓣电影Top250数据"""

    def __init__(self):
        """初始化方法，创建会话并设置请求头"""
        self.session = requests.Session()  # 创建持久会话
        self.session.headers.update(Config.HEADERS)  # 更新会话的请求头

    def fetch_page(self, start=0):
        """
        获取单页数据
        start参数表示从第几部电影开始（豆瓣的分页参数）
        返回HTML页面内容或None（如果请求失败）
        """
        try:
            params = {'start': start, 'filter': ''}  # 请求参数
            response = self.session.get(Config.BASE_URL, params=params, timeout=15)  # 发送GET请求
            response.raise_for_status()  # 如果响应状态码不是200，抛出异常
            response.encoding = 'utf-8'  # 设置编码为UTF-8
            time.sleep(Config.REQUEST_DELAY)  # 延迟，避免请求过快
            return response.text  # 返回HTML文本
        except Exception as e:
            print(f"❌ 获取页面失败 (start={start}): {e}")
            return None

    @staticmethod
    def parse_movie_item(item):
        """
        解析单个电影条目
        参数：BeautifulSoup解析出的单个电影条目
        返回：包含电影信息的字典
        """
        global re  # 声明re为全局变量，因为函数内部需要导入re模块

        # 初始化电影信息字典，设置默认值
        movie = {
            'rank': 0,  # 排名
            'title': '未知标题',  # 电影标题
            'rating': 0.0,  # 评分
            'votes': 0,  # 评价人数
            'director': '未知导演',  # 导演
            'year': 0,  # 上映年份
            'country': '未知国家/地区',  # 国家/地区
            'tags': '',  # 标签
            'quote': '',  # 经典台词/简介
            'url': '',  # 电影详情页URL
            'image_url': ''  # 电影封面图片URL
        }

        try:
            # 1. 解析排名（最稳定的选择器）
            rank_elem = item.find('em')  # 排名通常用<em>标签表示
            if rank_elem:
                movie['rank'] = int(rank_elem.get_text(strip=True))

            # 2. 解析标题
            title_elem = item.find('span', class_='title')
            if title_elem:
                movie['title'] = title_elem.get_text(strip=True)

            # 3. 解析评分与评价人数
            # 3.1 提取评分 - 从 property="v:average" 的属性中获取
            rating_elem = item.find('span', {'property': 'v:average'})
            if rating_elem:
                try:
                    movie['rating'] = float(rating_elem.get_text(strip=True))
                except ValueError:
                    movie['rating'] = 0.0
            else:
                # 备用方案：尝试旧的 class 选择器
                backup_elem = item.find('span', class_='rating_num')
                if backup_elem:
                    try:
                        movie['rating'] = float(backup_elem.get_text(strip=True))
                    except ValueError:
                        movie['rating'] = 0.0
                else:
                    movie['rating'] = 0.0

            # 3.2 提取评价人数 - 它在评分所在的div内，是下一个span
            rating_div = rating_elem.parent if rating_elem else None
            movie['votes'] = 0  # 默认值
            if rating_div:
                # 找到这个div里所有的span
                all_spans = rating_div.find_all('span')
                for span in all_spans:
                    text = span.get_text(strip=True)
                    if '人评价' in text:
                        # 提取数字
                        import re  # 在需要时导入re模块
                        num_match = re.search(r'(\d+)', text.replace(',', ''))
                        if num_match:
                            movie['votes'] = int(num_match.group(1))
                        break

            # 4. 提取简介/台词
            quote_candidate = None
            for span in item.find_all('span'):
                txt = span.get_text(strip=True)
                # 台词通常较短，且包含标点
                if 50 > len(txt) > 4 and ('。' in txt or '，' in txt):
                    quote_candidate = txt
                    break
            movie['quote'] = quote_candidate if quote_candidate else ''

            # 5. 提取链接和图片
            link_elem = item.find('a')
            if link_elem and 'href' in link_elem.attrs:
                movie['url'] = link_elem['href']

            img_elem = item.find('img')
            if img_elem and 'src' in img_elem.attrs:
                movie['image_url'] = img_elem['src']

            # 6. 提取导演、年份、国家等信息（从bd信息块解析）
            bd_div = item.find('div', class_='bd')
            if bd_div:
                info_text = bd_div.get_text(' ', strip=True)
                # 使用正则表达式提取信息
                # 导演
                director_match = re.search(r'导演:\s*(\S+)', info_text)
                if director_match:
                    movie['director'] = director_match.group(1)
                # 年份（寻找4位数字）
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', info_text)
                if year_match:
                    movie['year'] = int(year_match.group(1))
                # 国家（简化处理）
                if '/' in info_text:
                    parts = [p.strip() for p in info_text.split('/')]
                    if len(parts) > 2:
                        movie['country'] = parts[-2]  # 通常国家在倒数第二部分

            # 7. 提取标签
            tag_list = []
            for span in item.find_all('span'):
                if 'class' in span.attrs and len(span['class']) == 1:
                    cls = span['class'][0]
                    # 排除已知的其他类
                    if cls not in ['title', 'rating_num', 'inq', 'playable']:
                        tag_text = span.get_text(strip=True)
                        if tag_text and len(tag_text) < 8:  # 标签通常较短
                            tag_list.append(tag_text)
            movie['tags'] = ','.join(tag_list[:3])  # 最多取3个标签

        except Exception as e:
            # 即使解析出错，也返回一个带有默认值的完整字典
            print(f"⚠️  解析电影条目时遇到小问题（不影响整体）: {e}")

        # 8. 添加爬取时间戳
        movie['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return movie

    def crawl_all_pages(self):
        """
        爬取所有页面数据
        返回：包含所有电影信息的列表
        """
        all_movies = []
        print("🎬 开始爬取豆瓣电影Top250...")

        for page in range(Config.MAX_PAGES):
            start = page * 25  # 每页25部电影
            print(f"  正在爬取第 {page + 1} 页 (start={start})...")

            html = self.fetch_page(start)
            if not html:
                continue  # 如果获取页面失败，跳过当前页

            soup = BeautifulSoup(html, 'lxml')  # 使用lxml解析器解析HTML
            items = soup.find_all('div', class_='item')  # 找到所有电影条目

            for item in items:
                movie_data = self.parse_movie_item(item)
                if movie_data:
                    all_movies.append(movie_data)

            print(f"  ✓ 第 {page + 1} 页完成，累计 {len(all_movies)} 部电影")

            if len(items) < 25:  # 最后一页可能不足25部
                break

        print(f"✅ 爬取完成！共获取 {len(all_movies)} 部电影数据")
        return all_movies
# =================================================

# ==================== 数据处理模块 ====================
class DataProcessor:
    """数据清洗和预处理类"""

    @staticmethod
    def clean_data(movies_df):
        """
        数据清洗（安全版）
        参数：包含原始电影数据的DataFrame
        返回：清洗后的DataFrame
        """
        print("🧹 正在进行数据清洗...")

        # 1. 确保DataFrame包含所有必需的列
        required_columns = ['director', 'country', 'quote', 'tags', 'rating', 'votes']
        for col in required_columns:
            if col not in movies_df.columns:
                print(f"  ⚠️  警告：列 '{col}' 不存在，将创建并填充默认值")
                if col == 'director':
                    movies_df[col] = '未知导演'
                elif col == 'country':
                    movies_df[col] = '未知国家/地区'
                elif col == 'quote':
                    movies_df[col] = ''
                elif col == 'tags':
                    movies_df[col] = ''
                elif col == 'rating':
                    movies_df[col] = 0.0
                elif col == 'votes':
                    movies_df[col] = 0

        # 2. 移除完全重复的数据行
        initial_count = len(movies_df)
        movies_df.drop_duplicates(subset=['title', 'rating', 'director'], keep='first', inplace=True)

        # 3. 处理缺失值（现在这些列肯定存在了）
        movies_df['director'] = movies_df['director'].fillna('未知导演')
        movies_df['country'] = movies_df['country'].fillna('未知国家/地区')
        movies_df['quote'] = movies_df['quote'].fillna('')
        movies_df['tags'] = movies_df['tags'].fillna('')

        # 4. 创建衍生特征
        # 评分分类
        movies_df['rating_category'] = pd.cut(
            movies_df['rating'],
            bins=[0, 7.0, 8.0, 8.5, 9.0, 10],
            labels=['一般(<7)', '良好(7-8)', '优秀(8-8.5)', '经典(8.5-9)', '神作(>9)']
        )

        # 计算评价热度（归一化到0-100）
        if movies_df['votes'].max() > 0:
            movies_df['popularity'] = (movies_df['votes'] / movies_df['votes'].max() * 100).round(2)
        else:
            movies_df['popularity'] = 0.0

        print(f"  ✓ 数据清洗完成，移除 {initial_count - len(movies_df)} 条重复记录")
        print(f"  ✓ 最终数据形状: {movies_df.shape[0]} 行 × {movies_df.shape[1]} 列")
        return movies_df

    @staticmethod
    def extract_tags_statistics(movies_df):
        """
        提取标签统计信息
        参数：电影DataFrame
        返回：标签统计DataFrame
        """
        all_tags = []
        for tags in movies_df['tags'].dropna():
            if tags:
                all_tags.extend([tag.strip() for tag in tags.split(',') if tag.strip()])

        from collections import Counter
        tag_counts = Counter(all_tags)  # 统计每个标签出现的次数
        return pd.DataFrame(
            tag_counts.most_common(20),  # 取前20个最常见的标签
            columns=['tag', 'count']
        )
# =================================================

# ==================== 数据存储模块 ====================
class DatabaseManager:
    """数据库管理类，负责SQLite数据库操作"""

    def __init__(self, db_name=Config.DB_NAME):
        """初始化，连接数据库并创建表"""
        self.conn = sqlite3.connect(db_name)  # 连接SQLite数据库
        self.create_tables()  # 创建数据表

    def create_tables(self):
        """创建数据表"""
        cursor = self.conn.cursor()

        # 主电影表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank INTEGER,
                title TEXT NOT NULL,
                rating REAL,
                votes INTEGER,
                director TEXT,
                year INTEGER,
                country TEXT,
                tags TEXT,
                `quote` TEXT,  -- 这里修改：用反引号包裹（quote是SQL关键字）
                url TEXT,
                image_url TEXT,
                rating_category TEXT,
                popularity REAL,
                crawl_time TEXT,
                UNIQUE(title)  -- 标题唯一，避免重复
            )
        ''')

        # 标签统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT UNIQUE,
                count INTEGER,
                update_time TEXT
            )
        ''')

        # 分析结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value REAL,
                description TEXT,
                update_time TEXT
            )
        ''')

        self.conn.commit()  # 提交事务

    def save_movies(self, movies_df):
        """
        保存电影数据到数据库
        参数：清洗后的电影DataFrame
        """
        print("💾 正在保存数据到数据库...")

        try:
            # 将DataFrame保存到movies表，如果表存在则替换
            movies_df.to_sql('movies', self.conn, if_exists='replace', index=False)
            print(f"  ✓ 成功保存 {len(movies_df)} 条电影记录")

            # 保存标签统计
            tag_stats = DataProcessor.extract_tags_statistics(movies_df)
            tag_stats['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            tag_stats.to_sql('tags_stats', self.conn, if_exists='replace', index=False)

        except Exception as e:
            print(f"❌ 保存数据失败: {e}")

    def get_analysis_data(self):
        """从数据库获取分析数据"""
        return pd.read_sql_query("SELECT * FROM movies", self.conn)

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
# =================================================

# ==================== 可视化模块 ====================
class DataVisualizer:
    """数据可视化类，负责生成各种图表"""

    def __init__(self, movies_df):
        """初始化，设置图表样式和颜色"""
        self.df = movies_df  # 电影数据DataFrame
        plt.style.use('seaborn-v0_8-darkgrid')  # 使用seaborn样式
        # 明确指定为Python列表，避免类型推断问题
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']  # 配色方案
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']  # 中文字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    def plot_rating_distribution(self, save_path='rating_distribution.png'):
        """
        绘制评分分布直方图
        参数：保存路径
        """
        plt.figure(figsize=(12, 6))  # 创建图形，设置尺寸

        plt.subplot(1, 2, 1)  # 第一个子图（1行2列的第1个）
        # 绘制直方图
        n, bins, patches = plt.hist(self.df['rating'], bins=20, edgecolor='black', alpha=0.7, color=self.colors[0])
        plt.title('豆瓣Top250评分分布直方图', fontsize=14, fontweight='bold')
        plt.xlabel('评分', fontsize=12)
        plt.ylabel('电影数量', fontsize=12)
        plt.grid(True, alpha=0.3)  # 显示网格

        # 添加数据标签（在柱子顶部显示数量）
        for i in range(len(n)):
            if n[i] > 0:
                plt.text(float(bins[i]) + (float(bins[i+1]) - float(bins[i]))/2, float(n[i]) + 0.5,
                         str(int(n[i])), ha='center', va='bottom', fontsize=9)

        plt.subplot(1, 2, 2)  # 第二个子图
        rating_counts = self.df['rating_category'].value_counts().sort_index()
        bars = plt.bar(rating_counts.index, rating_counts.values, color=self.colors[1:])
        plt.xlabel('评分等级', fontsize=12)
        plt.ylabel('电影数量', fontsize=12)
        plt.title('评分等级分布', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)  # x轴标签旋转45度

        # 在柱子上添加数值
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height + 0.5,
                     f'{int(height)}', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()  # 自动调整子图参数
        plt.savefig(save_path, dpi=150, bbox_inches='tight')  # 保存图形
        print(f"  ✓ 评分分布图已保存为 {save_path}")

    def plot_scatter_rating_votes(self, save_path='rating_votes_scatter.png'):
        """
        绘制评分与评价人数散点图（气泡图）
        气泡大小表示热度，颜色表示年份
        """
        plt.figure(figsize=(10, 6))

        # 绘制散点图，颜色表示年份，大小表示热度
        scatter = plt.scatter(self.df['rating'], self.df['votes'],
                              c=self.df['year'], cmap='viridis',
                              s=self.df['popularity'], alpha=0.6, edgecolors='w', linewidth=0.5)

        plt.colorbar(scatter, label='上映年份')  # 添加颜色条
        plt.xlabel('评分', fontsize=12)
        plt.ylabel('评价人数', fontsize=12)
        plt.title('评分 vs 评价人数 (气泡大小=热度)', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)

        # 添加关键点标注（评分最高的几部）
        top_movies = self.df.nlargest(5, 'rating')  # 取评分最高的5部电影
        for _, movie in top_movies.iterrows():
            plt.annotate(movie['title'][:10] + '...',  # 只显示前10个字符
                         xy=(movie['rating'], movie['votes']),  # 标注点坐标
                         xytext=(5, 5), textcoords='offset points',  # 文本偏移
                         fontsize=9, arrowprops=dict(arrowstyle='->', alpha=0.5))

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  ✓ 散点图已保存为 {save_path}")

    def plot_yearly_trend(self, save_path='yearly_trend.png'):
        """绘制年度趋势分析图"""
        plt.figure(figsize=(12, 5))

        # 按年份统计电影数量
        yearly_counts = self.df.groupby('year').size()

        plt.subplot(1, 2, 1)  # 第一个子图：年份分布折线图
        plt.plot(yearly_counts.index, yearly_counts.values,
                 marker='o', linewidth=2, markersize=6, color=self.colors[2])
        plt.fill_between(yearly_counts.index, yearly_counts.values, alpha=0.3, color=self.colors[2])  # 填充区域
        plt.xlabel('年份', fontsize=12)
        plt.ylabel('电影数量', fontsize=12)
        plt.title('Top250电影年份分布', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)

        # 按年份平均评分
        plt.subplot(1, 2, 2)  # 第二个子图：各年份平均评分柱状图
        yearly_rating = self.df.groupby('year')['rating'].mean()
        plt.bar(yearly_rating.index, yearly_rating.values, color=self.colors[3], alpha=0.7)
        plt.xlabel('年份', fontsize=12)
        plt.ylabel('平均评分', fontsize=12)
        plt.title('各年份电影平均评分', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  ✓ 年度趋势图已保存为 {save_path}")

    def create_wordcloud(self, save_path='wordcloud.png'):
        """生成标签词云图"""
        all_text = ' '.join(self.df['tags'].dropna().tolist())  # 将所有标签合并为字符串
        if not all_text:
            print("⚠️  没有标签数据可用于生成词云")
            return

        # 使用中文停用词
        stopwords = set(STOPWORDS)
        stopwords.update(['电影', '影片', '导演'])  # 添加自定义停用词

        wordcloud = WordCloud(
            font_path='C:/Windows/Fonts/simhei.ttf',  # Windows系统黑体字体路径
            width=800, height=400,
            background_color='white',
            max_words=100,  # 最多显示100个词
            stopwords=stopwords,  # 停用词
            contour_width=1,  # 轮廓宽度
            contour_color='steelblue',  # 轮廓颜色
            colormap='viridis'  # 颜色映射
        ).generate(all_text)

        plt.figure(figsize=(12, 6))
        plt.imshow(wordcloud, interpolation='bilinear')  # 显示词云
        plt.axis('off')  # 关闭坐标轴
        plt.title('豆瓣Top250电影标签词云', fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  ✓ 词云图已保存为 {save_path}")

    def create_dashboard(self):
        """创建综合仪表板（包含多个子图）"""
        print("📊 生成数据分析仪表板...")

        # 创建2x2的仪表板
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('豆瓣电影Top250数据分析仪表板', fontsize=18, fontweight='bold', y=0.98)

        # 1. 评分分布箱线图
        axes[0, 0].boxplot(self.df['rating'], vert=False, patch_artist=True,
                           boxprops=dict(facecolor=self.colors[0], alpha=0.7))
        axes[0, 0].set_xlabel('评分')
        axes[0, 0].set_title('评分分布箱线图', fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3)

        # 2. 评分前十电影水平柱状图
        top10 = self.df.nlargest(10, 'rating')[['title', 'rating']]
        y_pos = range(len(top10))
        axes[0, 1].barh(y_pos, top10['rating'], color=self.colors[1])
        axes[0, 1].set_yticks(y_pos)
        # 标题太长时截断显示
        axes[0, 1].set_yticklabels([t[:15] + '...' if len(t) > 15 else t for t in top10['title']])
        axes[0, 1].set_xlabel('评分')
        axes[0, 1].set_title('评分Top10电影', fontweight='bold')
        axes[0, 1].invert_yaxis()  # 反转y轴，使最高评分在最上面

        # 3. 国家分布饼图（前10）
        country_counts = self.df['country'].str.split('/').explode().str.strip().value_counts().head(10)
        axes[1, 0].pie(country_counts.values, labels=country_counts.index,
                       autopct='%1.1f%%', colors=self.colors, startangle=90)
        axes[1, 0].set_title('电影国家/地区分布(Top10)', fontweight='bold')

        # 4. 评价人数分布直方图（对数尺度）
        axes[1, 1].hist(np.log10(self.df['votes'] + 1), bins=15,
                        edgecolor='black', alpha=0.7, color=self.colors[3])
        axes[1, 1].set_xlabel('评价人数(对数尺度)')
        axes[1, 1].set_ylabel('电影数量')
        axes[1, 1].set_title('评价人数分布(对数转换)', fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        dashboard_path = 'analysis_dashboard.png'
        plt.savefig(dashboard_path, dpi=150, bbox_inches='tight')
        print(f"  ✓ 综合仪表板已保存为 {dashboard_path}")
# =================================================

# ==================== 分析报告模块 ====================
class AnalysisReporter:
    """生成分析报告类"""

    @staticmethod
    def generate_report(movies_df):
        """生成文本分析报告"""
        report = ["豆瓣电影Top250榜单 **前50名（前20%）** 分析报告", "=" * 60,
                  f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                  f"分析范围: Top250榜单的前 {len(movies_df)} 部电影（前{len(movies_df) / 250 * 100:.0f}%）",
                  f"数据总量: {len(movies_df)} 部电影", "-" * 60, "📈 基本统计信息:",
                  f"  平均评分: {movies_df['rating'].mean():.2f}", f"  评分中位数: {movies_df['rating'].median():.2f}",
                  f"  最高评分: {movies_df['rating'].max():.2f}", f"  最低评分: {movies_df['rating'].min():.2f}"]

        # 基本统计
        total_votes = movies_df['votes'].sum()
        avg_votes = movies_df['votes'].mean()
        median_votes = movies_df['votes'].median()
        report.append(f"  评价人数总和 (前{len(movies_df)}部): {total_votes:,}")
        report.append(f"  平均每部评价人数: {avg_votes:,.0f}")
        report.append(f"  评价人数中位数: {median_votes:,.0f}")

        # 评分分布
        report.append("\n🏆 评分分布:")
        rating_dist = movies_df['rating_category'].value_counts().sort_index()
        for category, count in rating_dist.items():
            percentage = (count / len(movies_df)) * 100
            report.append(f"  {category}: {count} 部 ({percentage:.1f}%)")

        # 年代分析
        report.append("\n📅 年代分析:")
        decade_counts = (movies_df['year'] // 10 * 10).value_counts().sort_index()
        for decade, count in decade_counts.items():
            if decade > 1900:
                report.append(f"  {decade}s: {count} 部")

        # 导演分析
        report.append("\n🎬 导演作品数量Top5:")
        director_counts = movies_df['director'].value_counts().head(5)
        for director, count in director_counts.items():
            report.append(f"  {director}: {count} 部")

        # 热门标签
        all_tags = []
        for tags in movies_df['tags'].dropna():
            if tags:
                all_tags.extend([tag.strip() for tag in tags.split(',') if tag.strip()])

        from collections import Counter
        tag_counts = Counter(all_tags)
        report.append("\n🏷️  热门标签Top10:")
        for tag, count in tag_counts.most_common(10):
            report.append(f"  {tag}: {count} 次")

        report.append("=" * 60)

        # 保存报告到文件
        report_text = '\n'.join(report)
        with open('analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report_text)

        print("📝 分析报告已保存为 analysis_report.txt")
        print("\n" + report_text[:500] + "...\n")  # 打印报告开头部分
# =================================================

# ==================== 主程序 ====================
def main():
    """主程序流程"""
    print("=" * 60)
    print("豆瓣电影Top250数据分析系统 v2.0")
    print("=" * 60)

    # 1. 爬取数据
    spider = DoubanSpider()
    movies_data = spider.crawl_all_pages()

    if not movies_data:
        print("❌ 未获取到数据，程序退出")
        return

    # 2. 转换为DataFrame并进行数据处理
    df = pd.DataFrame(movies_data)
    processor = DataProcessor()
    df_cleaned = processor.clean_data(df)

    # 新增：数据完整性快速检查
    print("\n🔍 数据完整性检查：")
    print(f"总记录数: {len(df_cleaned)}")
    print(f"评分缺失数: {df_cleaned['rating'].isnull().sum()}")
    print(f"评价人数缺失数: {df_cleaned['votes'].isnull().sum()}")
    print(f"评分范围: {df_cleaned['rating'].min():.2f} - {df_cleaned['rating'].max():.2f}")
    print(f"评价人数总和（原始）: {df_cleaned['votes'].sum():,}")

    # 3. 保存到数据库
    db_manager = DatabaseManager()
    db_manager.save_movies(df_cleaned)

    # 4. 生成分析报告
    reporter = AnalysisReporter()
    reporter.generate_report(df_cleaned)

    # 5. 数据可视化
    visualizer = DataVisualizer(df_cleaned)
    visualizer.plot_rating_distribution()
    visualizer.plot_scatter_rating_votes()
    visualizer.plot_yearly_trend()
    visualizer.create_wordcloud()
    visualizer.create_dashboard()

    # 6. 关闭数据库连接
    db_manager.close()

    print("=" * 60)
    print("🎉 所有任务完成！")
    print("生成的文件:")
    print("  - douban_movies.db (SQLite数据库)")
    print("  - analysis_report.txt (分析报告)")
    print("  - rating_distribution.png (评分分布)")
    print("  - rating_votes_scatter.png (散点图)")
    print("  - yearly_trend.png (年度趋势)")
    print("  - wordcloud.png (词云图)")
    print("  - analysis_dashboard.png (综合仪表板)")
    print("=" * 60)
    print("项目制作人:")
    print("计23-2")
    print("刘文昊")
    print("23101020204")
    print("=" * 60)
# =================================================

# 程序入口
if __name__ == '__main__':
    main()