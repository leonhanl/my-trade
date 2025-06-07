import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager
from common.trading_products import TRADING_PRODUCTS
from common.constants import DB_PATH

@contextmanager
def get_db_connection():
    """数据库连接的上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def update_sp500_pe_ttm_data():
    """更新SP500的PE-TTM数据到数据库"""
    symbol = 'SPY'
    
    # 加载PE-TTM数据
    pe_ttm_file_path = os.path.join(os.path.dirname(__file__), 'sp500_pe_ttm_lixinger.json')
    with open(pe_ttm_file_path, 'r') as f:
        pe_ttm_data = json.load(f)

    updated_count = 0
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for entry in pe_ttm_data['data']:
            trade_date = datetime.strptime(entry['date'].split('T')[0], '%Y-%m-%d').strftime('%Y-%m-%d')
            pe_ttm_value = float(entry['pe_ttm.mcw'])
            
            #检查这个日期的row是否存在，如果不存在就skip掉，并且给出一个warning message
            cursor.execute('''
                SELECT COUNT(*) FROM stock_price
                WHERE symbol = ? AND trade_date = ?
            ''', (symbol, trade_date))

            if cursor.fetchone()[0] == 0:
                print(f"Warning: No record found for symbol {symbol} on date {trade_date}. Skipping update.")
                continue

            # 更新PE-TTM值
            cursor.execute('''
                UPDATE stock_price
                SET pe_ttm = ?
                WHERE symbol = ? AND trade_date = ?
            ''', (pe_ttm_value, symbol, trade_date))
            
            updated_count += cursor.rowcount

        conn.commit()
        print(f"更新了 {updated_count} 条PE-TTM记录")


def validate_sp500_pe_ttm_data():
    """验证SP500的PE-TTM数据"""
    symbol = 'SPY'
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT trade_date, pe_ttm FROM stock_price
            WHERE symbol = ?
            ORDER BY trade_date
        ''', (symbol,))
        
        rows = cursor.fetchall()
        
        for row in rows:
            trade_date, pe_ttm = row
            # 检查PE-TTM值是否存在
            if pe_ttm is None:
                print(f"Warning: No PE-TTM value for symbol {symbol} on date {trade_date}.")
            


if __name__ == "__main__":
    update_sp500_pe_ttm_data()
    validate_sp500_pe_ttm_data
