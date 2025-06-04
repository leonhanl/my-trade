"""
投资组合多时间段回测分析脚本

这个脚本用于对投资组合进行多个时间段的回测分析，通过在不同起始时间点进行回测，
来评估投资组合策略的稳定性和可靠性。

主要功能：
1. 从2013年8月1日开始，每月1日作为起始时间点进行回测
2. 每个回测周期为5年
3. 计算每个回测周期的年化收益率和最大回撤
4. 统计分析所有回测结果，包括最大值、最小值、平均值、中位数和标准差

配置说明：
- target_percentage: 各资产的目标配置比例
- start_date: 回测起始日期
- end_date: 回测结束日期
- initial_total_value: 初始投资金额
- rebalance_strategy: 再平衡策略
  * DRIFT_REBALANCE: 当资产偏离目标配置超过阈值时再平衡
  * ANNUAL_REBALANCE: 每年再平衡
  * NO_REBALANCE: 不进行再平衡
- drift_threshold: 再平衡阈值，当使用DRIFT_REBALANCE策略时有效

输出结果：
1. 所有回测时间段的年化收益率统计
2. 所有回测时间段的最大回撤统计
"""
from pprint import pprint
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import statistics
from portfolio_backtest import PortfolioBacktest, check_portfolio_config
from portfolio_analyzer import PortfolioAnalyzer
from portfolio_visualizer import PortfolioVisualizer
from common.trading_products import TRADING_PRODUCTS


CONFIG = {
    'target_percentage': {
        'SPY': 0.2,  # 标普500ETF
        '090010': 0.2,   # 大成中证红利
        '518880': 0.2,  # 黄金ETF
        '070009': 0.4,  # 嘉实超短债债券基金
    },
    'start_date': '2013-08-01',
    'end_date': '2025-04-30',
    'initial_total_value': 100000,
    'rebalance_strategy': 'DRIFT_REBALANCE', # 可选参数为'DRIFT_REBALANCE'或'ANNUAL_REBALANCE'或者'NO_REBALANCE'
    'drift_threshold': 0.2 # 当某个资产的持仓价值偏离预设值的20%时进行再平衡, 当rebalance_strategy为'DRIFT_REBALANCE'时有效
}

anualized_return_list = []
max_drawdown_list = []

# 从2013-08-01开始，每月1日，回测5年，最大为 2020-04-01
start_date_list = []
start_date = datetime.strptime('2013-08-01', '%Y-%m-%d')
end_date = datetime.strptime('2020-04-01', '%Y-%m-%d')

while start_date <= end_date:
    start_date_list.append(start_date.strftime('%Y-%m-%d'))
    start_date += relativedelta(months=1)    


for start_date in start_date_list:
    CONFIG['start_date'] = start_date
    #end_date 为start_date + 5年, 保持格式为'YYYY-MM-DD'
    CONFIG['end_date'] = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=365*5)).strftime('%Y-%m-%d')
    

    # 创建回测实例  
    backtest = PortfolioBacktest(CONFIG)
        
    # 运行回测
    backtest.run_backtest()

    # 创建分析器实例
    analyzer = PortfolioAnalyzer(backtest.get_results())

    # 分析结果
    portfolio_return_analysis = analyzer.calculate_portfolio_return()

    # 保留两位小数
    anualized_return_list.append(round(portfolio_return_analysis['annualized_portfolio_return']*100, 2)) 
    max_drawdown_list.append(round(analyzer.calculate_portfolio_max_drawdown()[0]['max_drawdown'], 2)) 

print("-"*100)
print("年化收益率:", anualized_return_list)
print("最大值：",max(anualized_return_list))
print("最小值：",min(anualized_return_list))
print(f"平均值：{statistics.mean(anualized_return_list):.2f}")
print(f"中位数：{statistics.median(anualized_return_list):.2f}")
print(f"标准差：{statistics.stdev(anualized_return_list):.2f}")

print("-"*100)
print("最大回撤:", max_drawdown_list)
print("最大值：",max(max_drawdown_list))
print("最小值：",min(max_drawdown_list))
print(f"平均值：{statistics.mean(max_drawdown_list):.2f}")
print(f"中位数：{statistics.median(max_drawdown_list):.2f}")
print(f"标准差：{statistics.stdev(max_drawdown_list):.2f}")
