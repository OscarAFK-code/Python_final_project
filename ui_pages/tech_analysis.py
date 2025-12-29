import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ccxt

def fetch_exchange_data(symbol="BTC/USDT", timeframe="1d", limit=100):
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df.set_index('Date', inplace=True)
        return df
    except Exception as e:
        st.error(f"Binance 連線失敗: {e}")
        return pd.DataFrame()

def show():
    st.title("專業技術分析室")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        coin_choice = st.selectbox("選擇幣種", ["BTC", "ETH", "SOL", "DOGE"])
        symbol = f"{coin_choice}/USDT"
    with col2:
        time_label = st.selectbox("抓取時間範圍", ["一天", "近七天", "一個月", "三個月", "一年"])
        range_config = {
            "一天": {"tf": "15m", "limit": 96},
            "近七天": {"tf": "1h", "limit": 168},
            "一個月": {"tf": "12h", "limit": 60},
            "三個月": {"tf": "1d", "limit": 90},
            "一年": {"tf": "1d", "limit": 365}
        }
        config = range_config[time_label]
    with col3:
        overlays = st.multiselect("疊加指標", ["MA20 (月線)", "MA60 (季線)", "Bollinger Bands"], default=["MA20 (月線)"])
    with col4:
        sub_chart = st.selectbox("副圖指標", ["Volume (成交量)", "RSI", "MACD"])

    st.markdown("---")

    buffer_size = 100 
    total_limit = config["limit"] + buffer_size
    
    with st.spinner(f'正在獲取 {symbol} 數據...'):
        df = fetch_exchange_data(symbol=symbol, timeframe=config["tf"], limit=total_limit)

    if df.empty: return

    # 根據定義計算指標
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA60"] = df["Close"].rolling(window=60).mean()
    
    # 布林通道定義
    std_20 = df["Close"].rolling(window=20).std()
    df["BB_Upper"] = df["MA20"] + (std_20 * 2)
    df["BB_Lower"] = df["MA20"] - (std_20 * 2)

    # RSI 計算
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # MACD 定義
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = exp12 - exp26  
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()  
    df['MACD_Hist'] = df['DIF'] - df['DEA']

    plot_df = df.iloc[buffer_size:].copy()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, 
                        subplot_titles=(f"{symbol} 趨勢分析", sub_chart), row_width=[0.4, 0.6])

    fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'],
                                 low=plot_df['Low'], close=plot_df['Close'], name="K線"), row=1, col=1)

    if "MA20 (月線)" in overlays:
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["MA20"], line=dict(color='orange', width=1.5), name="MA20"), row=1, col=1)
    if "MA60 (季線)" in overlays:
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["MA60"], line=dict(color='cyan', width=1.5), name="MA60"), row=1, col=1)
    if "Bollinger Bands" in overlays:
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["BB_Upper"], line=dict(color='rgba(255,255,255,0.2)', width=1), name="布林上軌"), row=1, col=1)
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["BB_Lower"], line=dict(color='rgba(255,255,255,0.2)', width=1), 
                                 fill='tonexty', fillcolor='rgba(173, 216, 230, 0.1)', name="布林下軌"), row=1, col=1)
    if sub_chart == "Volume (成交量)":
        colors = ['red' if r['Open'] > r['Close'] else 'green' for i, r in plot_df.iterrows()]
        fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['Volume'], marker_color=colors, name="成交量"), row=2, col=1)
    
    elif sub_chart == "RSI":
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['RSI'], line=dict(color='#AB63FA'), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    elif sub_chart == "MACD":
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['DIF'], line=dict(color='white', width=1.5), name="DIF (快線)"), row=2, col=1)
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['DEA'], line=dict(color='yellow', width=1.5), name="DEA (慢線)"), row=2, col=1)
        hist_colors = ['red' if val >= 0 else 'green' for val in plot_df['MACD_Hist']]
        fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['MACD_Hist'], marker_color=hist_colors, name="MACD柱狀圖"), row=2, col=1)

    fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.info(f"💡 目前 {symbol} 報價: ${plot_df['Close'].iloc[-1]:,.2f}")
    if df.empty:
        st.warning(f"無法獲取 {symbol} 的數據，可能是網路問題或交易所限制，請稍後再試。")
        return