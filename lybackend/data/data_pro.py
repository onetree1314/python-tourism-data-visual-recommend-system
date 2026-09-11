import pandas as pd
import os

def process_data(input_file='data.csv', output_file='data_pro.csv'):
    """数据清洗处理函数"""
    if not os.path.exists(input_file):
        print(f"文件 {input_file} 不存在")
        return None
    
    df = pd.read_csv(input_file)
    
    # 去重
    df = df.drop_duplicates(subset=['景点id'])
    
    # 填充评分缺失值
    df['评分'] = df['评分'].fillna(0)
    
    # 处理标签格式（可能是列表字符串，需要清理）
    df['标签'] = df['标签'].astype(str)
    # 清理列表格式的标签：去除方括号和引号
    df['标签'] = df['标签'].str.replace('[', '').str.replace(']', '').str.replace("'", '').str.replace('"', '')
    # 将多个标签用逗号连接（如果已经是逗号分隔则保持不变）
    df['标签'] = df['标签'].str.replace(', ', ',').str.replace(' ,', ',')
    
    # 处理评论数
    df['评论数'] = pd.to_numeric(df['评论数'], errors='coerce').fillna(0).astype(int)
    
    # 处理价格字段
    df['价格'] = df['价格'].fillna('免费')
    df['市场票价'] = pd.to_numeric(df['市场票价'], errors='coerce').fillna(0)
    df['优惠票价'] = pd.to_numeric(df['优惠票价'], errors='coerce').fillna(0)
    
    # 处理布尔字段
    df['是否广告'] = df['是否广告'].fillna(False).astype(bool)
    df['是否推荐'] = df['是否推荐'].fillna(False).astype(bool)
    df['是否免费'] = df['是否免费'].fillna(False).astype(bool)
    
    # 处理热度评分
    df['热度评分'] = pd.to_numeric(df['热度评分'], errors='coerce').fillna(0).astype(int)
    
    # 保存处理后的数据
    df.to_csv(output_file, index=False)
    print(f"数据处理完成，共 {len(df)} 条记录")
    return df

if __name__ == '__main__':
    process_data()