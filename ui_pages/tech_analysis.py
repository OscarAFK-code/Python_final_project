import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# --- 1. 資料抓取函式 (核心) ---
# 使用 ttl=300 (5分鐘) 快取，避免每次改指標都重新下載，但確保資料不過期
@st.cache_data(ttl=300)
def get_market_data(ticker, period, interval):
    """
    從 Yahoo Finance 抓取真實歷史資料
    """
    try:
        # 下載資料
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        
        # 處理 yfinance 多層索引問題 (如果有的話)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # 確保有需要的欄位
        needed_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in needed_cols):
            return pd.DataFrame() # 回傳空表代表失敗
            
        return df
    except Exception as e:
        st.error(f"資料抓取失敗: {e}")
        return pd.DataFrame()

# --- 2. 技術指標計算函式 ---
def calculate_indicators(df):
    """
    計算各種技術指標 (MA, BB, RSI, MACD)
    """
    # 複製一份以免改到原始資料
    data = df.copy()
    
    # --- 主圖指標 ---
    # MA (移動平均)
    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["MA60"] = data["Close"].rolling(window=60).mean()
    
    # Bollinger Bands (布林通道)
    std = data["Close"].rolling(window=20).std()
    data["BB_Upper"] = data["MA20"] + 2 * std
    data["BB_Lower"] = data["MA20"] - 2 * std
    
    # --- 副圖指標 ---
    # RSI (相對強弱指標, 14天)
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD (指數平滑異同移動平均線)
    # EMA12, EMA26
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema12 - ema26
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
    
    return data

# --- 3. 頁面顯示邏輯 ---
def show():
    # --- 標題與控制列 ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("📊 專業技術分析室")
        st.markdown("### 互動式 K 線圖與多維度指標")
    with c2:
        # [功能] 使用者手動更新按鈕
        # 這是處理「即時資料更新」最適合的方法
        if st.button("🔄 立即刷新數據", use_container_width=True):
            st.cache_data.clear() # 清除快取
            st.rerun() # 重新執行頁面

    st.markdown("---")

    # 參數設定區
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 支援更多熱門幣種
        coin_map = {
            "Bitcoin (BTC)": "BTC-USD",
            "Ethereum (ETH)": "ETH-USD",
            "Solana (SOL)": "SOL-USD",
            "Dogecoin (DOGE)": "DOGE-USD",
            "Binance Coin (BNB)": "BNB-USD"
        }
        selected_coin_label = st.selectbox("選擇幣種", list(coin_map.keys()))
        ticker = coin_map[selected_coin_label]
    
    with col2:
        # 設定時間範圍對應的 yfinance 參數
        # 為了讓 K 線圖好看，我們根據範圍自動調整 interval (K棒週期)
        range_map = {
            "1個月 (時線)": ("1mo", "60m"),
            "3個月 (日線)": ("3mo", "1d"),
            "6個月 (日線)": ("6mo", "1d"),
            "1年 (日線)": ("1y", "1d"),
            "今年至今 (YTD)": ("ytd", "1d")
        }
        selected_range = st.selectbox("時間範圍", list(range_map.keys()))
        period, interval = range_map[selected_range]
    
    with col3:
        overlays = st.multiselect("主圖疊加", ["MA20 (月線)", "MA60 (季線)", "Bollinger Bands"], default=["MA20 (月線)"])
        
    with col4:
        # 實作了 RSI 和 MACD
        sub_indicator = st.selectbox("副圖指標", ["Volume (成交量)", "RSI (相對強弱)", "MACD (趨勢)"])

    # --- 獲取數據 ---
    with st.spinner(f"正在從全球市場下載 {ticker} 數據..."):
        raw_df = get_market_data(ticker, period, interval)
        
    if raw_df.empty:
        st.error("❌ 無法取得數據，請檢查網路連線或稍後再試。")
        return

    # --- 計算指標 ---
    df = calculate_indicators(raw_df)
    
    # 取得最新一筆價格資訊
    latest = df.iloc[-1]
    last_price = latest['Close']
    prev_price = df.iloc[-2]['Close']
    change = (last_price - prev_price) / prev_price * 100
    color_code = "green" if change >= 0 else "red"
    
    # 顯示即時報價條
    st.markdown(f"""
    ### {ticker} 現價: <span style='color:{color_code}'>${last_price:,.2f}</span> 
    <span style='font-size:0.8em; color:{color_code}'>({change:+.2f}%)</span>
    """, unsafe_allow_html=True)

    # --- 繪圖 (Plotly) ---
    # 建立雙圖表 (上面是 K 線，下面是副圖)
    row_heights = [0.7, 0.3] # 主圖佔 70%，副圖佔 30%
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=row_heights,
        subplot_titles=(f"價格走勢", sub_indicator)
    )

    # [1] 主圖：K 線圖
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="K線"
    ), row=1, col=1)

    # [1] 主圖：疊加指標
    if "MA20 (月線)" in overlays:
        fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], line=dict(color='orange', width=1.5), name="MA20"), row=1, col=1)
    
    if "MA60 (季線)" in overlays:
        fig.add_trace(go.Scatter(x=df.index, y=df["MA60"], line=dict(color='skyblue', width=1.5), name="MA60"), row=1, col=1)

    if "Bollinger Bands" in overlays:
        # 上軌
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], line=dict(color='gray', width=1, dash='dot'), name="BB Upper"), row=1, col=1)
        # 下軌 (填色)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], fill='tonexty', fillcolor='rgba(128, 128, 128, 0.1)', line=dict(color='gray', width=1, dash='dot'), name="BB Lower"), row=1, col=1)

    # [2] 副圖：根據選擇繪製
    if "Volume" in sub_indicator:
        # 漲紅跌綠 (Crypto 常見配色: 漲=綠, 跌=紅，但在 Plotly 預設可能相反，這裡手動設定)
        colors = ['#00cc96' if row['Close'] >= row['Open'] else '#ef553b' for i, row in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), row=2, col=1)
        
    elif "RSI" in sub_indicator:
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#A367DC', width=2), name="RSI"), row=2, col=1)
        # RSI 超買超賣線
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1, annotation_text="超買 (70)")
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1, annotation_text="超賣 (30)")
        
    elif "MACD" in sub_indicator:
        # MACD 快線與慢線
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='cyan', width=1.5), name="DIF"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='orange', width=1.5), name="DEA"), row=2, col=1)
        # MACD 柱狀圖
        hist_colors = ['#00cc96' if v >= 0 else '#ef553b' for v in df['MACD_Hist']]
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=hist_colors, name="MACD Hist"), row=2, col=1)

    # --- 圖表美化 ---
    fig.update_layout(
        height=650,
        xaxis_rangeslider_visible=False, # 隱藏下方滑桿
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)
    
    st.caption(f"資料來源: Yahoo Finance | 週期: {interval} | 最後更新: {latest.name.strftime('%Y-%m-%d %H:%M')}")

# 測試用
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    show()