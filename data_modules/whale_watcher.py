import requests
import pandas as pd
from datetime import datetime
import time
import random

# 設定區
import streamlit as st

# 嘗試從 Secrets 讀取，如果沒有設定 (例如在本地跑)，就用空字串或預設值
if "ETHERSCAN_API_KEY" in st.secrets:
    ETHERSCAN_API_KEY = st.secrets["ETHERSCAN_API_KEY"]
else:
    # 這裡可以是空字串，或者你在本地測試用的 Key (不要上傳)
    ETHERSCAN_API_KEY = "你的測試KEY"
BTC_THRESHOLD = 5000000  
ETH_THRESHOLD = 2000000  

BTC_PRICE_FIXED = 95000
ETH_PRICE_FIXED = 3500

def get_btc_whales_real():
    """ [真實模式] 從 Blockchain.com 抓取 """
    url = "https://blockchain.info/unconfirmed-transactions?format=json"
    whales = []
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        for tx in data['txs'][:30]: 
            total_satoshi = sum([out['value'] for out in tx['out']])
            amount_btc = total_satoshi / 100000000
            value_usd = amount_btc * BTC_PRICE_FIXED
            
            if value_usd >= BTC_THRESHOLD:
                whales.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "symbol": "BTC",
                    "amount": round(amount_btc, 2),
                    "value_usd": round(value_usd / 1000000, 2), 
                    "from": "Mempool",
                    "link": f"https://www.blockchain.com/btc/tx/{tx['hash']}"
                })
    except Exception as e:
        print(f"⚠️ BTC API Error: {e}")
    return whales

def get_eth_whales_real():
    """ [真實模式] 從 Etherscan 抓取 """
    whales = []
    try:
        block_url = f"https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey={ETHERSCAN_API_KEY}"
        r_block = requests.get(block_url, timeout=5).json()
        
        if "result" not in r_block:
            return []
            
        latest_block = int(r_block['result'], 16)
        
        tx_url = f"https://api.etherscan.io/api?module=proxy&action=eth_getBlockByNumber&tag={hex(latest_block)}&boolean=true&apikey={ETHERSCAN_API_KEY}"
        r_tx = requests.get(tx_url, timeout=5).json()
        
        transactions = r_tx.get('result', {}).get('transactions', [])
        
        for tx in transactions:
            value_wei = int(tx['value'], 16)
            if value_wei == 0: continue
            
            amount_eth = value_wei / 10**18
            value_usd = amount_eth * ETH_PRICE_FIXED
            
            if value_usd >= ETH_THRESHOLD:
                whales.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "symbol": "ETH",
                    "amount": round(amount_eth, 2),
                    "value_usd": round(value_usd / 1000000, 2),
                    "from": tx['from'][:8] + "...",
                    "link": f"https://etherscan.io/tx/{tx['hash']}"
                })
    except Exception as e:
        print(f"⚠️ ETH API Error: {e}")
    return whales

def generate_fake_whales():
    """ [Demo 模式] 產生假資料 """
    fake_data = []
    for _ in range(random.randint(1, 2)):
        coin = random.choice(["BTC", "ETH"])
        amount = random.uniform(50, 200) if coin == "BTC" else random.uniform(500, 3000)
        val = (amount * BTC_PRICE_FIXED if coin == "BTC" else amount * ETH_PRICE_FIXED) / 1000000
        
        fake_data.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "symbol": coin,
            "amount": round(amount, 2),
            "value_usd": round(val, 2),
            "from": "Demo_Wallet",
            "link": "https://etherscan.io"
        })
    return fake_data

def get_whale_alerts(is_demo=False):
    """
    統一入口函式
    參數: is_demo (bool) - 決定是否回傳假資料
    """
    if is_demo:
        return generate_fake_whales()
    
    # 真實模式：抓 BTC + 抓 ETH
    btc = get_btc_whales_real()
    time.sleep(0.5) # 稍微休息一下避免 API 過載
    eth = get_eth_whales_real()
    
    return btc + eth