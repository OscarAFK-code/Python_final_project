import streamlit as st
import pandas as pd
import time
# --- 修正引用路徑 ---
from data_modules.market_data import get_price_data, get_fear_and_greed_index
# 這裡要改成引用你 whale_watcher.py 最後面定義的那個整合函式
from data_modules.whale_watcher import get_combined_whales 

def show():
    st.title("🚁 市場戰情總覽 Dashboard")
    st.caption("數據來源：Binance / OKX / Alternative.me / Etherscan (每 20 秒自動同步)")
    st.markdown("---")

    # --- 核心：20秒自動刷新的動態看板 ---
    @st.fragment(run_every=20)
    def show_live_dashboard():
        
        # 1. 統一抓取所有資料 (價格 + 情緒 + 鯨魚)
        # 放在同一個 spinner 裡，使用者只會感覺到一次載入
        with st.spinner('📡 正在同步全球報價與鏈上數據...'):
            # (A) 抓價格
            df = get_price_data(coins=['BTC', 'ETH', 'SOL', 'DOGE'])
            # (B) 抓情緒
            fgi_data = get_fear_and_greed_index()
            # (C) 抓鯨魚 (自動抓，不用按鈕了)
            # 這裡會稍微多花 1-2 秒，因為你有設 time.sleep(1)
            whale_data = get_combined_whales()
            
            # 取得更新時間
            current_time = time.strftime("%H:%M:%S")

        # ===========================
        # 第一區：重點幣種報價
        # ===========================
        st.subheader(f"💰 重點關注幣種 (Binance) - {current_time}")
        
        if not df.empty:
            df_binance = df[df['Exchange'] == 'Binance'].set_index('Coin')
            c1, c2, c3, c4 = st.columns(4)
            
            def render_card(col, coin):
                if coin in df_binance.index:
                    price = df_binance.loc[coin, 'Price']
                    change = df_binance.loc[coin, 'Change24h%']
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
            st.error("⚠️ 無法連接交易所 API")

        st.markdown("---")

        # ===========================
        # 第二區：情緒 & 比價
        # ===========================
        col_left, col_right = st.columns([1, 2])

        # 左邊：情緒指數
        with col_left:
            st.subheader("😱 市場情緒")
            if fgi_data:
                val = fgi_data['value']
                state = fgi_data['state']
                if val < 40:
                    color, emoji = "inverse", "😨"
                elif val > 60:
                    color, emoji = "normal", "🤑"
                else:
                    color, emoji = "off", "😐"
                
                st.metric("Fear & Greed", f"{val}", f"{emoji} {state}", delta_color=color)
                st.progress(val / 100)
            else:
                st.info("暫無情緒數據")

        # 右邊：比價表
        with col_right:
            st.subheader("📊 交易所價差監控")
            if not df.empty:
                pivot_df = df.pivot(index='Coin', columns='Exchange', values='Price')
                st.dataframe(pivot_df.style.format("${:,.2f}"), use_container_width=True)

        st.markdown("---")

        # ===========================
        # 第三區：鯨魚警報 (自動顯示)
        # ===========================
        st.subheader("🐋 鏈上鯨魚監控 (On-Chain Whale Alert)")
        st.caption("監控標準：BTC > $500萬 USD | ETH > $200萬 USD (自動掃描中...)")

        if whale_data:
            df_whale = pd.DataFrame(whale_data)
            
            # 1. 顯示最驚人的一筆
            max_whale = df_whale.loc[df_whale['value_usd'].idxmax()]
            st.warning(f"🚨 最新巨鯨動態：{max_whale['time']} 有人轉移了 {max_whale['amount']} {max_whale['symbol']} (價值 ${max_whale['value_usd']} M)")
            
            # 2. 顯示詳細清單
            st.dataframe(
                df_whale,
                column_config={
                    "time": "時間",
                    "symbol": "幣種",
                    "amount": st.column_config.NumberColumn("數量"),
                    "value_usd": st.column_config.NumberColumn("價值 (百萬鎂)", format="$%.2f M"),
                    "from": "發送方",
                    "link": st.column_config.LinkColumn("鏈上 Tx Hash", display_text="查看 Etherscan")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info(f"🌊 ({current_time}) 目前區塊鏈上一片風平浪靜，暫無巨額轉帳。")

    # 啟動自動刷新函式
    show_live_dashboard()