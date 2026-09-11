import asyncio
import aiohttp
import json
import random
import os
from datetime import date, datetime
from models import db, Attraction, SpiderTask
from config import Config
from utils.minio_client import minio_client
import hashlib
from urllib.parse import urlparse


def _cover_is_backend_proxy(url):
    """封面是否已是本后端 /api/media/ 代理地址（非外链）"""
    if not url or not url.startswith('http'):
        return False
    try:
        return urlparse(url).path.startswith('/api/media/')
    except Exception:
        return False


# 城市字典 - 保持原样
CITY_DICT = {
    "北京市": 1, "上海市": 2, "重庆市": 158, "天津市": 154,
    "广东省": 100051, "浙江省": 100065, "江苏省": 100066, "四川省": 100009,
    "湖北省": 100067, "湖南省": 100053, "河北省": 100059, "山西省": 100056,
    "辽宁省": 100061, "吉林省": 267, "黑龙江省": 100055, "安徽省": 100068,
    "福建省": 100038, "江西省": 100054, "山东省": 100039, "河南省": 100058,
    "海南省": 100001, "贵州省": 100064, "云南省": 100007, "陕西省": 100057,
    "甘肃省": 100060, "青海省": 100032, "台湾省": 100076,
    "内蒙古自治区": 100062, "广西壮族自治区": 100052, "西藏自治区": 100003,
    "宁夏回族自治区": 100063, "新疆维吾尔自治区": 100008,
    "香港特别行政区": 38, "澳门特别行政区": 39
}

HEADERS = {
    "referer": "https://you.ctrip.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
    "Content-Type": "application/json"
}

URL = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"

# 拉取携程 CDN 封面图时使用与站点一致的 Referer，提高成功率，便于统一落 MinIO
_IMAGE_DOWNLOAD_HEADERS = {
    "User-Agent": HEADERS["user-agent"],
    "Referer": HEADERS["referer"],
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}


class SpiderScheduler:
    """爬虫调度器 - 严格遵守君子协议"""
    
    # 爬取次数记录文件路径
    COUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'spider_daily_count.txt')
    
    def __init__(self, app):
        self.app = app
        self.today = date.today()
        self.daily_task_count = self._load_daily_count()
        self.crawled_cities_today = set()  # 今天已爬取的城市
    
    def _load_daily_count(self):
        """从文件加载今天的爬取次数"""
        try:
            if os.path.exists(self.COUNT_FILE):
                with open(self.COUNT_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        parts = content.split('|')
                        if len(parts) == 2:
                            saved_date = parts[0]
                            count = int(parts[1])
                            # 检查是否是今天
                            if saved_date == str(self.today):
                                return count
                            else:
                                # 不是今天，重置为0
                                print(f"检测到新的一天，重置爬取计数器（上次记录日期: {saved_date}）")
                                return 0
        except Exception as e:
            print(f"读取爬取次数文件失败: {e}")
        return 0
    
    def _save_daily_count(self):
        """保存今天的爬取次数到文件"""
        try:
            with open(self.COUNT_FILE, 'w', encoding='utf-8') as f:
                f.write(f"{self.today}|{self.daily_task_count}")
        except Exception as e:
            print(f"保存爬取次数文件失败: {e}")
    
    async def fetch_attraction_data(self, city_id, page):
        """异步获取景点数据 - 使用原有的爬虫逻辑"""
        data = {
            "head": {
                "cid": "09031049419176873112",
                "ctok": '', "cver": "1.0", "lang": "01",
                "sid": "8888", "syscode": "999",
                "auth": '', "xsid": '', "extension": []
            },
            "scene": "online",
            "districtId": city_id,
            "index": page,
            "sortType": 1,
            "count": 10,
            "filter": {"filterItems": []},
            "returnModuleType": "product"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(URL, headers=HEADERS, json=data, timeout=15) as response:
                    return await response.json()
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
    
    async def download_image_to_minio(self, image_url, poi_id):
        """
        下载封面到本机 MinIO，对外 URL 为 /api/media/...（永不过期，见 minio_client）。
        仅当下载非 200 或上传 MinIO 失败时，才退回保存原始携程链接。
        """
        if not image_url or not image_url.startswith('http'):
            return image_url
        
        try:
            # 生成唯一文件名（基于poi_id和URL的hash）
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            ext = 'jpg'  # 默认扩展名
            if '.' in image_url:
                ext = image_url.split('.')[-1].split('?')[0].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    ext = 'jpg'
            mime_subtype = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'gif': 'gif', 'webp': 'webp'}.get(ext, 'jpeg')
            content_type = f'image/{mime_subtype}'
            
            object_name = f"attractions/{poi_id}_{url_hash}.{ext}"
            
            # 检查MinIO中是否已存在
            try:
                # 尝试获取文件（如果存在）
                from minio.error import S3Error as MinIOS3Error
                minio_client.client.stat_object(minio_client.bucket_name, object_name)
                # 文件已存在，返回MinIO URL
                return minio_client.get_file_url(object_name)
            except MinIOS3Error:
                # 文件不存在，需要下载
                pass
            except Exception:
                # 其他错误，继续下载流程
                pass
            
            # 延迟1-2秒，避免请求过快（君子协议）
            await asyncio.sleep(random.uniform(1, 2))
            
            # 下载图片（带携程 Referer，减少 CDN 拒链）
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, headers=_IMAGE_DOWNLOAD_HEADERS, timeout=10) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # 上传到MinIO
                        minio_url = minio_client.upload_file(
                            image_data,
                            object_name,
                            content_type=content_type
                        )
                        
                        if minio_url:
                            print(f"  图片已保存到MinIO: {object_name}")
                            return minio_url
                        else:
                            print(f"  图片上传MinIO失败，保留携程原链")
                            return image_url
                    else:
                        print(f"  图片下载失败 (状态码: {response.status})，保留携程原链")
                        return image_url
        except Exception as e:
            print(f"  图片处理失败: {e}，保留携程原链")
            return image_url
    
    async def parse_and_save_attractions(self, resp, city_name):
        """解析并保存景点数据 - 智能去重和更新，图片下载到MinIO"""
        if not resp or 'attractionList' not in resp:
            return {'new': 0, 'updated': 0, 'skipped': 0}
        
        feeds = resp.get("attractionList", [])
        stats = {'new': 0, 'updated': 0, 'skipped': 0}
        
        with self.app.app_context():
            for feed in feeds:
                card = feed.get("card", {})
                poi_id = card.get("poiId", '')
                
                if not poi_id:
                    continue
                
                # 检查是否已存在
                existing = Attraction.query.filter_by(poi_id=poi_id).first()
                
                # 下载图片到MinIO（新数据、接口换图、或库里仍是携程等外链需迁移）
                original_image_url = card.get("coverImageUrl", '')
                final_image_url = original_image_url
                
                should_download_image = False
                if not existing:
                    should_download_image = True
                elif existing.cover_image_url != original_image_url:
                    should_download_image = True
                elif existing.cover_image_url and not _cover_is_backend_proxy(existing.cover_image_url):
                    # 接口返回的 URL 与库里一致，但库里仍是外链（从未成功迁到 MinIO）→ 继续尝试下载
                    should_download_image = True
                
                download_src = original_image_url
                if should_download_image and not download_src and existing and existing.cover_image_url:
                    download_src = existing.cover_image_url
                
                if should_download_image and download_src:
                    final_image_url = await self.download_image_to_minio(download_src, poi_id)
                
                coordinate = card.get("coordinate", {})
                attraction_data = {
                    'poi_id': poi_id,
                    'zone_name': card.get("zoneName", ''),
                    'poi_name': card.get("poiName", ''),
                    'comment_count': card.get("commentCount", 0),
                    'comment_score': card.get("commentScore", 0),
                    'is_advertisement': card.get("isAdvertisement", False),
                    'is_recommend': card.get("isRecommend", False),
                    'district_name': card.get("districtName", ''),
                    'cover_image_url': final_image_url,  # 优先 /api/media/...（MinIO 代理，永久）；失败时为携程原链
                    'distance_str': card.get("distanceStr", ''),
                    'tag_list': ','.join(card.get("tagNameList", [])),
                    'detail_url': card.get("detailUrl", ''),
                    'market_price': card.get("marketPrice", 0),
                    'preferential_price': card.get("preferentialPrice", 0),
                    'preferential_desc': card.get("preferentialDesc", ''),
                    'price': card.get("price", '免费'),
                    'price_type': card.get("priceType", ''),
                    'price_type_desc': card.get("priceTypeDesc", ''),
                    'is_free': card.get("isFree", False),
                    'latitude': coordinate.get("latitude", 0) if coordinate else 0,
                    'longitude': coordinate.get("longitude", 0) if coordinate else 0,
                    'heat_score': card.get("heatScore", 0),
                    'city': city_name
                }
                
                if existing:
                    # 检查数据是否有变化
                    has_changes = False
                    for key, value in attraction_data.items():
                        if key not in ['poi_id']:  # poi_id不需要比较
                            old_value = getattr(existing, key)
                            if str(old_value) != str(value):
                                has_changes = True
                                break
                    
                    if has_changes:
                        # 有变化，更新数据
                        for key, value in attraction_data.items():
                            setattr(existing, key, value)
                        stats['updated'] += 1
                    else:
                        # 数据一模一样，跳过
                        stats['skipped'] += 1
                else:
                    # 完全不一样，插入新数据
                    new_attraction = Attraction(**attraction_data)
                    db.session.add(new_attraction)
                    stats['new'] += 1
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"数据库错误: {e}")
                return {'new': 0, 'updated': 0, 'skipped': 0}
        
        return stats
    
    async def crawl_random_data(self):
        """
        定时爬取任务 - 每5分钟执行一次
        规则：
        1. 每天最多20次
        2. 每次随机爬取约30条数据（3页，每页10条）
        3. 当天爬过的城市不重复
        4. 智能去重：一模一样跳过，有变化更新，完全不同插入
        """
        # 检查是否是新的一天
        current_date = date.today()
        if current_date != self.today:
            self.today = current_date
            self.daily_task_count = 0
            self.crawled_cities_today.clear()
            self._save_daily_count()  # 保存重置后的计数
            print(f"新的一天开始，重置爬虫计数器")
        
        # 检查今日任务数量（每天最多20次）
        if self.daily_task_count >= Config.SPIDER_MAX_DAILY_TASKS:
            print(f"今日爬取任务已达上限: {Config.SPIDER_MAX_DAILY_TASKS}次（已使用: {self.daily_task_count}次），保护目标服务器")
            return
        
        # 选择未爬取的城市（当天爬过的不重复）
        available_cities = [city for city in CITY_DICT.keys() if city not in self.crawled_cities_today]
        if not available_cities:
            print("今日所有城市已爬取，明天再来")
            return
        
        # 随机选择一个城市
        city_name = random.choice(available_cities)
        city_id = CITY_DICT[city_name]
        self.crawled_cities_today.add(city_name)
        
        # 随机选择3页（每页10条，共约30条数据）
        # 页码范围1-300（根据你的观察）
        pages = random.sample(range(1, 301), 3)
        
        print(f"[爬虫任务 {self.daily_task_count + 1}/20] 城市: {city_name}, 页码: {pages}")
        
        total_stats = {'new': 0, 'updated': 0, 'skipped': 0}
        
        for page in pages:
            try:
                # 获取数据
                resp = await self.fetch_attraction_data(city_id, page)
                if resp:
                    stats = await self.parse_and_save_attractions(resp, city_name)
                    total_stats['new'] += stats['new']
                    total_stats['updated'] += stats['updated']
                    total_stats['skipped'] += stats['skipped']
                    
                    # 记录任务
                    with self.app.app_context():
                        task = SpiderTask(
                            city=city_name,
                            page_num=page,
                            status='success',
                            crawl_date=self.today
                        )
                        db.session.add(task)
                        db.session.commit()
                
                # 延迟2-4秒，避免请求过快（君子协议，考虑图片下载时间）
                await asyncio.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"  第{page}页失败: {e}")
                with self.app.app_context():
                    task = SpiderTask(
                        city=city_name,
                        page_num=page,
                        status='failed',
                        crawl_date=self.today
                    )
                    db.session.add(task)
                    db.session.commit()
        
        print(f"  完成: 新增{total_stats['new']}条, 更新{total_stats['updated']}条, 跳过{total_stats['skipped']}条")
        self.daily_task_count += 1
        self._save_daily_count()  # 保存更新后的计数
        print(f"  今日已爬取: {self.daily_task_count}/{Config.SPIDER_MAX_DAILY_TASKS}次")
    
    async def initial_crawl(self):
        """
        首次爬取 - 只在数据库为空时执行
        规则：
        1. 随机选择16个城市
        2. 每个城市爬取15页
        3. 页码也是随机的（1-300范围内）
        """
        print("=" * 60)
        print("首次数据初始化开始...")
        print("=" * 60)
        
        # 随机选择16个城市
        selected_cities = random.sample(list(CITY_DICT.keys()), Config.SPIDER_INITIAL_CITIES)
        print(f"已选择 {len(selected_cities)} 个城市: {', '.join(selected_cities)}")
        
        for idx, city_name in enumerate(selected_cities, 1):
            city_id = CITY_DICT[city_name]
            
            # 随机选择15页（页码范围1-300）
            pages = random.sample(range(1, 301), Config.SPIDER_PAGES_PER_CITY)
            
            print(f"\n[{idx}/{len(selected_cities)}] 正在爬取: {city_name}")
            print(f"  页码: {sorted(pages)}")
            
            total_stats = {'new': 0, 'updated': 0, 'skipped': 0}
            
            for page in pages:
                try:
                    resp = await self.fetch_attraction_data(city_id, page)
                    if resp:
                        stats = await self.parse_and_save_attractions(resp, city_name)
                        total_stats['new'] += stats['new']
                        total_stats['updated'] += stats['updated']
                        total_stats['skipped'] += stats['skipped']
                    
                    # 延迟1.5-3秒（君子协议，考虑图片下载时间，不要太嚣张）
                    await asyncio.sleep(random.uniform(1.5, 3))
                except Exception as e:
                    print(f"    第{page}页失败: {e}")
            
            print(f"  完成: 新增{total_stats['new']}条, 更新{total_stats['updated']}条, 跳过{total_stats['skipped']}条")
        
        print("\n" + "=" * 60)
        print("首次数据初始化完成！")
        print("=" * 60)

# 全局调度器实例
scheduler = None

def init_scheduler(app):
    """初始化调度器"""
    global scheduler
    scheduler = SpiderScheduler(app)
    return scheduler
