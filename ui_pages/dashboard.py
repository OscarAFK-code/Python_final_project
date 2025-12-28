import streamlit as st
import pandas as pd
import time
from data_modules.market_data import get_price_data, get_fear_and_greed_index
from data_modules.whale_watcher import get_whale_alerts 
def show():
    # 使用 container 讓標題區塊更集中
    with st.container():
        st.title("市場總覽")
        st.markdown("Global Crypto Market Dashboard")
    
    st.markdown("---")

    # --- 核心：20秒自動刷新的動態看板 ---
    @st.fragment(run_every=20)
    def show_live_dashboard():
        
        # 0. 檢查是否為 Demo 模式
        is_demo = st.session_state.get("IS_DEMO", False)

        # 1. 統一抓取所有資料
        # 使用 spinner 雖然好，但每 20 秒閃一次可能會擾民
        # 我們改用一個小的 toast 或者右上角狀態提示
        if is_demo:
            st.toast("🔴 Demo 模式：使用模擬數據中...")
            
        with st.spinner('正在同步全球報價與鏈上數據...'):
            # (A) 抓價格
            df = get_price_data(coins=['BTC', 'ETH', 'SOL', 'DOGE'])
            # (B) 抓情緒
            fgi_data = get_fear_and_greed_index()
            # (C) 抓鯨魚 (傳入 is_demo 參數!)
            whale_data = get_whale_alerts(is_demo=is_demo)
            
            # 取得更新時間
            current_time = time.strftime("%H:%M:%S")

        # ===========================
        # 第一區：重點幣種報價 (KPI Cards)
        # ===========================
        # 使用 border=True 創造卡片感
        with st.container(border=True):
            col_header, col_time = st.columns([3, 1])
            col_header.subheader("重點關注幣種 (Binance)")
            col_time.caption(f"Last Updated: {current_time}")
            
            if not df.empty:
                df_binance = df[df['Exchange'] == 'Binance'].set_index('Coin')
                c1, c2, c3, c4 = st.columns(4)
                
                def render_card(col, coin):
                    if coin in df_binance.index:
                        price = df_binance.loc[coin, 'Price']
                        change = df_binance.loc[coin, 'Change24h%']
                        fmt = "${:,.4f}" if price < 1 else "${:,.2f}"
                        
                        # 根據漲跌變色 (Streamlit 預設是綠漲紅跌，但我們可以強化)
                        col.metric(
                            label=f"{coin}/USDT",
                            value=fmt.format(price),
                            delta=f"{change:.2f}%"
                        )
                    else:
                        col.warning(f"{coin} N/A")

                render_card(c1, 'BTC')
                render_card(c2, 'ETH')
                render_card(c3, 'SOL')
                render_card(c4, 'DOGE')
            else:
                st.error("⚠️ 無法連接交易所 API")

        # ===========================
        # 第二區：情緒 & 比價 (Split View)
        # ===========================
        col_left, col_right = st.columns([1, 2], gap="medium")

        # 左邊：情緒指數 (Gauge)
        with col_left:
            with st.container(border=True):
                st.subheader("市場情緒")
                if fgi_data:
                    val = fgi_data['value']
                    state = fgi_data['state']
                    
                    # 顏色邏輯
                    if val < 25: color, emoji = "inverse", "💀 極度恐懼"
                    elif val < 45: color, emoji = "inverse", "😨 恐懼"
                    elif val > 75: color, emoji = "normal", "🤡 極度貪婪"
                    elif val > 55: color, emoji = "normal", "🤑 貪婪"
                    else: color, emoji = "off", "🤓 中立"
                    
                    st.metric("Fear & Greed", f"{val}", f"{emoji}", delta_color=color)
                    st.progress(val / 100)
                    st.caption(f"目前狀態：{state}")
                else:
                    st.info("暫無情緒數據")

        # 右邊：比價表 (Table)
        with col_right:
            with st.container(border=True):
                st.subheader("跨交易所價差")
                if not df.empty:
                    pivot_df = df.pivot(index='Coin', columns='Exchange', values='Price')
                    # 高亮顯示最大值 (Highlighter)
                    st.dataframe(
                        pivot_df.style.format("${:,.2f}").highlight_max(axis=1, color='#1f77b4'), 
                        use_container_width=True
                    )
                else:
                    st.info("暫無比價數據")

        # ===========================
        # 第三區：鯨魚警報 (Terminal Style)
        # ===========================
        with st.container(border=True):
            st.subheader("鏈上鯨魚監控 (On-Chain Alert)")
            
            if whale_data:
                df_whale = pd.DataFrame(whale_data)
                
                # 1. 警報區 (Alert Box)
                max_whale = df_whale.loc[df_whale['value_usd'].idxmax()]
                st.warning(
                    f"🚨 **Whale Alert**: {max_whale['time']} | "
                    f"轉移 **{max_whale['amount']} {max_whale['symbol']}** "
                    f"( ${max_whale['value_usd']} M)"
                )
                
                # 2. 詳細清單
                with st.expander("查看詳細交易紀錄", expanded=True):
                    st.dataframe(
                        df_whale,
                        column_config={
                            "time": "Time",
                            "symbol": "Token",
                            "amount": st.column_config.NumberColumn("Amount"),
                            "value_usd": st.column_config.NumberColumn("Value (M)", format="$%.2f M"),
                            "from": "From Address",
                            "link": st.column_config.LinkColumn("Tx Hash", display_text="Etherscan ↗")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
            else:
                st.success(f" ({current_time}) 區塊鏈平靜無波，暫無大額轉帳。")

    # 啟動自動刷新函式
    show_live_dashboard()