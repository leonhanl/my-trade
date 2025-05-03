"""
投资组合回测主类
实现了一个简单的投资组合回测系统，支持多资产配置和定期再平衡
"""
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List
from trading_products import TRADING_PRODUCTS
from data_loader import DataLoader
from pprint import pprint

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

DEBUG = True


class PortfolioBacktest:
    def __init__(self, config: Dict):
        """
        初始化回测类
        
        Args:
            config: 回测配置字典，包含以下字段：
                - target_percentage: Dict[str, float] 目标持仓比例，如 {'510300': 0.33}
                - start_date: str 回测开始日期，格式为 'YYYY-MM-DD'
                - end_date: str 回测结束日期，格式为 'YYYY-MM-DD'
                - initial_total_value: float 初始投资金额
                - show_plot: bool 是否显示图形化结果
        """
        self.config = config
        self.data_loader = DataLoader()
        self.portfolio_data = None
        self.portfolio = list(config['target_percentage'].keys())
        
    def initialize_portfolio(self) -> None:
        """
        初始化投资组合数据
        包括：加载历史数据、计算初始持仓数量、设置初始持仓价值
        """
        # 从数据库加载历史价格数据
        self.portfolio_data = self.data_loader.load_portfolio_data(
            self.portfolio,
            self.config['start_date'],
            self.config['end_date']
        )
        
        if self.portfolio_data is None or self.portfolio_data.empty:
            raise ValueError("无法加载投资组合数据，请检查产品代码和日期范围")

        # 使用新的方法填充缺失值
        self.portfolio_data = self.portfolio_data.ffill().bfill()

        # 初始化持仓数量和价值
        initial_total_value = self.config['initial_total_value']
        
        for symbol in self.portfolio:
            # 计算初始持仓数量：根据目标比例和初始总价值计算
            initial_close = self.portfolio_data[f"{symbol}_close"].iloc[0]
            initial_share_number = initial_total_value * self.config['target_percentage'][symbol] / initial_close
            
            # 添加持仓数量列，用于记录每日持仓数量
            self.portfolio_data.insert(
                self.portfolio_data.columns.get_loc(f"{symbol}_close") + 1,
                f"{symbol}_share_number",
                0.0
            )
            
            # 添加持仓价值列，用于记录每日持仓市值
            self.portfolio_data.insert(
                self.portfolio_data.columns.get_loc(f"{symbol}_close") + 2,
                f"{symbol}_value",
                0.0
            )
            
            # 设置初始值：持仓数量和持仓价值
            self.portfolio_data[f"{symbol}_share_number"] = self.portfolio_data[f"{symbol}_share_number"].astype('float64')
            self.portfolio_data.at[self.portfolio_data.index[0], f"{symbol}_share_number"] = initial_share_number
            self.portfolio_data.at[self.portfolio_data.index[0], f"{symbol}_value"] = float(initial_share_number * initial_close)
        
        # 添加总价值列，用于记录每日投资组合总市值
        self.portfolio_data['total_value'] = 0.0
        self.portfolio_data.at[self.portfolio_data.index[0], 'total_value'] = float(initial_total_value)
        
        # 输出初始数据
        if DEBUG:
            print("\n初始投资组合数据:")
            print(self.portfolio_data)
        
    def run_simple_backtest(self) -> None:
        """
        运行回测
        计算每日持仓变化和投资组合总价值
        """
        if self.portfolio_data is None:
            self.initialize_portfolio()
            
        # 循环计算每天的持仓变化
        for i in range(1, len(self.portfolio_data)):
            current_date = self.portfolio_data.index[i]
            previous_date = self.portfolio_data.index[i-1]
            
            # 计算每个资产的持仓变化
            for symbol in self.portfolio:
                # 获取当前价格
                current_price = self.portfolio_data.at[current_date, f"{symbol}_close"]
                
                # 保持持仓数量不变（简单回测策略，不进行再平衡）
                previous_shares = float(self.portfolio_data.at[previous_date, f"{symbol}_share_number"])
                self.portfolio_data.at[current_date, f"{symbol}_share_number"] = previous_shares
                
                # 计算当前持仓价值：持仓数量 * 当前价格
                current_value = float(previous_shares * current_price)
                self.portfolio_data.at[current_date, f"{symbol}_value"] = current_value
            
            # 计算总价值：所有资产持仓价值之和
            total_value = float(sum(self.portfolio_data.at[current_date, f"{symbol}_value"] 
                            for symbol in self.portfolio))
            self.portfolio_data.at[current_date, 'total_value'] = total_value
        
        if DEBUG:
            print("\n回测结果:")
            print(self.portfolio_data)

    def run_rebalance_backtest(self, rebalance_strategy: str) -> None:
        """
        运行年化再平衡回测
        每年1月1日进行再平衡，恢复到预设的目标比例
        """
        if self.portfolio_data is None:
            self.initialize_portfolio() 
            
        for i in range(1, len(self.portfolio_data)):
            current_date = self.portfolio_data.index[i]
            previous_date = self.portfolio_data.index[i-1]
            
            is_rebalance_day = False
            if rebalance_strategy == 'ANNUAL_REBALANCE':
                # 判断是否是1月1日
                if current_date.month == 1 and previous_date.month == 12:
                    is_rebalance_day = True
                    if DEBUG:
                        print(f"年度再平衡日: {current_date}")
            elif rebalance_strategy == 'DRIFT_REBALANCE':  # 当某个资产的持仓价值偏离预设值的20%时进行再平衡 
                for symbol in self.portfolio:
                    previous_value = self.portfolio_data.at[previous_date, f"{symbol}_value"]
                    target_value = self.config['target_percentage'][symbol] * self.portfolio_data.at[previous_date, 'total_value']
                    if abs(previous_value - target_value) / target_value > 0.2:
                        is_rebalance_day = True
                        if DEBUG:
                            print(f"日期: {current_date} {symbol} {TRADING_PRODUCTS[symbol]['name']} 持仓价值偏离预设值的20%,当前百分比为: {previous_value/target_value*100:.2f}%，进行再平衡")
                        break
               

            # 计算每个资产的持仓变化
            for symbol in self.portfolio:
                # 获取当前价格
                current_price = self.portfolio_data.at[current_date, f"{symbol}_close"]
                
                if is_rebalance_day:
                    # 如果是再平衡日，根据目标比例重新计算持仓数量
                    previous_total_value = self.portfolio_data.at[previous_date, 'total_value']
                    share_number = previous_total_value * self.config['target_percentage'][symbol] / current_price
                    if DEBUG:
                        # 打印再平衡日持仓数量比例的变化
                        previous_share_number = self.portfolio_data.at[previous_date, f"{symbol}_share_number"]
                        change_percentage = (share_number - previous_share_number)/previous_share_number * 100
                        print(f"{symbol} {TRADING_PRODUCTS[symbol]['name']} 持仓数量变化百分比: {change_percentage:.2f}%")

                else:
                    # 如果不是再平衡日，保持持仓数量不变
                    share_number = self.portfolio_data.at[previous_date, f"{symbol}_share_number"]
                
                # 更新持仓数量
                self.portfolio_data.at[current_date, f"{symbol}_share_number"] = share_number
                
                # 计算当前持仓价值：持仓数量 * 当前价格
                previous_value = float(share_number * current_price)
                self.portfolio_data.at[current_date, f"{symbol}_value"] = previous_value
            
            # 计算总价值：所有资产持仓价值之和
            total_value = float(sum(self.portfolio_data.at[current_date, f"{symbol}_value"] 
                            for symbol in self.portfolio))
            self.portfolio_data.at[current_date, 'total_value'] = total_value
        
        if DEBUG:
            print("\n回测结果:")
            print(self.portfolio_data)

    def get_results(self) -> pd.DataFrame:
        """
        获取回测结果
        
        Returns:
            DataFrame: 包含回测结果的数据框，包括每日价格、持仓数量、持仓价值和总价值
        """
        if self.portfolio_data is None:
            raise ValueError("请先运行回测")
        return self.portfolio_data

    def plot_portfolio_returns(self, save_path: str = 'portfolio_return_analysis.png') -> None:
        """
        绘制投资组合和各资产的相对收益率变化图
        
        Args:
            save_path: 图表保存路径，默认为'portfolio_return_analysis.png'
        """
        if self.portfolio_data is None:
            raise ValueError("请先运行回测")
            
        plt.figure(figsize=(12, 6))
        
        # 绘制投资组合总价值的相对收益率
        initial_total_value = self.portfolio_data['total_value'].iloc[0]
        normalized_total_value = self.portfolio_data['total_value'] / initial_total_value * 100
        plt.plot(self.portfolio_data.index, normalized_total_value, label='投资组合总价值', linewidth=2)
        
        # 绘制各个资产的相对收益率
        for symbol in self.portfolio:
            initial_price = self.portfolio_data[f"{symbol}_close"].iloc[0]
            normalized_price = self.portfolio_data[f"{symbol}_close"] / initial_price * 100
            plt.plot(self.portfolio_data.index, normalized_price, 
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

def check_portfolio_config(config: Dict) -> tuple[int, str]:
    """
    检查投资组合配置的有效性
    
    Args:
        config: 投资组合配置字典
        
    Returns:
        tuple[int, str]: (错误代码, 错误信息)
            - 错误代码: 0表示无错误，非0表示有错误
            - 错误信息: 如果有错误，包含所有错误信息的字符串
    """
    errors = []
    
    # 检查投资组合中每个产品的最早可用日期
    for symbol in config['target_percentage'].keys():
        # 检查产品是否在支持列表中
        if symbol not in TRADING_PRODUCTS:
            errors.append(f"错误: {symbol} 不在支持的投资品种列表中")
            continue
            
        product_info = TRADING_PRODUCTS[symbol]
        earliest_date = datetime.strptime(product_info['earliest_date'], '%Y-%m-%d')
        start_date = datetime.strptime(config['start_date'], '%Y-%m-%d')
        
        if earliest_date > start_date:
            errors.append(f"错误: {symbol} ({product_info['name']}) 的最早可用日期是 {earliest_date.date()}, "
                        f"晚于回测开始日期 {start_date.date()}")
    
    if errors:
        return 1, "\n".join(errors)
    return 0, "" 