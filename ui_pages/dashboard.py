import streamlit as st
import requests
from datetime import datetime
import yfinance as yf
import pandas as pd
import time

# --- 1. 抓取價格函式 ---
def get_crypto_price(ticker):
    """使用 yfinance 抓取即時價格與漲跌幅"""
    try:
        data = yf.Ticker(ticker)
        # 這裡改用 1d 或 5d 抓取資料量會小一點，速度快一點
        hist = data.history(period="1d") 
        if len(hist) == 0:
            return 0, 0
        
        current_price = hist['Close'].iloc[-1]
        # yfinance有時只會回傳最新一筆，做個防呆
        if len(hist) > 1:
            prev_close = hist['Close'].iloc[-2]
            change_percent = ((current_price - prev_close) / prev_close) * 100
        else:
            prev_close = current_price # 暫時視為沒漲跌
            change_percent = 0.0
        
        return current_price, change_percent
    except Exception as e:
        return 0, 0

# --- 2. 抓取恐懼貪婪指數函式 (維持不變) ---
def get_fear_and_greed():
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=5) # 加個 timeout 避免卡住
        data = response.json()
        value = data['data'][0]['value']
        classification = data['data'][0]['value_classification']
        return int(value), classification
    except:
        return 50, "Unknown"

# --- 3. 抓取鯨魚警報函式 ---
def get_whale_alerts(threshold=500000): 
    # 幣安 API: 抓取最近成交
    url = "https://api.binance.com/api/v3/aggTrades"
    params = {
        "symbol": "BTCUSDT",
        "limit": 500 
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        trades = response.json()
        
        whale_trades = []
        
        for trade in reversed(trades):
            price = float(trade['p'])
            quantity = float(trade['q'])
            timestamp = trade['T'] 
            is_buyer_maker = trade['m'] 
            
            total_value = price * quantity
            
            if total_value >= threshold:
                dt_object = datetime.fromtimestamp(timestamp / 1000)
                time_str = dt_object.strftime("%H:%M:%S")
                
                side = "🔴 賣出 (Sell)" if is_buyer_maker else "🟢 買入 (Buy)"
                
                whale_trades.append({
                    "時間": time_str,
                    "幣種": "BTC",
                    "方向": side,
                    "價格": f"${price:,.2f}",
                    "數量": f"{quantity:.4f}",
                    "總價值 (USD)": f"${total_value:,.0f}"
                })
                
                if len(whale_trades) >= 5:
                    break
        
        if not whale_trades:
            return pd.DataFrame(columns=["時間", "幣種", "方向", "價格", "數量", "總價值 (USD)"])
            
        return pd.DataFrame(whale_trades)
        
    except Exception as e:
        # print(f"API Error: {e}") # Debug用
        return pd.DataFrame()


# --- A. 價格儀表板 (刷新：3秒) ---
@st.fragment(run_every=3)
def show_metrics_section():
    st.caption(f"⚡ 價格更新: {time.strftime('%H:%M:%S')} (每3秒)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. 恐懼貪婪
    fng_value, fng_label = get_fear_and_greed()
    col1.metric("😨 恐懼貪婪", f"{fng_value}", fng_label)
    
    # 2. BTC
    btc_price, btc_change = get_crypto_price("BTC-USD")
    col2.metric("BTC 價格", f"${btc_price:,.2f}", f"{btc_change:.2f}%")
    
    # 3. ETH
    eth_price, eth_change = get_crypto_price("ETH-USD")
    col3.metric("ETH 價格", f"${eth_price:,.2f}", f"{eth_change:.2f}%")

    # 4. SOL
    sol_price, sol_change = get_crypto_price("SOL-USD")
    col4.metric("SOL 價格", f"${sol_price:,.2f}", f"{sol_change:.2f}%")

# --- B. 鯨魚警報區 (刷新：30秒) ---
@st.fragment(run_every=30)
def show_whale_section():
    st.caption(f"🐋 鏈上數據更新: {time.strftime('%H:%M:%S')} (每30秒)")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("🐋 鯨魚大戶警報")
        # 這裡為了展示效果，我把門檻調低一點點，比較容易看到資料
        whale_df = get_whale_alerts(threshold=100000) 
        st.table(whale_df)
        
    with c2:
        st.subheader("📊 策略說明")
        st.info("左側數據每 30 秒自動掃描一次區塊鏈上的大額轉帳。\n\n**紅色 (賣出)**：可能為倒貨訊號\n**綠色 (買入)**：可能為大戶進場")

# --- 主程式進入點 ---
def show():
    # 標題不隨時間變動，放在最外面
    st.markdown("### 🚀 市場即時儀表板 (多頻率更新版)")
    st.markdown("---")

    # 呼叫快速更新區塊
    show_metrics_section()

    st.markdown("---")

    # 呼叫慢速更新區塊
    show_whale_section()