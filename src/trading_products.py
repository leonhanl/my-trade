# 交易品种字典
TRADING_PRODUCTS = {
    # 美国
    'SPY': {
        'name': '标普500ETF-Invesco',
        'category': 'ETF',
        'market': 'US',
        'akshare_symbol': '107.SPY',
        'earliest_date': '2001-01-02'
    },
    'QQQ': {
        'name': '纳斯达克100ETF-Invesco',
        'category': 'ETF',
        'market': 'US',
        'akshare_symbol': '105.QQQ',
        'earliest_date': '2001-01-02'
    },
    'TLT': {
        'name': '20年期美国国债ETF-Invesco',
        'category': 'ETF',
        'market': 'US',
        'akshare_symbol': '105.TLT',
        'earliest_date': '2016-02-02'
    },
    'GLD': {
        'name': '黄金ETF-SPDR',
        'category': 'ETF',
        'market': 'US',
        'akshare_symbol': '107.GLD',
        'earliest_date': '2004-11-18'
    },
    'BIL': {
        'name': '美国国债1-3月ETF-SPDR',
        'category': 'ETF',
        'market': 'US',
        'akshare_symbol': '107.BIL',
        'earliest_date': '2007-05-30'
    },
    'NVDA':{
        'name': '英伟达',
        'category': 'stock',
        'market': 'US',
        'akshare_symbol': '105.NVDA',       
        'earliest_date': '2001-01-02'
    },

    # 中国指数
    '000001': {
        'name': '上证指数',
        'category': 'index',
        'market': 'CN',
        'earliest_date': '1990-12-19'
    },

    # 中国ETF
    '510300': {
        'name': '华泰柏瑞沪深300ETF',
        'category': 'ETF',
        'market': 'CN',
        'earliest_date': '2012-05-28'
    },
    '515100': {
        'name': '景顺长城中证红利低波动ETF',
        'category': 'ETF',
        'market': 'CN',
        'earliest_date': '2020-07-03'
    },
    '518880': {
        'name': '黄金ETF',
        'category': 'ETF',
        'market': 'CN',
        'earliest_date': '2013-07-29'
    },

    # 中国基金
    '090010': {
        'name': '大成中证红利',
        'category': 'stock_fund',
        'market': 'CN',
        'earliest_date': '2010-02-02'
    },
    '008114': {
        'name': '天弘中证红利低波动100联接A',
        'category': 'stock_fund',
        'market': 'CN',
        'earliest_date': '2019-12-10'
    },
    '070009': {
        'name': '嘉实超短债债券基金',
        'category': 'bond_fund',
        'market': 'CN',
        'earliest_date': '2006-04-26'
    },
    '003358': {
        'name': '易方达中债7-10年国开行债券指数',
        'category': 'bond_fund',
        'market': 'CN',
        'earliest_date': '2016-09-27'
    },

   

    # 中国货币基金
    # '040003': {
    #     'name': '华安现金富利投资基金',
    #     'category': 'money_fund',
    #     'market': 'CN',
    #     'earliest_date': '2003-12-30'
    # },
    # '050003': {
    #     'name': '博时现金收益证券投资基金',
    #     'category': 'money_fund',
    #     'market': 'CN',
    #     'earliest_date': '2004-01-16'
    # },
    # '217004': {
    #     'name': '招商现金增值开放式证券投资基金',
    #     'category': 'money_fund',
    #     'market': 'CN',
    #     'earliest_date': '2004-01-14'
    # }
}
