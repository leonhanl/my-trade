"""
投资组合回测主类
实现了一个简单的投资组合回测系统，支持多资产配置和定期再平衡
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List
import logging
from common.trading_products import TRADING_PRODUCTS
from portfolio.data_loader import DataLoader
from portfolio.config_validator import check_portfolio_config

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 将处理器添加到日志记录器
logger.addHandler(console_handler)

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
        logger.debug("\n初始投资组合数据:\n" + str(self.portfolio_data))
        
    def get_results(self) -> pd.DataFrame:
        """
        获取回测结果
        
        Returns:
            DataFrame: 包含回测结果的 pandas.DataFrame，包括每日价格、持仓数量、持仓价值和总价值
        """
        if self.portfolio_data is None:
            raise ValueError("请先运行回测")
        return self.portfolio_data 
        
    def run_backtest(self) -> None:
        """
        根据再平衡策略运行回测        
        """
        if self.portfolio_data is None:
            self.initialize_portfolio() 
            
        rebalance_strategy = self.config['rebalance_strategy']

            
        for i in range(1, len(self.portfolio_data)):
            current_date = self.portfolio_data.index[i]
            previous_date = self.portfolio_data.index[i-1]
            
            is_rebalance_day = False
            
            if rebalance_strategy == 'NO_REBALANCE':
                pass
            elif rebalance_strategy == 'ANNUAL_REBALANCE':
                # 判断是否是1月1日
                if current_date.month == 1 and previous_date.month == 12:
                    is_rebalance_day = True
                    logger.debug(f"年度再平衡日: {current_date}")
            elif rebalance_strategy == 'DRIFT_REBALANCE':  # 当某个资产的持仓价值偏离预设值的20%时进行再平衡 
                for symbol in self.portfolio:
                    previous_value = self.portfolio_data.at[previous_date, f"{symbol}_value"]
                    target_value = self.config['target_percentage'][symbol] * self.portfolio_data.at[previous_date, 'total_value']
                    if abs(previous_value - target_value) / target_value > self.config['drift_threshold']:
                        is_rebalance_day = True
                        logger.debug(f"日期: {current_date} {symbol} {TRADING_PRODUCTS[symbol]['name']} 持仓价值偏离预设值的{self.config['drift_threshold']*100}%，当前百分比为: {previous_value/target_value*100:.2f}%，进行再平衡")
                        break
               

            # 计算每个资产的持仓变化
            for symbol in self.portfolio:
                # 获取当前价格
                current_price = self.portfolio_data.at[current_date, f"{symbol}_close"]
                
                if is_rebalance_day:
                    # 如果是再平衡日，根据目标比例重新计算持仓数量
                    previous_total_value = self.portfolio_data.at[previous_date, 'total_value']
                    share_number = previous_total_value * self.config['target_percentage'][symbol] / current_price
                    # 打印再平衡日持仓数量比例的变化
                    previous_share_number = self.portfolio_data.at[previous_date, f"{symbol}_share_number"]
                    change_percentage = (share_number - previous_share_number)/previous_share_number * 100
                    logger.debug(f"{symbol} {TRADING_PRODUCTS[symbol]['name']} 持仓数量变化百分比: {change_percentage:.2f}%")

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
        
        logger.debug("\n回测结果:\n" + str(self.portfolio_data))

    

   



   