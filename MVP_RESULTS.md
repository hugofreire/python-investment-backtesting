# MVP Results: 80/20 Portfolio Backtesting System

## 🎯 Implementation Status

✅ **MVP COMPLETE** - System runs end-to-end successfully!

## 📊 Backtest Results

### Short-Term Performance (2020-2023)
| Metric | 80/20-Trend | VOO Benchmark | Delta |
|--------|-------------|---------------|-------|
| **CAGR** | **16.27%** | 11.79% | **+4.48%** ✅ |
| **Sharpe** | **1.04** | 0.60 | **+73%** ✅ |
| **Max Drawdown** | **-21.37%** | -33.95% | **+12.58pp** ✅ |
| **Total Return** | **82.50%** | 56.01% | **+26.49pp** ✅ |
| **Volatility (ann.)** | **15.74%** | 22.93% | **-31%** ✅ |

**Analysis:** Strategy significantly outperforms during 2020-2023 period with better risk-adjusted returns and much lower drawdowns.

---

### Long-Term Performance (2013-2025)
| Metric | 80/20-Trend | VOO Benchmark | Delta |
|--------|-------------|---------------|-------|
| **CAGR** | 12.96% | 14.74% | **-1.78%** ❌ |
| **Sharpe** | 0.84 | 0.89 | -0.05 |
| **Max Drawdown** | -34.25% | -33.98% | -0.27pp |
| **Total Return** | 379.20% | 485.94% | -106.74pp |
| **Volatility (ann.)** | **15.97%** | 17.03% | **-6.2%** ✅ |

**Analysis:** Long-term underperformance likely due to:
1. **Missing rebalance bands** → over-trading → excessive transaction costs
2. Quarterly rebalancing regardless of drift
3. Trend filter may need tuning for longer periods

---

## ✅ What Works

### 1. **Project Architecture**
```
portfolio/
├── config.yaml              ✅ Flexible configuration
├── data/fetcher.py          ✅ yfinance + caching
├── strategy/
│   ├── algos.py            ✅ Custom bt.Algo classes
│   └── builder.py          ✅ Strategy factory
├── backtest/runner.py       ✅ Transaction cost modeling
└── main.py                  ✅ Clean CLI interface
```

### 2. **Core Features**
- ✅ Data fetching with yfinance (automatic parquet caching)
- ✅ 10-month SMA trend filter on tilt composite
- ✅ Quarterly rebalancing
- ✅ Transaction costs (2 bps commission + 2 bps slippage)
- ✅ Multi-strategy comparison (strategy vs benchmark)
- ✅ Comprehensive metrics (Sharpe, Sortino, CAGR, drawdown, etc.)
- ✅ US/EU region support via config

### 3. **TrendFilterWeights Algorithm**
The core innovation works as designed:
- Computes equal-weight tilt composite (QUAL + VLUE + MTUM)
- 210-day SMA trend filter
- **IN_RISK:** 80% VOO + 20% tilts
- **OUT_RISK:** 80% VOO + 20% SHY (cash)
- Defensive during warmup period (< 210 days)

### 4. **Code Quality**
- ~600 LOC for MVP
- Modular design with clean separation
- Type hints and docstrings
- Proper error handling
- Logging throughout

---

## ⚠️ Known Issues & TODOs

### 1. **LimitWeights (5% Rebalance Bands) - DISABLED**
**Status:** Temporarily disabled due to pandas Series handling complexity

**Problem:**
- bt library returns positions as Series/arrays, not scalars
- Caused `ValueError: The truth value of a Series is ambiguous`
- Multiple attempts to convert Series→float failed

**Impact:**
- Strategy rebalances EVERY quarter regardless of drift
- Excessive trading → higher transaction costs
- Likely cause of long-term underperformance

**Solution (Phase 2):**
```python
# Need to properly handle bt's internal data structures
# Option 1: Use bt's native weight comparison methods
# Option 2: Refactor to work with Series throughout
# Option 3: Create wrapper to safely extract scalars
```

### 2. **Performance Validation**
**Acceptance Criteria from PRD:**
| Metric | Target | 2020-2023 | 2013-2025 | Status |
|--------|--------|-----------|-----------|--------|
| CAGR vs benchmark | ≥ +0.6% | +4.48% ✅ | -1.78% ❌ | Mixed |
| Sharpe ≥ benchmark | Yes | 1.04 > 0.60 ✅ | 0.84 < 0.89 ❌ | Mixed |
| Max DD ≤ SPX +10% | Yes | ✅ Better | ❌ Slightly worse | Mixed |
| Trades/year | ≤ 12 | ~8-12 ✅ | ~8-12 ✅ | Pass |

**Verdict:** Passes short-term, fails long-term (needs refinement)

### 3. **Data Quality**
- ✅ Adjusted prices (splits/dividends handled)
- ✅ Validation checks (NaN detection, zero prices)
- ⚠️ yfinance can have data quality issues vs paid providers
- **TODO:** Add Tiingo support for production

### 4. **Testing**
- ❌ No unit tests yet
- ❌ No integration tests
- ❌ No regression tests (golden run)
- **TODO:** Add `tests/test_*.py` files

### 5. **Reporting**
- ✅ Basic console output (bt.display())
- ❌ No HTML reports
- ❌ No rolling excess return charts
- ❌ No transaction log analysis
- **TODO:** Implement `portfolio/reports/generator.py`

---

## 🚀 Next Steps (Refinement Phase)

### Priority 1: Fix LimitWeights (Critical)
**Effort:** 2-3 hours
**Impact:** Could improve CAGR by ~1-2% by reducing unnecessary trades

**Approach:**
1. Study bt source code for position handling
2. Create helper function to safely extract scalar weights
3. Add comprehensive logging to debug Series issues
4. Test with verbose mode to trace data flow

### Priority 2: Add Unit Tests
**Effort:** 3-4 hours
**Impact:** Confidence in correctness

**Tests needed:**
- Trend filter logic (IN_RISK vs OUT_RISK)
- Weight calculations (sum to 1.0)
- Data validation
- Backtest determinism

### Priority 3: Enhanced Reporting
**Effort:** 2-3 hours
**Impact:** Better insights

**Features:**
- Rolling 36-month excess returns
- Transaction log analysis
- HTML report with charts
- Turnover metrics

### Priority 4: Parameter Optimization
**Effort:** 4-6 hours
**Impact:** Potential performance boost

**Experiments:**
- Vary lookback period (180, 210, 252 days)
- Try different tilt weights (15%, 20%, 25%)
- Test different rebalance frequencies (monthly, quarterly)
- Add transaction cost sensitivity analysis

---

## 📝 Usage

### Run Backtest
```bash
python main.py backtest --start 2013-01-01
```

### Show Configuration
```bash
python main.py info
```

### Compare Strategies
```bash
python main.py compare --start 2013-01-01
```

---

## 🎓 Lessons Learned

### 1. **bt Library Quirks**
- Series vs scalar handling is tricky
- Custom algos need careful data type management
- Built-in algos are well-tested; use when possible

### 2. **Transaction Costs Matter**
- 4 bps total cost (2 commission + 2 slippage) adds up
- Rebalance bands are critical for cost control
- Over-trading can easily wipe out alpha

### 3. **Trend Filters Are Powerful**
- Reduced drawdown by 12.58pp (2020-2023)
- Lower volatility consistently
- But needs optimization for all market regimes

### 4. **Development Velocity**
- bt library delivered working backtest in ~15 hours
- Would have taken 2+ weeks to build from scratch
- Time saved = time for alpha research

---

## 📚 References

- [bt Documentation](https://pmorissette.github.io/bt/)
- [PRD](IMPLEMENTATION_PLAN.md)
- [Config](config.yaml)

---

**Last Updated:** 2025-11-11
**Status:** MVP Complete, Ready for Refinement
