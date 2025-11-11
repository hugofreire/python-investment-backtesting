# 80/20 Portfolio Backtesting System

A Python-based portfolio backtesting system implementing an 80/20 Core/Tilt strategy with trend filtering, targeting +1% annual outperformance vs S&P 500.

## Strategy Overview

- **Core (80%):** VOO (S&P 500)
- **Tilt (20%):** QUAL/VLUE/MTUM (equally weighted at 6.67% each)
- **Risk Filter:** 10-month SMA on tilt composite → park in SHY if bearish
- **Rebalancing:** Quarterly with 5% bands
- **Costs:** 2 bps commission + 2 bps slippage per trade

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run backtest
python main.py backtest --start 2013-01-01 --region US

# Generate report
python main.py report --output report.html
```

## Target Performance

- CAGR vs VOO: ≥ +0.6%/year
- Sharpe ratio: ≥ VOO
- Max drawdown: ≤ S&P +10%
- Trades/year: ≤ 12

## Architecture

Built with Python `bt` library for:
- ✅ Rebalancing logic with bands
- ✅ Transaction cost modeling
- ✅ Performance metrics (Sharpe, drawdown, CAGR)
- ✅ Multiple backtests + benchmark comparison

## Project Structure

```
portfolio/
├── data/          # Data fetching and caching
├── strategy/      # Custom bt.Algo implementations
├── backtest/      # Backtest runner and metrics
└── reports/       # Report generation
```

## License

MIT
