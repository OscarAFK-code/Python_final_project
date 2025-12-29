import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta

# 真實歷史事件庫
REAL_EVENTS = {
    "🇺🇸 SEC 批准比特幣現貨 ETF": "2024-01-10",
    "FTX 交易所申請破產 (黑天鵝)": "2022-11-11",
    "🇨🇳 中國全面禁止加密貨幣挖礦與交易": "2021-09-24",
    "Terra (LUNA) 崩盤與死亡螺旋": "2022-05-09",
    "Tesla 宣布暫停接受比特幣支付": "2021-05-12",
    "COVID-19 全球市場崩盤 (312慘案)": "2020-03-12"
}


@st.cache_data(ttl=3600) 
def get_binance_history(symbol, start_date_str, end_date_str):
    """
    [Tab 1 & Tab 3 通用] 呼叫幣安 API 抓取特定時間段的日線資料 (K線)
    """
    try:
        start_ts = int(pd.to_datetime(start_date_str).timestamp() * 1000)
        end_ts = int(pd.to_datetime(end_date_str).timestamp() * 1000)
        
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": "1d",
            "startTime": start_ts,
            "endTime": end_ts,
            "limit": 1000
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        
        df = pd.DataFrame(data, columns=[
            "Open Time", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore"
        ])
        
        df["Date"] = pd.to_datetime(df["Open Time"], unit="ms")
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = df[col].astype(float)
            
        return df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=60) 
def get_market_snapshot():
    """
    [Tab 2 專用] 抓取 Binance 所有交易對的 24h 數據，並篩選出前 30 名
    """
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        resp = requests.get(url)
        data = resp.json()
        df = pd.DataFrame(data)
        
        df = df[df['symbol'].str.endswith('USDT')]
        df = df[~df['symbol'].str.contains('UP|DOWN|BEAR|BULL')]
        
        df['priceChangePercent'] = df['priceChangePercent'].astype(float)
        df['quoteVolume'] = df['quoteVolume'].astype(float) 
        df['lastPrice'] = df['lastPrice'].astype(float)
        
        df_top = df.sort_values(by='quoteVolume', ascending=False).head(30)
        
        df_top['Coin'] = df_top['symbol'].str.replace('USDT', '')
        
        return df_top
    except Exception as e:
        st.error(f"API 連線失敗: {e}")
        return pd.DataFrame()

def fetch_real_market_data(event_name, symbol="BTCUSDT"):
    """
    計算「事件發生後」的價格走勢與回報率
    """
    event_date_str = REAL_EVENTS.get(event_name)
    if not event_date_str:
        return pd.DataFrame()
    
    event_date = pd.to_datetime(event_date_str)
    start_date = event_date - timedelta(days=2) # 前看2天
    end_date = event_date + timedelta(days=30)  # 後看30天
    
    df = get_binance_history(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    
    if df.empty:
        return df

    base_price = df[df["Date"] >= event_date].iloc[0]["Close"]
    df["Return %"] = ((df["Close"] - base_price) / base_price) * 100
    df["Days After"] = (df["Date"] - event_date).dt.days
    
    return df



def show():
    st.title("數據可視化中心")
    st.markdown("### 透過數據回測、熱力圖與相關性分析，尋找市場規律")
    
    tab1, tab2, tab3 = st.tabs(["事件驅動回測", "市場熱力圖", "幣種相關性矩陣"])

    #  事件驅動回測
    with tab1:
        st.subheader("歷史重演？重大新聞對幣價的影響")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_event = st.selectbox("選擇歷史重大事件", list(REAL_EVENTS.keys()))
        with col2:
            target_coin = st.selectbox("觀察幣種", ["BTC", "ETH", "SOL", "BNB", "DOGE"])
            
        symbol = f"{target_coin}USDT"
        
        if st.button("開始回測分析"):
            with st.spinner(f"正在調閱 {selected_event} 期間的 {target_coin} 數據..."):
                df_res = fetch_real_market_data(selected_event, symbol)
                
            if not df_res.empty:
                fig = px.line(
                    df_res, 
                    x="Days After", 
                    y="Return %", 
                    title=f"{target_coin} 在「{selected_event}」後的走勢",
                    markers=True
                )
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                fig.add_vline(x=0, line_color="red", annotation_text="事件發生日")
                st.plotly_chart(fig, width="stretch")
                
                max_drop = df_res[df_res["Days After"] > 0]["Return %"].min()
                max_gain = df_res[df_res["Days After"] > 0]["Return %"].max()
                
                m1, m2 = st.columns(2)
                m1.metric("事件後最大跌幅", f"{max_drop:.2f}%")
                m2.metric("事件後最大漲幅", f"{max_gain:.2f}%")
            else:
                st.warning("查無數據，可能是事件時間過於久遠或 API 限制。")

    # 全市場熱力圖
    with tab2:
        st.subheader("加密貨幣市場資金流向 (Top 30 Volume)")
        st.caption("方塊大小 = 24h成交額 (錢流到哪去) | 顏色 = 24h漲跌幅 (紅跌綠漲)")
        
        if st.button("刷新熱力圖"):
            st.cache_data.clear() 

        with st.spinner("正在掃描全球市場數據..."):
            df_snapshot = get_market_snapshot()
        
        if not df_snapshot.empty:
            fig_treemap = px.treemap(
                df_snapshot, 
                path=['Coin'], 
                values='quoteVolume',
                color='priceChangePercent',
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0,     
                hover_data=['lastPrice']
            )

            fig_treemap.update_traces(
                textinfo="label+value+percent entry",
                hovertemplate='<b>%{label}</b><br>成交額: $%{value:,.0f}<br>價格: $%{customdata[0]}<br>漲跌: %{color:.2f}%'
            )
            
            st.plotly_chart(fig_treemap, width="stretch")
        else:
            st.error("無法連接到 Binance API，請檢查網路狀態。")

    # 相關性矩陣
    with tab3:
        st.subheader("主流幣種連動性分析 (近半年)")
        st.markdown("""
        - **1.0 (深紅)**：完全正相關（一起漲、一起跌）。
        - **-1.0 (深藍)**：完全負相關（走勢相反，適合避險）。
        - **0 (白色)**：無相關性（各走各的）。
        """)
        
        target_coins = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'ADA', 'XRP', 'AVAX']
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        if st.button(" 開始計算相關係數矩陣"):
            combined_df = pd.DataFrame()
        
            prog_bar = st.progress(0, text="正在抓取數據...")
            
            try:
                for i, coin in enumerate(target_coins):
                    symbol = f"{coin}USDT"
                    df_coin = get_binance_history(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                    
                    if not df_coin.empty:
                        combined_df[coin] = df_coin['Close']
                    time.sleep(0.1) 
                    prog_bar.progress((i + 1) / len(target_coins), text=f"正在分析 {coin}...")
                
                prog_bar.empty()

                if not combined_df.empty:
                    corr_matrix = combined_df.corr()
                    fig_corr = px.imshow(
                        corr_matrix,
                        text_auto=".2f",
                        aspect="auto",
                        color_continuous_scale="RdBu_r", 
                        zmin=-1, zmax=1,
                        origin='lower'
                    )
                    st.plotly_chart(fig_corr, width="stretch")
                else:
                    st.error("數據不足，無法計算。")
            
            except Exception as e:
                st.error(f"發生錯誤: {e}")
 
            