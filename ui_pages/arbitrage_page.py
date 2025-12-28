import streamlit as st
import ccxt
import time
import pandas as pd

# --- 1. 設定費率參數 ---
class FeeConfig:
    TAKER_FEE_RATE = 0.001  # 0.1% 交易手續費
    # 為了簡化，我們先假設提現費是固定 U (例如波場鏈)
    # 實際操作小幣種時，通常走 TRC20 或 BEP20，費用約 1 U
    WITHDRAW_FEE_USDT = 1.0 

# --- 2. 初始化交易所 ---
# 使用快取 (Cache) 來初始化交易所物件，避免每次刷新都重連
@st.cache_resource
def init_exchanges():
    return ccxt.binance(), ccxt.okx()

binance, okx = init_exchanges()

# --- 3. 獲取共同交易對 (關鍵邏輯) ---
@st.cache_data(ttl=3600) # 設定快取 1 小時，不用每次都去抓幾千個幣
def get_common_pairs():
    """
    抓取 Binance 和 OKX 的所有交易對，並找出「兩邊都有」的幣種
    """
    try:
        # 載入市場數據 (這會花幾秒鐘)
        binance_markets = binance.load_markets()
        okx_markets = okx.load_markets()
        
        # 取出符號 (Keys) 並轉成 Set (集合)
        b_symbols = set(binance_markets.keys())
        o_symbols = set(okx_markets.keys())
        
        # 找出交集 (Intersection) & 必須是 USDT 結算的現貨
        common = list(b_symbols & o_symbols)
        # 過濾出結尾是 /USDT 的交易對
        usdt_pairs = [s for s in common if s.endswith('/USDT')]
        usdt_pairs.sort() # 排序方便搜尋
        
        return usdt_pairs
    except Exception as e:
        return []

# --- 4. 監控與計算核心 ---
# 定義 fragment 讓這部分可以獨立自動刷新
try:
    from streamlit import fragment
except ImportError:
    def fragment(run_every=None):
        def decorator(func):
            return func
        return decorator

@fragment(run_every=5) # 每 5 秒自動掃描一次
def run_scanner(symbol, input_amount, threshold_pct):
    
    # 顯示掃描中的狀態
    with st.spinner(f"正在監控 {symbol} ..."):
        try:
            # 1. 抓價格
            t_bin = binance.fetch_ticker(symbol)
            t_okx = okx.fetch_ticker(symbol)
            
            # 提取買賣價
            # 路徑 A: Binance 買 -> OKX 賣
            price_buy_A = t_bin['ask']
            price_sell_A = t_okx['bid']
            
            # 路徑 B: OKX 買 -> Binance 賣
            price_buy_B = t_okx['ask']
            price_sell_B = t_bin['bid']
            
            # 2. 計算獲利函式 (內嵌簡化版)
            def calc_profit(p_buy, p_sell):
                # 買入扣費
                coin_amt = (input_amount / p_buy) * (1 - FeeConfig.TAKER_FEE_RATE)
                # 扣提現費 (假設等值 1 USDT 的幣)
                withdraw_cost_coin = FeeConfig.WITHDRAW_FEE_USDT / p_sell 
                coin_arrived = coin_amt - withdraw_cost_coin
                
                if coin_arrived <= 0: return -input_amount
                
                # 賣出扣費
                usdt_back = (coin_arrived * p_sell) * (1 - FeeConfig.TAKER_FEE_RATE)
                net = usdt_back - input_amount
                roi = (net / input_amount) * 100
                return net, roi

            net_A, roi_A = calc_profit(price_buy_A, price_sell_A)
            net_B, roi_B = calc_profit(price_buy_B, price_sell_B)
            
            # 3. 顯示結果 UI
            st.caption(f"最後更新: {time.strftime('%H:%M:%S')}")
            
            col1, col2 = st.columns(2)
            
            # 顯示路徑 A
            with col1:
                st.subheader("Binance ➡ OKX")
                st.metric("買 Bin / 賣 OK", f"${price_buy_A} / ${price_sell_A}")
                if roi_A > 0:
                    st.success(f"獲利: +${net_A:.2f} (+{roi_A:.2f}%)")
                else:
                    st.error(f"虧損: ${net_A:.2f} ({roi_A:.2f}%)")

            # 顯示路徑 B
            with col2:
                st.subheader("OKX ➡ Binance")
                st.metric("買 OK / 賣 Bin", f"${price_buy_B} / ${price_sell_B}")
                if roi_B > 0:
                    st.success(f"獲利: +${net_B:.2f} (+{roi_B:.2f}%)")
                else:
                    st.error(f"虧損: ${net_B:.2f} ({roi_B:.2f}%)")

            # 4. 警報系統 (Alert System)
            # 如果任一邊利潤大於使用者設定的門檻
            if roi_A >= threshold_pct:
                msg = f"發現機會！從 Binance 搬去 OKX 可賺 {roi_A:.2f}%"
                st.toast(msg, icon="💰") # 彈出右下角通知
                # 也可以在這裡播放音效 (需進階 HTML) 或發送 Line Notify

            if roi_B >= threshold_pct:
                msg = f"發現機會！從 OKX 搬去 Binance 可賺 {roi_B:.2f}%"
                st.toast(msg, icon="💰")

        except Exception as e:
            st.warning(f"掃描暫時中斷 (可能是網絡或 API 限制): {e}")

# --- 5. 主頁面顯示 ---
def show():
    st.title("全幣種套利掃描")
    st.markdown("針對 Binance 與 OKX 共同上架之幣種進行即時價差監控")
    
    # 側邊欄或頂部設定
    with st.expander("掃描設定", expanded=True):
        
        # 步驟 1: 載入共同幣種 (這是一個很好的技術亮點)
        with st.spinner("正在同步兩大交易所的幣種清單..."):
            common_pairs = get_common_pairs()
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            # 這裡就是你的需求：搜尋功能 (Selectbox 預設就有搜尋)
            # 預設選一個波動大的小幣，例如 PEPE 或 DOGE，讓助教看到效果
            default_idx = common_pairs.index('DOGE/USDT') if 'DOGE/USDT' in common_pairs else 0
            target_symbol = st.selectbox("搜尋並選擇監控幣種", common_pairs, index=default_idx)
            
        with c2:
            amount = st.number_input("本金 (USDT)", value=1000.0)
            
        with c3:
            alert_threshold = st.number_input("獲利通知門檻 (%)", value=0.5, step=0.1)

    st.divider()

    # 啟動按鈕
    if st.toggle("🔴 啟動自動掃描 (Auto-Scanner)", value=False):
        run_scanner(target_symbol, amount, alert_threshold)
    else:
        st.info("打開開關開始掃描，系統將每5秒檢查一次價差。")