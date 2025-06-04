"""
投资组合可视化模块
负责处理投资组合回测结果的可视化展示
"""
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
from typing import Dict
from common.trading_products import TRADING_PRODUCTS
from common.constants import PROJECT_ROOT

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class PortfolioVisualizer:
    def __init__(self):
        """初始化可视化器"""
        pass
        
    def plot_portfolio_returns(self, portfolio_data: pd.DataFrame, save_path: str = 'portfolio_return_analysis.png') -> None:
        """
        绘制投资组合和各资产的相对收益率变化图
        
        Args:
            portfolio_data: 包含回测结果的DataFrame
            save_path: 图表保存路径，默认为'portfolio_return_analysis.png'
        """
        if portfolio_data is None or portfolio_data.empty:
            raise ValueError("请提供有效的投资组合数据")
            
        plt.figure(figsize=(12, 6))
        
        # 绘制投资组合总价值的相对收益率
        initial_total_value = portfolio_data['total_value'].iloc[0]
        normalized_total_value = portfolio_data['total_value'] / initial_total_value * 100
        plt.plot(portfolio_data.index, normalized_total_value, label='投资组合总价值', linewidth=2)
        
        # 绘制各个资产的相对收益率
        for symbol in [col.split('_')[0] for col in portfolio_data.columns if col.endswith('_close')]:
            initial_price = portfolio_data[f"{symbol}_close"].iloc[0]
            normalized_price = portfolio_data[f"{symbol}_close"] / initial_price * 100
            plt.plot(portfolio_data.index, normalized_price, 
                    label=f"{symbol} ({TRADING_PRODUCTS[symbol]['name']})")
        
        # 添加标题和时间戳
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        plt.title(f'投资组合及各资产相对收益率变化\n生成时间：{current_time}')
        plt.xlabel('日期')
        plt.ylabel('相对收益率(%)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close() 