"""
数据加载模块
负责从数据库加载投资组合相关的数据
"""
import pandas as pd
import sqlite3
from typing import List

class DataLoader:
    def __init__(self):
        """初始化数据加载器，设置数据库路径"""
        self.db_path = 'trade_data.db'
        
    def load_portfolio_data(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """
        从数据库加载投资组合数据
        
        Args:
            symbols: 投资组合中的产品代码列表，如 ['510300', '515100', 'GLD', 'QQQ']
            start_date: 开始日期，格式为 'YYYY-MM-DD'
            end_date: 结束日期，格式为 'YYYY-MM-DD'
            
        Returns:
            DataFrame: 包含所有产品价格数据的DataFrame，索引为日期，列为各产品的收盘价
        """
        conn = sqlite3.connect(self.db_path)
        
        # 构建SQL查询，使用参数化查询防止SQL注入
        placeholders = ','.join(['?'] * len(symbols))
        query = f"""
        SELECT 
            symbol,
            date,
            close
        FROM unified_price_view
        WHERE symbol IN ({placeholders})
        AND date BETWEEN ? AND ?
        ORDER BY date
        """
        
        # 执行查询，将查询参数和日期范围合并
        params = symbols + [start_date, end_date]
        df = pd.read_sql_query(query, conn, params=params)
        
        # 将日期列转换为datetime类型，便于后续处理
        df['date'] = pd.to_datetime(df['date'])
        
        # 将数据透视为宽格式，每个产品一列
        df_pivot = df.pivot(index='date', columns='symbol', values='close')
        
        # 重命名列以添加后缀，便于后续处理
        df_pivot.columns = [f"{col}_close" for col in df_pivot.columns]
        
        conn.close()
        return df_pivot 