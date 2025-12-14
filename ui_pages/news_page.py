import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from pygooglenews import GoogleNews
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import re

# --- 初始化分析器 (放在外面避免重複載入) ---
analyzer = SentimentIntensityAnalyzer()

# --- 1. 核心功能函式 (爬蟲與分析) ---

def get_live_news():
    """
    抓取 Google News 上關於加密貨幣的即時新聞 (英文準確度較高)
    """
    gn = GoogleNews(lang='en', country='US')
    search = gn.search('Bitcoin OR Ethereum OR Solana OR Crypto')
    
    news_items = []
    
    # 只取前 8 則最新新聞
    for entry in search['entries'][:8]:
        title = entry.title
        published = entry.published_parsed
        # 將時間轉為 HH:MM 格式
        time_str = datetime(*published[:6]).strftime('%H:%M')
        
        # 情緒分析
        score = analyzer.polarity_scores(title)['compound']
        
        if score >= 0.05:
            sentiment = "正向 🔥"
            sentiment_color = "green"
        elif score <= -0.05:
            sentiment = "負向 📉"
            sentiment_color = "red"
        else:
            sentiment = "中立 😐"
            sentiment_color = "gray"
            
        # 簡單判定幣種 (正規表達式)
        ticker = "BTC" # 預設
        if re.search(r'Ethereum|ETH|Ether', title, re.IGNORECASE):
            ticker = "ETH"
        elif re.search(r'Solana|SOL', title, re.IGNORECASE):
            ticker = "SOL"
        elif re.search(r'Bitcoin|BTC', title, re.IGNORECASE):
            ticker = "BTC"
            
        news_items.append({
            "時間": time_str,
            "標題": title,
            "情緒": sentiment,
            "分數": score,
            "幣種": ticker,
            "連結": entry.link
        })
        
    return pd.DataFrame(news_items)

def get_crypto_price(ticker, days=7):
    """
    抓取指定幣種過去 N 天的價格
    """
    symbol_map = {"BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD"}
    symbol = symbol_map.get(ticker, "BTC-USD") # 找不到就預設 BTC
    
    # 抓取資料
    df = yf.download(symbol, period=f"{days}d", interval="1h", progress=False)
    return df, symbol

# --- 2. 頁面顯示邏輯 (加上自動刷新) ---

# 使用 @st.fragment 讓這個區塊獨立刷新
@st.fragment(run_every=30)
def show():
    # --- 頁面標題 ---
    st.title("📰 全球加密貨幣輿情分析 (Live)")
    st.caption(f"最後更新: {datetime.now().strftime('%H:%M:%S')} | 資料來源: Google News & Yahoo Finance")
    st.markdown("---")

    # --- 抓取即時資料 ---
    # 這裡會真的去爬蟲，所以可能會花 1-2 秒
    with st.spinner("正在掃描全球新聞..."):
        df_news = get_live_news()

    # --- 版面配置 ---
    col1, col2 = st.columns([1, 2])

    # --- 左側：新聞列表 ---
    with col1:
        st.subheader("📡 即時新聞快訊")
        
        # 讓使用者選擇新聞
        # 注意：我們加上 key，這樣刷新時狀態才不會跑掉
        selected_index = st.selectbox(
            "👇 點擊選擇新聞以分析：",
            options=range(len(df_news)),
            format_func=lambda x: df_news.iloc[x]['標題'][:40] + "..." # 只顯示標題前40字
        )
        
        # 顯示簡易表格 (隱藏連結和分數，只看重點)
        st.dataframe(
            df_news[["時間", "幣種", "情緒", "標題"]], 
            hide_index=True,
            use_container_width=True,
            height=400
        )
        
        st.info("💡 系統每 30 秒自動爬取最新頭條。")

    # --- 右側：分析圖表 ---
    with col2:
        st.subheader("📈 市場趨勢對照")
        
        # 取得使用者選中的那則新聞資料
        target_news = df_news.iloc[selected_index]
        
        # 顯示新聞詳情卡片
        st.markdown(f"""
        > **📰 選中新聞：** [{target_news['標題']}]({target_news['連結']})  
        > **關聯幣種：** `{target_news['幣種']}` | **AI 情緒判定：** {target_news['情緒']} (分數: {target_news['分數']})
        """)
        
        # 抓取該幣種的真實走勢 (最近 7 天)
        price_df, symbol = get_crypto_price(target_news['幣種'])
        
        if not price_df.empty:
            # 處理 yfinance 多層索引問題 (如果有的話)
            if isinstance(price_df.columns, pd.MultiIndex):
                price_df.columns = price_df.columns.get_level_values(0)
                
            close_col = 'Close' if 'Close' in price_df.columns else price_df.columns[0]
            current_price = price_df[close_col].iloc[-1]
            
            # 畫圖
            fig = go.Figure()
            
            # 價格線
            fig.add_trace(go.Scatter(
                x=price_df.index, 
                y=price_df[close_col], 
                mode='lines',
                name=symbol,
                line=dict(color='#00CC96', width=2)
            ))
            
            fig.update_layout(
                title=f"{symbol} 近七日走勢 (現價: ${current_price:,.2f})",
                xaxis_title="時間",
                yaxis_title="價格 (USD)",
                height=450,
                template="plotly_dark",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 根據情緒給出簡單建議
            if target_news['分數'] > 0.05:
                st.success(f"🤖 **AI 分析建議：** 此新聞偏向利多，且 {target_news['幣種']} 近期趨勢若向上，可視為買入訊號。")
            elif target_news['分數'] < -0.05:
                st.error(f"🤖 **AI 分析建議：** 此新聞偏向利空，請留意 {target_news['幣種']} 是否出現拋售壓力。")
            else:
                st.warning(f"🤖 **AI 分析建議：** 此新聞情緒中立，市場可能正在觀望，建議等待趨勢明確。")
        else:
            st.error("無法抓取價格數據，請稍後再試。")

# 這一行是為了讓你單獨執行這個檔案測試用的
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    show()