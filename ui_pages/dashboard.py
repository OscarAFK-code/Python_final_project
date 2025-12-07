import streamlit as st
import random
import time

def show():
    # --- 1. 頁面標題區 ---
    st.title("🏠 市場總覽 Dashboard")
    st.markdown("### 全球加密貨幣市場情緒與大戶動向")
    st.markdown("---")

    # --- 2. 第一區塊：關鍵指標 (Key Metrics) ---
    # 我們切成 3 個欄位，看起來比較專業
    col1, col2, col3 = st.columns(3)

    # 模擬數據生成 (之後會換成真正的 API)
    fgi_value = random.randint(10, 90)
    btc_price = 65000 + random.randint(-500, 500)
    eth_price = 3500 + random.randint(-50, 50)

    # 根據恐懼指數決定顏色
    if fgi_value < 40:
        fgi_state = "恐懼 (Fear)"
        fgi_color = "inverse" # 紅色
    elif fgi_value > 60:
        fgi_state = "貪婪 (Greed)"
        fgi_color = "normal" # 綠色
    else:
        fgi_state = "中立 (Neutral)"
        fgi_color = "off" # 灰色

    # 顯示數據
    with col1:
        st.metric(
            label="Fear & Greed Index", 
            value=f"{fgi_value}", 
            delta=fgi_state,
            delta_color=fgi_color
        )
    
    with col2:
        st.metric(
            label="Bitcoin (BTC)",
            value=f"${btc_price:,}",
            delta="+2.4%", # 假裝今天漲了
        )

    with col3:
        st.metric(
            label="Ethereum (ETH)",
            value=f"${eth_price:,}",
            delta="-0.8%", # 假裝今天跌了
            delta_color="inverse"
        )

    st.markdown("---")

    # --- 3. 第二區塊：鯨魚警報 (Whale Alerts) ---
    st.subheader("🐋 即時鯨魚警報 (Whale Alert)")
    
    # 這裡利用 st.expander 做成可收合的說明
    with st.expander("ℹ️ 什麼是鯨魚警報？"):
        st.write("監控鏈上單筆超過 **1,000 BTC** 的大額轉帳。通常轉入交易所暗示**賣壓**，轉出暗示**囤幣**。")

    # 模擬警報數據列表
    alerts = [
        {"time": "09:45", "coin": "BTC", "amount": 1200, "from": "Unknown", "to": "Binance", "type": "sell"},
        {"time": "08:30", "coin": "ETH", "amount": 15000, "from": "OKX", "to": "Unknown", "type": "buy"},
        {"time": "07:15", "coin": "BTC", "amount": 850, "from": "Coinbase", "to": "Unknown", "type": "buy"},
        {"time": "06:50", "coin": "USDT", "amount": 50000000, "from": "Tether Treasury", "to": "Binance", "type": "pump"},
    ]

    # 用迴圈把每一條警報印出來
    for alert in alerts:
        # 根據類型決定圖示和顏色
        if alert['type'] == 'sell':
            icon = "🚨"
            msg = f"**{alert['time']}** | ⚠️ 大額轉入交易所 (疑似倒貨): **{alert['amount']:,} {alert['coin']}** 從 {alert['from']} -> {alert['to']}"
            st.error(f"{icon} {msg}")
        
        elif alert['type'] == 'buy':
            icon = "🟢"
            msg = f"**{alert['time']}** | 💰 大戶提現囤幣: **{alert['amount']:,} {alert['coin']}** 從 {alert['from']} -> {alert['to']}"
            st.success(f"{icon} {msg}")
            
        elif alert['type'] == 'pump':
            icon = "⛽"
            msg = f"**{alert['time']}** | 燃料補充 (印鈔): **{alert['amount']:,} {alert['coin']}** 注入市場"
            st.info(f"{icon} {msg}")