import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import requests  # 新增 requests 用於呼叫幣安 API
from datetime import timedelta, datetime

# --- 1. 真實歷史事件庫 (保留原有功能) ---
REAL_EVENTS = {
    "🇺🇸 SEC 批准比特幣現貨 ETF": "2024-01-10",
    "💀 FTX 交易所申請破產 (黑天鵝)": "2022-11-11",
    "🇨🇳 中國全面禁止加密貨幣挖礦與交易": "2021-09-24",
    "🌕 Terra (LUNA) 崩盤與死亡螺旋": "2022-05-09",
    "🚗 Tesla 宣布暫停接受比特幣支付": "2021-05-12",
    "🦠 COVID-19 全球市場崩盤 (312慘案)": "2020-03-12"
}

# --- 輔助函式：從幣安抓取單一幣種資料 ---
def get_binance_history(symbol, start_date_str, end_date_str):
    """
    呼叫幣安 API 抓取特定時間段的日線資料
    """
    try:
        # 轉換日期為 Unix Timestamp (毫秒)
        start_ts = int(pd.to_datetime(start_date_str).timestamp() * 1000)
        end_ts = int(pd.to_datetime(end_date_str).timestamp() * 1000)
        
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": "1d",
            "startTime": start_ts,
            "endTime": end_ts,
            "limit": 1000
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if not isinstance(data, list):
            return None

        # 幣安回傳格式: [Open Time, Open, High, Low, Close, Volume, ...]
        # 我們只需要 Open Time (索引0) 和 Close (索引4)
        df = pd.DataFrame(data, columns=[
            "Open Time", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore"
        ])
        
        df["Date"] = pd.to_datetime(df["Open Time"], unit='ms')
        df["Close"] = df["Close"].astype(float)
        
        return df[["Date", "Close"]]
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# --- 2. 抓取真實股價函式 (已修改為幣安來源) ---
@st.cache_data(ttl=3600)
def fetch_real_market_data(event_date_str, days_after=7):
    # 定義要抓取的幣種 (幣安代號通常是 BTCUSDT 格式)
    coins_map = {
        'BTC': 'BTCUSDT',
        'ETH': 'ETHUSDT',
        'BNB': 'BNBUSDT',
        'SOL': 'SOLUSDT',
        'DOGE': 'DOGEUSDT',
        'XRP': 'XRPUSDT',
        'ADA': 'ADAUSDT'
    }
    
    start_date = pd.to_datetime(event_date_str)
    # 幣安 API 的 endTime 是包含在內的，所以我們要抓多一點點確保數據足夠，之後再切片
    end_date = start_date + timedelta(days=days_after + 5) 
    
    data_list = []
    
    # 建立進度條，因為 API 是一次抓一支
    progress_text = "正在連線幣安 API..."
    my_bar = st.progress(0, text=progress_text)
    total_coins = len(coins_map)
    
    for idx, (coin_name, symbol) in enumerate(coins_map.items()):
        # 更新進度條
        my_bar.progress((idx + 1) / total_coins, text=f"正在抓取 {coin_name}...")
        
        df_coin = get_binance_history(symbol, start_date, end_date)
        
        if df_coin is not None and not df_coin.empty:
            # 確保數據從事件當天開始
            # 有時候時區問題會差一點，我們用日期字串比對最保險
            mask = df_coin['Date'] >= start_date
            df_coin = df_coin.loc[mask].reset_index(drop=True)
            
            # 只取前 N+1 天 (包含第0天)
            df_coin = df_coin.head(days_after + 1)
            
            if len(df_coin) > 0:
                base_price = df_coin.iloc[0]['Close']
                
                # 避免分母為 0
                if base_price > 0:
                    # 計算回報率
                    for i, row in df_coin.iterrows():
                        current_price = row['Close']
                        return_pct = ((current_price - base_price) / base_price) * 100
                        
                        data_list.append({
                            "Day": f"Day {i}",
                            "Date": row['Date'].strftime('%Y-%m-%d'),
                            "Days_Num": i,
                            "Coin": coin_name,
                            "Return_Pct": return_pct
                        })
    
    my_bar.empty() # 清除進度條
    
    if not data_list:
        return None
        
    return pd.DataFrame(data_list)

def show():
    st.title("📈 數據分析與歷史回測")
    
    tab1, tab2, tab3 = st.tabs(["⚡ 事件驅動回測 (真實數據)", "🔥 全市場熱力圖", "🔗 幣種相關性矩陣"])

    # --- Tab 1: 事件驅動回測 (使用幣安數據) ---
    with tab1:
        st.subheader("📰 真實歷史事件回測")
        st.markdown("針對 **真實發生** 的重大新聞事件，從 **幣安 (Binance)** 調閱歷史數據分析 **事件後 N 天** 的市場反應。")
        
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                selected_event_name = st.selectbox("選擇歷史重大事件", list(REAL_EVENTS.keys()))
                real_date_str = REAL_EVENTS[selected_event_name]
            with col2:
                st.text_input("事件發生日期 (系統鎖定)", value=real_date_str, disabled=True)
            with col3:
                window_days = st.slider("觀察窗口 (天數)", min_value=3, max_value=14, value=7)
        
        st.markdown("---")

        if st.button("🚀 調閱幣安數據並分析", type="primary"):
            # 這裡不需要 with st.spinner，因為我們在函式裡做了進度條
            df_backtest = fetch_real_market_data(real_date_str, window_days)
            
            if df_backtest is not None and not df_backtest.empty:
                final_day_data = df_backtest[df_backtest['Days_Num'] == df_backtest['Days_Num'].max()].sort_values('Return_Pct', ascending=False)
                
                if not final_day_data.empty:
                    avg_return = final_day_data['Return_Pct'].mean()
                    
                    # 看板與圖表
                    m1, m2, m3 = st.columns(3)
                    color_mode = "normal" if avg_return > 0 else "inverse"
                    m1.metric("Top 幣種平均漲跌幅", f"{avg_return:.2f}%", delta_color=color_mode)
                    m2.metric("🏆 表現最強", f"{final_day_data.iloc[0]['Coin']}", f"+{final_day_data.iloc[0]['Return_Pct']:.2f}%")
                    m3.metric("🥀 表現最弱", f"{final_day_data.iloc[-1]['Coin']}", f"{final_day_data.iloc[-1]['Return_Pct']:.2f}%", delta_color="inverse")
                    
                    st.subheader(f"📊 事件後 {window_days} 天價格走勢")
                    fig_line = px.line(df_backtest, x="Days_Num", y="Return_Pct", color="Coin", markers=True, title=f"'{selected_event_name}' 市場反應")
                    st.plotly_chart(fig_line, use_container_width=True)
                    
                    st.subheader("💰 最終戰績排行")
                    fig_bar = px.bar(final_day_data, x="Coin", y="Return_Pct", color="Return_Pct", color_continuous_scale="RdYlGn", text_auto='.2f')
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.error("❌ 數據計算錯誤 (天數不足)。")
            else:
                st.error("❌ 無法取得數據，請檢查網路連線或幣安 API 狀態。")

    # --- Tab 2: 市場熱力圖 (保留模擬數據，因需即時大量數據較複雜) ---
    with tab2:
        st.subheader("全球加密貨幣板塊熱力圖")
        st.caption("註：此為示意數據 (區塊大小=市值 / 顏色=24h漲跌)")
        
        # 產生模擬數據
        data = {
            "Coin": ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "SHIB", "UNI", "AAVE", "FET", "WLD"],
            "Category": ["Layer 1", "Layer 1", "Layer 1", "Exchange", "Layer 1", "Layer 1", "Meme", "Meme", "DeFi", "DeFi", "AI", "AI"],
            "MarketCap": [1200, 400, 80, 70, 30, 20, 15, 10, 8, 4, 3, 2],
            "Change24h": [2.5, 1.8, 5.2, -0.5, 0.2, -1.2, 8.5, 4.2, -2.1, -0.8, 12.3, 15.6]
        }
        df_treemap = pd.DataFrame(data)
        fig_treemap = px.treemap(
            df_treemap, 
            path=[px.Constant("Crypto Market"), 'Category', 'Coin'], 
            values='MarketCap', 
            color='Change24h', 
            color_continuous_scale='RdYlGn', 
            color_continuous_midpoint=0
        )
        st.plotly_chart(fig_treemap, use_container_width=True)

        with st.expander("ℹ️ 點擊查看：如何解讀這張熱力圖？"):
            st.markdown("""
            這張圖能幫助你一眼掌握市場資金流向：
            1. **區塊大小 (Size)**：代表 **市值 (Market Cap)**。
            2. **顏色 (Color)**：代表 **24小時漲跌幅**。
               - 🟢 **綠色**：上漲 (顏色越深漲越多)。
               - 🔴 **紅色**：下跌 (顏色越深跌越慘)。
            """)

    # --- Tab 3: 相關性矩陣 (保留模擬數據) ---
    with tab3:
        st.subheader("主流幣種價格相關性分析")
        st.caption("註：此為示意數據")
        
        # 產生模擬數據
        coins = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE']
        days = 100
        price_data = np.random.normal(0, 1, size=(days, len(coins))).cumsum(axis=0)
        df_corr = pd.DataFrame(price_data, columns=coins)
        corr_matrix = df_corr.corr()
        
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="Viridis",
            origin='lower'
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        with st.expander("ℹ️ 點擊查看：如何解讀相關性矩陣？"):
            st.markdown("""
            此圖表用於分析不同幣種之間的「連動程度」：
            - 🟨 **數值接近 1 (黃色)**：**高度正相關** (同漲同跌)。
            - 🟦 **數值接近 0 或負數 (深紫色)**：**低相關 / 負相關** (走勢較無關聯)。
            """)

# --- 主程式執行入口 ---
if __name__ == "__main__":
    show()