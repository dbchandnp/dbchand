import ccxt
import pandas as pd
import time
from datetime import datetime

# Initialize Binance exchange
exchange = ccxt.binance({
    'enableRateLimit': True,
})

# Parameters
timeframe = '3m'
ema_short = 9
ema_long = 20
min_volume = 1000000  # Minimum 24h volume in USDT to filter coins (adjust as needed)

def calculate_ema(data, period):
    return data['close'].ewm(span=period, adjust=False).mean()

def get_active_symbols():
    print("Fetching active trading pairs from Binance...")
    markets = exchange.load_markets()
    active_symbols = []
    
    for symbol in markets:
        market = markets[symbol]
        # Filter for USDT pairs and spot markets
        if market['quote'] == 'USDT' and market['active'] and market['spot']:
            # Check 24h volume
            try:
                ticker = exchange.fetch_ticker(symbol)
                if ticker['quoteVolume'] is not None and ticker['quoteVolume'] >= min_volume:
                    active_symbols.append(symbol)
            except:
                continue
    
    print(f"Found {len(active_symbols)} active trading pairs with sufficient volume")
    return active_symbols

def check_crossover(symbol):
    try:
        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=50)
        
        if len(ohlcv) < 50:
            return None
            
        # Create DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Calculate EMAs
        df['ema_short'] = calculate_ema(df, ema_short)
        df['ema_long'] = calculate_ema(df, ema_long)
        
        # Get the last two candles
        prev_short = df['ema_short'].iloc[-2]
        prev_long = df['ema_long'].iloc[-2]
        current_short = df['ema_short'].iloc[-1]
        current_long = df['ema_long'].iloc[-1]
        
        # Check for crossover
        if prev_short < prev_long and current_short > current_long:
            return "Bullish Crossover"
        elif prev_short > prev_long and current_short < current_long:
            return "Bearish Crossover"
        else:
            return None
            
    except Exception as e:
        print(f"Error processing {symbol}: {str(e)}")
        return None

def main():
    print(f"Scanning for EMA {ema_short}/{ema_long} crossovers on {timeframe} timeframe...")
    symbols = get_active_symbols()
    
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{now} - Scanning {len(symbols)} symbols...")
        
        crossovers_found = 0
        
        for symbol in symbols:
            result = check_crossover(symbol)
            if result:
                crossovers_found += 1
                print(f"{symbol}: {result} detected!")
        
        print(f"Scan complete. Found {crossovers_found} crossovers.")
        
        # Wait for the next candle (3 minutes)
        time.sleep(18)

if __name__ == "__main__":
    main()