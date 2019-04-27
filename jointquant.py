#银行股增强指数量化策略
#每个周期开始，通过pb指标计算2只银行股的比例，通过加权pb计算持仓比例
#


# 导入函数库
from jqdata import *
import math
# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000001.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')

    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')

 
    g.stock1 = '601166.XSHG'
    g.stock2 = '600036.XSHG'
    run_monthly(fun, 1, time='9:31', reference_security='000001.XSHG')

## 每月运行一次，进行调仓
def fun(context):
    #计算出持仓计划
    # log.info('1')
    ans=ratio(context)
    # log.info('5')
    cash=context.portfolio.subportfolios[0].available_cash
    value=context.portfolio.subportfolios[0].positions_value
    a1=ans[0]*ans[2]*(cash+value)
    a2=ans[1]*ans[2]*(cash+value)
    # log.info('6')
    log.info(a1)
    log.info(a2)
    order_target_value(g.stock1, ans[0]*ans[2]*(cash+value))
    order_target_value(g.stock2, ans[1]*ans[2]*(cash+value))
#计算持仓计划
def ratio(conext):
    q = query(
      valuation
    ).filter(
      valuation.code == g.stock1
    )
    df = get_fundamentals(q)
  # 打印出总市值
    # log.info('2')
    a=df['pb_ratio'][0] #s1 pb

    q = query(
      valuation
    ).filter(
      valuation.code == g.stock2
    )
    df = get_fundamentals(q)
    # log.info('3')
  # 打印出总市值
    b=df['pb_ratio'][0] #s2 pb
    # log.info('4')
 
    
    r=a/b
    
    p1=1/(1+r)
    p2=1-p1;
    if p1>0.7:
        p1=0.7
        p2=1-p1
    elif p1<0.3:
        p1=0.3
        p2=1-p1
    log.info(p1) 
    #计算加权pb
    tpb=(p1*a+p2*b)
    if tpb>1:
        log.info("warming")
        tpb=(floor(tpb*10))/10
        if tpb>=1.5:
            cw=0
        else:
            cw=1.5-tpb
    else:
        cw=1
    log.info(cw)    
    
    # p1 = 股票1 的仓位占比 p2= 股票2的仓位占比 cw 总仓位
    ans=[p1,(1-p1),cw]
    return ans
    
    

    
    
