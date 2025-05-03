"""
投资组合回测运行脚本
用于执行投资组合回测并输出分析结果
"""
from portfolio_backtest import PortfolioBacktest, check_portfolio_config
from portfolio_analyzer import PortfolioAnalyzer
from portfolio_visualizer import PortfolioVisualizer

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
    # 回测配置
    config = {
        'target_percentage': {
            'SPY': 0.2,  # 标普500ETF
            '090010': 0.2,   # 大成中证红利
            '518880': 0.2,  # 黄金ETF
            '070009': 0.4,  # 嘉实超短债债券基金
        },
        'start_date': '2013-08-01',
        'end_date': '2025-04-30',
        'initial_total_value': 100000,
        'show_plot': True
    }
    
    # 检查配置
    error_code, error_msg = check_portfolio_config(config)
    if error_code != 0:
        print(error_msg)
        return
        
    # 创建回测实例
    backtest = PortfolioBacktest(config)
    
    # 运行回测
    backtest.run_rebalance_backtest('ANNUAL_REBALANCE')
    
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
    print("\n回测结果分析:")
    print(f"总收益率: {portfolio_return_analysis['portfolio_return']*100:.2f}%")
    print(f"年化收益率: {portfolio_return_analysis['annualized_portfolio_return']*100:.2f}%")

    # 计算最大回撤
    max_drawdowns = analyzer.calculate_portfolio_max_drawdown()
    print("\n最大回撤分析:")
    for i, drawdown in enumerate(max_drawdowns, 1):
        print(f"\n第{i}大回撤:")
        print(f"回撤幅度: {drawdown['max_drawdown']:.2f}%")
    
    return 0

if __name__ == "__main__":
    main() 