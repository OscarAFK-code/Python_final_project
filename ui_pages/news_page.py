import streamlit as st
import pandas as pd
from data_modules.news_scraper import fetch_google_news

def show():
    # 標題區塊
    with st.container():
        st.title("新聞輿情分析")
        st.markdown("Global Sentiment & News Analysis")
    
    st.markdown("---")

    # --- 1. 搜尋設定區 ---
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1, 1], vertical_alignment="bottom")
        
        with c1:
            keyword = st.text_input("搜尋關鍵字", "Bitcoin")
        
        with c2:
            lang_choice = st.selectbox("語言區域", ["Global (En)", "Taiwan (Ch)"])
            lang_code = 'en' if "Global" in lang_choice else 'zh'
            
        with c3:
            run_search = st.button("開始分析", type="primary", use_container_width=True)

    if run_search:
        with st.spinner(f"正在檢索關於 {keyword} 的全球報導..."):
            try:
                # 呼叫真實爬蟲
                df = fetch_google_news(keyword=keyword, limit=50, lang=lang_code)
            except Exception as e:
                st.error(f"爬蟲發生錯誤: {e}")
                df = pd.DataFrame()

        # --- 2. 顯示結果 ---
        if not df.empty:
            # (A) 關鍵指標區
            pos_count = len(df[df['情緒分數'] > 0])
            neg_count = len(df[df['情緒分數'] < 0])
            avg_score = df['情緒分數'].mean()
            
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("市場熱度 (利多)", f"{pos_count} 篇", delta="Bullish", delta_color="normal")
            with col_m2:
                st.metric("市場恐慌 (利空)", f"{neg_count} 篇", delta="Bearish", delta_color="inverse")
            with col_m3:
                if avg_score > 0.3: state = "偏多"
                elif avg_score < -0.3: state = "偏空"
                else: state = "中立觀望"
                st.metric("整體氣氛", state, f"{avg_score:.2f} Score")

            st.markdown("---")

            # (B) 圖表區與列表區
            col_chart, col_list = st.columns([1, 2])
            
            with col_chart:
                st.subheader("多空勢力")
                
                # 修正長條圖資料結構
                chart_df = pd.DataFrame({
                    "利多 (Positive)": [pos_count],
                    "利空 (Negative)": [neg_count]
                })
                
                # 指定顏色：前者給綠，後者給紅
                st.bar_chart(
                    chart_df, 
                    color=["#00CC96", "#FF4B4B"], 
                    horizontal=False
                )
                
            with col_list:
                st.subheader("新聞清單")
                
                # --- 核心修改：將分數轉換為簡單的文字標籤 ---
                def get_simple_label(score):
                    if score > 0:
                        return "利多"
                    elif score < 0:
                        return "利空"
                    else:
                        return "中立"

                # 建立一個新欄位來顯示文字
                df['AI 訊號'] = df['情緒分數'].apply(get_simple_label)

                # 顯示表格 (不使用 style.bar，回歸單純)
                st.dataframe(
                    df,
                    column_config={
                        "標題": st.column_config.TextColumn("新聞標題", width="medium"),
                        "來源": st.column_config.TextColumn("媒體來源", width="small"),
                        "發布時間": st.column_config.TextColumn("時間", width="small"),
                        "連結": st.column_config.LinkColumn(
                            "閱讀", display_text="前往報導 🔗"
                        ),
                        "AI 訊號": st.column_config.TextColumn("AI 訊號", width="small"),
                        
                        # 隱藏原始數字與舊欄位
                        "情緒標籤": None, 
                        "情緒分數": None
                    },
                    use_container_width=True,
                    height=500,
                    hide_index=True
                )
        else:
            st.warning("查無相關新聞，請嘗試更換關鍵字。")

    elif not run_search:
        st.info("請在左側輸入關鍵字開始分析")