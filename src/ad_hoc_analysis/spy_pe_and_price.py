import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from matplotlib.dates import MonthLocator, DateFormatter  # Add this import

# 连接数据库
conn = sqlite3.connect('trade_data.db')  # 请替换为您的数据库文件路径

# 参数化起止日期
START_DATE = '2010-06-01'
END_DATE = '2025-06-01'

# 查询SPY最近10年的数据，限制时间段以减少数据量
query = f"""
SELECT trade_date, close, pe_ttm
FROM stock_price 
WHERE symbol = 'SPY' 
    AND trade_date >= '{START_DATE}'
    AND trade_date <= '{END_DATE}'
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
plt.title(f'SPY股价与PE-TTM走势对比图 ({START_DATE} - {END_DATE})', fontsize=16, pad=20)

# 添加图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

# 优化x轴日期显示
ax1.xaxis.set_major_locator(MonthLocator(interval=3))  # 每3个月显示一个刻度
ax1.xaxis.set_major_formatter(DateFormatter('%y%m'))  # 设置日期格式为"年月"，如2201
plt.xticks(rotation=45)
fig.tight_layout()

# 显示图表
plt.show()


print("\n分析完成！")