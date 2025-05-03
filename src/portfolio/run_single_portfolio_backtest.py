"""
投资组合单次回测脚本

本脚本用于执行单个投资组合配置的回测，并生成可视化分析结果。
使用固定的投资组合配置：

- 标普500ETF(SPY): 20%
- 大成中证红利(090010): 20%
- 黄金ETF(518880): 20%
- 嘉实超短债债券基金(070009): 40%

回测参数：
- 时间范围: 2013-08-01 至 2025-04-30
- 初始资金: 100,000
- 再平衡策略: 当资产偏离目标配置20%时进行再平衡 (DRIFT_REBALANCE)

输出内容：
1. 回测结果分析：
   - 总收益率
   - 年化收益率
   - 最大回撤分析
2. 可视化图表：
   - 生成portfolio_return_analysis.png文件，展示投资组合收益走势
"""
from pprint import pprint
from portfolio_backtest import PortfolioBacktest, check_portfolio_config
from portfolio_analyzer import PortfolioAnalyzer
from portfolio_visualizer import PortfolioVisualizer
from trading_products import TRADING_PRODUCTS


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

# 检查配置
error_code, error_msg = check_portfolio_config(CONFIG)
if error_code != 0:
    print(error_msg)
    exit(error_code)


# 创建回测实例
backtest = PortfolioBacktest(CONFIG)
    
# 运行回测
backtest.run_backtest()
    
# 获取回测结果
results = backtest.get_results()
    
# 使用可视化器绘制结果
visualizer = PortfolioVisualizer()
visualizer.plot_portfolio_returns(results, 'portfolio_return_analysis.png')

# 创建分析器实例
analyzer = PortfolioAnalyzer(results)

# 分析结果
portfolio_return_analysis = analyzer.calculate_portfolio_return()

# 输出分析结果
print("\n回测结果分析")
print(f"总收益率: {portfolio_return_analysis['portfolio_return']*100:.2f}%")
print(f"年化收益率: {portfolio_return_analysis['annualized_portfolio_return']*100:.2f}%")

# 计算最大回撤
max_drawdowns = analyzer.calculate_portfolio_max_drawdown()
print("\n最大回撤分析:")
for i, drawdown in enumerate(max_drawdowns, 1):
    print(f"第{i}大回撤 - 回撤幅度: {drawdown['max_drawdown']:.2f}%, 持续时间: {drawdown['drawdown_length']}天，恢复时间: {drawdown['recovery_length']}天") 