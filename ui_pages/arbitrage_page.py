import streamlit as st
import pandas as pd
import numpy as np
import time
import random

# --- 0. 自動刷新機制 (相容性處理) ---
# 為了確保不同 Streamlit 版本都能跑，我們做個防呆檢查
# 如果版本太舊沒有 fragment，就定義一個假的裝飾器讓程式不報錯
try:
    from streamlit import fragment
except ImportError:
    def fragment(run_every=None):
        def decorator(func):
            return func
        return decorator

def show():
    # --- 1. 頁面標題與說明 ---
    st.title("💰 跨交易所搬磚套利監控")
    st.markdown("### 實時監控 Binance 與 OKX 之價差機會")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("ℹ️ **搬磚原理：** 當 `Binance 價格` > `OKX 價格` 且價差大於手續費時，從 OKX 買入、Binance 賣出即可獲利。")
    with col2:
        # 控制開關：讓使用者可以暫停監控，避免眼睛花掉
        is_running = st.toggle("🟢 啟動即時監控", value=True)

    # --- 2. 自動刷新區域 (Core Logic) ---
    # @fragment 是 Streamlit 1.37+ 的新功能
    # run_every=3 代表：這個函式每 3 秒會自己重新執行一次！
    @fragment(run_every=3 if is_running else None)
    def monitor_prices():
        st.caption(f"最後更新時間: {time.strftime('%H:%M:%S')}")
        
        # --- A. 模擬即時價格 (Simulate Prices) ---
        # 這裡用亂數產生，實際上你們會用 ccxt 去 fetch_ticker
        base_price = 65000
        noise = random.randint(-100, 100) # 市場波動
        
        # 故意製造兩個交易所的價差
        price_binance = base_price + noise + random.randint(0, 50)
        price_okx = base_price + noise - random.randint(0, 50)
        
        # 計算價差與獲利百分比
        spread = price_binance - price_okx
        spread_pct = (spread / price_okx) * 100
        
        # --- B. 顯示價格看板 (Dashboard) ---
        # 使用三個欄位顯示：Binance價格 | OKX價格 | 價差
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.metric("Binance (BTC/USDT)", f"${price_binance:,.2f}", delta="賣出價")
            
        with c2:
            st.metric("OKX (BTC/USDT)", f"${price_okx:,.2f}", delta="買入價", delta_color="inverse")
            
        with c3:
            # 判斷是否為「獲利機會」
            # 假設手續費成本約 0.1% (約 $65)，價差超過 $100 才算有賺
            threshold = 100 
            
            if spread > threshold:
                # 有套利機會！顯示綠色並放煙火
                st.metric("價差獲利 (Spread)", f"${spread:.2f}", f"+{spread_pct:.2f}% 🚀", delta_color="normal")
                st.success(f"🔥 **發現機會！** 建議：從 OKX 買入 -> 轉帳 -> Binance 賣出，預估每顆獲利 ${spread:.2f}")
            else:
                # 無機會，顯示灰色
                st.metric("價差 (Spread)", f"${spread:.2f}", "利潤不足", delta_color="off")

        # --- C. 歷史價差走勢 (選配) ---
        # 這裡簡單畫一個最近幾次的價差圖 (模擬)
        st.markdown("#### ⏳ 近期價差波動")
        fake_history = [random.randint(20, 150) for _ in range(20)]
        fake_history.append(spread) # 把最新的加進去
        st.line_chart(fake_history, height=200)

    # --- 3. 執行監控函式 ---
    # 這行很重要！一定要呼叫上面的函式，畫面才會出來
    monitor_prices() 