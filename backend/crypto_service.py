#работа с внешними API:
import requests
from fastapi import HTTPException

#Получение цены криптовалюты с Binance API |  symbol: Символ криптовалюты (BTC, ETH, etc)
def get_crypto_price(symbol: str) -> float:
    try:
        resource = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT")
        return float(resource.json()["price"])
    except:
        raise HTTPException(status_code=500, detail="Error while getting price from Binance API")
