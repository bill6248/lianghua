# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 01:50:02 2019

@author: bill

因子分析。可以调节分析周期长度，次数，以及n日均涨幅。
rs为因子秩相关系数df
res_ci 为统计学有效性检验结果df
1.将周期始末涨幅计算变成周期始末n日均价涨幅，以减少单日波动造成的误差，因子值同理。
2.遇到数据缺失，所以每次数据帧运算前都会清洗数据
"""

import pandas as pd
import numpy as np
import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import scipy as sc
from jqdatasdk import *
from scipy import stats

auth('17765703568', 'Wyk123321')
# 结果矩阵
finalres = pd.DataFrame(columns=["vol", "pe", "roe", "pb", 'tr'])
res_test = pd.DataFrame(columns=["vol", "pe", "roe", "pb", 'tr'])

# 开始时间
t = datetime.datetime.strptime("2006-12-1", "%Y-%m-%d")
t = t.date()

# 分析
interval = 60  # 周期长度
n = 6  # 分析 n 个周期
for i in range(n):
    # 每次分析延后 interval 天
    t = t + datetime.timedelta(days=interval)
    sl = get_index_stocks('000300.XSHG', t)
    # 检验周期 开始日期
    lt = t - datetime.timedelta(days=interval)
    ts = t.strftime('%Y-%m-%d')
    lts = lt.strftime('%Y-%m-%d')

    # 获取过去nk天因子均值
    nk = 5
    for k in range(nk):
        q = query(
            valuation.code,
            valuation.market_cap.label("vol"),
            valuation.pe_ratio_lyr.label("pe"),
            indicator.roe.label("roe"),
            valuation.pb_ratio.label("pb"),
            valuation.turnover_ratio.label('tr')
        ).filter(
            valuation.code.in_(sl)
        )
        qd = lt - datetime.timedelta(days=k)
        df = get_fundamentals(q, qd)
        df = df.set_index('code')
        if k == 0:
            df1 = df
        else:
            df1 = df1 + df
        k = k + 1
    # 求均值
    df = df / nk


    # 获取周期内涨幅
    ct = 6  # 最近ct天股票收盘均价
    
    price = get_price(sl, end_date=t, count=ct)
    stock_close = price['close'].T
    stock_close.insert(len(stock_close.columns), 'mean', stock_close.mean(1))  # 计算均值并且插入

    price1 = get_price(sl, end_date=lt, count=ct)
    stock_close1 = price1['close'].T
    stock_close1.insert(len(stock_close1.columns), 'mean', stock_close1.mean(1))  # 计算均值并且插入

    # 数据清洗
    stock_close1 = stock_close1.dropna()
    stock_close = stock_close.dropna()
    
    # 计算均值涨幅
    zf = (stock_close['mean'] - stock_close1['mean']) / stock_close1['mean']

    # 插入涨幅数据进df
    df.insert(len(df.columns), 'zf', zf)
    df = df.dropna()

    rl = []
    rl2 = []
    # 建立 结果df
    # 分析每个因子与涨幅的秩相关性，将结果放进rl rl2 ，临时结果存放
    for i in range(len(df.columns) - 1):
        factor = df.columns[i]
        coef, p = stats.spearmanr(df[factor], df['zf'])
        rl.append(coef)
        rl2.append(p)

    # 插入新的分析结果进入final结果dataframe
    rs1 = pd.DataFrame(columns=["vol", "pe", "roe", "pb", 'tr'], data=[rl])
    #插入最终rs数据
    finalres = finalres.append(rs1, ignore_index=True)
    
    # 插入新的统计检验结果进入res_test
    rsp1 = pd.DataFrame(columns=["vol", "pe", "roe", "pb", 'tr'], data=[rl2])
    #统计学检验
    res_test = res_test.append(rsp1, ignore_index=True)

# 画出分布图
finalres.plot(kind='kde')
