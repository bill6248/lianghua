#!/usr/bin/env python
# coding:utf-8
from PoboAPI import *
import datetime


def OnStart(context):
    print
    "I\'m starting..."
    g.code = GetMainContract('SHFE', 'rb', 20)
    SubscribeQuote(g.code)
    context.MyAlarm1 = SetAlarm(datetime.time(9, 01), RepeatType.Daily)

    if context.accounts.has_key("回测期货"):
        print
        "登录交易账号 回测期货"
        if context.accounts["回测期货"].Login():
            context.myacc = context.accounts["回测期货"]
    g.h = 0  # 初始持有天数
    g.hd = 25  # j计划持hd交易日
    g.k = 30  # 观察k交易日


# 选择理想主力下单
def open(context):
    mclist = []
    pzlist = []
    ch = GetVarieties('SHFE')
    # 找出主力合约list
    for i in ch:
        if i != 'Ocu' and i != 'Oru' and i != 'sp' and i != 'fu' and i != 'wr':
            zhuli = GetMainContract('SHFE', i, 20)
            #             print i + str(zhuli)
            mclist.append(str(zhuli))
            pzlist.append(i)
    #     for i in mclist:
    #         print i
    max = -1
    min = 100
    # 选择最好的主合约
    for i in mclist:
        today = GetCurrentTradingDate('SHFE')
        ago = today - datetime.timedelta(days=g.k)

        # 找出30天历史数据
        option = PBObj()
        option.WeightType = 1
        option.StartDate = ago
        option.Count = g.k
        klinedata = GetHisData(i, BarType.Day, option)

        if len(klinedata) > 10:
            increase = (klinedata[-1].close - klinedata[0].close) / klinedata[0].close
            decrease = increase

            if increase >= max:
                max = increase
                g.best = i

            if decrease <= min:
                min = decrease
                g.worst = i

    print(g.best, "is the best")
    print(g.worst, "is the worst")

    # 买入best
    QuickOpenPosition(context.accounts["回测期货"], g.best, 'buy', 4)
    # 卖出worst
    QuickOpenPosition(context.accounts["回测期货"], g.worst, 'sell', 4)

    # 清仓


def close(context):
    option = PBObj()
    pos = context.accounts["回测期货"].GetPositions(option)
    for c in pos:
        if c.bstype.BuySellFlag == "0":
            context.accounts["回测期货"].InsertOrder(c.contract, BSType.SellClose, 2, c.volume)
        #               print "sellclose-"+str(c.contract)
        if c.bstype.BuySellFlag == "1":
            QuickClosePosition(context.accounts["回测期货"], c.contract, 'sell')


#               print "buyclose-"+str(c.contract)

def OnAlarm(context, alarmid):
    if istradedate():
        if empty(context):
            open(context)
            checkposition(context)
            g.h = 1
        else:
            if g.h == g.hd:
                close(context)
                open(context)
                checkposition(context)
                g.h = 1

            elif g.h < g.hd:
                g.h = g.h + 1
            elif g.h > g.hd:
                close(context)
                open(context)
                checkposition(context)
                g.h = 1
        # 检查委托单状况


#         getorder1(context)


# 判断是否是交易日
def istradedate():
    gt = str(GetCurrentTime())
    td = str(GetCurrentTradingDate('SHFE'))
    d = ""
    for i in gt:
        if i != " ":
            d = d + i
        else:
            break
    #     print d
    if d == td:
        #         print"今日交易日"
        return 1

    # 判断是否空仓


def empty(context):
    # 持仓情况
    option = PBObj()
    pos = context.accounts["回测期货"].GetPositions(option)
    if len(pos) != 0:
        return 0
    else:
        return 1

    # 查询持仓


def getorder1(context):
    option = PBObj()

    # 显示所有未完成的订单
    s = [0, 4, 5, 33]
    for i in s:
        option.status = i
        ods = context.accounts["回测期货"].GetOrders(option)
        if len(ods) != 0:
            for j in ods:
                print("order##", j.bstype.BuySellFlag, j.contract, j.status, j.bstype.OffsetFlag)

    # 查询持仓


def checkposition(context):
    # 持仓情况
    option = PBObj()
    pos = context.accounts["回测期货"].GetPositions(option)
    if len(pos) != 0:
        for i in pos:
            if i.bstype.BuySellFlag == "1":

                print("------hold sell", i.contract, i.volume)
            else:
                print("------hold buy", i.contract, i.volume)
    else:
        print
        "is empty"

