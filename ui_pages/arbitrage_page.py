import streamlit as st
import ccxt
import time
import pandas as pd

# 設定費率參數
class FeeConfig:
    # 交易手續費 (Taker Fee 0.1%)
    TAKER_FEE_RATE = 0.001
    # 模擬鏈上提現費 (假設走 TRC20/BEP20 等便宜網路，約 1 USDT)
    WITHDRAW_FEE_USDT = 1.0 

# 初始化交易所
@st.cache_resource
def init_exchanges():
    config = {'enableRateLimit': True}
    return ccxt.binance(config), ccxt.okx(config)
binance, okx = init_exchanges()

# 獲取共同交易對
@st.cache_data(ttl=3600)
def get_common_pairs():
    """找出 Binance 與 OKX 都有上架的 USDT 交易對"""
    try:
        binance_markets = binance.load_markets()
        okx_markets = okx.load_markets()
        # 取交集
        common = set(binance_markets.keys()) & set(okx_markets.keys())
        usdt_pairs = [s for s in common if s.endswith('/USDT')]
        usdt_pairs.sort()
        return usdt_pairs
    except Exception as e:
        return []


def calculate_and_render_card(direction, buy_price, sell_price, input_amount):
    """
    負責計算單一路徑的利潤，並畫出卡片與折疊選單
    """
    coin_amount = (input_amount / buy_price) * (1 - FeeConfig.TAKER_FEE_RATE)
    withdraw_fee_coin = FeeConfig.WITHDRAW_FEE_USDT / sell_price
    coin_arrived = coin_amount - withdraw_fee_coin
    
    # 如果錢太少，報錯
    if coin_arrived <= 0:
        st.metric(label="預估淨利", value="N/A", delta="-100%", delta_color="inverse")
        return -input_amount 

    revenue_usdt = (coin_arrived * sell_price) * (1 - FeeConfig.TAKER_FEE_RATE)
    net_profit = revenue_usdt - input_amount
    roi = (net_profit / input_amount) * 100
    
    st.subheader(direction)
    
    color = "normal" if net_profit > 0 else "off"
    st.metric(
        label="預估淨利 (Net Profit)",
        value=f"${net_profit:.2f}",
        delta=f"{roi:.2f}%",
        delta_color=color
    )
    
    with st.expander("查看成本詳情 (Details)"):
        st.markdown(f"""
        - **1. 買入價 (Ask)**: `${buy_price:,.4f}`
        - **2. 賣出價 (Bid)**: `${sell_price:,.4f}`
        - **3. 交易手續費**: 約 `${(input_amount + revenue_usdt) * 0.001:.2f}`
        - **4. 提現成本**: 固定 `${FeeConfig.WITHDRAW_FEE_USDT}`
        - **5. 實際到帳**: `{coin_arrived:.5f}` 顆
        """)
        
        if net_profit > 0:
            st.success("**有利可圖！** 建議立即執行搬磚。")
        else:
            st.caption("利潤不足：價差無法覆蓋手續費。")
            
    return roi 

try:
    from streamlit import fragment
except ImportError:
    def fragment(run_every=None):
        def decorator(func): return func
        return decorator

@fragment(run_every=5) 
def run_scanner(symbol, input_amount, threshold_pct):
    is_demo = st.session_state.get('IS_DEMO', False)
    status_text = "🟢 Demo 模式: 強制製造價差中" if is_demo else "🔵 真實數據監控中"
    st.caption(f"{status_text} | 最後更新: {time.strftime('%H:%M:%S')} | 目標: {symbol}")
    
    try:
        t_bin = binance.fetch_ticker(symbol)
        t_okx = okx.fetch_ticker(symbol)

        # demo 模式
        if is_demo:
            
            fake_drop_rate = 0.93  # 讓價格跌一丟丟
            t_bin['ask'] = t_bin['ask'] * fake_drop_rate
            t_bin['bid'] = t_bin['bid'] * fake_drop_rate
        col1, col2 = st.columns(2)
        
        with col1:
            roi_a = calculate_and_render_card(
                direction="Binance ➡ OKX",
                buy_price=t_bin['ask'],   
                sell_price=t_okx['bid'],  
                input_amount=input_amount
            )
        with col2:
            roi_b = calculate_and_render_card(
                direction="OKX ➡ Binance",
                buy_price=t_okx['ask'],  
                sell_price=t_bin['bid'],
                input_amount=input_amount
            )
        if roi_a >= threshold_pct:
            st.toast(f"發現機會！Binance -> OKX 預估獲利 {roi_a:.2f}%")
        
        if roi_b >= threshold_pct:
            st.toast(f"發現機會！OKX -> Binance 預估獲利 {roi_b:.2f}%")

    except Exception as e:
        st.error(f"連線錯誤 (請稍候): {e}")

def show():
    st.title("全幣種套利監控")
    st.markdown("### 雙向監控 Binance 與 OKX 之價差機會")
    
    is_demo = st.session_state.get('IS_DEMO', False)
    if is_demo:
        st.warning("⚠️ 目前為 Demo 模式：數據經過調整以演示套利機會，非真實市場價格。")
    with st.container(border=True):
        st.markdown("**參數設定**")
        with st.spinner("正在同步交易所幣種清單..."):
            common_pairs = get_common_pairs()
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            default_idx = common_pairs.index('DOGE/USDT') if 'DOGE/USDT' in common_pairs else 0
            target_symbol = st.selectbox("🔍 搜尋幣種", common_pairs, index=default_idx)
        with c2:
            amount = st.number_input("本金 (USDT)", value=1000.0, step=100.0)
        with c3:
            threshold = st.number_input("通知門檻 (%)", value=0.5, step=0.1)
    st.divider()
    
    c_toggle, c_info = st.columns([1, 3], vertical_alignment="center")
    with c_toggle:
        if 'scanner_running' not in st.session_state:
            st.session_state['scanner_running'] = False
        
        is_running = st.toggle("🔴 啟動自動掃描", key='scanner_running')
        
    with c_info:
        if is_running:
            st.success("✅ 系統運作中 (每 5 秒刷新)")
        else:
            st.info("請開啟開關以開始獲取即時數據")

    if is_running:
        run_scanner(target_symbol, amount, threshold)