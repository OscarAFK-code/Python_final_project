import streamlit as st
import pandas as pd
# 記得匯入新的函式
from data_modules.market_data import get_price_data, get_fear_and_greed_index

def show():
    st.title("🏠 市場總覽 Dashboard")
    st.markdown("### 🌐 全球主流交易所即時報價監控")
    st.markdown("---")

    # --- 定義資料抓取函式 (快取 60秒) ---
    @st.cache_data(ttl=60)
    def fetch_dashboard_data():
        # 1. 抓幣價
        price_df = get_price_data(coins=['BTC', 'ETH', 'SOL', 'DOGE'])
        # 2. 抓恐懼貪婪指數
        fgi_data = get_fear_and_greed_index()
        return price_df, fgi_data

    # 執行抓取
    with st.spinner('🚀 正在同步全球市場數據...'):
        df, fgi_data = fetch_dashboard_data()

    # --- 第一區塊：重點關注幣種 (Binance) ---
    st.subheader("🔥 重點關注幣種 (Binance 24h 漲跌)")
    
    df_binance = df[df['Exchange'] == 'Binance'].set_index('Coin')
    col1, col2, col3, col4 = st.columns(4)

    def show_metric(col, coin_name):
        if coin_name in df_binance.index:
            price = df_binance.loc[coin_name, 'Price']
            change = df_binance.loc[coin_name, 'Change24h%']
            
            # 沒抓到資料的防呆
            if pd.isna(price): 
                col.warning(f"{coin_name} N/A")
                return

            fmt = ",.4f" if price < 1 else ",.2f"
            col.metric(
                label=f"{coin_name}/USDT",
                value=f"${price:{fmt}}",
                delta=f"{change:.2f}%"  # 這裡就是 24h 漲跌幅
            )
        else:
            col.error("No Data")

    show_metric(col1, 'BTC')
    show_metric(col2, 'ETH')
    show_metric(col3, 'SOL')
    show_metric(col4, 'DOGE')

    st.markdown("---")

    # --- 第二區塊：真實的恐懼貪婪指數 ---
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("😱 市場情緒 (Real-Time)")
        
        if fgi_data:
            value = fgi_data['value']
            state = fgi_data['state']  # 例如 "Extreme Fear"
            
            # 顏色邏輯
            if value < 40:
                color = "inverse" # 紅色 (恐懼)
            elif value > 60:
                color = "normal"  # 綠色 (貪婪)
            else:
                color = "off"     # 灰色 (中立)
                
            st.metric("Fear & Greed Index", f"{value}", state, delta_color=color)
            
            # 畫一個簡單的進度條來視覺化
            st.progress(value / 100)
            st.caption(f"資料來源: Alternative.me (每日更新)")
        else:
            st.warning("暫時無法獲取情緒指數")

    # --- 第三區塊：交易所比價表 (維持不變) ---
    with c2:
        st.subheader("📊 三大交易所價格比較")
        if not df.empty:
            pivot_df = df.pivot(index='Coin', columns='Exchange', values='Price')
            st.dataframe(pivot_df.style.format("${:,.2f}"), use_container_width=True)

    # ... (鯨魚警報部分保持不變) ...
    
    # --- 6. 鯨魚警報 (保留原本樣式) ---
    st.subheader("🐋 近期大額轉帳警報")
    alerts = [
        {"time": "10:23", "msg": "🚨 2,000 BTC 從 未知錢包 轉入 Binance (可能賣壓)"},
        {"time": "09:45", "msg": "🟢 50,000 SOL 從 OKX 提現至 錢包 (可能囤幣)"},
        {"time": "08:12", "msg": "🚨 10,000,000 DOGE 轉入 Coinbase"},
    ]
    for alert in alerts:
        st.text(f"{alert['time']} | {alert['msg']}")