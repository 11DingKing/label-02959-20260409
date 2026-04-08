#!/usr/bin/env python3
"""
创建示例数据文件
"""

import pandas as pd
import random
from datetime import datetime, timedelta

def create_sample_data(rows: int = 100):
    """创建示例数据"""
    
    data = {
        'wm_poi_id': [f'POI{str(i).zfill(8)}' for i in range(1, rows + 1)],
        'provider_id': [f'PRV{str(random.randint(1, 50)).zfill(4)}' for _ in range(rows)],
        'lead_tag': [random.choice(['新客', '老客', '潜在', '流失']) for _ in range(rows)],
        'status': [random.choice(['active', 'inactive', 'pending']) for _ in range(rows)],
        'modifier': [f'user_{random.randint(1, 20)}' for _ in range(rows)],
        'ctime': [
            int((datetime.now() - timedelta(days=random.randint(1, 365))).timestamp())
            for _ in range(rows)
        ]
    }
    
    df = pd.DataFrame(data)
    
    # 保存为 Excel
    output_file = 'sample_data.xlsx'
    df.to_excel(output_file, index=False)
    print(f'已创建示例数据文件: {output_file}, 共 {rows} 条数据')
    
    return output_file

if __name__ == '__main__':
    create_sample_data(100)
