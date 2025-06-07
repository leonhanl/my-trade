import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

# 连接数据库
conn = sqlite3.connect('trade_data.db')  # 请替换为您的数据库文件路径

# 查询SPY的历史数据
query = """
SELECT trade_date, close, pe_ttm
FROM stock_price 
WHERE symbol = 'SPY' 
    AND pe_ttm IS NOT NULL
    AND close IS NOT NULL
ORDER BY trade_date
"""

# 读取数据
df = pd.read_sql_query(query, conn)
conn.close()

# 转换日期格式
df['trade_date'] = pd.to_datetime(df['trade_date'])
df = df.sort_values('trade_date').reset_index(drop=True)

print(f"总数据行数: {len(df)}")
print(f"时间范围: {df['trade_date'].min()} 到 {df['trade_date'].max()}")

def find_divergent_periods(df, min_days=7):
    """
    查找股价下跌但PE-TTM上涨的连续时间段
    
    参数:
    df: 包含trade_date, close, pe_ttm的DataFrame
    min_days: 最小持续天数
    
    返回:
    符合条件的时间段列表
    """
    
    # 计算移动平均来平滑数据（可选，避免单日波动的影响）
    window = 3  # 3日移动平均
    df['close_ma'] = df['close'].rolling(window=window, center=True).mean()
    df['pe_ttm_ma'] = df['pe_ttm'].rolling(window=window, center=True).mean()
    
    # 使用原始数据或平滑数据
    price_col = 'close'  # 或 'close_ma'
    pe_col = 'pe_ttm'    # 或 'pe_ttm_ma'
    
    divergent_periods = []
    current_period_start = None
    current_period_data = []
    
    for i in range(1, len(df)):
        prev_price = df.iloc[i-1][price_col]
        curr_price = df.iloc[i][price_col]
        prev_pe = df.iloc[i-1][pe_col]
        curr_pe = df.iloc[i][pe_col]
        
        # 检查是否满足条件：股价下跌且PE-TTM上涨
        price_down = curr_price < prev_price
        pe_up = curr_pe > prev_pe
        
        if price_down and pe_up:
            if current_period_start is None:
                current_period_start = i - 1
                current_period_data = [i - 1, i]
            else:
                current_period_data.append(i)
        else:
            # 如果当前不满足条件，检查之前的连续期间是否足够长
            if current_period_start is not None:
                period_length = len(current_period_data)
                if period_length >= min_days:
                    start_idx = current_period_data[0]
                    end_idx = current_period_data[-1]
                    
                    period_info = {
                        'start_date': df.iloc[start_idx]['trade_date'],
                        'end_date': df.iloc[end_idx]['trade_date'],
                        'duration_days': period_length,
                        'start_price': df.iloc[start_idx][price_col],
                        'end_price': df.iloc[end_idx][price_col],
                        'start_pe': df.iloc[start_idx][pe_col],
                        'end_pe': df.iloc[end_idx][pe_col],
                        'price_change_pct': ((df.iloc[end_idx][price_col] - df.iloc[start_idx][price_col]) / df.iloc[start_idx][price_col]) * 100,
                        'pe_change_pct': ((df.iloc[end_idx][pe_col] - df.iloc[start_idx][pe_col]) / df.iloc[start_idx][pe_col]) * 100,
                        'data_indices': current_period_data
                    }
                    divergent_periods.append(period_info)
                
                # 重置
                current_period_start = None
                current_period_data = []
    
    # 检查最后一个期间
    if current_period_start is not None and len(current_period_data) >= min_days:
        start_idx = current_period_data[0]
        end_idx = current_period_data[-1]
        
        period_info = {
            'start_date': df.iloc[start_idx]['trade_date'],
            'end_date': df.iloc[end_idx]['trade_date'],
            'duration_days': len(current_period_data),
            'start_price': df.iloc[start_idx][price_col],
            'end_price': df.iloc[end_idx][price_col],
            'start_pe': df.iloc[start_idx][pe_col],
            'end_pe': df.iloc[end_idx][pe_col],
            'price_change_pct': ((df.iloc[end_idx][price_col] - df.iloc[start_idx][price_col]) / df.iloc[start_idx][price_col]) * 100,
            'pe_change_pct': ((df.iloc[end_idx][pe_col] - df.iloc[start_idx][pe_col]) / df.iloc[start_idx][pe_col]) * 100,
            'data_indices': current_period_data
        }
        divergent_periods.append(period_info)
    
    return divergent_periods

# 查找符合条件的时间段
min_duration = 7  # 至少7天
divergent_periods = find_divergent_periods(df, min_duration)

print(f"\n找到 {len(divergent_periods)} 个符合条件的时间段（至少{min_duration}天）:")
print("=" * 80)

for i, period in enumerate(divergent_periods, 1):
    print(f"\n时间段 {i}:")
    print(f"  开始日期: {period['start_date'].strftime('%Y-%m-%d')}")
    print(f"  结束日期: {period['end_date'].strftime('%Y-%m-%d')}")
    print(f"  持续天数: {period['duration_days']} 天")
    print(f"  股价变化: ${period['start_price']:.2f} → ${period['end_price']:.2f} ({period['price_change_pct']:.2f}%)")
    print(f"  PE-TTM变化: {period['start_pe']:.2f} → {period['end_pe']:.2f} ({period['pe_change_pct']:.2f}%)")

# 可视化这些时间段
if divergent_periods:
    print(f"\n开始绘制可视化图表...")
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 绘制整体趋势图，高亮显示发散期间
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    
    # 股价走势
    ax1.plot(df['trade_date'], df['close'], color='blue', linewidth=1, alpha=0.7, label='SPY收盘价')
    ax1.set_ylabel('SPY收盘价 ($)', fontsize=12)
    ax1.set_title('SPY股价与PE-TTM走势 - 高亮显示发散期间', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # PE-TTM走势
    ax2.plot(df['trade_date'], df['pe_ttm'], color='red', linewidth=1, alpha=0.7, label='PE-TTM')
    ax2.set_ylabel('PE-TTM', fontsize=12)
    ax2.set_xlabel('日期', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 高亮显示发散期间
    colors = ['orange', 'green', 'purple', 'brown', 'pink']
    for i, period in enumerate(divergent_periods):
        color = colors[i % len(colors)]
        indices = period['data_indices']
        
        # 获取期间的数据
        period_data = df.iloc[indices]
        
        # 在股价图上高亮
        ax1.plot(period_data['trade_date'], period_data['close'], 
                color=color, linewidth=3, alpha=0.8, 
                label=f'发散期间 {i+1}')
        
        # 在PE-TTM图上高亮
        ax2.plot(period_data['trade_date'], period_data['pe_ttm'], 
                color=color, linewidth=3, alpha=0.8,
                label=f'发散期间 {i+1}')
    
    # 更新图例
    ax1.legend()
    ax2.legend()
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # 为每个主要的发散期间创建详细图表
    for i, period in enumerate(divergent_periods[:3]):  # 只显示前3个最重要的期间
        if period['duration_days'] >= 14:  # 只为较长的期间创建详细图
            print(f"\n创建时间段 {i+1} 的详细图表...")
            
            # 扩展时间范围以显示上下文
            start_idx = max(0, period['data_indices'][0] - 10)
            end_idx = min(len(df), period['data_indices'][-1] + 10)
            
            detail_df = df.iloc[start_idx:end_idx]
            period_df = df.iloc[period['data_indices']]
            
            fig, ax1 = plt.subplots(figsize=(12, 8))
            
            # 绘制上下文数据
            ax1.plot(detail_df['trade_date'], detail_df['close'], 'b-', alpha=0.5, linewidth=1)
            ax1.set_ylabel('SPY收盘价 ($)', color='blue', fontsize=12)
            ax1.tick_params(axis='y', labelcolor='blue')
            
            # 高亮发散期间
            ax1.plot(period_df['trade_date'], period_df['close'], 'b-', linewidth=3, 
                    label=f'股价下跌: {period["price_change_pct"]:.2f}%')
            
            # 创建第二个y轴
            ax2 = ax1.twinx()
            ax2.plot(detail_df['trade_date'], detail_df['pe_ttm'], 'r-', alpha=0.5, linewidth=1)
            ax2.plot(period_df['trade_date'], period_df['pe_ttm'], 'r-', linewidth=3,
                    label=f'PE-TTM上涨: {period["pe_change_pct"]:.2f}%')
            ax2.set_ylabel('PE-TTM', color='red', fontsize=12)
            ax2.tick_params(axis='y', labelcolor='red')
            
            plt.title(f'发散期间详细分析 - {period["start_date"].strftime("%Y-%m-%d")} 到 {period["end_date"].strftime("%Y-%m-%d")}', 
                     fontsize=14)
            
            # 添加图例
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()

else:
    print("未找到符合条件的时间段。")
    print("您可以尝试:")
    print("1. 减少最小持续天数")
    print("2. 使用移动平均来平滑数据")
    print("3. 调整判断条件的严格程度")

print("\n分析完成！")