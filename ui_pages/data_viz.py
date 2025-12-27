import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

def show():
    st.title("📈 數據分析與歷史回測")
    st.markdown("### 市場板塊輪動與幣種相關性分析")
    st.markdown("---")

    # 使用 Tab 分頁來整理兩個大圖表，避免畫面太長
    tab1, tab2 = st.tabs(["🔥 全市場熱力圖 (Coin360 風格)", "🔗 幣種相關性矩陣"])

    # --- Tab 1: 市場熱力圖 (Treemap) ---
    with tab1:
        st.subheader("全球加密貨幣板塊熱力圖")
        st.caption("區塊大小 = 市值 (Market Cap) | 顏色 = 24h 漲跌幅")
        
        # 1. 模擬市場數據 (之後可接 CoinGecko API)
        # 我們建立不同板塊：Layer1, DeFi, Meme, AI
        data = {
            "Coin": ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "SHIB", "UNI", "AAVE", "FET", "WLD"],
            "Category": ["Layer 1", "Layer 1", "Layer 1", "Exchange", "Layer 1", "Layer 1", "Meme", "Meme", "DeFi", "DeFi", "AI", "AI"],
            "MarketCap": [1200, 400, 80, 70, 30, 20, 15, 10, 8, 4, 3, 2], # 模擬市值(十億)
            "Change24h": [2.5, 1.8, 5.2, -0.5, 0.2, -1.2, 8.5, 4.2, -2.1, -0.8, 12.3, 15.6] # 模擬漲跌幅
        }
        df_treemap = pd.DataFrame(data)

        # 2. 繪製樹狀圖 (Treemap)
        fig_treemap = px.treemap(
            df_treemap, 
            path=[px.Constant("Crypto Market"), 'Category', 'Coin'], 
            values='MarketCap',
            color='Change24h',
            color_continuous_scale='RdYlGn', # 紅-黃-綠 配色
            color_continuous_midpoint=0,     # 0 為中間值
            hover_data=['Change24h']
        )
        
        fig_treemap.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=500)
        st.plotly_chart(fig_treemap, width=True)

    # --- Tab 2: 相關性矩陣 (Correlation Matrix) ---
    with tab2:
        st.subheader("主流幣種價格相關性分析")
        st.caption("數值越接近 1 (黃色) 代表連動性越高；越接近 -1 (藍色) 代表走勢相反。")
        
        # 1. 模擬歷史價格數據
        coins = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE']
        days = 100
        # 產生隨機漫步數據
        price_data = np.random.normal(0, 1, size=(days, len(coins))).cumsum(axis=0)
        df_corr = pd.DataFrame(price_data, columns=coins)
        
        # 2. 計算相關係數矩陣 (Correlation Matrix)
        corr_matrix = df_corr.corr()
        
        # 3. 繪製熱圖 (Heatmap)
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f", # 顯示數值
            aspect="auto",
            color_continuous_scale="Viridis", # 專業配色
            origin='lower'
        )
        
        fig_corr.update_layout(height=500)
        st.plotly_chart(fig_corr, width=True)
        
        # 4. 簡單結論生成
        high_corr_pair = corr_matrix.unstack().sort_values(ascending=False)
        # 排除自己對自己 (數值為1) 的
        high_corr_pair = high_corr_pair[high_corr_pair < 0.999]
        top_pair = high_corr_pair.index[0]
        st.info(f"💡 數據洞察：過去 100 天內，**{top_pair[0]}** 與 **{top_pair[1]}** 的連動性最高，適合進行配對交易或風險對沖。")