import akshare as ak
import sqlite3
import os
import pandas as pd
from datetime import timedelta, date, datetime
from trading_products import TRADING_PRODUCTS

def create_database():
    """创建交易数据库及相关表结构"""
    # 数据库文件路径
    db_path = 'trade_data.db'

    # # 如果数据库文件已存在，直接退出
    # if os.path.exists(db_path):
    #     print("数据库文件已存在,跳过创建")
    #     return

    # 连接到数据库（如果不存在会自动创建）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建股票历史数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_price (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol VARCHAR(20) NOT NULL,
        name VARCHAR(100) NOT NULL,
        trade_date DATE NOT NULL,
        open DECIMAL(10,2),
        close DECIMAL(10,2),
        high DECIMAL(10,2),
        low DECIMAL(10,2),
        volume BIGINT,
        amount DECIMAL(20,2),
        amplitude DECIMAL(10,2),
        change_percent DECIMAL(10,2),
        change_amount DECIMAL(10,2),
        turnover_rate DECIMAL(10,2),
        UNIQUE (symbol, trade_date)
    )
    ''')

    # 创建基金净值表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fund_nav (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fund_code VARCHAR(20) NOT NULL,
        name VARCHAR(100) NOT NULL,
        nav_date DATE NOT NULL,
        nav DECIMAL(10,4) NOT NULL,
        UNIQUE (fund_code, nav_date)
    )
    ''')

    # 创建索引以提高查询性能
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_stock_price_symbol ON stock_price(symbol)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_stock_price_date ON stock_price(trade_date)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_stock_price_symbol_date ON stock_price(symbol, trade_date)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_fund_nav_code ON fund_nav(fund_code)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_fund_nav_date ON fund_nav(nav_date)
    ''')

    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_fund_nav_code_date ON fund_nav(fund_code, nav_date)
    ''')

    # 提交事务并关闭连接
    conn.commit()
    conn.close()

    print(f"数据库 {db_path} 创建成功！")

   
def update_us_stockprice_data_to_today(symbol):
    """更新股票价格数据到最新日期"""
    product_info = TRADING_PRODUCTS.get(symbol)
    if not product_info or product_info['market'] != 'US':
        print(f"未找到 {symbol} 的配置信息或不是美股")
        return
        
    conn = sqlite3.connect('trade_data.db')
    cursor = conn.cursor()

    # 查询最新的数据日期
    cursor.execute('''
    SELECT MAX(trade_date) 
    FROM stock_price 
    WHERE symbol = ?
    ''', (symbol,))
    
    last_date = cursor.fetchone()[0] # 返回的是字符串类型，格式为 'YYYY-MM-DD'    

    if not last_date:
        # 如果未找到历史数据,使用配置中的最早日期
        start_date = datetime.strptime(product_info['earliest_date'], '%Y-%m-%d').date()
        print(f"未找到 {symbol} {product_info['name']} 的历史数据,设定开始时间为 {start_date}")
    else:
        # 如果找到历史数据,设定开始时间为最新数据日期的后一天
        last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
        start_date = last_date + timedelta(days=1)
    
    # 设定end_date为当前日期
    end_date = date.today()

    # 如果start_date大于等于end_date,跳过更新
    if start_date >= end_date:
        print(f"{symbol} 历史数据最新日期为 {last_date},已为最新,跳过更新")
        return
    
    # 获取新数据
    stock_us_hist_df = ak.stock_us_hist(symbol=product_info['akshare_symbol'], period="daily", 
                                       start_date=start_date.strftime('%Y%m%d'), 
                                       end_date=end_date.strftime('%Y%m%d'), 
                                       adjust="hfq")

    if stock_us_hist_df.empty:
        print(f"{symbol} {product_info['name']} 没有发现 {start_date} 到 {end_date} 的新数据, 可能是非交易日或者数据尚未更新，跳过更新")
        return

    print(f"开始更新 {symbol} {product_info['name']} 从 {stock_us_hist_df['日期'].min()} 到 {stock_us_hist_df['日期'].max()} 的数据...")

    try:        
        # 遍历DataFrame的每一行数据
        for index, row in stock_us_hist_df.iterrows():
            cursor.execute('''
            INSERT INTO stock_price (
                symbol,
                name,
                trade_date,
                open,
                close, 
                high,
                low,
                volume,
                amount,
                amplitude,
                change_percent,
                change_amount,
                turnover_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                product_info['name'],
                row['日期'],
                row['开盘'],
                row['收盘'],
                row['最高'],
                row['最低'],
                row['成交量'],
                row['成交额'],
                row['振幅'],
                row['涨跌幅'],
                row['涨跌额'],
                row['换手率']
            ))
        
        conn.commit()
        print(f"成功更新 {symbol} 历史价格数据")
        
    except sqlite3.Error as e:
        print(f"价格数据更新错误: {e}")
        conn.rollback()
        
    finally:
        conn.close()

def update_cn_fund_nav_to_today(symbol):
    """更新基金净值数据到最新日期"""
    product_info = TRADING_PRODUCTS.get(symbol)
    if not product_info or product_info['market'] != 'CN' or product_info['category'] not in ['stock_fund', 'bond_fund', 'money_fund']:
        print(f"未找到 {symbol} 的配置信息或不是中国基金")
        return
        
    conn = sqlite3.connect('trade_data.db')
    cursor = conn.cursor()

    # 查询最新的数据日期
    cursor.execute('''
    SELECT MAX(nav_date) 
    FROM fund_nav 
    WHERE fund_code = ?
    ''', (symbol,))
    
    last_date = cursor.fetchone()[0] # 返回的是字符串类型，格式为 'YYYY-MM-DD'
    
    if not last_date:
        start_date = datetime.strptime(product_info['earliest_date'], '%Y-%m-%d').date()
        print(f"未找到 {symbol} {product_info['name']} 的历史数据,设定开始时间为 {start_date}")
    else:
        start_date = datetime.strptime(last_date, '%Y-%m-%d').date() + timedelta(days=1)
    
    if start_date >= date.today():
        print(f"{symbol} {product_info['name']} 历史数据已是最新,跳过更新")
        return
    
    try:
        # 获取所有历史数据
        fund_nav_df = ak.fund_open_fund_info_em(symbol=symbol, indicator="累计净值走势")
        
        # 筛选出大于等于start_date的数据
        fund_nav_df['净值日期'] = pd.to_datetime(fund_nav_df['净值日期']).dt.date
        fund_nav_df = fund_nav_df[fund_nav_df['净值日期'] >= start_date]

        if fund_nav_df.empty:
            print(f"{symbol} {product_info['name']} 没有发现 {start_date} 到 {date.today()} 的新数据, 可能是非交易日或者数据尚未更新，跳过更新")
            return

        print(f"开始更新 {symbol} {product_info['name']} 从 {fund_nav_df['净值日期'].min()}  到 {fund_nav_df['净值日期'].max()} 的数据...")
        # 遍历DataFrame的每一行数据
        for index, row in fund_nav_df.iterrows():
            cursor.execute('''
            INSERT INTO fund_nav (
                fund_code,
                name,
                nav_date,
                nav
            ) VALUES (?, ?, ?, ?)
            ''', (
                symbol,
                product_info['name'],  
                row['净值日期'].strftime('%Y-%m-%d'),
                row['累计净值']
            ))
        
        conn.commit()
        print(f"成功更新 {symbol} 历史净值数据")
        
    except sqlite3.Error as e:
        print(f"净值数据更新错误: {e}")
        conn.rollback()
    except Exception as e:
        print(f"获取数据错误: {e}")
        conn.rollback()
        
    finally:
        conn.close()


def update_cn_stock_etf_data_to_today(symbol):
    """更新中国ETF数据到最新日期"""
    product_info = TRADING_PRODUCTS.get(symbol)
    if not product_info or product_info['market'] != 'CN' or product_info['category'] != 'ETF':
        print(f"未找到 {symbol} 的配置信息或不是中国ETF")
        return
        
    conn = sqlite3.connect('trade_data.db')
    cursor = conn.cursor()

    # 查询最新的数据日期
    cursor.execute('''
    SELECT MAX(trade_date) 
    FROM stock_price 
    WHERE symbol = ?
    ''', (symbol,))
    
    last_date = cursor.fetchone()[0] # 返回的是字符串类型，格式为 'YYYY-MM-DD'    

    if not last_date:
        start_date = datetime.strptime(product_info['earliest_date'], '%Y-%m-%d').date()
        print(f"未找到 {symbol} 的历史数据,设定开始时间为 {start_date}")
    else:
        start_date = datetime.strptime(last_date, '%Y-%m-%d').date() + timedelta(days=1)
    
    # 设定end_date为当前日期
    end_date = date.today()

    # 如果start_date大于等于end_date,跳过更新
    if start_date >= end_date:
        print(f"{symbol} {product_info['name']} 历史数据最新日期为 {last_date},已为最新,跳过更新")
        return
    
    # 获取新数据
    etf_hist_df = ak.fund_etf_hist_em(symbol=symbol, period="daily", 
                                     start_date=start_date.strftime('%Y%m%d'), 
                                     end_date=end_date.strftime('%Y%m%d'), 
                                     adjust="hfq")
    if etf_hist_df.empty:
        print(f"{symbol} {product_info['name']} 没有发现 {start_date} 到 {end_date} 的新数据, 可能是非交易日或者数据尚未更新，跳过更新")
        return
    
    print(f"开始更新 {symbol} {product_info['name']} 从 {etf_hist_df['日期'].min()} 到 {etf_hist_df['日期'].max()} 的数据...")

    try:        
        # 遍历DataFrame的每一行数据
        for index, row in etf_hist_df.iterrows():
            cursor.execute('''
            INSERT INTO stock_price (
                symbol,
                name,
                trade_date,
                open,
                close, 
                high,
                low,
                volume,
                amount,
                amplitude,
                change_percent,
                change_amount,
                turnover_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                product_info['name'],
                row['日期'],
                row['开盘'],
                row['收盘'],
                row['最高'],
                row['最低'],
                row['成交量'],
                row['成交额'],
                row['振幅'],
                row['涨跌幅'],
                row['涨跌额'],
                row['换手率']
            ))
        
        conn.commit()
        print(f"成功更新 {symbol} {product_info['name']} 历史价格数据")
        
    except sqlite3.Error as e:
        print(f"价格数据更新错误: {e}")
        conn.rollback()
        
    finally:
        conn.close()


def create_unified_price_view():
    """创建统一的价格视图，合并股票价格和基金净值数据"""
    conn = sqlite3.connect('trade_data.db')
    cursor = conn.cursor()

    # 创建视图
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS unified_price_view AS
    SELECT 
        symbol as symbol,
        name as name,
        trade_date as date,
        close as close
    FROM stock_price
    UNION ALL
    SELECT 
        fund_code as symbol,
        name as name,
        nav_date as date,
        nav as close
    FROM fund_nav
    ''')

    conn.commit()
    conn.close()
    print("统一价格视图创建成功！")

if __name__ == "__main__":
    # 创建数据库和表结构
    # create_database()

    # 创建统一价格视图
    create_unified_price_view()


    for symbol, info in TRADING_PRODUCTS.items():
        if info['market'] == 'US':
            update_us_stockprice_data_to_today(symbol)
        elif info['market'] == 'CN' and info['category'] == 'ETF':
            update_cn_stock_etf_data_to_today(symbol)
        elif info['market'] == 'CN' and info['category'] in ['stock_fund', 'bond_fund']:
            update_cn_fund_nav_to_today(symbol)

    
    