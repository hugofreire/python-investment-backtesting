"""Crypto data fetching module using yfinance (supports BTC-USD, ETH-USD, etc.)"""

import pandas as pd
import yfinance as yf
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class CryptoDataFetcher:
    """
    Fetch cryptocurrency data using yfinance

    Supports major crypto pairs like:
    - BTC-USD, ETH-USD, SOL-USD (Coinbase/Binance data)
    - GBTC, ETHE (Grayscale trusts)
    - BITO, BTCW (Bitcoin ETFs)
    """

    def __init__(self, cache_dir: str = "portfolio/data/cache"):
        """
        Initialize crypto data fetcher

        Args:
            cache_dir: Directory for caching data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def normalize_crypto_ticker(self, ticker: str) -> str:
        """
        Normalize crypto ticker to yfinance format

        Examples:
            BTC -> BTC-USD
            ETH -> ETH-USD
            bitcoin -> BTC-USD

        Args:
            ticker: Crypto ticker symbol

        Returns:
            Normalized ticker for yfinance
        """
        # Common crypto mappings
        crypto_map = {
            'BTC': 'BTC-USD',
            'BITCOIN': 'BTC-USD',
            'ETH': 'ETH-USD',
            'ETHEREUM': 'ETH-USD',
            'SOL': 'SOL-USD',
            'SOLANA': 'SOL-USD',
            'ADA': 'ADA-USD',
            'CARDANO': 'ADA-USD',
            'DOT': 'DOT-USD',
            'POLKADOT': 'DOT-USD',
            'AVAX': 'AVAX-USD',
            'AVALANCHE': 'AVAX-USD',
            'MATIC': 'MATIC-USD',
            'POLYGON': 'MATIC-USD',
            'LINK': 'LINK-USD',
            'CHAINLINK': 'LINK-USD',
            'UNI': 'UNI-USD',
            'UNISWAP': 'UNI-USD',
            'ATOM': 'ATOM-USD',
            'COSMOS': 'ATOM-USD',
        }

        # Convert to uppercase for lookup
        ticker_upper = ticker.upper()

        # If already in format XXX-USD, return as-is
        if '-USD' in ticker_upper:
            return ticker_upper

        # Check if in mapping
        if ticker_upper in crypto_map:
            return crypto_map[ticker_upper]

        # Default: assume it's a crypto symbol and append -USD
        return f"{ticker_upper}-USD"

    def get_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        use_cache: bool = True,
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Fetch crypto price data

        Args:
            tickers: List of crypto ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today
            use_cache: Whether to use cached data
            normalize: Whether to normalize ticker symbols (BTC -> BTC-USD)

        Returns:
            DataFrame with adjusted close prices
        """
        # Normalize tickers if requested
        if normalize:
            original_tickers = tickers.copy()
            tickers = [self.normalize_crypto_ticker(t) for t in tickers]
            logger.info(f"Normalized tickers: {dict(zip(original_tickers, tickers))}")

        cache_file = self._get_cache_path(tickers, start_date, end_date)

        # Try to load from cache
        if use_cache and cache_file.exists():
            logger.info(f"Loading crypto data from cache: {cache_file}")
            try:
                data = pd.read_parquet(cache_file)
                if self._validate_data(data, tickers):
                    return data
                else:
                    logger.warning("Cached data failed validation, re-fetching...")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}, re-fetching...")

        # Fetch from yfinance
        logger.info(f"Fetching crypto data for {len(tickers)} tickers from {start_date}")
        try:
            data = yf.download(
                tickers,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=False,  # Crypto doesn't need adjustment
                threads=True
            )

            # Handle single ticker
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
                logger.info(f"Cached crypto data to: {cache_file}")

            return data

        except Exception as e:
            logger.error(f"Failed to fetch crypto data: {e}")
            raise

    def _validate_data(self, data: pd.DataFrame, tickers: List[str]) -> bool:
        """
        Validate crypto data quality

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

        # Check for excessive NaN values (crypto can have gaps during early days)
        for ticker in tickers:
            nan_pct = data[ticker].isna().sum() / len(data)
            if nan_pct > 0.15:  # 15% threshold (more lenient for crypto)
                logger.error(f"{ticker} has {nan_pct:.1%} missing values")
                return False

        # Check for zero/negative prices
        if (data <= 0).any().any():
            logger.error("Data contains zero or negative prices")
            return False

        # Check we have reasonable amount of data
        if len(data) < 30:  # At least 30 days
            logger.error(f"Insufficient data: only {len(data)} rows")
            return False

        logger.info(f"Crypto data validation passed: {len(data)} rows, {len(tickers)} tickers")
        return True

    def _get_cache_path(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str]
    ) -> Path:
        """Generate cache file path"""
        tickers_str = "_".join(sorted(tickers))
        end_str = end_date or "latest"
        filename = f"crypto_{tickers_str}_{start_date}_{end_str}.parquet"
        # Truncate if too long
        if len(filename) > 200:
            filename = f"crypto_cache_{hash(filename)}.parquet"
        return self.cache_dir / filename


def get_crypto_data(
    tickers: List[str],
    start_date: str,
    end_date: Optional[str] = None,
    use_cache: bool = True,
    normalize: bool = True
) -> pd.DataFrame:
    """
    Convenience function to fetch crypto data

    Args:
        tickers: List of crypto ticker symbols (e.g., ['BTC', 'ETH', 'SOL'])
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), defaults to today
        use_cache: Whether to use cached data
        normalize: Whether to normalize symbols (BTC -> BTC-USD)

    Returns:
        DataFrame with crypto prices
    """
    fetcher = CryptoDataFetcher()
    return fetcher.get_data(tickers, start_date, end_date, use_cache, normalize)
