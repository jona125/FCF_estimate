install packages

pip install -r requirement.txt
source FCF/bin/activate

usage 

python fair_price_calculator.py -t AAPL

python fair_price_calculator.py -t AAPL -i 0.03 -g 0.08 -d 0.08 -y 10

-i: inflation rate
-g: growth rate
-d: discount rate
-y: years

python3 stock_screening.py -i sp500
Replace sp500 with nasdaq100, dowjones, or russell1000 as needed.
