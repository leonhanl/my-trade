# 量化交易分析工具

这是一个基于 Python 的量化交易分析工具，用于分析交易数据并生成投资组合收益分析报告。

## 功能特点

- 使用 AKShare 获取金融市场数据
- 交易数据本地存储（SQLite数据库）
- 投资组合收益分析可视化
- 自动生成分析报告和图表

## 环境要求

- Python 3.8+
- 依赖包：
  - akshare
  - matplotlib

## 安装说明

1. 克隆项目到本地：
```bash
git clone [项目地址]
cd my-trade
```

2. 创建并激活虚拟环境：
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 确保已激活虚拟环境
2. 运行主程序：
```bash
python src/portfolio/run_backtest.py
```

## 项目结构

```
my-trade/
├── src/                    # 源代码目录
├── .venv/                  # Python虚拟环境
├── trade_data.db          # 交易数据数据库
├── requirements.txt       # 项目依赖
└── README.md             # 项目说明文档
```

## 注意事项

- 首次运行前请确保已正确安装所有依赖包
- 数据库文件会自动创建，无需手动初始化
- 建议定期备份 trade_data.db 文件

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件