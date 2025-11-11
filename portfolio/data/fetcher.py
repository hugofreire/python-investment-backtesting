"""Data fetching module using yfinance"""

import pandas as pd
import yfinance as yf
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetch and validate historical price data"""

    def __init__(self, cache_dir: str = "portfolio/data/cache"):
        """
        Initialize data fetcher

        Args:
            cache_dir: Directory for caching data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch adjusted close prices for tickers

        Args:
            tickers: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with adjusted close prices (columns = tickers)
        """
        cache_file = self._get_cache_path(tickers, start_date, end_date)

        # Try to load from cache
        if use_cache and cache_file.exists():
            logger.info(f"Loading data from cache: {cache_file}")
            try:
                data = pd.read_parquet(cache_file)
                if self._validate_data(data, tickers):
                    return data
                else:
                    logger.warning("Cached data failed validation, re-fetching...")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}, re-fetching...")

        # Fetch from yfinance
        logger.info(f"Fetching data for {len(tickers)} tickers from {start_date}")
        try:
            data = yf.download(
                tickers,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True,  # Get adjusted prices (handles splits/dividends)
                threads=True
            )

            # Handle single ticker (yfinance returns Series instead of DataFrame)
            if len(tickers) == 1:
                data = data[['Close']].rename(columns={'Close': tickers[0]})
            else:
                # Multi-ticker: get Close prices
                data = data['Close']

            # Ensure we have all tickers as columns
            if isinstance(data, pd.Series):
                data = data.to_frame(name=tickers[0])

            # Validate data
            if not self._validate_data(data, tickers):
                raise ValueError("Downloaded data failed validation")

            # Cache the data
            if use_cache:
                data.to_parquet(cache_file)
                logger.info(f"Cached data to: {cache_file}")

            return data

        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            raise

    def _validate_data(self, data: pd.DataFrame, tickers: List[str]) -> bool:
        """
        Validate data quality

        Args:
            data: DataFrame to validate
            tickers: Expected ticker symbols

        Returns:
            True if data is valid
        """
        if data is None or data.empty:
            logger.error("Data is empty")
            return False

        # Check we have all tickers
        missing_tickers = set(tickers) - set(data.columns)
        if missing_tickers:
            logger.error(f"Missing tickers: {missing_tickers}")
            return False

        # Check for excessive NaN values
        for ticker in tickers:
            nan_pct = data[ticker].isna().sum() / len(data)
            if nan_pct > 0.05:  # More than 5% missing
                logger.error(f"{ticker} has {nan_pct:.1%} missing values")
                return False

        # Check for zero/negative prices
        if (data <= 0).any().any():
            logger.error("Data contains zero or negative prices")
            return False

        # Check we have reasonable amount of data
        if len(data) < 100:
            logger.error(f"Insufficient data: only {len(data)} rows")
            return False

        logger.info(f"Data validation passed: {len(data)} rows, {len(tickers)} tickers")
        return True

    def _get_cache_path(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str]
    ) -> Path:
        """Generate cache file path based on parameters"""
        tickers_str = "_".join(sorted(tickers))
        end_str = end_date or "latest"
        filename = f"{tickers_str}_{start_date}_{end_str}.parquet"
        # Truncate if too long
        if len(filename) > 200:
            filename = f"cache_{hash(filename)}.parquet"
        return self.cache_dir / filename


def get_data(
    tickers: List[str],
    start_date: str,
    end_date: Optional[str] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Convenience function to fetch data

    Args:
        tickers: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), defaults to today
        use_cache: Whether to use cached data

    Returns:
        DataFrame with adjusted close prices
    """
    fetcher = DataFetcher()
    return fetcher.get_data(tickers, start_date, end_date, use_cache)
