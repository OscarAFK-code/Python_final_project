import streamlit as st

# 引入你的子頁面模組
from ui_pages import dashboard, news_page, tech_analysis, arbitrage_page, data_viz

# --- 1. 全域設定 (Global Settings) ---
st.set_page_config(
    page_title="Crypto Analytics Pro", # 網頁標題改英文比較專業
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded" # 預設展開側邊欄
)

# --- [進階技巧] 注入 CSS 隱藏預設樣式，讓介面更像一個獨立 App ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            /* 調整上方邊距，讓內容不要離頂部太遠 */
            .block-container {
                padding-top: 1rem;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. 側邊欄設定 (Sidebar) ---
with st.sidebar:
    st.title("Crypto Pro") # 側邊欄大標題
    st.markdown("加密貨幣分析系統")
    st.markdown("---")
    
    # 選單：移除 Emoji，改用更專業的命名
    # 使用 radio 雖然簡單，但配合 CSS 會很乾淨
    page = st.radio(
        "功能導航",
        [
            "市場戰情總覽", 
            "全球輿情分析", 
            "重大事件回測", 
            "技術分析室", 
            "搬磚套利監控"
        ],
        label_visibility="collapsed" # 隱藏 "功能導航" 這幾個字，更簡潔
    )

    st.markdown("---")
    
    # 系統設定區塊
    st.caption("系統設定")
    
    # Demo 模式開關
    use_demo_mode = st.toggle("啟動 Demo 演示模式", value=False) # 使用 toggle 開關比 checkbox 更現代
    
    # [關鍵修正] 將 Demo 狀態寫入 Session State
    # 這樣所有的子頁面 (dashboard, news...) 都能讀到這個變數
    if use_demo_mode:
        st.session_state['IS_DEMO'] = True
        st.success("✅ 已進入演示模式")
    else:
        st.session_state['IS_DEMO'] = False

    # 顯示版本號或作者，增加專業感
    st.markdown("---")
    st.caption("v1.0.2 Release ")
    st.caption(" By 顏家駿 潘鑫哲 吳昕睿")

# --- 3. 頁面路由邏輯 (Page Routing) ---

if page == "市場戰情總覽":
    dashboard.show()

elif page == "全球輿情分析":
    news_page.show()

elif page == "重大事件回測":
    data_viz.show()

elif page == "技術分析室":
    tech_analysis.show()

elif page == "搬磚套利監控":
    arbitrage_page.show()
