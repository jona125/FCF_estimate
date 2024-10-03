import pandas as pd
import subprocess
import numpy as np
import re
import argparse

def get_tickers(index):
    urls = {
        'sp500': "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        'nasdaq100': "https://en.wikipedia.org/wiki/NASDAQ-100",
        'dowjones': "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average",
        'russell1000': "https://en.wikipedia.org/wiki/Russell_1000_Index",
        'taiwan50': "https://en.wikipedia.org/wiki/Template:FTSE_TWSE_Taiwan_50"
    }
    
    if index not in urls:
        raise ValueError("Invalid index selected. Choose from: sp500, nasdaq100, dowjones, russell1000, taiwan50.")
    
    tables = pd.read_html(urls[index])
    if index == 'sp500':
        return tables[0]['Symbol'].tolist()
    elif index == 'nasdaq100':
        return tables[4]['Ticker'].tolist()
    elif index == 'dowjones':
        return tables[1]['Symbol'].tolist()
    elif index == 'russell1000':
        return tables[2]['Symbol'].tolist()
    elif index == 'taiwan50':
       # Parse the Taiwan 50 tickers
        tickers = []
        for cols in tables[0]:
            for col in tables[0][cols]:
                matches = re.findall(r'TWSE:\s?(\d+)', col)
                tickers.extend([f"{match}.TW" for match in matches]) 
        return tickers 

def calculate_fair_price(ticker, inflation_rate=0.03, growth_rate=0.05, discount_rate=0.08, years=10):
    try:
        result = subprocess.run(
            ["python3", "valuation_calculator.py", "-t", ticker, "-i", str(inflation_rate), 
             "-g", str(growth_rate), "-d", str(discount_rate), "-y", str(years)],
            capture_output=True, text=True
        )

        fair_price = None
        current_price = None

        for line in result.stdout.splitlines():
            if "The fair price" in line:
                fair_price = float(line.split('$')[1])
            if "Current price" in line:
                current_price = float(line.split('$')[1])

        if fair_price is None or fair_price < 0:
            print(f"Fair price is negative or not available for {ticker}. Skipping.")
            return current_price, None  # Return None for fair price

        return current_price, fair_price

    except Exception as e:
        print(f"Error running valuation for {ticker}: {e}")
        return None, None

def screen_stocks(tickers):
    results = []
    skipped_count = 0
    
    for ticker in tickers:
        current_price, fair_price = calculate_fair_price(ticker)

        if current_price is None or fair_price is None:
            print(f"Price data not available for {ticker}. Skipping.")
            skipped_count += 1
            continue

        percentage_difference = ((fair_price - current_price) / fair_price) * 100

        # Print progress
        print(f"{ticker}: Current Price = ${current_price:.2f}, Fair Price = ${fair_price:.2f}, "
              f"Percentage Difference = {percentage_difference:.2f}%")

        if percentage_difference < 0:
            print(f"Skipping {ticker}: Fair price is less than current price.")
            skipped_count += 1
            continue

        results.append((ticker, current_price, fair_price, percentage_difference))

    return results, skipped_count

def find_above_threshold_stocks(results):
    positive_percentages = [x[3] for x in results if x[3] > 0]
    
    if len(positive_percentages) == 0:
        return []

    mean = np.mean(positive_percentages)
    std_dev = np.std(positive_percentages)

    threshold = mean + std_dev
    above_threshold = [x for x in results if x[3] > threshold]

    return above_threshold

def main():
    parser = argparse.ArgumentParser(description="Stock screening for various indices.")
    parser.add_argument('-i', '--index', type=str, required=True,
                        choices=['sp500', 'nasdaq100', 'dowjones', 'russell1000', 'taiwan50'],
                        help='Index to screen: sp500, nasdaq100, dowjones, russell1000, or taiwan50')

    args = parser.parse_args()
    
    tickers = get_tickers(args.index)
    results, skipped_count = screen_stocks(tickers)
    above_threshold_stocks = find_above_threshold_stocks(results)

    print(f"\nTotal skipped tickers: {skipped_count}")
    print("Tickers with Percentage Difference Over 1 Standard Deviations:")
    for ticker, current_price, fair_price, percentage in above_threshold_stocks:
        print(f"{ticker}: Current Price = ${current_price:.2f}, Fair Price = ${fair_price:.2f}, "
              f"Percentage Difference = {percentage:.2f}%")

if __name__ == "__main__":
    main()

