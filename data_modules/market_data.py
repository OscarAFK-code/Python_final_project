import ccxt
import pandas as pd
import requests

# 初始化交易所
# 我們使用全域變數來儲存連線實例，避免每次呼叫都重新連線
exchanges = {
    'binance': ccxt.binance({'enableRateLimit': True}),
    'okx': ccxt.okx({'enableRateLimit': True}),
    'coinbase': ccxt.coinbase({'enableRateLimit': True}) 
}

def get_symbol_for_exchange(exchange_name, coin):
    """
    自動適配不同交易所的交易對名稱
    Binance/OKX 通常用 USDT，Coinbase 通常用 USD
    """
    if exchange_name == 'coinbase':
        return f"{coin}/USD"
    else:
        return f"{coin}/USDT"

def get_price_data(coins=['BTC', 'ETH', 'SOL', 'DOGE']):
    """
    功能：一次抓取指定幣種在所有交易所的價格
    回傳：一個 DataFrame，包含幣種、交易所、最新價格、漲跌幅
    """
    all_data = []

    for exchange_name, exchange_obj in exchanges.items():
        for coin in coins:
            symbol = get_symbol_for_exchange(exchange_name, coin)
            
            try:
                ticker = exchange_obj.fetch_ticker(symbol)
                
                all_data.append({
                    'Exchange': exchange_name.capitalize(), 
                    'Coin': coin,
                    'Price': ticker['last'],
                    'Change24h%': ticker.get('percentage', 0), 
                    'Volume': ticker.get('baseVolume', 0)
                })
            except Exception as e:
                print(f"⚠️ Error fetching {symbol} from {exchange_name}: {e}")
                all_data.append({
                    'Exchange': exchange_name.capitalize(),
                    'Coin': coin,
                    'Price': None,
                    'Change24h%': None,
                    'Volume': 0
                })

    return pd.DataFrame(all_data)

def get_fear_and_greed_index():
    """
    功能：從 alternative.me 抓取恐懼貪婪指數
    """
    url = "https://api.alternative.me/fng/"
    try:
        response = requests.get(url, timeout=10) 
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            item = data['data'][0]
            return {
                'value': int(item['value']),
                'state': item['value_classification']
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching FGI: {e}")
        return None