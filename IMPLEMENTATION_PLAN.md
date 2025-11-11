# Implementation Plan: 80/20 Portfolio Backtesting System

## Overview
Build a production-ready portfolio backtesting system using Python's `bt` library to implement an 80/20 Core/Tilt strategy with trend filtering, targeting +1% annual outperformance vs S&P 500.

---

## Phase 1: Project Foundation (Step 1-3)

### Step 1: Project Structure & Dependencies
**Goal:** Set up the project skeleton and install required packages

**Tasks:**
- Create directory structure following the PRD architecture
- Create `requirements.txt` with all dependencies
- Create `.gitignore` for Python projects
- Create initial `README.md` with project description
- Create `config.yaml` with strategy parameters

**Deliverables:**
```
portfolio/
├── config.yaml
├── requirements.txt
├── .gitignore
├── README.md
├── data/
│   ├── __init__.py
│   ├── fetcher.py
│   └── cache/
├── strategy/
│   ├── __init__.py
│   ├── algos.py
│   └── builder.py
├── backtest/
│   ├── __init__.py
│   ├── runner.py
│   └── metrics.py
├── reports/
│   ├── __init__.py
│   └── generator.py
├── tests/
│   ├── __init__.py
│   ├── test_trend_filter.py
│   └── test_backtest.py
└── main.py
```

**Acceptance:**
- [ ] All directories created
- [ ] `requirements.txt` lists all dependencies
- [ ] Config file has all parameters from PRD

---

### Step 2: Configuration Management
**Goal:** Implement configuration loading and validation

**Tasks:**
- Create `config.yaml` with all strategy parameters (weights, tickers, costs, etc.)
- Add configuration validation
- Support both US and EU regions
- Create helper functions to load config

**Implementation:**
```yaml
# config.yaml structure
region: US
weights:
  core: 0.80
  tilt_per_factor: 0.0667
tickers:
  US:
    core: VOO
    tilts: [QUAL, VLUE, MTUM]
    cash: SHY
rebalance:
  frequency: quarterly
  band_pct: 0.05
trend_filter:
  lookback_days: 210
costs:
  commission_bps: 2
  slippage_bps: 2
backtest:
  start_date: '2013-01-01'
  initial_capital: 100000
```

**Acceptance:**
- [ ] Config loads successfully
- [ ] Validation catches invalid parameters
- [ ] Both US/EU regions supported

---

### Step 3: Data Fetcher (yfinance)
**Goal:** Implement data fetching using yfinance for quick MVP

**File:** `data/fetcher.py`

**Tasks:**
- Implement `get_data()` function
- Download adjusted prices (handles splits/dividends)
- Add basic error handling
- Cache data to avoid repeated downloads
- Validate data quality (no missing dates, NaNs)

**Key Functions:**
```python
def get_data(start_date, region='US', cache=True):
    """Fetch adjusted price data for all tickers"""
    pass

def validate_data(df):
    """Check for missing data, gaps, etc."""
    pass
```

**Acceptance:**
- [ ] Successfully downloads data for all US tickers
- [ ] Returns pandas DataFrame with adjusted close prices
- [ ] Handles missing data gracefully
- [ ] Data validation catches issues

---

## Phase 2: Core Strategy Logic (Step 4-6)

### Step 4: Custom bt Algorithms - Trend Filter
**Goal:** Implement the 10-month SMA trend filter

**File:** `strategy/algos.py`

**Tasks:**
- Implement `TrendFilterWeights` class (inherits from `bt.Algo`)
- Calculate tilt composite (equal-weight average of QUAL/VLUE/MTUM)
- Calculate 10-month (210-day) SMA of composite
- Generate signal: IN_RISK if composite >= SMA, else OUT_RISK
- Set target weights based on signal:
  - IN_RISK: 80% VOO + 6.67% each tilt
  - OUT_RISK: 80% VOO + 20% SHY (cash)

**Key Implementation:**
```python
class TrendFilterWeights(bt.Algo):
    """Apply 10-month SMA trend filter to tilt sleeve"""

    def __init__(self, core_weight=0.80, tilt_tickers=None,
                 cash_ticker='SHY', lookback_days=210):
        pass

    def __call__(self, target):
        # Compute tilt composite
        # Calculate SMA
        # Generate signal
        # Set weights
        pass
```

**Acceptance:**
- [ ] Filter correctly identifies IN_RISK vs OUT_RISK states
- [ ] Weights sum to 1.0
- [ ] Handles initial period (< 210 days) correctly
- [ ] Works with both US and EU tickers

---

### Step 5: Custom bt Algorithms - Rebalance Bands
**Goal:** Implement 5% rebalance bands to reduce spurious trades

**File:** `strategy/algos.py`

**Tasks:**
- Implement `LimitWeights` class
- Compare current portfolio weights to target weights
- Only proceed with rebalance if max drift > 5%
- Track rebalance decisions for reporting

**Key Implementation:**
```python
class LimitWeights(bt.Algo):
    """Only rebalance if drift exceeds band_pct threshold"""

    def __init__(self, band_pct=0.05):
        pass

    def __call__(self, target):
        # Get target and current weights
        # Calculate max drift
        # Return True if drift > band, else False
        pass
```

**Acceptance:**
- [ ] Skips rebalance when drift < 5%
- [ ] Triggers rebalance when drift >= 5%
- [ ] Works correctly on first rebalance (no current weights)

---

### Step 6: Strategy Builder
**Goal:** Assemble all algos into complete bt.Strategy

**File:** `strategy/builder.py`

**Tasks:**
- Implement `create_strategy(region)` function
- Combine all bt.Algos in correct order:
  1. `RunQuarterly()` - timing
  2. `SelectThese()` - universe selection
  3. `TrendFilterWeights()` - custom signal
  4. `LimitWeights()` - band filter
  5. `Rebalance()` - execution
- Create benchmark strategy (buy & hold core)
- Add strategy validation

**Key Implementation:**
```python
def create_strategy(region='US'):
    """Build 80/20 strategy with trend filter"""

    strategy = bt.Strategy('80/20-Trend', [
        bt.algos.RunQuarterly(run_on_end_of_period=True),
        bt.algos.SelectThese(all_tickers),
        TrendFilterWeights(...),
        LimitWeights(band_pct=0.05),
        bt.algos.Rebalance()
    ])

    return strategy

def create_benchmark(region='US'):
    """Buy & hold benchmark"""
    pass
```

**Acceptance:**
- [ ] Strategy object created successfully
- [ ] Algos execute in correct order
- [ ] Benchmark created for comparison
- [ ] Works for both US and EU

---

## Phase 3: Backtesting Engine (Step 7-8)

### Step 7: Backtest Runner
**Goal:** Execute backtests with transaction costs

**File:** `backtest/runner.py`

**Tasks:**
- Implement `run_backtest()` function
- Create bt.Backtest with strategy
- Add commission costs (2 bps per trade)
- Add slippage costs (2 bps per trade)
- Run against benchmark
- Return bt.Result object

**Key Implementation:**
```python
def run_backtest(start_date='2013-01-01', region='US', initial_capital=100000):
    """Execute backtest and return results"""

    # Get data
    data = get_data(start_date, region)

    # Create strategy and benchmark
    strategy = create_strategy(region)
    benchmark = create_benchmark(region)

    # Create backtests with costs
    test = bt.Backtest(
        strategy,
        data,
        initial_capital=initial_capital,
        commissions=lambda q, p: abs(q) * p * 0.0002,  # 2 bps
    )

    bench = bt.Backtest(benchmark, data)

    # Run
    results = bt.run(test, bench)

    return results
```

**Acceptance:**
- [ ] Backtest executes without errors
- [ ] Transaction costs applied correctly
- [ ] Results object contains both strategy and benchmark
- [ ] Performance metrics available

---

### Step 8: Custom Metrics
**Goal:** Calculate additional performance metrics

**File:** `backtest/metrics.py`

**Tasks:**
- Implement rolling excess returns (36-month)
- Calculate annual turnover
- Compute drawdown comparison
- Calculate hit rate (% of time beating benchmark)
- Add statistical tests (t-test for significance)

**Key Functions:**
```python
def calculate_rolling_excess(results, window_months=36):
    """Calculate rolling excess returns vs benchmark"""
    pass

def calculate_turnover(results):
    """Annual turnover from transaction log"""
    pass

def calculate_hit_rate(results):
    """% of periods with positive excess return"""
    pass

def generate_metrics_summary(results):
    """Combine all custom metrics"""
    pass
```

**Acceptance:**
- [ ] Rolling excess returns calculated correctly
- [ ] Turnover matches transaction log
- [ ] All metrics validate against manual calculations

---

## Phase 4: Reporting & Validation (Step 9-10)

### Step 9: Report Generator
**Goal:** Create comprehensive HTML/text reports

**File:** `reports/generator.py`

**Tasks:**
- Use bt's built-in `results.display()` and `results.plot()`
- Add custom charts (rolling excess, drawdown comparison)
- Create HTML report with all metrics
- Add transaction log summary
- Export key metrics to JSON

**Key Functions:**
```python
def generate_report(results, output_path='report.html'):
    """Generate comprehensive backtest report"""

    # Built-in metrics
    # Custom metrics
    # Charts
    # Transaction log
    # Save to HTML
    pass

def print_summary(results):
    """Print key metrics to console"""
    pass
```

**Deliverables:**
- HTML report with:
  - Performance summary table
  - Equity curve chart
  - Drawdown chart
  - Rolling excess returns
  - Transaction log
  - Statistical tests

**Acceptance:**
- [ ] HTML report generates successfully
- [ ] All charts render correctly
- [ ] Metrics match acceptance criteria from PRD

---

### Step 10: Validation Against Acceptance Criteria
**Goal:** Verify backtest meets all requirements from PRD

**Tasks:**
- Run full backtest 2013-01-01 to present
- Validate against acceptance criteria:
  - [ ] Net CAGR vs VOO ≥ +0.6%
  - [ ] Max drawdown ≤ S&P +10%
  - [ ] Sharpe ratio ≥ VOO
  - [ ] Trades/year ≤ 12
  - [ ] 36-month rolling excess positive ≥ 55%
- Verify data quality:
  - [ ] Adjusted prices used
  - [ ] First signal waits for 210-day lookback
  - [ ] Quarterly rebalances (Mar/Jun/Sep/Dec)
  - [ ] 5% bands prevent spurious trades
  - [ ] Transaction costs applied
  - [ ] Benchmark uses same data

**Deliverables:**
- Validation report with pass/fail for each criterion
- Debug any failures
- Document any deviations from expected results

---

## Phase 5: CLI & Testing (Step 11-12)

### Step 11: Command-Line Interface
**Goal:** Create user-friendly CLI

**File:** `main.py`

**Tasks:**
- Implement CLI using `argparse` or `click`
- Add commands:
  - `backtest` - Run backtest
  - `report` - Generate report
  - `weights` - Show current target weights
  - `compare` - Compare regions
- Add logging
- Add progress indicators

**Usage:**
```bash
python main.py backtest --start 2013-01-01 --region US
python main.py report --output report.html
python main.py weights --live
python main.py compare --regions US EU
```

**Acceptance:**
- [ ] All commands work correctly
- [ ] Help text is clear
- [ ] Errors are user-friendly
- [ ] Logging provides visibility

---

### Step 12: Unit Tests
**Goal:** Ensure code reliability

**File:** `tests/test_*.py`

**Tasks:**
- Test trend filter logic:
  - [ ] IN_RISK when composite > SMA
  - [ ] OUT_RISK when composite < SMA
  - [ ] Correct weight allocation in each state
- Test rebalance bands:
  - [ ] Skip rebalance when drift < 5%
  - [ ] Trigger rebalance when drift ≥ 5%
- Test backtest determinism:
  - [ ] Same inputs → same outputs
- Test data validation:
  - [ ] Detects missing data
  - [ ] Handles edge cases

**Run Tests:**
```bash
pytest tests/ -v
```

**Acceptance:**
- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Edge cases handled

---

## Phase 6: Documentation & Polish (Step 13-14)

### Step 13: Documentation
**Goal:** Create comprehensive docs

**Tasks:**
- Write detailed README.md:
  - Project overview
  - Installation instructions
  - Quick start guide
  - Configuration options
  - CLI usage
  - Examples
- Add docstrings to all functions
- Create architecture diagram
- Document strategy logic
- Add FAQ section

**Acceptance:**
- [ ] README is complete and clear
- [ ] New users can get started in < 10 minutes
- [ ] All functions have docstrings

---

### Step 14: Final Polish & Optimization
**Goal:** Production-ready code

**Tasks:**
- Add type hints to all functions
- Format code with `black`
- Lint with `pylint` or `flake8`
- Optimize slow operations (caching, vectorization)
- Add error handling for edge cases
- Create example configs for different scenarios
- Add GitHub Actions for CI/CD (optional)

**Acceptance:**
- [ ] Code is clean and well-formatted
- [ ] No linting errors
- [ ] Performance is acceptable (backtest < 30s)

---

## Success Metrics

### Technical Requirements Met
- [x] Uses `bt` library for backtesting
- [x] Implements 80/20 Core/Tilt allocation
- [x] 10-month SMA trend filter on tilt composite
- [x] Quarterly rebalancing with 5% bands
- [x] Transaction costs (2 bps commission + 2 bps slippage)
- [x] Supports both US and EU regions

### Performance Requirements Met (from PRD)
- [ ] Net CAGR vs VOO ≥ +0.6%/year
- [ ] Max drawdown ≤ S&P +10%
- [ ] Sharpe ratio ≥ VOO
- [ ] Trades/year ≤ 12
- [ ] 36-month rolling excess positive ≥ 55%

### Code Quality
- [ ] ~500 LOC for core functionality
- [ ] 80%+ test coverage
- [ ] All functions documented
- [ ] No linting errors
- [ ] Type hints on public functions

---

## Estimated Timeline

| Phase | Steps | Time | Cumulative |
|-------|-------|------|------------|
| 1. Foundation | 1-3 | 2 hours | 2 hours |
| 2. Strategy Logic | 4-6 | 4 hours | 6 hours |
| 3. Backtesting | 7-8 | 2 hours | 8 hours |
| 4. Reporting | 9-10 | 2 hours | 10 hours |
| 5. CLI & Testing | 11-12 | 3 hours | 13 hours |
| 6. Documentation | 13-14 | 2 hours | 15 hours |

**Total: ~15 hours to production-ready system**

---

## Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Start with Step 1** - Set up project structure
3. **Implement incrementally** - Commit after each step
4. **Test continuously** - Validate each component
5. **Iterate** - Refine based on backtest results

---

## Open Questions

1. **Data source preference:** Start with yfinance or go straight to Tiingo?
   - **Recommendation:** Start with yfinance for MVP, switch to Tiingo later

2. **Reporting format:** HTML only or add PDF/email options?
   - **Recommendation:** HTML for MVP, add PDF in Phase 6

3. **Live trading:** Build broker integration now or later?
   - **Recommendation:** Later - focus on validation first

4. **Parameter optimization:** Run grid search on lookback period?
   - **Recommendation:** Later - use 210 days (10 months) as specified

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data quality issues | High | Validate all data, use adjusted prices, add checks |
| bt library bugs | Medium | Test thoroughly, have fallback manual calculations |
| Performance doesn't meet targets | High | Validate methodology, check for implementation bugs |
| Overfitting to backtest period | High | Use out-of-sample testing, walk-forward analysis |
| Transaction costs too low | Medium | Use conservative estimates (2 bps), sensitivity analysis |

---

**Ready to start implementation!**
