install packages

```
python -m venv FCF
source FCF/bin/activate
pip install -r requirements.txt
```

usage 
```
python valuation_calculator.py -t AAPL
```

```
python valuation_calculator.py -t AAPL -i 0.03 -g 0.08 -d 0.09 -y 10
```
-i: inflation rate
-g: growth rate
-d: discount rate
-y: years


```
python3 stock_screening.py -i sp500
```

Replace sp500 with nasdaq100, dowjones, russell1000 or taiwan50 as needed.
