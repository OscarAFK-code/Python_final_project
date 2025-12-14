import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- 1. 定義要抓取的幣種與板塊 (Config) ---
# 為了讓熱力圖好看，我們手動定義一些熱門幣種及其分類
COIN_SECTORS = [
    {"symbol": "BTC-USD", "name": "Bitcoin", "category": "Layer 1"},
    {"symbol": "ETH-USD", "name": "Ethereum", "category": "Layer 1"},
    {"symbol": "SOL-USD", "name": "Solana", "category": "Layer 1"},
    {"symbol": "BNB-USD", "name": "BNB", "category": "Exchange"},
    {"symbol": "ADA-USD", "name": "Cardano", "category": "Layer 1"},
    {"symbol": "XRP-USD", "name": "XRP", "category": "Payment"},
    {"symbol": "DOGE-USD", "name": "Dogecoin", "category": "Meme"},
    {"symbol": "SHIB-USD", "name": "Shiba Inu", "category": "Meme"},
    # 改回標準代碼，Yahoo 通常能識別
    {"symbol": "PEPE-USD", "name": "Pepe", "category": "Meme"}, 
    {"symbol": "UNI-USD", "name": "Uniswap", "category": "DeFi"},
    {"symbol": "AAVE-USD", "name": "Aave", "category": "DeFi"},
    {"symbol": "LINK-USD", "name": "Chainlink", "category": "Oracle"},
    {"symbol": "FET-USD", "name": "Fetch.ai", "category": "AI"},
    {"symbol": "RNDR-USD", "name": "Render", "category": "AI/Depin"},
]

@st.cache_data(ttl=600)
def get_heatmap_data():
    data_list = []
    
    # 定義要抓取的幣種
    symbols = [item["symbol"] for item in COIN_SECTORS]
    
    # 使用 Tickers 一次建立物件
    tickers = yf.Tickers(" ".join(symbols))
    
    print("--- 開始抓取熱力圖數據 (含強力候補機制) ---")

    for item in COIN_SECTORS:
        symbol = item["symbol"]
        try:
            ticker = tickers.tickers[symbol]
            
            # --- 第一層嘗試：使用 fast_info (最快) ---
            mcap = ticker.fast_info.market_cap
            last_price = ticker.fast_info.last_price
            prev_close = ticker.fast_info.previous_close
            
            # --- 第二層嘗試：如果有數據缺失 (NaN 或 None)，改抓歷史 K 線 ---
            if last_price is None or prev_close is None:
                print(f"⚠️ {symbol} fast_info 缺失，啟動歷史數據候補下載...")
                # 下載最近 5 天的資料 (避免週末或假期沒資料)
                hist = ticker.history(period="5d")
                
                if len(hist) >= 2:
                    last_price = hist['Close'].iloc[-1]   # 最新一筆收盤價
                    prev_close = hist['Close'].iloc[-2]   # 前一筆收盤價
                    # 如果 fast_info 沒抓到市值，嘗試用 info 補 (或是給個預設值)
                    if mcap is None:
                         mcap = ticker.info.get('marketCap', 1000000) # 沒抓到就給假數字避免報錯
                else:
                    print(f"❌ {symbol} 歷史數據也不足，跳過。")
                    continue

            # --- 計算與資料整理 ---
            if last_price and prev_close:
                # 計算漲跌幅
                change_pct = ((last_price - prev_close) / prev_close) * 100
                
                # 防呆：如果市值還是空的，給它一個最小預設值讓它能畫出來
                if mcap is None or pd.isna(mcap):
                    mcap = 1000000000 # 10億 (預設)
                
                data_list.append({
                    "Coin": item["name"],
                    "Symbol": symbol,
                    "Category": item["category"],
                    "MarketCap": mcap,
                    "Change24h": change_pct
                })
                print(f"✅ {symbol} 成功: {change_pct:.2f}%")
            else:
                print(f"❌ {symbol} 最終無法計算漲跌幅")

        except Exception as e:
            print(f"❌ 抓取 {symbol} 時發生未知錯誤: {e}")
            continue
            
    # 轉成 DataFrame 並且把所有可能的 NaN 填補為 0
    df = pd.DataFrame(data_list)
    if not df.empty:
        df = df.fillna(0) 
        
    return df

# [B] 抓取相關性歷史數據
# 設定 ttl=3600 (1小時)，因為日線歷史資料盤中不會變動太大
@st.cache_data(ttl=3600)
def get_correlation_data(days=90):
    # 選取幾個代表性的幣種
    target_coins = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "DOGE-USD", "XRP-USD", "ADA-USD"]
    
    try:
        # 一次下載所有幣種的歷史資料
        df = yf.download(target_coins, period=f"{days}d", interval="1d", progress=False)['Close']
        
        # 簡化欄位名稱 (移除 -USD)
        df.columns = [col.replace("-USD", "") for col in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

# --- 3. 頁面顯示邏輯 ---
def show():
    st.title("📈 數據分析與歷史回測")
    st.markdown("### 市場板塊輪動與幣種相關性分析")
    
    # [功能] 手動刷新按鈕 (因為我們用了快取，提供使用者強制更新的選項)
    if st.button("🔄 刷新最新數據"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    # 使用 Tab 分頁
    tab1, tab2 = st.tabs(["🔥 全市場熱力圖 (Real-time)", "🔗 幣種相關性矩陣 (History)"])

    # --- Tab 1: 市場熱力圖 ---
    with tab1:
        st.subheader("全球加密貨幣板塊熱力圖")
        st.caption("數據來源: Yahoo Finance | 更新頻率: 每 10 分鐘 | 區塊大小 = 市值")
        
        with st.spinner("正在分析板塊數據..."):
            df_treemap = get_heatmap_data()
        
        if not df_treemap.empty:
            # 繪製樹狀圖
            fig_treemap = px.treemap(
                df_treemap, 
                path=[px.Constant("Crypto Market"), 'Category', 'Coin'], 
                values='MarketCap',      
                color='Change24h',       
                color_continuous_scale=['#FF4136', '#1E1E1E', '#2ECC40'], 
                color_continuous_midpoint=0,
                
                # --- 修改點 1: 縮小範圍，讓顏色更敏感 ---
                # 原本是 [-10, 10]，改成 [-3, 3]
                # 這樣只要漲跌 3% 顏色就會很明顯
                range_color=[-3, 3],   
                
                hover_data={'Change24h': ':.2f%', 'MarketCap': True}
            )
            
            # --- 修改點 2: 讓方塊上直接顯示 "+1.5%" 這種字樣 ---
            fig_treemap.update_traces(textinfo="label+text+value", texttemplate="%{label}<br>%{color:.2f}%")
            
            fig_treemap.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=550)
            
            # 顯示圖表
            st.plotly_chart(fig_treemap, use_container_width=True)
            
            # 顯示漲跌幅排行
            top_gainer = df_treemap.loc[df_treemap['Change24h'].idxmax()]
            top_loser = df_treemap.loc[df_treemap['Change24h'].idxmin()]
            
            c1, c2 = st.columns(2)
            c1.success(f"🚀 今日領漲: **{top_gainer['Coin']}** (+{top_gainer['Change24h']:.2f}%)")
            c2.error(f"📉 今日領跌: **{top_loser['Coin']}** ({top_loser['Change24h']:.2f}%)")
        else:
            st.error("無法取得市場數據，請稍後再試。")

    # --- Tab 2: 相關性矩陣 ---
    with tab2:
        st.subheader("主流幣種價格相關性分析 (近 90 天)")
        st.caption("💡 投資策略參考：\n- **高相關 (接近 1)**: 同漲同跌，分散風險效果差。\n- **低相關/負相關 (接近 0 或 -1)**: 走勢不同步，適合用來做資產配置分散風險。")
        
        with st.spinner("正在計算價格相關係數..."):
            df_prices = get_correlation_data(days=90)
        
        if not df_prices.empty:
            # 計算相關係數矩陣
            corr_matrix = df_prices.corr()
            
            # 繪製熱圖
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r", # 紅藍配色 (紅=正相關, 藍=負相關)
                zmin=-1, zmax=1, # 鎖定範圍 -1 到 1
                origin='lower'
            )
            
            fig_corr.update_layout(height=600)
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # 自動找尋最高相關性的幣種 (排除自己跟自己)
            # 將矩陣轉為列表
            corr_unstack = corr_matrix.unstack()
            # 排序並排除 1.0 (自己對自己)
            sorted_corr = corr_unstack[corr_unstack < 0.99].sort_values(ascending=False)
            
            if not sorted_corr.empty:
                top_pair = sorted_corr.index[0] # 取得第一名 (('BTC', 'ETH'))
                score = sorted_corr.iloc[0]
                
                st.info(f"""
                📊 **數據洞察：** 目前市場上連動性最高的是 **{top_pair[0]}** 與 **{top_pair[1]}** (相關係數: {score:.2f})。
                這意味著當 {top_pair[0]} 上漲時，{top_pair[1]} 有極高機率也會跟著上漲。
                """)
        else:
            st.error("無法取得歷史數據。")

# 測試用
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    show()