import matplotlib.pyplot as plt
import matplotlib as mpl

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class PyramidTradingSimulator:
    def __init__(self, params):
        self.total_capital = params['total_capital']
        self.initial_price = params['initial_price']
        self.drop_points = sorted(params['drop_points'], key=lambda x: abs(x))
        self.position_weights = params['position_weights']
        self._validate_input()
        
        # 计算每份价值
        self.unit_value = self.total_capital / sum(self.position_weights)
        
        # 初始化状态
        self.reset()
        
    def _validate_input(self):
        if len(self.drop_points) != len(self.position_weights):
            raise ValueError("加仓点位与仓位权重数量不匹配")
        if any(p >= 0 for p in self.drop_points):
            raise ValueError("加仓点位应为负值（下跌百分比）")
            
    def reset(self):
        """重置模拟器状态"""
        self.remaining_capital = self.total_capital
        self.total_shares = 0.0
        self.avg_cost = 0.0
        self.history = []
        self.current_price = self.initial_price
        
    def _calculate_fv_loss(self, price):
        """计算浮亏"""
        market_value = self.total_shares * price
        cost_basis = self.total_shares * self.avg_cost
        loss = market_value - cost_basis
        loss_pct = loss / cost_basis if cost_basis != 0 else 0
        return loss_pct, loss
        
    def execute(self, verbose=True):
        """执行加仓策略"""
        print(f"{'='*40}\n策略开始执行 初始价格: {self.initial_price} 总资金: {self.total_capital:.2f}\n{'='*40}")
        
        for idx, (drop_pct, weight) in enumerate(zip(self.drop_points, self.position_weights)):
            # 计算触发价格
            trigger_price = self.initial_price * (1 + drop_pct/100)
            
            # 到达触发点
            self.current_price = trigger_price
            investment = weight * self.unit_value
            
            # 记录加仓前状态
            pre_loss_pct, pre_loss = self._calculate_fv_loss(trigger_price)
            
            # 执行加仓
            if investment - self.remaining_capital > 0.01:  # 添加0.01的容差值
                print(f"⚠️ 资金不足！在 {drop_pct}% 点位需要 {investment:.2f}，剩余资金 {self.remaining_capital:.2f}")
                break
                
            shares_bought = investment / trigger_price
            new_total_shares = self.total_shares + shares_bought
            new_avg_cost = (self.avg_cost*self.total_shares + investment) / new_total_shares if new_total_shares !=0 else 0
            
            # 更新状态
            self.remaining_capital -= investment
            self.avg_cost = new_avg_cost
            self.total_shares = new_total_shares
            
            # 计算加仓后浮亏
            post_loss_pct, post_loss = self._calculate_fv_loss(trigger_price)
            
            # 记录交易
            record = {
                'trigger_price': trigger_price,
                'drop_pct': drop_pct,
                'investment': investment,
                'shares_bought': shares_bought,
                'pre_loss_pct': pre_loss_pct,
                'pre_loss': pre_loss,
                'post_loss_pct': post_loss_pct,
                'post_loss': post_loss,
                'remaining_capital': self.remaining_capital,
                'total_shares': self.total_shares,
                'avg_cost': self.avg_cost
            }
            self.history.append(record)
            
            if verbose:
                print(f"{'-'*40}\n加仓点 #{idx+1}（下跌 {drop_pct}%）")
                print(f"📉 当前价格: {trigger_price:.2f}")
                print(f"💵 投入资金: {investment:.2f} | 剩余资金: {self.remaining_capital:.2f}")
                print(f"📊 加仓前浮亏: {pre_loss:.2f} ({pre_loss_pct:.2%})")
                print(f"📈 加仓后浮亏: {post_loss:.2f} ({post_loss_pct:.2%})")
                print(f"🔄 平均成本: {self.avg_cost:.2f} | 持仓数量: {self.total_shares:.2f}")
                
        return self.history
    
# 策略参数配置（示例）
strategy_params = {
    'total_capital': 1000000,     # 总资金100万元
    'initial_price': 100,        # 初始价格100元
    'drop_points': [-10, -15, -20, -25, -30],  # 加仓点位
    'position_weights': [2, 3, 4, 5, 2],      # 仓位权重，最后一笔为2份资金购买3倍杠杆ETF
    # 'drop_points': [-8, -13, -18, -23, -30],  # 加仓点位
    # 'position_weights': [3, 5, 7, 4, 1]      # 仓位权重
}

# 执行策略
simulator = PyramidTradingSimulator(strategy_params)
history = simulator.execute()

# 输出最终状态
final_price = simulator.current_price
final_value = simulator.total_shares * final_price
total_invested = simulator.total_capital - simulator.remaining_capital

print(f"\n{'='*40}\n策略执行结束:")
print(f"🏦 剩余资金: {simulator.remaining_capital:.2f}")
print(f"📈 持仓市值: {final_value:.2f}")
print(f"💰 总投入资金: {total_invested:.2f}")
print(f"📉 最终浮亏: {history[-1]['post_loss']:.2f} ({history[-1]['post_loss_pct']:.2%})")
print(f"🔢 平均持仓成本: {simulator.avg_cost:.2f}")