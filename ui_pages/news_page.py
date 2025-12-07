import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

def show():
    # --- 1. 頁面標題 ---
    st.title("📰 全球加密貨幣輿情分析")
    st.markdown("### 透過 AI 解析新聞情緒，並回測歷史事件對幣價的影響")
    st.markdown("---")

    # --- 2. 版面配置 (Layout) ---
    # 左邊 1/3 放列表，右邊 2/3 放圖表
    col1, col2 = st.columns([1, 2])

    # --- 3. 左側：新聞列表 (Left Column) ---
    with col1:
        st.subheader("📡 即時新聞快訊")
        
        # 模擬從 Google News 爬下來的資料
        # 之後這裡會換成 data_modules.news_scraper 的結果
        news_data = [
            {"時間": "10:30", "標題": "SEC 批准比特幣現貨 ETF 上市", "情緒": "正向 🔥", "幣種": "BTC"},
            {"時間": "09:45", "標題": "以太坊基金會拋售 2,000 ETH", "情緒": "負向 📉", "幣種": "ETH"},
            {"時間": "09:15", "標題": "聯準會宣布維持利率不變", "情緒": "中立 😐", "幣種": "Macro"},
            {"時間": "08:50", "標題": "Solana 網路發生短暫擁堵", "情緒": "負向 📉", "幣種": "SOL"},
            {"時間": "08:10", "標題": "MicroStrategy 再度買入 3,000 BTC", "情緒": "正向 🔥", "幣種": "BTC"},
        ]
        
        # 轉成 DataFrame 方便顯示
        df_news = pd.DataFrame(news_data)
        
        # 使用者互動：選擇要分析哪一則新聞
        # (這裡用 Selectbox 模擬「點擊新聞」的效果，比較不容易出錯)
        selected_news_title = st.selectbox(
            "👇 請選擇一則新聞進行回測：",
            df_news["標題"]
        )
        
        # 顯示簡易表格
        st.dataframe(
            df_news[["時間", "幣種", "情緒", "標題"]], 
            hide_index=True,
            use_container_width=True
        )
        
        st.info("💡 提示：情緒分數由 NLP 模型自動計算，🔥 代表極度看漲，📉 代表看跌。")

    # --- 4. 右側：回測分析 (Right Column) ---
    with col2:
        st.subheader("📈 事件影響力回測 (Event Backtesting)")
        
        # 找出使用者選了哪一則新聞
        target_news = df_news[df_news["標題"] == selected_news_title].iloc[0]
        
        st.markdown(f"""
        **正在分析事件：** `{target_news['標題']}`  
        **關聯幣種：** `{target_news['幣種']}` | **情緒判定：** {target_news['情緒']}
        """)
        
        # 模擬：產生該事件發生後 7 天的價格走勢
        # 這裡用隨機亂數模擬，之後會接 yfinance 抓真實歷史數據
        days = 7
        dates = [datetime.today() + timedelta(days=i) for i in range(days)]
        
        # 根據情緒造假數據 (如果是正向就畫漲，負向就畫跌)
        start_price = 60000 if target_news['幣種'] == 'BTC' else 3000
        volatility = start_price * 0.05 # 5% 波動
        
        if "正向" in target_news['情緒']:
            # 模擬上漲趨勢
            prices = [start_price * (1 + 0.02 * i) + np.random.normal(0, volatility/5) for i in range(days)]
        elif "負向" in target_news['情緒']:
            # 模擬下跌趨勢
            prices = [start_price * (1 - 0.02 * i) + np.random.normal(0, volatility/5) for i in range(days)]
        else:
            # 模擬盤整
            prices = [start_price + np.random.normal(0, volatility/2) for i in range(days)]

        # 畫圖 (使用 Plotly)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, 
            y=prices, 
            mode='lines+markers',
            name=target_news['幣種'],
            line=dict(width=3)
        ))
        
        fig.update_layout(
            title=f"{target_news['幣種']} 在新聞發布後 7 天的走勢",
            xaxis_title="日期 (模擬預測)",
            yaxis_title="價格 (USD)",
            height=400,
            template="plotly_dark" # 使用深色主題看起來比較專業
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示回測結論
        avg_change = ((prices[-1] - prices[0]) / prices[0]) * 100
        if avg_change > 0:
            st.success(f"✅ 回測結果：此類新聞發布後，一週內平均上漲 **{avg_change:.2f}%**")
        else:
            st.error(f"🔻 回測結果：此類新聞發布後，一週內平均下跌 **{avg_change:.2f}%**")