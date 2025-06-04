"""
投资组合回测比较实验脚本

本脚本用于执行不同投资组合配置的回测，并比较其表现差异。
当前实验主要比较：
1. 使用中证红利指数(090010)作为A股投资标的的组合
2. 使用沪深300指数(510300)作为A股投资标的的组合

两个组合的其他配置完全相同：
- 标普500ETF(SPY): 20%
- A股指数(090010/510300): 20%
- 黄金ETF(518880): 20%
- 嘉实超短债债券基金(070009): 40%

回测参数：
- 时间范围: 2013-08-01 至 2025-04-30
- 初始资金: 100,000
- 再平衡策略: 当资产偏离目标配置20%时进行再平衡

输出结果包括：
- 总收益率
- 年化收益率
- 最大回撤分析
"""
from pprint import pprint
from portfolio_backtest import PortfolioBacktest, check_portfolio_config
from portfolio_analyzer import PortfolioAnalyzer
from portfolio_visualizer import PortfolioVisualizer
from common.trading_products import TRADING_PRODUCTS



CONFIGS = [
    {
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
    },
    {
        'target_percentage': {
            'SPY': 0.2,  # 标普500ETF
            '510300': 0.2,   # 沪深300ETF
            '518880': 0.2,  # 黄金ETF
            '070009': 0.4,  # 嘉实超短债债券基金
        },
        'start_date': '2013-08-01',
        'end_date': '2025-04-30',
        'initial_total_value': 100000,
        'rebalance_strategy': 'DRIFT_REBALANCE', # 可选参数为'DRIFT_REBALANCE'或'ANNUAL_REBALANCE'或者'NO_REBALANCE'
        'drift_threshold': 0.2 # 当某个资产的持仓价值偏离预设值的20%时进行再平衡, 当rebalance_strategy为'DRIFT_REBALANCE'时有效
    },
   
] 

# 检查配置
for config in CONFIGS:
    error_code, error_msg = check_portfolio_config(config)
    if error_code != 0:
        print(error_msg)
        exit(error_code)

for config in CONFIGS:
    print("-"*100)
    print("回测配置:")
    pprint(config)

    # 打印投资组合中的产品名称
    print("\n投资组合产品:")
    for symbol in config['target_percentage'].keys():
        product_info = TRADING_PRODUCTS[symbol]
        print(f"{symbol}: {product_info['name']}")

    # 创建回测实例
    backtest = PortfolioBacktest(config)
    
    # 运行回测
    backtest.run_backtest()
    
    # 获取回测结果
    results = backtest.get_results()
    
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