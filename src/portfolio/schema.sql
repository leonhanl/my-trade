-- 创建股票历史数据表
CREATE TABLE IF NOT EXISTS stock_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    trade_date DATE NOT NULL,
    open DECIMAL(10,2),
    close DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    volume BIGINT,
    amount DECIMAL(20,2),
    amplitude DECIMAL(10,2),
    change_percent DECIMAL(10,2),
    change_amount DECIMAL(10,2),
    turnover_rate DECIMAL(10,2),
    UNIQUE (symbol, trade_date)
);

-- 创建基金净值表
CREATE TABLE IF NOT EXISTS fund_nav (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    nav_date DATE NOT NULL,
    nav DECIMAL(10,4) NOT NULL,
    UNIQUE (fund_code, nav_date)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_stock_price_symbol ON stock_price(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_price_date ON stock_price(trade_date);
CREATE INDEX IF NOT EXISTS idx_stock_price_symbol_date ON stock_price(symbol, trade_date);
CREATE INDEX IF NOT EXISTS idx_fund_nav_code ON fund_nav(fund_code);
CREATE INDEX IF NOT EXISTS idx_fund_nav_date ON fund_nav(nav_date);
CREATE INDEX IF NOT EXISTS idx_fund_nav_code_date ON fund_nav(fund_code, nav_date);

-- 创建统一价格视图
CREATE VIEW IF NOT EXISTS unified_price_view AS
SELECT 
    symbol as symbol,
    name as name,
    trade_date as date,
    close as close
FROM stock_price
UNION ALL
SELECT 
    fund_code as symbol,
    name as name,
    nav_date as date,
    nav as close
FROM fund_nav;


-- 在 stock_price 表中添加 PE-TTM 列
ALTER TABLE stock_price ADD COLUMN pe_ttm DECIMAL(10,2);


-- 删除现有视图
DROP VIEW IF EXISTS unified_price_view;

-- 创建新的视图，包含 pe_ttm
CREATE VIEW unified_price_view AS
SELECT 
    symbol as symbol,
    name as name,
    trade_date as date,
    close as close,
    pe_ttm as pe_ttm
FROM stock_price
UNION ALL
SELECT 
    fund_code as symbol,
    name as name,
    nav_date as date,
    nav as close,
    NULL as pe_ttm  -- 基金没有 PE-TTM，用 NULL 填充
FROM fund_nav;