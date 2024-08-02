import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import streamlit as st

def get_broker_volumn(stock_id, broker_idx):
    a = str(broker_idx)[:2]+"00"
    b = "".join([hex(ord(char)) for char in str(broker_idx)]).replace("x","0")

    base_url = "https://fubon-ebrokerdj.fbs.com.tw/z/zc/zco/zco0/zco0.djhtm"
    params = {
        "a":stock_id,
        "BHID": a,
        "b": b,
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"}


    response = requests.get(base_url,params=params,headers=headers)
    df = pd.read_html(response.content)[3]
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index()
    return float(df.iloc[0]['買賣超(張)'])

def get_df(broker_dict, stock_id_list):
    df = pd.DataFrame(index=stock_id_list, columns=broker_dict.keys())
    for idx in df.index:
        for col in df.columns:
            df.loc[idx, col] = get_broker_volumn(idx, broker_dict[col])
    stock_name_df = pd.read_csv('TWstock.csv', usecols=['stock id','stock name'])
    stock_name_df = stock_name_df.set_index('stock id')
    stock_name_df.loc[stock_id_list]
    df.index.name = 'stock id'
    df['stock name'] = stock_name_df.loc[stock_id_list]
    cols = df.columns.tolist()
    cols = [cols[-1]] + cols[:-1]
    df = df[cols]

    yfdf = pd.read_csv('yfid.csv')
    df['yf id'] = yfdf.set_index('stock id').loc[df.index]
    price_df = yf.download(df['yf id'].to_list(), period = '1d')['Close'].round(2)
    df['price'] = df.apply(lambda row: price_df[row['yf id']],axis = 1)
    df[list(broker_dict.keys())] = df[broker_dict.keys()].apply(lambda row: row * df.loc[row.name,'price'],axis = 1)
    df = df.drop(columns=['price', 'yf id'])

    return df


broker_dict = {"凱基-信義":'9216'
              ,"國票-安和":'779Z'
              }

stock_id_list = st.multiselect(
    'stock id list:',
    pd.read_csv('TWstock.csv', usecols=['stock id'])['stock id'].to_list(),
    [2330, 2454, 2610])

broker_list = st.multiselect(
    'broker list:',
    pd.read_csv('brokeridx.csv')['證券商名稱'].to_list(),
    ["凱基-信義", "國票-安和"])

broker_dict = dict(zip(broker_list, pd.read_csv('brokeridx.csv').set_index('證券商名稱').loc[broker_list, '代號'].to_list()))

df = get_df(broker_dict, stock_id_list)

st.dataframe(df)

