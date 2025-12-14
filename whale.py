import websocket
import json
from datetime import datetime

# 設定門檻：只顯示超過 500,000 美金的成交
WHALE_THRESHOLD_USD = 500000 

def on_message(ws, message):
    data = json.loads(message)
    
    # 解析數據
    # 'p': 價格, 'q': 數量, 'm': 是否為賣方做市 (True=主動賣, False=主動買)
    price = float(data['p'])
    quantity = float(data['q'])
    is_buyer_maker = data['m'] 
    
    # 計算總價值
    total_value = price * quantity
    
    # 只有超過門檻才顯示
    if total_value >= WHALE_THRESHOLD_USD:
        # 判斷是買單還是賣單
        # 在幣安數據中，如果 'm' 是 True，代表 Maker 是 Buyer -> Taker 是 Seller -> 這是賣單
        # 如果 'm' 是 False，代表 Maker 是 Seller -> Taker 是 Buyer -> 這是買單
        side = "🔴 鯨魚倒貨 (SELL)" if is_buyer_maker else "🟢 鯨魚吃貨 (BUY)"
        color = "\033[91m" if is_buyer_maker else "\033[92m" # 紅/綠色代碼
        reset = "\033[0m"
        
        print(f"{color}=== WHALE ALERT! ==={reset}")
        print(f"時間: {datetime.now().strftime('%H:%M:%S')}")
        print(f"方向: {side}")
        print(f"價格: {price:,.2f}")
        print(f"數量: {quantity:.4f} BTC")
        print(f"價值: ${total_value:,.0f} USD")
        print("-" * 30)

def on_error(ws, error):
    print(f"錯誤: {error}")

def on_close(ws, close_status_code, close_msg):
    print("連線已關閉")

def on_open(ws):
    print("--- 正在連線至 Binance 監控大戶成交 ---")
    print(f"監控門檻: ${WHALE_THRESHOLD_USD:,.0f} USD")

if __name__ == "__main__":
    # Binance Aggregated Trade Stream (btcusdt)
    socket_url = "wss://stream.binance.com:9443/ws/btcusdt@aggTrade"
    
    ws = websocket.WebSocketApp(socket_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()