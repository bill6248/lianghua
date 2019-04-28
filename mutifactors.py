# 多因子策略入门


'''
================================================================================
总体回测前
================================================================================
'''



def initialize(context):
    set_para()  # 1设置策参数
    set_var()  # 2设置中间变量
    set_con()  # 3设置回测条件



# 设置策参数
def set_para():
    g.f = 55  # 调仓频率
    g.yb = 63  # 样本长度
    g.N = 20  # 持仓数目
    g.factors = ["pe_ratio", "turnover_ratio"]  # 用户选出来的因子
    # 因子等权重里1表示因子值越小越好，-1表示因子值越大越好
    g.weights = [[1], [-1]]



# 设置变量
def set_var():
    g.tt = 0  # 记录回测运行的天数
    g.iftrade = False  # 当天是否交易




def set_con():
    set_option('use_real_price', True)  # 用真实价格交易
    log.set_level('order', 'error')


'''
================================================================================
每天开盘前
================================================================================
'''


# 每天开盘前
def before_trading_start(context):
    if g.tt % g.f == 0:
        # 每g.f天，交易一次行
        g.iftrade = True
        g.all_stocks = set_feasible_stocks(get_index_stocks('000300.XSHG'), g.yb, context)
        # 查询所有财务因子
        g.q = query(valuation, balance, cash_flow, income, indicator).filter(valuation.code.in_(g.all_stocks))
    g.tt += 1



# 设置可行股票池
def set_feasible_stocks(sl, days, context):
    # 得到是否停牌信息的dataframe，停牌的1，未停牌得0
    suspened = get_price(list(sl), start_date=context.current_dt, end_date=context.current_dt, frequency='daily',
                                 fields='paused')['paused'].T
    # 过滤停牌股票 返回dataframe
    unsuspened = suspened.iloc[:, 0] < 1
    # 得到当日未停牌股票的代码list:
    unsuspened_stocks = suspened[unsuspened].index
    # 进一步，筛选出前days天未曾停牌的股票list:
    available_stocks = []
    current_data = get_current_data()
    for stock in unsuspened_stocks:
        if sum(attribute_history(stock, days, unit='1d', fields=('paused'), skip_paused=False))[0] == 0:
            available_stocks.append(stock)
    return available_stocks


'''
================================================================================
每天交易时
================================================================================
'''


def handle_data(context, data):
    if g.iftrade == True:
        # 计算现在的总资产，以分配资金，这里是等额权重分配
        g.stockvalue = context.portfolio.portfolio_value / g.N
        # 获得因子排序
        r, l = Factorrank(g.factors, str(context.current_dt)[0:10])
        # 计算每个股票的得分
        marks = np.dot(r, g.weights)
        # 复制股票代码
        stocklist = l[:]
        # 对股票的得分进行排名
        marks, stocklist = rank(marks, stocklist)
        # 取前N名的股票
        toBuy = stocklist[0:g.N]
        # 对于不需要持仓的股票，全仓卖出
        order_stock_sell(context, data, toBuy)
        # 对于不需要持仓的股票，按分配到的份额买入
        order_stock_buy(context, data, toBuy)
    g.iftrade = False


# 6
# 获得卖出信号，并执行卖出操作
# 输入：context, data，toBuy-list
# 输出：none
def order_stock_sell(context, data, toBuy):
    # 如果现有持仓股票不在股票池，清空
    position = context.portfolio.positions.keys()
    for stock in position:
        if stock not in toBuy:
            order_target(stock, 0)


# 买入操作

def order_stock_buy(context, data, toBuy):
    # 对于需要持仓的股票，按分配到的份额买入
    for i in toBuy:
        order_target_value(i, g.stockvalue)



# 取因子rank数据

def Factorrank(f, day):
    # 获得股票的基本面数据
    df = get_fundamentals(g.q, day)
    res = [([0] * len(f)) for i in range(len(df))]
    # 把数据填充
    for i in range(0, len(df)):
        for j in range(0, len(f)):
            res[i][j] = df[f[j]][i]
    fillNan(res)
    # 将数据变成排名
    res1=getRank(res)
    # 返回因子rank数据和股票的代码
    return res1, df['code']



# 获取rank
def getRank(r):
    index = list(range(0, len(r)))
    # 对每一列进行冒泡排序
    for k in range(len(r[0])):
        for i in range(len(r)):
            for j in range(i):
                if r[j][k] < r[i][k]:
                    # 交换所有的列以及用于记录一开始的顺序的数组
                    index[j], index[i] = index[i], index[j]
                    for l in range(len(r[0])):
                        r[j][l], r[i][l] = r[i][l], r[j][l]
        # 将排序好的因子顺序变成排名
        for i in range(len(r)):
            r[i][k] = i + 1
    # 再进行一次冒泡排序恢复一开始的股票顺序
    for i in range(len(r)):
        for j in range(i):
            if index[j] > index[i]:
                index[j], index[i] = index[i], index[j]
                for k in range(len(r[0])):
                    r[j][k], r[i][k] = r[i][k], r[j][k]
    return r



# 用均值填充Nan

def fillNan(m):
    rows = len(m)
    columns = len(m[0])
    for j in range(0, columns):
        sum = 0.0
        count = 0.0
        for i in range(0, rows):
            if not (isnan(m[i][j])):
                sum += m[i][j]
                count += 1
        # 计算平均值，为了防止全是NaN，如果当整列都是NaN的时候认为平均值是0
        avg = sum / max(count, 1)
        for i in range(0, rows):
            # 这个for循环是用来把NaN值填充为刚才计算出来的平均值的
            if isnan(m[i][j]):
                m[i][j] = avg
    return m



# 定义一个冒泡排序的函数
def rank(num, index):
    for i in range(len(num)):
        for j in range(i):
            if num[j][0] < num[i][0]:
                # 在进行交换的时候同时交换得分以记录哪些股票得分比较高
                num[j][0], num[i][0] = num[i][0], num[j][0]
                index[j], index[i] = index[i], index[j]
    return num, index











