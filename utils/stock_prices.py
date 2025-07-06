import yfinance as yf
import asyncio
import random
import json

async def get_random_stock_price():
    stock_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'TSLA', 'NVDA', 'JPM', 'V', 'WMT',
        'DIS', 'NFLX', 'PYPL', 'ADBE', 'INTC'
    ]

    random_ticker = random.choice(stock_tickers)

    try:
        stock = yf.Ticker(random_ticker)
        current_data = stock.history(period='1d')

        if not current_data.empty:
            price = current_data['Close'].iloc[-1]
            return float(price)
        else:
            return 1.0

    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return 1.0

async def update_all_company_prices(companies_file):
    while True:
        try:
            with open(companies_file, "r") as f:
                companies = json.load(f)

            for name, data in companies.items():
                new_price = await get_random_stock_price()
                data['share_price'] = round(new_price, 2)

            with open(companies_file, "w") as f:
                json.dump(companies, f, indent=4)

            print("✅ Company prices updated.")
        except Exception as e:
            print(f"Error updating company prices: {e}")

        await asyncio.sleep(300)
