import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 輔助函式：產生逼真的模擬 K 線數據 ---
def generate_fake_market_data(days=100, start_price=60000, volatility=0.02):
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    data = []
    price = start_price
    
    for date in dates:
        # 模擬每日漲跌 (隨機漫步)
        change = np.random.normal(0, volatility)
        open_price = price
        close_price = price * (1 + change)
        
        # 根據開盤收盤，隨機產生最高最低價
        if close_price > open_price:
            high_price = close_price * (1 + abs(np.random.normal(0, volatility/2)))
            low_price = open_price * (1 - abs(np.random.normal(0, volatility/2)))
        else:
            high_price = open_price * (1 + abs(np.random.normal(0, volatility/2)))
            low_price = close_price * (1 - abs(np.random.normal(0, volatility/2)))
            
        data.append({
            "Date": date,
            "Open": open_price,
            "High": high_price,
            "Low": low_price,
            "Close": close_price,
            "Volume": np.random.randint(1000, 5000)
        })
        price = close_price # 更新隔天價格
        
    return pd.DataFrame(data).set_index("Date")

def show():
    # --- 1. 頁面標題與控制列 ---
    st.title("📊 專業技術分析室")
    st.markdown("### 互動式 K 線圖與技術指標疊加")
    
    # 建立 4 欄的控制列，讓使用者選擇參數
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        coin = st.selectbox("選擇幣種", ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"])
    
    with col2:
        time_range = st.selectbox("時間範圍", ["1個月", "3個月", "6個月", "1年"])
        # 這裡根據選擇設定天數 (模擬用)
        days_map = {"1個月": 30, "3個月": 90, "6個月": 180, "1年": 365}
        days = days_map[time_range]
    
    with col3:
        # 多選選單：讓使用者疊加指標
        overlays = st.multiselect("疊加指標", ["MA20 (月線)", "MA60 (季線)", "Bollinger Bands"], default=["MA20 (月線)"])
        
    with col4:
        # 副圖指標 (尚未實作，先放選單)
        sub_chart = st.selectbox("副圖指標", ["Volume (成交量)", "RSI", "MACD"])

    st.markdown("---")

    # --- 2. 獲取數據 (模擬) ---
    # 根據幣種設定不同價格
    start_price = 65000 if "BTC" in coin else (3500 if "ETH" in coin else 150)
    df = generate_fake_market_data(days=days, start_price=start_price)

    # --- 3. 計算技術指標 ---
    # 移動平均線
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA60"] = df["Close"].rolling(window=60).mean()
    
    # 布林通道 (中軌=MA20, 上下軌=2個標準差)
    df["BB_Upper"] = df["MA20"] + 2 * df["Close"].rolling(window=20).std()
    df["BB_Lower"] = df["MA20"] - 2 * df["Close"].rolling(window=20).std()

    # --- 4. 繪製圖表 (使用 Plotly) ---
    # 建立主圖 (K線) 與 副圖 (成交量/RSI) 的框架
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=(f"{coin} 價格走勢", "成交量"), 
                        row_width=[0.2, 0.7])

    # [主圖] 繪製 K 線
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="K線"
    ), row=1, col=1)

    # [主圖] 疊加指標 (根據使用者選擇)
    if "MA20 (月線)" in overlays:
        fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], line=dict(color='orange', width=1), name="MA20"), row=1, col=1)
    
    if "MA60 (季線)" in overlays:
        fig.add_trace(go.Scatter(x=df.index, y=df["MA60"], line=dict(color='blue', width=1), name="MA60"), row=1, col=1)

    if "Bollinger Bands" in overlays:
        # 畫布林通道上軌
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], line=dict(color='gray', width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
        # 畫布林通道下軌 (並填滿顏色)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], fill='tonexty', fillcolor='rgba(128, 128, 128, 0.2)', line=dict(color='gray', width=0), name="布林通道"), row=1, col=1)

    # [副圖] 繪製成交量
    colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

    # --- 5. 圖表美化設定 ---
    fig.update_layout(
        height=600, # 設定圖表高度
        xaxis_rangeslider_visible=False, # 隱藏下方預設的滑桿 (因為我們有副圖了)
        template="plotly_dark", # 深色主題
        hovermode="x unified", # 游標移過去會顯示所有數值
        margin=dict(l=0, r=0, t=30, b=0) # 縮減邊界
    )

    # 顯示圖表
    st.plotly_chart(fig, use_container_width=True)
    
    # 顯示簡易數據統計
    st.info(f"📊 {coin} 統計數據 ({time_range}): 最高價 ${df['High'].max():.2f} | 最低價 ${df['Low'].min():.2f} | 目前價格 ${df['Close'].iloc[-1]:.2f}")