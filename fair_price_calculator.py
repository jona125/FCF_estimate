import yfinance as yf
import argparse

def get_fcf(ticker):
    stock = yf.Ticker(ticker)
    cash_flow = stock.cashflow
    if 'Free Cash Flow' in cash_flow.index:
        fcf = cash_flow.loc['Free Cash Flow'].values[0]
        return fcf
    else:
        raise ValueError("Free Cash Flow data is not available for this ticker.")

def get_current_price(ticker):
    stock = yf.Ticker(ticker)
    current_price = stock.history(period="1d")['Close'].iloc[-1]
    return current_price

def calculate_fair_price(ticker, inflation_rate=0.03, growth_rate=0.05, discount_rate=0.08, years=10):
    fcf = get_fcf(ticker)

    # Check for division by zero risk
    if discount_rate <= growth_rate:
        raise ValueError("Discount rate must be greater than growth rate to avoid division by zero.")

    # Calculate future FCFs
    future_fcfs = []
    for year in range(1, years + 1):
        fcf *= (1 + growth_rate)
        future_fcfs.append(fcf / ((1 + discount_rate) ** year))

    # Calculate terminal value
    terminal_value = future_fcfs[-1] * (1 + growth_rate) / (discount_rate - growth_rate)
    future_fcfs[-1] += terminal_value / ((1 + discount_rate) ** years)

    # Calculate fair value
    fair_value = sum(future_fcfs)

    # Adjust for inflation
    fair_value_adjusted = fair_value / ((1 + inflation_rate) ** years)

    # If necessary, convert to per-share value
    shares_outstanding = yf.Ticker(ticker).info['sharesOutstanding']
    fair_value_per_share = fair_value_adjusted / shares_outstanding

    return fair_value_per_share

def main():
    parser = argparse.ArgumentParser(description="Calculate the fair price of a stock using FCF.")
    parser.add_argument('-t', '--ticker', type=str, required=True, help='Stock ticker symbol')
    parser.add_argument('-i', '--inflation_rate', type=float, default=0.03, help='Yearly inflation rate')
    parser.add_argument('-g', '--growth_rate', type=float, default=0.05, help='Expected benchmark growth rate')
    parser.add_argument('-d', '--discount_rate', type=float, default=0.08, help='Discount rate')
    parser.add_argument('-y', '--years', type=int, default=10, help='Number of years for projection')

    args = parser.parse_args()

    try:
        current_price = get_current_price(args.ticker)
        fair_price = calculate_fair_price(args.ticker, args.inflation_rate, args.growth_rate, args.discount_rate, args.years)
        
        print(f"Current price of {args.ticker}: ${current_price:.2f}")
        print(f"The fair price of {args.ticker} is ${fair_price:.2f}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

