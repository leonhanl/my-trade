import akshare as ak
import sqlite3
import os
import pandas as pd
from datetime import timedelta, date, datetime
from common.trading_products import TRADING_PRODUCTS
from common.constants import DB_PATH

def update_stock_price_data_to_today(symbol):
    """更新股票价格数据到最新日期，支持美股、中国ETF、中国指数"""
    product_info = TRADING_PRODUCTS.get(symbol)
    if not product_info:
        print(f"未找到 {symbol} 的配置信息")
        return
        
    # 检查产品类型
    if product_info['market'] == 'US':
        pass  # 美股直接通过
    elif product_info['market'] == 'CN':
        if product_info['category'] not in ['ETF', 'index']:
            print(f"{symbol} 不是中国ETF或中国指数")
            return
    else:
        print(f"{symbol} 不支持的市场类型")
        return
        
    conn = sqlite3.connect(DB_PATH)
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
        print(f"未找到 {symbol} {product_info['name']} 的历史数据,设定开始时间为 {start_date}")
    else:
        start_date = datetime.strptime(last_date, '%Y-%m-%d').date() + timedelta(days=1)
    
    # 设定end_date为当前日期
    end_date = date.today()

    # 如果start_date大于等于end_date,跳过更新
    if start_date >= end_date:
        print(f"{symbol} {product_info['name']} 历史数据最新日期为 {last_date},已为最新,跳过更新")
        return
    
    try:
        # 根据市场类型获取数据
        if product_info['market'] == 'US':
            hist_df = ak.stock_us_hist(symbol=product_info['akshare_symbol'], period="daily", 
                                     start_date=start_date.strftime('%Y%m%d'), 
                                     end_date=end_date.strftime('%Y%m%d'), 
                                     adjust="hfq")
        elif product_info['market'] == 'CN' and product_info['category'] == 'ETF':
            hist_df = ak.fund_etf_hist_em(symbol=symbol, period="daily", 
                                        start_date=start_date.strftime('%Y%m%d'), 
                                        end_date=end_date.strftime('%Y%m%d'), 
                                        adjust="hfq")
        elif product_info['market'] == 'CN' and product_info['category'] == 'index':
            hist_df = ak.index_zh_a_hist(symbol=symbol, period="daily", 
                                         start_date=start_date.strftime('%Y%m%d'), 
                                         end_date=end_date.strftime('%Y%m%d'))
        
            
        if hist_df.empty:
            print(f"{symbol} {product_info['name']} 没有发现 {start_date} 到 {end_date} 的新数据, 可能是非交易日或者数据尚未更新，跳过更新")
            return

        print(f"开始更新 {symbol} {product_info['name']} 从 {hist_df['日期'].min()} 到 {hist_df['日期'].max()} 的数据...")

        # 遍历DataFrame的每一行数据
        for index, row in hist_df.iterrows():
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
                turnover_rate,
                pe_ttm
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                row['换手率'],
                None  # 先设置为 None，后续可以通过其他方式更新 PE-TTM 数据
            ))
        
        conn.commit()
        print(f"成功更新 {symbol} {product_info['name']} 历史价格数据")
        
    except sqlite3.Error as e:
        print(f"价格数据更新错误: {e}")
        conn.rollback()
    except Exception as e:
        print(f"获取数据错误: {e}")
        conn.rollback()
        
    finally:
        conn.close()

def update_cn_fund_nav_to_today(symbol):
    """更新基金净值数据到最新日期"""
    product_info = TRADING_PRODUCTS.get(symbol)
    if not product_info or product_info['market'] != 'CN' or product_info['category'] not in ['stock_fund', 'bond_fund', 'money_fund']:
        print(f"未找到 {symbol} 的配置信息或不是中国基金")
        return
        
    conn = sqlite3.connect(DB_PATH)
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


if __name__ == "__main__":
    # 确保数据库文件存在
    if not os.path.exists(DB_PATH):
        print("数据库文件不存在，请先创建数据库")
        exit(1)

    for symbol, info in TRADING_PRODUCTS.items():
        if info['market'] == 'US' or (info['market'] == 'CN' and info['category'] in ['ETF', 'index']):
            update_stock_price_data_to_today(symbol)
        elif info['market'] == 'CN' and info['category'] in ['stock_fund', 'bond_fund']:
            update_cn_fund_nav_to_today(symbol)


