"""
配置验证模块
用于验证投资组合配置的有效性
"""
from datetime import datetime
from typing import Dict
from trading_products import TRADING_PRODUCTS

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