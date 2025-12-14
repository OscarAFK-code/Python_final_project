import streamlit as st
import pandas as pd
import time
import ccxt

# --- 0. 自動刷新機制 (相容性處理) ---
try:
    from streamlit import fragment
except ImportError:
    def fragment(run_every=None):
        def decorator(func):
            return func
        return decorator

# --- 1. 初始化交易所連線 ---
@st.cache_resource
def init_exchanges():
    binance = ccxt.binance()
    okx = ccxt.okx()
    return binance, okx

binance, okx = init_exchanges()

def get_realtime_prices(symbol="BTC/USDT"):
    try:
        ticker_b = binance.fetch_ticker(symbol)
        ticker_o = okx.fetch_ticker(symbol)
        
        return {
            "binance": ticker_b['last'],
            "okx": ticker_o['last'],
            "timestamp": time.time()
        }
    except Exception as e:
        return None

def show():
    # --- 2. 頁面標題與設定 ---
    st.title("💰 跨交易所搬磚套利監控 (Live)")
    st.markdown("### 實時監控 Binance vs OKX 價差機會")
    st.caption("資料來源: 交易所真實即時 API (CCXT)")
    st.markdown("---")

    # --- [新增] 初始化歷史數據暫存區 ---
    # 如果這是第一次執行，就建立一個空的列表來放價差紀錄
    if 'spread_history' not in st.session_state:
        st.session_state['spread_history'] = []

    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])
    with col_cfg1:
        target_symbol = st.selectbox("監控幣種", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT"])
        # 如果使用者切換幣種，我們應該把舊的歷史圖表清空，重新開始畫
        if 'last_symbol' not in st.session_state or st.session_state['last_symbol'] != target_symbol:
            st.session_state['spread_history'] = [] # 清空
            st.session_state['last_symbol'] = target_symbol # 更新記錄

    with col_cfg2:
        threshold_pct = st.number_input("獲利門檻 (%)", value=0.2, step=0.1)
    with col_cfg3:
        is_running = st.toggle("🟢 啟動即時監控", value=True)

    # --- 3. 自動刷新區域 ---
    @fragment(run_every=3 if is_running else None)
    def monitor_prices():
        # A. 抓取真實資料
        data = get_realtime_prices(target_symbol)
        
        if data is None:
            st.error("⚠️ 無法連線至交易所 API，請檢查網路。")
            return

        p_binance = data['binance']
        p_okx = data['okx']
        
        # B. 計算價差
        diff = p_binance - p_okx 
        abs_diff = abs(diff)
        spread_pct = (abs_diff / min(p_binance, p_okx)) * 100
        
        # --- [新增] 將最新價差存入歷史紀錄 ---
        # 1. 把新的價差加入列表
        st.session_state['spread_history'].append(abs_diff)
        
        # 2. 限制長度 (例如只保留最近 30 次的紀錄)，避免跑太久記憶體爆掉
        if len(st.session_state['spread_history']) > 30:
            st.session_state['spread_history'].pop(0) # 移除最舊的一筆

        st.caption(f"最後更新: {time.strftime('%H:%M:%S')} | 監控中: {target_symbol}")

        # C. 顯示價格看板
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Binance 價格", f"${p_binance:,.2f}")
        with c2:
            st.metric("OKX 價格", f"${p_okx:,.2f}")
        with c3:
            if diff > 0:
                st.metric("價差 (Spread)", f"${abs_diff:.2f}", f"Binance 溢價 {spread_pct:.2f}%", delta_color="normal")
            else:
                st.metric("價差 (Spread)", f"${abs_diff:.2f}", f"OKX 溢價 {spread_pct:.2f}%", delta_color="normal")

        # --- [新增] 繪製即時波動圖 ---
        st.markdown("#### ⏳ 近期價差波動 (Live Chart)")
        
        # 建立一個 DataFrame 方便畫圖
        chart_data = pd.DataFrame(
            st.session_state['spread_history'], 
            columns=["價差 (USD)"]
        )
        # 使用 Streamlit 內建線圖，它會自動縮放
        st.line_chart(chart_data, height=250, color="#29b5e8")

        # D. 套利建議 (保持不變)
        st.markdown("#### 🤖 AI 套利建議")
        if spread_pct >= threshold_pct:
            direction = "OKX 買 -> Binance 賣" if diff > 0 else "Binance 買 -> OKX 賣"
            st.success(f"🔥 **發現機會！** ({direction}) 預估獲利: {spread_pct:.2f}%")
        else:
            st.info(f"😴 目前價差僅 **{spread_pct:.4f}%**，低於門檻，建議觀望。")

    # 4. 執行監控
    monitor_prices()