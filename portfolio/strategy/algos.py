"""Custom bt.Algo implementations for 80/20 strategy"""

import bt
import pandas as pd
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TrendFilterWeights(bt.Algo):
    """
    Apply 10-month SMA trend filter to tilt sleeve

    If tilt composite >= 10-month SMA: allocate to tilt factors
    If tilt composite < 10-month SMA: park tilt sleeve in cash (SHY/BIL)
    """

    def __init__(
        self,
        core_ticker: str,
        core_weight: float,
        tilt_tickers: List[str],
        cash_ticker: str,
        lookback_days: int = 210
    ):
        """
        Initialize trend filter

        Args:
            core_ticker: Core holding (e.g., 'VOO')
            core_weight: Core allocation (e.g., 0.80)
            tilt_tickers: List of tilt factor tickers (e.g., ['QUAL', 'VLUE', 'MTUM'])
            cash_ticker: Cash proxy for defensive positioning (e.g., 'SHY')
            lookback_days: Lookback period for SMA (default 210 ~= 10 months)
        """
        super(TrendFilterWeights, self).__init__()
        self.core_ticker = core_ticker
        self.core_weight = core_weight
        self.tilt_tickers = tilt_tickers
        self.cash_ticker = cash_ticker
        self.lookback = lookback_days
        self.tilt_weight_per_factor = (1 - core_weight) / len(tilt_tickers)

        logger.info(f"TrendFilterWeights: core={core_weight:.1%}, "
                   f"tilt_per_factor={self.tilt_weight_per_factor:.2%}, "
                   f"lookback={lookback_days}d")

    def __call__(self, target):
        """
        Execute trend filter and set target weights

        Args:
            target: bt.Target node

        Returns:
            True to continue to next algo, False to stop
        """
        # Get current date
        now = target.now

        # Get price data up to current date
        prices = target.universe.loc[:now]

        if len(prices) == 0:
            logger.warning(f"No price data available at {now}")
            return False

        # Get tilt factor prices
        tilt_prices = prices[self.tilt_tickers]

        # Compute equal-weighted tilt composite
        composite = tilt_prices.mean(axis=1)

        # Calculate 10-month SMA
        sma = composite.rolling(window=self.lookback, min_periods=self.lookback).mean()

        # Get latest values
        current_composite = composite.iloc[-1]
        current_sma = sma.iloc[-1]

        # Generate signal
        if pd.isna(current_sma):
            # Not enough data yet - default to core only (defensive)
            logger.debug(f"{now}: Insufficient lookback data, defaulting to core only")
            weights = {
                self.core_ticker: self.core_weight,
                self.cash_ticker: 1 - self.core_weight
            }
            signal = "WARMING_UP"

        elif current_composite >= current_sma:
            # IN_RISK: Allocate to tilt factors
            weights = {self.core_ticker: self.core_weight}
            for ticker in self.tilt_tickers:
                weights[ticker] = self.tilt_weight_per_factor

            signal = "IN_RISK"
            logger.debug(f"{now}: {signal} - composite={current_composite:.2f} >= SMA={current_sma:.2f}")

        else:
            # OUT_RISK: Park tilt sleeve in cash
            weights = {
                self.core_ticker: self.core_weight,
                self.cash_ticker: 1 - self.core_weight
            }
            signal = "OUT_RISK"
            logger.debug(f"{now}: {signal} - composite={current_composite:.2f} < SMA={current_sma:.2f}")

        # Verify weights sum to 1.0
        total_weight = sum(weights.values())
        if not np.isclose(total_weight, 1.0, atol=0.001):
            logger.error(f"Weights sum to {total_weight:.4f}, not 1.0!")
            return False

        # Store weights in temp for next algo (keep as dict for LimitWeights)
        target.temp['weights_dict'] = weights
        target.temp['signal'] = signal

        return True


class LimitWeights(bt.Algo):
    """
    Only rebalance if portfolio drift exceeds threshold

    This reduces spurious trades and transaction costs by implementing
    rebalancing bands (e.g., only rebalance if drift > 5%)
    """

    def __init__(self, band_pct: float = 0.05):
        """
        Initialize rebalance bands

        Args:
            band_pct: Drift threshold (e.g., 0.05 = 5%)
        """
        super(LimitWeights, self).__init__()
        self.band_pct = band_pct
        logger.info(f"LimitWeights: band={band_pct:.1%}")

    def __call__(self, target):
        """
        Check if rebalance is needed

        Args:
            target: bt.Target node

        Returns:
            True if rebalance needed, False to skip
        """
        # Get target weights from previous algo
        try:
            target_weights = target.temp.get('weights_dict', None)
        except:
            logger.warning("No target weights found in temp")
            return False

        if target_weights is None:
            logger.warning("No target weights found in temp")
            return False

        # Get current portfolio value and positions
        # On first rebalance, value will be 0 or positions will be empty
        if target.value == 0 or not hasattr(target, 'positions') or len(target.positions) == 0:
            # First rebalance - always execute
            logger.debug(f"{target.now}: First rebalance, executing")
            return True

        # Calculate current weights from positions
        current_weights = {}
        total_value = float(target.value)

        for sec, pos in target.positions.items():
            if hasattr(sec, 'name'):
                ticker = sec.name
            else:
                ticker = str(sec)

            # Ensure pos is a scalar
            if hasattr(pos, 'item'):
                pos = pos.item()

            current_weights[ticker] = float(pos) / total_value

        # Calculate maximum drift across all positions
        max_drift = 0.0
        all_tickers = set(list(target_weights.keys()) + list(current_weights.keys()))
        for ticker in all_tickers:
            target_w = target_weights.get(ticker, 0.0)
            current_w = current_weights.get(ticker, 0.0)

            # Ensure scalar values (in case Series slips through)
            if hasattr(target_w, 'item'):
                target_w = float(target_w)
            if hasattr(current_w, 'item'):
                current_w = float(current_w)

            drift = abs(float(target_w) - float(current_w))
            max_drift = max(max_drift, drift)

        # Check if drift exceeds band
        if max_drift < self.band_pct:
            logger.debug(f"{target.now}: Max drift {max_drift:.2%} < {self.band_pct:.1%}, skipping rebalance")
            return False
        else:
            logger.debug(f"{target.now}: Max drift {max_drift:.2%} >= {self.band_pct:.1%}, rebalancing")
            return True


class WeighTarget(bt.Algo):
    """
    Custom algo to set target weights from temp storage

    This is needed because bt's built-in algos expect weights in a specific format
    """

    def __call__(self, target):
        """Set target weights"""
        # Check if weights were set by previous algo
        try:
            weights_dict = target.temp.get('weights_dict', None)
        except:
            return False

        if weights_dict is None:
            return False

        # Convert dict to Series for bt.algos.Rebalance
        weights = pd.Series(weights_dict)

        # Set the weights for the Rebalance algo to use
        target.temp['weights'] = weights

        return True
