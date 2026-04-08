#!/usr/bin/env python3
"""
生成真实的中文测试数据
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

# 真实的商家名称前缀
SHOP_PREFIXES = [
    "老王", "小李", "张记", "刘氏", "陈家", "王妈", "李姐", "赵哥",
    "周记", "吴家", "郑氏", "孙记", "钱家", "冯记", "褚氏", "卫家"
]

# 真实的商家类型
SHOP_TYPES = [
    "川菜馆", "火锅店", "烧烤店", "面馆", "饺子馆", "米线店",
    "奶茶店", "咖啡厅", "蛋糕店", "水果店", "便利店", "超市",
    "药店", "理发店", "洗衣店", "快餐店", "粥铺", "包子铺",
    "炸鸡店", "披萨店", "寿司店", "烤肉店", "麻辣烫", "冒菜店"
]

# 真实的城市区域
CITY_AREAS = [
    "朝阳区", "海淀区", "西城区", "东城区", "丰台区", "石景山区",
    "浦东新区", "徐汇区", "静安区", "黄浦区", "长宁区", "普陀区",
    "天河区", "越秀区", "荔湾区", "白云区", "番禺区", "南山区",
    "福田区", "罗湖区", "宝安区", "龙岗区", "武侯区", "锦江区"
]

# 线索标签
LEAD_TAGS = ["新客户", "老客户", "潜在客户", "流失客户", "高价值客户", "待跟进"]

# 状态
STATUSES = ["待联系", "已联系", "意向中", "已签约", "已流失"]

# 操作人
MODIFIERS = [
    "张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十",
    "郑小明", "王小红", "李小华", "陈小强", "刘小芳", "杨小军"
]

# 服务商
PROVIDERS = [
    "美团优选服务商", "饿了么金牌服务商", "本地生活服务商",
    "数字营销服务商", "商户运营服务商", "品牌推广服务商"
]


def generate_shop_name():
    """生成商家名称"""
    prefix = random.choice(SHOP_PREFIXES)
    shop_type = random.choice(SHOP_TYPES)
    area = random.choice(CITY_AREAS)
    
    # 随机决定是否加区域
    if random.random() > 0.7:
        return f"{prefix}{shop_type}({area}店)"
    return f"{prefix}{shop_type}"


def generate_sample_data(rows: int = 100) -> pd.DataFrame:
    """
    生成示例数据
    
    Args:
        rows: 数据行数
        
    Returns:
        DataFrame
    """
    data = []
    
    for i in range(1, rows + 1):
        # 生成时间戳（过去一年内）
        days_ago = random.randint(1, 365)
        ctime = int((datetime.now() - timedelta(days=days_ago)).timestamp())
        
        record = {
            'wm_poi_id': f'POI{str(i).zfill(10)}',
            'provider_id': f'PRV{str(random.randint(1, 100)).zfill(6)}',
            'lead_tag': random.choice(LEAD_TAGS),
            'status': random.choice(STATUSES),
            'modifier': random.choice(MODIFIERS),
            'ctime': ctime,
            'shop_name': generate_shop_name(),
            'contact_phone': f'1{random.choice(["3", "5", "7", "8", "9"])}{random.randint(100000000, 999999999)}',
            'city_area': random.choice(CITY_AREAS),
            'provider_name': random.choice(PROVIDERS),
        }
        data.append(record)
    
    return pd.DataFrame(data)


def create_sample_files():
    """创建示例数据文件"""
    # 确保目录存在
    data_dir = Path(__file__).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成不同规模的数据
    datasets = [
        (50, "线索池_小型测试_50条.xlsx"),
        (100, "线索池_标准测试_100条.xlsx"),
        (500, "线索池_大型测试_500条.xlsx"),
    ]
    
    for rows, filename in datasets:
        df = generate_sample_data(rows)
        filepath = data_dir / filename
        df.to_excel(filepath, index=False, engine='openpyxl')
        print(f"✅ 已生成: {filename} ({rows} 条数据)")
    
    # 生成 CSV 格式
    df = generate_sample_data(100)
    csv_path = data_dir / "线索池_CSV格式_100条.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')  # utf-8-sig 确保 Excel 打开不乱码
    print(f"✅ 已生成: 线索池_CSV格式_100条.csv (100 条数据)")
    
    print("\n📁 示例数据文件已生成到 data/ 目录")


if __name__ == "__main__":
    create_sample_files()
