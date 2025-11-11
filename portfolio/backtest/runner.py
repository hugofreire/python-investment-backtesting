"""Backtest runner with transaction costs"""

import bt
import pandas as pd
from typing import Optional, Dict, Any
import logging

from portfolio.config import get_config
from portfolio.data.fetcher import get_data
from portfolio.strategy.builder import create_strategy, create_benchmark

logger = logging.getLogger(__name__)


class BacktestRunner:
    """Run backtests with transaction costs"""

    def __init__(self, config=None):
        """
        Initialize backtest runner

        Args:
            config: Config object (defaults to global config)
        """
        self.config = config or get_config()

    def run(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        region: Optional[str] = None,
        initial_capital: Optional[float] = None,
        include_benchmark: bool = True,
        use_cache: bool = True
    ):
        """
        Run backtest

        Args:
            start_date: Backtest start date (defaults to config)
            end_date: Backtest end date (defaults to today)
            region: Region to test (defaults to config)
            initial_capital: Starting capital (defaults to config)
            include_benchmark: Whether to include benchmark
            use_cache: Whether to use cached data

        Returns:
            bt.Result object with backtest results
        """
        # Set defaults
        start_date = start_date or self.config.start_date
        region = region or self.config.region
        initial_capital = initial_capital or self.config.initial_capital

        logger.info(f"Running backtest:")
        logger.info(f"  Start: {start_date}")
        logger.info(f"  End: {end_date or 'today'}")
        logger.info(f"  Region: {region}")
        logger.info(f"  Initial capital: ${initial_capital:,.0f}")

        # Get data
        tickers = self.config.get_all_tickers(region)
        logger.info(f"Fetching data for {len(tickers)} tickers: {tickers}")

        data = get_data(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache
        )

        logger.info(f"Data: {len(data)} rows from {data.index[0]} to {data.index[-1]}")

        # Create strategies
        strategy = create_strategy(region=region, config=self.config)

        # Create backtests with transaction costs
        commission_bps = self.config.commission_bps
        slippage_bps = self.config.slippage_bps
        total_cost_bps = commission_bps + slippage_bps

        logger.info(f"Transaction costs: {commission_bps} bps commission + {slippage_bps} bps slippage = {total_cost_bps} bps total")

        # Commission function: cost = quantity * price * bps
        def commission_fn(quantity, price):
            """Calculate commission cost"""
            return abs(quantity) * price * (total_cost_bps / 10000.0)

        test = bt.Backtest(
            strategy,
            data,
            initial_capital=initial_capital,
            commissions=commission_fn
        )

        backtests = [test]

        # Add benchmark if requested
        if include_benchmark:
            benchmark = create_benchmark(region=region, config=self.config)
            bench_test = bt.Backtest(
                benchmark,
                data,
                initial_capital=initial_capital,
                commissions=commission_fn
            )
            backtests.append(bench_test)

        # Run!
        logger.info("Running backtest...")
        results = bt.run(*backtests)
        logger.info("Backtest complete!")

        return results

    def run_comparison(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        region: Optional[str] = None,
        initial_capital: Optional[float] = None
    ):
        """
        Run comparison: strategy vs benchmark vs always-invested

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            region: Region to test
            initial_capital: Starting capital

        Returns:
            bt.Result with all strategies
        """
        from portfolio.strategy.builder import create_always_invested_strategy

        # Set defaults
        start_date = start_date or self.config.start_date
        region = region or self.config.region
        initial_capital = initial_capital or self.config.initial_capital

        # Get data
        tickers = self.config.get_all_tickers(region)
        data = get_data(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date
        )

        # Transaction cost function
        total_cost_bps = self.config.commission_bps + self.config.slippage_bps

        def commission_fn(quantity, price):
            return abs(quantity) * price * (total_cost_bps / 10000.0)

        # Create strategies
        strategy = create_strategy(region=region, config=self.config)
        benchmark = create_benchmark(region=region, config=self.config)
        always_invested = create_always_invested_strategy(region=region, config=self.config)

        # Create backtests
        test1 = bt.Backtest(strategy, data, initial_capital=initial_capital, commissions=commission_fn)
        test2 = bt.Backtest(benchmark, data, initial_capital=initial_capital, commissions=commission_fn)
        test3 = bt.Backtest(always_invested, data, initial_capital=initial_capital, commissions=commission_fn)

        # Run
        logger.info("Running comparison backtest (3 strategies)...")
        results = bt.run(test1, test2, test3)
        logger.info("Comparison complete!")

        return results


def run_backtest(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    region: Optional[str] = None,
    initial_capital: Optional[float] = None,
    include_benchmark: bool = True,
    use_cache: bool = True
):
    """
    Convenience function to run backtest

    Args:
        start_date: Backtest start date
        end_date: Backtest end date
        region: Region to test
        initial_capital: Starting capital
        include_benchmark: Include benchmark
        use_cache: Use cached data

    Returns:
        bt.Result object
    """
    runner = BacktestRunner()
    return runner.run(
        start_date=start_date,
        end_date=end_date,
        region=region,
        initial_capital=initial_capital,
        include_benchmark=include_benchmark,
        use_cache=use_cache
    )
