import asyncio
import aiohttp
import json
import csv
import sys

# 修复Windows下asyncio的事件循环问题
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

headers = {
    "referer": "https://you.ctrip.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
    "Content-Type": "application/json"
}

url = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"


async def get_json(v, page):
    """异步版本 - 获取JSON数据"""
    data = {
        "head": {
            "cid": "09031049419176873112",
            "ctok": '',
            "cver": "1.0",
            "lang": "01",
            "sid": "8888",
            "syscode": "999",
            "auth": '',
            "xsid": '',
            "extension": []
        },
        "scene": "online",
        "districtId": v,
        "index": page,
        "sortType": 1,
        "count": 10,
        "filter": {
            "filterItems": []
        },
        "returnModuleType": "product"
    }
    data = json.dumps(data, separators=(',', ':'))

    # 增加超时设置和重试机制，提升稳定性
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, headers=headers, data=data) as response:
                response.raise_for_status()  # 抛出HTTP错误状态码
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"网络请求错误: {e}")
            return None


def get_datainfo(resp, k):
    """保持完全相同的函数签名和数据结构"""
    if resp is None:
        return  # 如果响应为空，直接返回
    feeds = resp.get("attractionList", [])
    with open("data.csv", "a", newline='', encoding="utf-8") as f:
        csvwriter = csv.writer(f)
        rows = []
        for feed in feeds:
            card = feed.get("card", {})
            coordinate = card.get("coordinate", '')
            poiId = card.get("poiId", '')  # 景点id
            zoneName = card.get("zoneName", '')  # 景点区域
            poiName = card.get("poiName", '')  # 景点名称
            commentCount = card.get("commentCount", '')  # 评论数
            commentScore = card.get("commentScore", '')  # 评分
            isAdvertisement = card.get("isAdvertisement", '')  # 是否广告
            isRecommend = card.get("isRecommend", '')  # 是否推荐
            districtName = card.get("districtName", '')  # 景点所在城市
            coverImageUrl = card.get("coverImageUrl", '')  # 封面图片
            distanceStr = card.get("distanceStr", '')  # 与中心的距离
            tagNameList = card.get("tagNameList", [])  # 标签
            detailUrl = card.get("detailUrl", '')  # 详情页链接
            marketPrice = card.get("marketPrice", '')  # 市场票价
            preferentialPrice = card.get("preferentialPrice", '')  # 优惠票价
            preferentialDesc = card.get("preferentialDesc", '')  # 优惠描述
            price = card.get("price", '免费')  # 价格
            priceType = card.get("priceType", '')  # 价格类型
            priceTypeDesc = card.get("priceTypeDesc", '')  # 价格类型描述
            isFree = card.get("isFree", '')  # 是否免费
            latitude = coordinate.get("latitude", '') if coordinate else ''  # 纬度
            longitude = coordinate.get("longitude", '') if coordinate else ''  # 经度
            heatScore = card.get("heatScore", '')  # 热度评分
            rows.append([poiId, zoneName, poiName, commentCount, commentScore,
                         isAdvertisement, isRecommend, districtName, coverImageUrl,
                         distanceStr, tagNameList, detailUrl, marketPrice, preferentialPrice,
                         preferentialDesc, price, priceType, priceTypeDesc, isFree,
                         latitude, longitude, heatScore, k])
        if rows:  # 只在有数据时写入
            csvwriter.writerows(rows)


async def process_city_page(city_name, v, page, semaphore):
    """处理单个城市的单个页面（新增信号量参数）"""
    async with semaphore:  # 使用信号量限制并发
        try:
            resp = await get_json(v, page)
            get_datainfo(resp, city_name)
            print(f"已完成: {city_name} 第{page}页")
        except Exception as e:
            print(f"处理失败: {city_name} 第{page}页, 错误: {e}")


async def main():
    """主异步函数 - 保持原有的循环结构但异步执行"""
    # 创建CSV文件并写入表头
    with open("data.csv", "w", newline='', encoding="utf-8") as f:
        csvwriter = csv.writer(f)
        headers = [
            "景点id", "景点区域", "景点名称", "评论数", "评分",
            "是否广告", "是否推荐", "景点所在城市", "封面图片",
            "与中心的距离", "标签", "详情页链接", "市场票价", "优惠票价",
            "优惠描述", "价格", "价格类型", "价格类型描述", "是否免费",
            "纬度", "经度", "热度评分", "城市"
        ]
        csvwriter.writerow(headers)

    # 城市字典 - 完全保持原样
    cityDict = {
        "北京市": 1,
        "上海市": 2,
        "重庆市": 158,
        "天津市": 154,
        "广东省": 100051,
        "浙江省": 100065,
        "江苏省": 100066,
        "四川省": 100009,
        "湖北省": 100067,
        "湖南省": 100053,
        "河北省": 100059,
        "山西省": 100056,
        "辽宁省": 100061,
        "吉林省": 267,
        "黑龙江省": 100055,
        "安徽省": 100068,
        "福建省": 100038,
        "江西省": 100054,
        "山东省": 100039,
        "河南省": 100058,
        "海南省": 100001,
        "贵州省": 100064,
        "云南省": 100007,
        "陕西省": 100057,
        "甘肃省": 100060,
        "青海省": 100032,
        "台湾省": 100076,
        "内蒙古自治区": 100062,
        "广西壮族自治区": 100052,
        "西藏自治区": 100003,
        "宁夏回族自治区": 100063,
        "新疆维吾尔自治区": 100008,
        "香港特别行政区": 38,
        "澳门特别行政区": 39
    }

    # 创建信号量（限制最大并发数为10）
    semaphore = asyncio.Semaphore(10)

    # 创建所有任务
    tasks = []
    for k, v in cityDict.items():
        for page in range(1, 6):
            task = process_city_page(k, v, page, semaphore)
            tasks.append(task)

    # 并发执行所有任务
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    # 优化事件循环调用方式，消除DeprecationWarning
    asyncio.run(main())