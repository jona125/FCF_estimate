import yfinance as yf
import argparse
import numpy as np

def fetch_historical_data(ticker, start_date='2004-01-01', end_date='2024-01-01'):
    stock = yf.Ticker(ticker)
    historical_data = stock.history(start=start_date, end=end_date)
    return historical_data['Close']

def get_sector_for_ticker(ticker):
    stock = yf.Ticker(ticker)
    return stock.info.get('sector', 'Unknown')

def get_sector_averages(sector):
    SECTOR_AVERAGES = {
        'Technology': {'average_pe': 25, 'average_pb': 5},
        'Healthcare': {'average_pe': 20, 'average_pb': 4},
        'Financials': {'average_pe': 15, 'average_pb': 1.5},
        'Consumer Discretionary': {'average_pe': 18, 'average_pb': 3},
        'Consumer Staples': {'average_pe': 17, 'average_pb': 2.5},
        'Energy': {'average_pe': 10, 'average_pb': 1.2},
        'Utilities': {'average_pe': 19, 'average_pb': 2.2},
        'Materials': {'average_pe': 12, 'average_pb': 1.8},
        'Industrials': {'average_pe': 16, 'average_pb': 2.0},
        'Real Estate': {'average_pe': 22, 'average_pb': 3.5},
    }
    return SECTOR_AVERAGES.get(sector, {'average_pe': 20, 'average_pb': 3})

def get_fcf(ticker):
    stock = yf.Ticker(ticker)
    cash_flow = stock.cashflow
    if 'Free Cash Flow' in cash_flow.index:
        return cash_flow.loc['Free Cash Flow'].values[0]
    else:
        raise ValueError("Free Cash Flow data is not available for this ticker.")

def get_current_price(ticker):
    stock = yf.Ticker(ticker)
    current_price = stock.history(period="5d")['Close'].iloc[-1]
    return current_price

def calculate_fair_price(ticker, inflation_rate=0.03, growth_rate=0.05, discount_rate=0.08, years=10):
    fcf = get_fcf(ticker)

    if discount_rate <= growth_rate:
        raise ValueError("Discount rate must be greater than growth rate to avoid division by zero.")

    future_fcfs = []
    for year in range(1, years + 1):
        fcf *= (1 + growth_rate)
        future_fcfs.append(fcf / ((1 + discount_rate) ** year))

    terminal_value = future_fcfs[-1] * (1 + growth_rate) / (discount_rate - growth_rate)
    future_fcfs[-1] += terminal_value / ((1 + discount_rate) ** years)

    fair_value = sum(future_fcfs)
    fair_value_adjusted = fair_value / ((1 + inflation_rate) ** years)

    shares_outstanding = yf.Ticker(ticker).info['sharesOutstanding']
    fair_value_per_share = fair_value_adjusted / shares_outstanding

    return fair_value_per_share

def calculate_graham_number(ticker):
    stock = yf.Ticker(ticker)
    earnings_per_share = stock.info.get('trailingEps', 0)
    book_value_per_share = stock.info.get('bookValue', 0)

    if earnings_per_share <= 0 or book_value_per_share <= 0:
        print(f"Warning: EPS or Book Value is not available or is zero for {ticker}. Calculating Graham number with available data.")

    sector = get_sector_for_ticker(ticker)
    sector_averages = get_sector_averages(sector)

    average_pe = sector_averages['average_pe']
    average_pb = sector_averages['average_pb']
    
    graham_number = (average_pe * (earnings_per_share if earnings_per_share > 0 else 1) * 
                     average_pb * (book_value_per_share if book_value_per_share > 0 else 1)) ** 0.5
    return graham_number

def monte_carlo_future_move(ticker, simulations=1000, years=10):
    stock = yf.Ticker(ticker)
    current_price = get_current_price(ticker)
    returns = np.random.normal(0.1, 0.2, (simulations, years))
    future_prices = current_price * np.exp(np.cumsum(returns, axis=1))
    average_future_price = np.mean(future_prices[:, -1])
    return average_future_price

def calculate_fair_price_using_weights(dcf_value, graham_number, monte_carlo_value):
    # Define fixed weights
    weights = {
        'dcf': 0.6,
        'graham': 0.3,
        'monte_carlo': 0.1
    }

    # Replace graham_number with dcf_value if graham_number is 0
    if graham_number == 0:
        graham_number = dcf_value

    fair_price = (
        weights['dcf'] * dcf_value +
        weights['graham'] * graham_number +
        weights['monte_carlo'] * monte_carlo_value
    )
    return fair_price

def main():
    parser = argparse.ArgumentParser(description="Calculate combined fair price, DCF value, and Graham number.")
    parser.add_argument('-t', '--ticker', type=str, required=True, help='Stock ticker symbol')
    parser.add_argument('-i', '--inflation_rate', type=float, default=0.03, help='Yearly inflation rate')
    parser.add_argument('-g', '--growth_rate', type=float, default=0.05, help='Expected benchmark growth rate')
    parser.add_argument('-d', '--discount_rate', type=float, default=0.08, help='Discount rate')
    parser.add_argument('-y', '--years', type=int, default=10, help='Number of years for projection')

    args = parser.parse_args()

    try:
        sector = get_sector_for_ticker(args.ticker)
        fcf = get_fcf(args.ticker)
        dcf_value = calculate_fair_price(args.ticker, args.inflation_rate, args.growth_rate, args.discount_rate, args.years)
        graham_number = calculate_graham_number(args.ticker)
        monte_carlo_value = monte_carlo_future_move(args.ticker)

        # Calculate the fair price using fixed weights
        fair_price = calculate_fair_price_using_weights(dcf_value, graham_number, monte_carlo_value)
        current_price = get_current_price(args.ticker)

        print(f"Current price of {args.ticker}: ${current_price:.2f}")
        print(f"The DCF value of {args.ticker} is ${dcf_value:.2f}")
        print(f"The Graham number for {args.ticker} is ${graham_number:.2f}")
        print(f"The Monte-Carlo future move value for {args.ticker} is ${monte_carlo_value:.2f}")
        print(f"The fair price for {args.ticker} is ${fair_price:.2f}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

