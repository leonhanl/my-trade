"""
投资组合回测主类
实现了一个简单的投资组合回测系统，支持多资产配置和定期再平衡
"""
import pandas as pd
import sqlite3
from typing import Dict, List
import matplotlib.pyplot as plt
from datetime import datetime
from trading_products import TRADING_PRODUCTS
from pprint import pprint

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

DEBUG = True


class DataLoader:
    def __init__(self):
        """初始化数据加载器，设置数据库路径"""
        self.db_path = 'trade_data.db'
        
    def load_portfolio_data(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """
        从数据库加载投资组合数据
        
        Args:
            symbols: 投资组合中的产品代码列表，如 ['510300', '515100', 'GLD', 'QQQ']
            start_date: 开始日期，格式为 'YYYY-MM-DD'
            end_date: 结束日期，格式为 'YYYY-MM-DD'
            
        Returns:
            DataFrame: 包含所有产品价格数据的DataFrame，索引为日期，列为各产品的收盘价
        """
        conn = sqlite3.connect(self.db_path)
        
        # 构建SQL查询，使用参数化查询防止SQL注入
        placeholders = ','.join(['?'] * len(symbols))
        query = f"""
        SELECT 
            symbol,
            date,
            close
        FROM unified_price_view
        WHERE symbol IN ({placeholders})
        AND date BETWEEN ? AND ?
        ORDER BY date
        """
        
        # 执行查询，将查询参数和日期范围合并
        params = symbols + [start_date, end_date]
        df = pd.read_sql_query(query, conn, params=params)
        
        # 将日期列转换为datetime类型，便于后续处理
        df['date'] = pd.to_datetime(df['date'])
        
        # 将数据透视为宽格式，每个产品一列
        df_pivot = df.pivot(index='date', columns='symbol', values='close')
        
        # 重命名列以添加后缀，便于后续处理
        df_pivot.columns = [f"{col}_close" for col in df_pivot.columns]
        
        conn.close()
        return df_pivot

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

    def calculate_portfolio_return(self) -> Dict:
        """
        计算年化收益率
        """
        if self.portfolio_data is None:
            raise ValueError("请先运行回测")
        
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
    
    # 计算组合中每个资产的收益率
    def calculate_asset_return(self) -> Dict:
        """
        计算每个资产的收益率
        """
        if self.portfolio_data is None:
            raise ValueError("请先运行回测")

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

    # 计算前三名的最大回撤，确保时间段不重叠
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
        if self.portfolio_data is None:
            raise ValueError("请先运行回测")

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