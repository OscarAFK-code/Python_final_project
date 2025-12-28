import requests
import pandas as pd
from datetime import datetime
import time

# --- 設定參數 ---
ETHERSCAN_API_KEY = "ETUAVQGCEJS6Z755JGQ2K9C1GSEHTGHK2Z"  # 去 etherscan.io 免費申請一個
BTC_THRESHOLD_USD = 5000000  # 設定比特幣鯨魚門檻 (例如 500萬美金)
ETH_THRESHOLD_USD = 2000000  # 設定以太幣鯨魚門檻 (例如 200萬美金)

# 為了簡化，我們這裡寫死一個大概的價格，或者你可以從 dashboard.py 傳入即時價格
BTC_PRICE_FIXED = 90000   # 假設 BTC 價格
ETH_PRICE_FIXED = 3000    # 假設 ETH 價格

def get_btc_whales():
    """
    使用 Blockchain.com 免費 API (不需 Key) 抓取最新比特幣大額交易
    """
    url = "https://blockchain.info/unconfirmed-transactions?format=json"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        whales = []
        # 遍歷最新的交易池 (Mempool)
        for tx in data['txs'][:50]: # 只看最新的 50 筆以節省效能
            total_val_satoshi = 0
            
            # 計算輸出的總價值
            for output in tx['out']:
                total_val_satoshi += output['value']
            
            # 換算成 USD
            # 1 BTC = 100,000,000 Satoshi
            amount_btc = total_val_satoshi / 100000000
            value_usd = amount_btc * BTC_PRICE_FIXED
            
            if value_usd >= BTC_THRESHOLD_USD:
                whales.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "symbol": "BTC",
                    "amount": round(amount_btc, 2),
                    "value_usd": round(value_usd / 1000000, 2), # 顯示為百萬單位
                    "from": "Unknown (Mempool)", 
                    "to": "Unknown",
                    "link": f"https://www.blockchain.com/btc/tx/{tx['hash']}"
                })
        
        return whales
        
    except Exception as e:
        print(f"BTC API Error: {e}")
        return []

def get_eth_whales():
    """
    使用 Etherscan API 抓取最新區塊的大額交易
    """
    # 1. 先取得最新區塊號碼
    try:
        block_url = f"https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey={ETHERSCAN_API_KEY}"
        r_block = requests.get(block_url, timeout=5).json()
        latest_block = int(r_block['result'], 16)
        
        # 2. 取得該區塊內的交易細節
        tx_url = f"https://api.etherscan.io/api?module=proxy&action=eth_getBlockByNumber&tag={hex(latest_block)}&boolean=true&apikey={ETHERSCAN_API_KEY}"
        r_tx = requests.get(tx_url, timeout=5).json()
        
        transactions = r_tx['result']['transactions']
        whales = []
        
        for tx in transactions:
            # 轉換 Wei 到 ETH (1 ETH = 10^18 Wei)
            value_wei = int(tx['value'], 16)
            if value_wei == 0: continue
            
            amount_eth = value_wei / 10**18
            value_usd = amount_eth * ETH_PRICE_FIXED
            
            if value_usd >= ETH_THRESHOLD_USD:
                whales.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "symbol": "ETH",
                    "amount": round(amount_eth, 2),
                    "value_usd": round(value_usd / 1000000, 2),
                    "from": tx['from'][:6] + "...",
                    "to": tx['to'][:6] + "..." if tx['to'] else "Contract",
                    "link": f"https://etherscan.io/tx/{tx['hash']}"
                })
                
        return whales

    except Exception as e:
        print(f"ETH API Error: {e}")
        return []

def get_combined_whales():
    """
    整合函式，讓前端呼叫
    """
    btc = get_btc_whales()
    # 稍微睡一下避免 API Rate Limit
    time.sleep(1)
    eth = get_eth_whales()
    
    # 合併並按時間排序
    all_whales = btc + eth
    return all_whales