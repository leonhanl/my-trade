"""
投资组合回测配置文件
包含不同策略的回测配置参数
"""

# 回测配置列表
CONFIGS_REBALANCE_COMPARISON = [
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
        'rebalance_strategy': 'NO_REBALANCE', # 可选参数为'DRIFT_REBALANCE'或'ANNUAL_REBALANCE'或者'NO_REBALANCE'
    },
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
        'rebalance_strategy': 'ANNUAL_REBALANCE', # 可选参数为'DRIFT_REBALANCE'或'ANNUAL_REBALANCE'或者'NO_REBALANCE'
    },
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
            '090010': 0.2,   # 大成中证红利
            '518880': 0.2,  # 黄金ETF
            '070009': 0.4,  # 嘉实超短债债券基金
        },
        'start_date': '2013-08-01',
        'end_date': '2025-04-30',
        'initial_total_value': 100000,
        'rebalance_strategy': 'DRIFT_REBALANCE', # 可选参数为'DRIFT_REBALANCE'或'ANNUAL_REBALANCE'或者'NO_REBALANCE'
        'drift_threshold': 0.3 # 当某个资产的持仓价值偏离预设值的30%时进行再平衡, 当rebalance_strategy为'DRIFT_REBALANCE'时有效
    },
] 



