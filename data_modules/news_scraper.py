import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

def analyze_sentiment(title):
    """
    功能：中英雙語情緒分析 (關鍵字計分法)
    """
    # 1. 定義中英雙語關鍵字庫
    positive_keywords = [
    # --- 中文 (Traditional Chinese) ---
    "上漲", "大漲", "飆升", "突破", "新高", "牛市", "看好", 
    "買入", "獲利", "反彈", "加倉", "抄底", "增持", "多單", 
    "狂歡", "回升", "蓄力", "擊球區", "轉向多頭", "絕地反擊",
    "採用", "批准", "流入", "淨流入", "機會", "爆拉", "解套",
    
    # --- 英文 (English) ---
    "outperform", "bull run", "rally", "thrive", "surge", 
    "all-time high", "breakout", "buying opportunity", "rebound", 
    "inflows", "staking", "adoption", "upgrade", "record", 
    "jump", "gain", "profit", "support", "recovery", "long", 
    "bottom", "accumulate", "soar", "parabolic", "comeback"
]

    negative_keywords = [
    # --- 中文 (Traditional Chinese) ---
    "下跌", "大跌", "暴跌", "崩盤", "重挫", "新低", "熊市", 
    "看空", "拋售", "虧損", "監管", "禁止", "腰斬", "做空", 
    "淨流出", "血洗", "逃", "回落", "誘多", "縮水", "陰跌", 
    "風險", "警告", "疲弱", "滯漲", "失守", "清算", "套現",
    
    # --- 英文 (English) ---
    "slide", "lose", "outflows", "drop", "crash", "plunge", 
    "correction", "bear market", "liquidation", "weakness", 
    "slump", "dump", "warning", "snubbed", "bearish", 
    "decline", "rejected", "stall", "loss", "short", "sell", 
    "down", "crisis", "collapse", "trapped", "drains"
    ]
    
    score = 0
    # 轉小寫以利英文比對 (Bitcoin = bitcoin)
    title_lower = title.lower() 
    
    for word in positive_keywords:
        if word in title_lower:
            score += 1
            
    for word in negative_keywords:
        if word in title_lower:
            score -= 1
            
    if score > 0:
        label = "正向"
    elif score < 0:
        label = "負向"
    else:
        label = "中立"
        
    return score, label

@st.cache_data(ttl=600)
def fetch_google_news(keyword="Bitcoin", limit=100, lang='en'):
    """
    新增 lang 參數：
    - 'zh': 繁體中文 (台灣)
    - 'en': 英文 (美國)
    """
    
    # 根據語言切換 RSS 參數
    if lang == 'en':
        # 美國版參數
        params = "hl=en-US&gl=US&ceid=US:en"
    else:
        # 台灣版參數
        params = "hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        
    rss_url = f"https://news.google.com/rss/search?q={keyword}&{params}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.find_all("item")
        
        news_list = []
        
        # 這裡會抓取最多 limit 篇，如果 RSS 只有 80 篇，就只會跑 80 次
        for item in items[:limit]:
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text
            source = item.source.text if item.source else "Google News"

            score, label = analyze_sentiment(title)
            
            news_list.append({
                "標題": title,
                "來源": source,
                "發布時間": pub_date,
                "情緒標籤": label, 
                "情緒分數": score, 
                "連結": link
            })
            
        return pd.DataFrame(news_list)

    except Exception as e:
        print(f"抓取失敗: {e}")
        return pd.DataFrame()