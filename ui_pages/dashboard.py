import streamlit as st
import pandas as pd
import time
# 確保引用路徑正確
from data_modules.market_data import get_price_data, get_fear_and_greed_index

def show():
    st.title(" 市場總覽 Dashboard")
    st.markdown("全球主流交易所即時看板")
    st.caption("數據來源：Binance / OKX / Kraken / Alternative.me / Etherscan")
    st.markdown("---")

    # 20秒自動刷新的動態看板
    @st.fragment(run_every=20)
    def show_live_dashboard():
        # 1. 在這裡統一抓取資料 (確保資料一致性)
        # 不使用 cache 或 ttl=0，確保每次都是新的
        with st.spinner('正在同步全球市場數據...'):
            df = get_price_data(coins=['BTC', 'ETH', 'SOL', 'DOGE'])
            fgi_data = get_fear_and_greed_index()
            
            # 取得當前時間
            current_time = time.strftime("%H:%M:%S")

        # --- 區塊 A: 重點幣種報價 (Binance) ---
        st.subheader(f" 重點關注幣種 (Binance) - {current_time} 更新")
        
        if not df.empty:
            # 篩選出 Binance 的資料
            df_binance = df[df['Exchange'] == 'Binance'].set_index('Coin')
            
            c1, c2, c3, c4 = st.columns(4)
            
            # 定義一個內部小函式來顯示卡片，減少重複代碼
            def render_card(col, coin):
                if coin in df_binance.index:
                    price = df_binance.loc[coin, 'Price']
                    change = df_binance.loc[coin, 'Change24h%']
                    
                    # 格式設定：小幣顯示4位小數，大幣顯示2位
                    fmt = "${:,.4f}" if price < 1 else "${:,.2f}"
                    
                    col.metric(
                        label=f"{coin}/USDT",
                        value=fmt.format(price),
                        delta=f"{change:.2f}%"
                    )
                else:
                    col.warning(f"{coin} 載入中")

            render_card(c1, 'BTC')
            render_card(c2, 'ETH')
            render_card(c3, 'SOL')
            render_card(c4, 'DOGE')
        else:
            st.error("⚠️ 無法連接交易所 API，請檢查網路或 API 設定")

        st.markdown("---")

        # --- 區塊 B: 詳細數據 (情緒指數 & 比價表) ---
        # 我們將這兩塊並排顯示
        col_left, col_right = st.columns([1, 2])

        # 左邊：情緒指數
        with col_left:
            st.subheader("😱 市場情緒")
            if fgi_data:
                val = fgi_data['value']
                state = fgi_data['state']
                
                # 決定顏色
                if val < 40:
                    color = "inverse" # 紅 (恐懼)
                    emoji = "😨"
                elif val > 60:
                    color = "normal"  # 綠 (貪婪)
                    emoji = "🤑"
                else:
                    color = "off"     # 灰 (中立)
                    emoji = "😐"
                
                st.metric("Fear & Greed Index", f"{val}", f"{emoji} {state}", delta_color=color)
                st.progress(val / 100)
                st.caption("資料來源: Alternative.me")
            else:
                st.info("暫無情緒數據")

        # 右邊：交易所比價表
        with col_right:
            st.subheader("📊 三大交易所價格比較")
            if not df.empty:
                # 製作 Pivot Table: Index=幣種, Columns=交易所, Values=價格
                pivot_df = df.pivot(index='Coin', columns='Exchange', values='Price')
                # 顯示表格並格式化為金錢符號
                st.dataframe(
                    pivot_df.style.format("${:,.2f}"), 
                    use_container_width=True
                )
            else:
                st.info("暫無比價數據")

    # 執行上面的自動刷新函式
    show_live_dashboard()


    # --- 6. 鯨魚警報 (保留原本樣式) ---
    st.subheader("🐋 近期大額轉帳警報")
    alerts = [
        {"time": "10:23", "msg": "🚨 2,000 BTC 從 未知錢包 轉入 Binance (可能賣壓)"},
        {"time": "09:45", "msg": "🟢 50,000 SOL 從 OKX 提現至 錢包 (可能囤幣)"},
        {"time": "08:12", "msg": "🚨 10,000,000 DOGE 轉入 Coinbase"},
    ]
    for alert in alerts:
        st.text(f"{alert['time']} | {alert['msg']}")