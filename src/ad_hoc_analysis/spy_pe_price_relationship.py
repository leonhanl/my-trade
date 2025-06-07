import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 连接数据库
conn = sqlite3.connect('trade_data.db')  # 请替换为您的数据库文件路径

# 查询SPY最近10年的数据，限制时间段以减少数据量
query = """
SELECT trade_date, close, pe_ttm
FROM stock_price 
WHERE symbol = 'SPY' 
    AND trade_date >= '2008-01-01'
    AND trade_date <= '2011-01-01'
    AND pe_ttm IS NOT NULL
    AND close IS NOT NULL
ORDER BY trade_date
"""

# 读取数据
df = pd.read_sql_query(query, conn)
conn.close()

# 转换日期格式
df['trade_date'] = pd.to_datetime(df['trade_date'])

print(f"数据行数: {len(df)}")
print(f"时间范围: {df['trade_date'].min()} 到 {df['trade_date'].max()}")

# 创建双轴图表
fig, ax1 = plt.subplots(figsize=(14, 8))

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 绘制股价走势（左轴）
color1 = 'tab:blue'
ax1.set_xlabel('日期', fontsize=12)
ax1.set_ylabel('SPY收盘价 ($)', color=color1, fontsize=12)
line1 = ax1.plot(df['trade_date'], df['close'], color=color1, linewidth=2, label='SPY收盘价')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, alpha=0.3)

# 创建右轴绘制PE-TTM
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('PE-TTM', color=color2, fontsize=12)
line2 = ax2.plot(df['trade_date'], df['pe_ttm'], color=color2, linewidth=2, label='PE-TTM')
ax2.tick_params(axis='y', labelcolor=color2)

# 设置标题
plt.title('SPY股价与PE-TTM走势对比图 (2022-2025)', fontsize=16, pad=20)

# 添加图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

# 优化x轴日期显示
plt.xticks(rotation=45)
fig.tight_layout()

# 显示图表
plt.show()

# 计算相关性
correlation = df['close'].corr(df['pe_ttm'])
print(f"\nSPY收盘价与PE-TTM的相关系数: {correlation:.4f}")

# 基本统计信息
print("\n基本统计信息:")
print(f"SPY收盘价 - 最小值: ${df['close'].min():.2f}, 最大值: ${df['close'].max():.2f}")
print(f"PE-TTM - 最小值: {df['pe_ttm'].min():.2f}, 最大值: {df['pe_ttm'].max():.2f}")

# 分析价格与PE-TTM的变化关系
df['price_change'] = df['close'].pct_change()
df['pe_change'] = df['pe_ttm'].pct_change()

# 去除NaN值
df_clean = df.dropna()

if len(df_clean) > 0:
    change_correlation = df_clean['price_change'].corr(df_clean['pe_change'])
    print(f"价格变化率与PE-TTM变化率的相关系数: {change_correlation:.4f}")

# 可选：绘制散点图显示价格与PE-TTM的关系
plt.figure(figsize=(10, 6))
plt.scatter(df['pe_ttm'], df['close'], alpha=0.6, c=range(len(df)), cmap='viridis')
plt.xlabel('PE-TTM')
plt.ylabel('SPY收盘价 ($)')
plt.title('SPY收盘价与PE-TTM散点图')
plt.colorbar(label='时间顺序 (颜色越亮越新)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("\n分析完成！")