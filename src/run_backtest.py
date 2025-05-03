"""
投资组合回测运行脚本
用于执行投资组合回测并输出分析结果
"""
from portfolio_backtest import PortfolioBacktest, check_portfolio_config
from trading_products import TRADING_PRODUCTS
import matplotlib.pyplot as plt

# 示例投资组合配置
PORTFOLIO_CONFIG = {
    'target_percentage': {
        'SPY': 0.2,  # 标普500ETF
        '090010': 0.2,   # 大成中证红利
        '518880': 0.2,  # 黄金ETF
        '070009': 0.4,  # 嘉实超短债债券基金
    },
    'start_date': '2013-08-01',
    'end_date': '2025-04-30',
    'initial_total_value': 100000,
}

def main():
    """
    主函数：运行回测并输出结果
    """
    # 检查配置
    error_code, error_message = check_portfolio_config(PORTFOLIO_CONFIG)
    if error_code != 0:
        print(error_message)
        return error_code

    # 创建回测实例
    backtest = PortfolioBacktest(PORTFOLIO_CONFIG)
    
    # 运行回测
    backtest.run_rebalance_backtest('DRIFT_REBALANCE')
    
    # 获取结果
    results = backtest.get_results()
    
    # 分析结果
    portfolio_return_analysis = backtest.calculate_portfolio_return()
    
    # 输出分析结果
    print("\n回测结果分析:")
    print(f"总收益率: {portfolio_return_analysis['portfolio_return']*100:.2f}%")
    print(f"年化收益率: {portfolio_return_analysis['annualized_portfolio_return']*100:.2f}%")

    # 计算最大回撤
    max_drawdowns = backtest.calculate_portfolio_max_drawdown()
    print("\n最大回撤分析:")
    for i, drawdown in enumerate(max_drawdowns, 1):
        print(f"\n第{i}大回撤:")
        print(f"回撤幅度: {drawdown['max_drawdown']:.2f}%")
    
    # 绘制投资组合总价值的相对收益率
    plt.figure(figsize=(12, 6))
    
    # 绘制投资组合总价值的相对收益率
    initial_total_value = results['total_value'].iloc[0]
    normalized_total_value = results['total_value'] / initial_total_value * 100
    plt.plot(results.index, normalized_total_value, label='投资组合总价值', linewidth=2)
    
    # 绘制各个资产的相对收益率
    for symbol in backtest.portfolio:
        initial_price = results[f"{symbol}_close"].iloc[0]
        normalized_price = results[f"{symbol}_close"] / initial_price * 100
        plt.plot(results.index, normalized_price, label=f"{symbol} ({TRADING_PRODUCTS[symbol]['name']})")
    
    plt.title('投资组合及各资产相对收益率变化')
    plt.xlabel('日期')
    plt.ylabel('相对收益率(%)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig('portfolio_return_analysis.png')
    
    return 0

if __name__ == "__main__":
    exit(main()) 