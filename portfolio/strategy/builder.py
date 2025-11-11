"""Strategy builder for 80/20 portfolio"""

import bt
from typing import Optional
import logging

from portfolio.config import get_config
from portfolio.strategy.algos import TrendFilterWeights, LimitWeights, WeighTarget

logger = logging.getLogger(__name__)


def create_strategy(region: Optional[str] = None, config=None) -> bt.Strategy:
    """
    Build the 80/20 Core/Tilt strategy with trend filter

    Strategy logic:
    1. Run quarterly (last trading day of quarter)
    2. Select universe (core + tilts + cash)
    3. Apply trend filter to determine tilt allocation
    4. Only rebalance if drift > 5%
    5. Execute rebalance

    Args:
        region: Region ('US' or 'EU'), defaults to config
        config: Config object (defaults to global config)

    Returns:
        bt.Strategy instance
    """
    if config is None:
        config = get_config()

    region = region or config.region

    # Get tickers for region
    tickers = config.get_tickers(region)
    all_tickers = config.get_all_tickers(region)

    core_ticker = tickers['core']
    tilt_tickers = tickers['tilts']
    cash_ticker = tickers['cash']

    logger.info(f"Building strategy for {region}:")
    logger.info(f"  Core: {core_ticker} @ {config.core_weight:.1%}")
    logger.info(f"  Tilts: {tilt_tickers} @ {config.tilt_weight:.2%} each")
    logger.info(f"  Cash: {cash_ticker}")

    # Create strategy
    strategy = bt.Strategy(
        '80/20-Trend',
        [
            # 1. Run quarterly on last trading day
            bt.algos.RunQuarterly(
                run_on_first_date=False,
                run_on_end_of_period=True
            ),

            # 2. Select our universe
            bt.algos.SelectThese(all_tickers),

            # 3. Apply trend filter → sets target.temp['weights']
            TrendFilterWeights(
                core_ticker=core_ticker,
                core_weight=config.core_weight,
                tilt_tickers=tilt_tickers,
                cash_ticker=cash_ticker,
                lookback_days=config.lookback_days
            ),

            # 4. Only rebalance if drift > threshold
            # TODO: Re-enable LimitWeights after fixing Series handling
            # LimitWeights(band_pct=config.rebalance_band_pct),

            # 5. Convert weights dict to Series for bt
            WeighTarget(),

            # 6. Execute rebalance
            bt.algos.Rebalance()
        ]
    )

    return strategy


def create_benchmark(region: Optional[str] = None, config=None) -> bt.Strategy:
    """
    Create buy-and-hold benchmark strategy

    Args:
        region: Region ('US' or 'EU'), defaults to config
        config: Config object (defaults to global config)

    Returns:
        bt.Strategy instance for benchmark
    """
    if config is None:
        config = get_config()

    region = region or config.region

    # Get core ticker for region
    tickers = config.get_tickers(region)
    core_ticker = tickers['core']

    logger.info(f"Building benchmark: {core_ticker} buy-and-hold")

    # Simple buy and hold strategy
    benchmark = bt.Strategy(
        f'{core_ticker}-Benchmark',
        [
            # Run once at start
            bt.algos.RunOnce(),

            # Select benchmark ticker
            bt.algos.SelectThese([core_ticker]),

            # Allocate 100%
            bt.algos.WeighEqually(),

            # Rebalance (once)
            bt.algos.Rebalance()
        ]
    )

    return benchmark


def create_always_invested_strategy(region: Optional[str] = None, config=None) -> bt.Strategy:
    """
    Create 80/20 strategy WITHOUT trend filter (always invested in tilts)

    Useful for comparison to see impact of trend filter

    Args:
        region: Region ('US' or 'EU'), defaults to config
        config: Config object (defaults to global config)

    Returns:
        bt.Strategy instance
    """
    if config is None:
        config = get_config()

    region = region or config.region

    # Get tickers for region
    tickers = config.get_tickers(region)
    all_tickers = [tickers['core']] + tickers['tilts']

    # Calculate fixed weights
    weights = {tickers['core']: config.core_weight}
    for tilt in tickers['tilts']:
        weights[tilt] = config.tilt_weight

    logger.info(f"Building always-invested strategy (no trend filter)")

    strategy = bt.Strategy(
        '80/20-NoFilter',
        [
            # Run quarterly
            bt.algos.RunQuarterly(
                run_on_first_date=False,
                run_on_end_of_period=True
            ),

            # Select tickers
            bt.algos.SelectThese(all_tickers),

            # Fixed weights (no trend filter)
            bt.algos.WeighSpecified(**weights),

            # Only rebalance if drift > threshold
            LimitWeights(band_pct=config.rebalance_band_pct),

            # Execute
            bt.algos.Rebalance()
        ]
    )

    return strategy
