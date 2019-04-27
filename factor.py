# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 01:50:02 2019

@author: bill

因子分析。可以调节分析周期长度，次数，以及n日均涨幅。
rs为因子秩相关系数df
rsp 为统计学有效性检验结果df
1.将周期始末涨幅计算变成周期始末n日均价涨幅，以较少单日波动造成的误差，因子值同理。
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
auth('17765703568','Wyk123321')
#结果矩阵
rs = pd.DataFrame(columns = ["vol", "pe", "roe", "pb",'tr'])
rsp = pd.DataFrame(columns = ["vol", "pe", "roe", "pb",'tr'])

#开始时间
t=datetime.datetime.strptime("2006-12-1", "%Y-%m-%d")
t=t.date()


#分析


interval=60  #周期长度

n=66 # 分析 n 个周期
for i in range(n):
    #每次分析延后 interval 天
    t=t+ datetime.timedelta(days=interval)
    
    sl = get_index_stocks('000300.XSHG',t)
    #检验周期 开始日期
    lt=t- datetime.timedelta(days=interval)
    ts=t.strftime('%Y-%m-%d')
    lts=lt.strftime('%Y-%m-%d')
    
    print (lt)
    print (t)
    
    #获取过去nk天因子均值
    nk=5
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
        qd=lt- datetime.timedelta(days=k)
#        print(qd)
        df = get_fundamentals(q,qd)
        df=df.set_index('code')
        if k==0:
            df1=df
        else:
            df1=df1+df
        k=k+1
    #求均值
    df=df/nk
    #设置index
 
    #获取涨幅
    #停牌问题！！
    
    #获取周期内涨幅
    ct=6    #最近ct天股票收盘均价
    tt=get_price(sl,end_date=t,count=ct)
    z=tt['close'].T
    z.insert(len(z.columns),'mean',z.mean(1))#计算均值并且插入
    
    tt1=get_price(sl,end_date=lt,count=ct)
    z1=tt1['close'].T
    z1.insert(len(z1.columns),'mean',z1.mean(1))#计算均值并且插入
    
    #数据清洗
    z1=z1.dropna()
    z=z.dropna()  
    
    print(len(z1))
    print(len(z))
    #计算均值涨幅
    zf=(z['mean']-z1['mean'])/z1['mean']
    
#    
    #插入涨幅数据进df
    df.insert(len(df.columns),'zf',zf)
    print('01')
    df=df.dropna()

    # =============================================================================
    # x=df['pb_ratio']
    # y=df['market_cap']
    # sns.kdeplot(x,y,shade=True)
    #df.corr('spearman') 相关性分析
    # =============================================================================
    rl=[]
    rl2=[]
    #建立 结果df
    print('1')
    #分析 每个因子 的 相关性 放进rl rl2
    for i in range(len(df.columns)-1):
        la=df.columns[i]
       
        coef, p = stats.spearmanr(df[la], df['zf'])
        rl.append(coef)
        rl2.append(p)
    
    #插入新的分析结果进入结果dataframe
    
    rs1 = pd.DataFrame(columns = ["vol", "pe", "roe", "pb",'tr'],data=[rl])
    rs=rs.append(rs1,ignore_index=True)
    rsp1 = pd.DataFrame(columns = ["vol", "pe", "roe", "pb",'tr'],data=[rl2])
    rsp=rsp.append(rsp1,ignore_index=True)
    
#画出分布图
    
rs.plot(kind='kde')
