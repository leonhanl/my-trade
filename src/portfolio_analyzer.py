"""
投资组合分析模块
负责分析回测结果，计算各种性能指标
"""
import pandas as pd
from typing import Dict, List
from datetime import datetime

class PortfolioAnalyzer:
    def __init__(self, portfolio_data: pd.DataFrame):
        """
        初始化分析器
        
        Args:
            portfolio_data: 包含回测结果的DataFrame
        """
        self.portfolio_data = portfolio_data
        self.portfolio = [col.split('_')[0] for col in portfolio_data.columns if col.endswith('_close')]

    def calculate_portfolio_return(self) -> Dict:
        """
        计算投资组合的收益率指标
        
        Returns:
            Dict: 包含总收益率、年化收益率和年度收益率的字典
        """
        # 计算年化收益率
        total_days = (self.portfolio_data.index[-1] - self.portfolio_data.index[0]).days
        portfolio_return = self.portfolio_data['total_value'].iloc[-1] / self.portfolio_data['total_value'].iloc[0] - 1
        annualized_portfolio_return = (1 + portfolio_return) ** (365/total_days) - 1
        
        # 计算每年的收益率
        annual_returns = {}
        for year in range(self.portfolio_data.index[0].year, self.portfolio_data.index[-1].year + 1):
            year_data = self.portfolio_data[self.portfolio_data.index.year == year]
            year_return = (year_data['total_value'].iloc[-1] / year_data['total_value'].iloc[0] - 1)
            annual_returns[year] = year_return

        return {
            'portfolio_return': portfolio_return,
            'annualized_portfolio_return': annualized_portfolio_return,
            'annual_returns': annual_returns
        }
    
    def calculate_asset_return(self) -> Dict:
        """
        计算每个资产的收益率
        
        Returns:
            Dict: 包含每个资产的总收益率和年化收益率的字典
        """
        # 计算总天数
        total_days = (self.portfolio_data.index[-1] - self.portfolio_data.index[0]).days

        # 计算每个资产的总收益率和年化收益率
        asset_returns = {}
        annulized_asset_returns = {}
        for symbol in self.portfolio:
            # 计算总收益率
            asset_return = self.portfolio_data[f"{symbol}_close"].iloc[-1] / self.portfolio_data[f"{symbol}_close"].iloc[0] - 1
            asset_returns[symbol] = asset_return
            # 计算年化收益率
            annulized_asset_returns[symbol] = (1 + asset_return) ** (365/total_days) - 1

        return {
            'asset_returns': asset_returns,
            'annulized_asset_returns': annulized_asset_returns
        }

    def calculate_portfolio_max_drawdown(self) -> List[Dict]:
        """
        计算前三名的最大回撤，确保时间段不重叠
        
        Returns:
            List[Dict]: 包含前三名最大回撤信息的列表，每个字典包含：
                - max_drawdown: 最大回撤百分比
                - peak_date: 峰值日期
                - trough_date: 谷值日期
                - recovery_date: 恢复日期
                - drawdown_length: 回撤持续天数
                - recovery_length: 恢复持续天数
        """
        # 获取总价值序列
        series = self.portfolio_data['total_value'].copy()
        
        # 计算累积最大值
        rolling_max = series.cummax()
        
        # 计算回撤百分比
        drawdown = (series / rolling_max - 1) * 100
        
        # 找到所有局部最小值（回撤点）
        local_minima = []
        for i in range(1, len(drawdown)-1):
            if drawdown.iloc[i] < drawdown.iloc[i-1] and drawdown.iloc[i] < drawdown.iloc[i+1]:
                local_minima.append({
                    'date': drawdown.index[i],
                    'value': drawdown.iloc[i]
                })
        
        # 按回撤值排序
        local_minima.sort(key=lambda x: x['value'])
        
        # 获取前三名最大回撤，确保时间段不重叠
        top_three_drawdowns = []
        used_periods = []  # 记录已使用的时间段
        
        for minima in local_minima:
            if len(top_three_drawdowns) >= 3:
                break
                
            trough_date = minima['date']
            peak_date = series[:trough_date].idxmax()
            
            # 计算恢复日期（如果存在）
            recovery_series = series[trough_date:]
            recovery_date = None
            for date, value in recovery_series.items():
                if value >= series[peak_date]:
                    recovery_date = date
                    break
            
            # 检查时间段是否与已有回撤重叠
            current_period = (peak_date, recovery_date if recovery_date else series.index[-1])
            is_overlapping = False
            
            for used_period in used_periods:
                # 检查时间段是否重叠
                if (current_period[0] <= used_period[1] and current_period[1] >= used_period[0]):
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                used_periods.append(current_period)
                top_three_drawdowns.append({
                    'max_drawdown': minima['value'],
                    'peak_date': peak_date,
                    'trough_date': trough_date,
                    'recovery_date': recovery_date,
                    'drawdown_length': len(series[peak_date:trough_date]),
                    'recovery_length': len(series[trough_date:recovery_date]) if recovery_date else None
                })
        
        return top_three_drawdowns 