"""
投资组合回测运行脚本
用于执行投资组合回测并输出分析结果
"""
from pprint import pprint
from portfolio_backtest import PortfolioBacktest, check_portfolio_config
from portfolio_analyzer import PortfolioAnalyzer
from portfolio_visualizer import PortfolioVisualizer
from portfolio_configs import CONFIGS_REBALANCE_COMPARISON, CONFIGS_CN_COMPARISON


def run_portfolio_backtest(config: dict) -> None:
        """
        运行投资组合回测并输出分析结果
        
        Args:
            config: 回测配置字典
        """
        print("-"*100)
        print("回测配置:")
        pprint(config)

        # 打印投资组合中的产品名称
        print("\n投资组合产品:")
        from trading_products import TRADING_PRODUCTS
        for symbol in config['target_percentage'].keys():
            product_info = TRADING_PRODUCTS[symbol]
            print(f"{symbol}: {product_info['name']}")

        # 创建回测实例
        backtest = PortfolioBacktest(config)
        
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
    


def main():
    """
    主函数：运行回测并输出结果
    """
    # 检查配置
    for config in CONFIGS_CN_COMPARISON:
        error_code, error_msg = check_portfolio_config(config)
        if error_code != 0:
            print(error_msg)
            return error_code

    for config in CONFIGS_CN_COMPARISON:
        run_portfolio_backtest(config)
    
    return 0

if __name__ == "__main__":
    main() 