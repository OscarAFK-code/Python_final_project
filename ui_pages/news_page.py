import streamlit as st
import pandas as pd
from data_modules.news_scraper import fetch_google_news

def show():
    st.title("📰 全球加密貨幣輿情分析")
    
    # --- 搜尋設定區 ---
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            keyword = st.text_input("輸入關鍵字 (英文搜尋更精準)：", "Bitcoin")
        
        with col2:
            # 讓使用者選語言
            lang_choice = st.selectbox("新聞語言", ["英文 (Global)", "中文 (Taiwan)"])
            lang_code = 'en' if "英文" in lang_choice else 'zh'
            
        with col3:
            st.write("")
            st.write("")
            run_search = st.button("🔍 搜尋 100 篇", type="primary")

    if run_search:
        with st.spinner(f"正在分析關於 {keyword} 的 100 篇全球報導..."):
            # 呼叫後端，設定 limit=100
            df = fetch_google_news(keyword=keyword, limit=100, lang=lang_code)
        
        if not df.empty:
            # --- 1. 顯示統計數據 ---
            st.success(f"✅ 成功抓取 {len(df)} 篇新聞！")
            
            # 簡單計算一下情緒分佈
            pos_count = len(df[df['情緒分數'] > 0])
            neg_count = len(df[df['情緒分數'] < 0])
            
            m1, m2, m3 = st.columns(3)
            m1.metric("🔥 利多新聞", f"{pos_count} 篇")
            m2.metric("📉 利空新聞", f"{neg_count} 篇")
            m3.metric("😐 整體氣氛", "偏多" if pos_count > neg_count else "偏空")
            
            st.markdown("---")

            # --- 2. 使用 Dataframe 顯示 (適合大量資料) ---
            # 把連結變成可以點擊的 HTML (這招很進階)
            st.subheader("📋 新聞清單一覽")
            
            # 為了讓連結可點擊，我們用 st.data_editor 或 st.markdown 表格
            # 這裡示範一個比較美觀的表格設定
            st.dataframe(
                df[['情緒標籤', '標題', '來源', '發布時間']],
                use_container_width=True,
                height=400, # 固定高度，內容可捲動
                hide_index=True
            )
            
            # --- 3. (選用) 詳細列表 ---
            with st.expander("點擊展開詳細連結列表"):
                for index, row in df.iterrows():
                    st.markdown(f"{row['情緒標籤']} **[{row['標題']}]({row['連結']})** - *{row['來源']}*")

        else:
            st.warning("找不到新聞，請嘗試更換關鍵字 (例如改用英文搜尋)。")