"""Configuration management for portfolio backtesting"""

import yaml
from pathlib import Path
from typing import Dict, List, Any


class Config:
    """Load and validate configuration from YAML file"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Load configuration from YAML file

        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

        self._validate()

    def _validate(self):
        """Validate configuration parameters"""
        # Check required top-level keys
        required_keys = ['region', 'weights', 'tickers', 'rebalance',
                        'trend_filter', 'costs', 'backtest']
        for key in required_keys:
            if key not in self._config:
                raise ValueError(f"Missing required config key: {key}")

        # Validate region
        region = self._config['region']
        if region not in ['US', 'EU']:
            raise ValueError(f"Invalid region: {region}. Must be 'US' or 'EU'")

        # Validate weights sum to ~1.0
        core_weight = self._config['weights']['core']
        tilt_weight = self._config['weights']['tilt_per_factor']
        total = core_weight + (3 * tilt_weight)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total:.4f}")

        # Validate tickers exist for region
        if region not in self._config['tickers']:
            raise ValueError(f"No tickers defined for region: {region}")

        region_tickers = self._config['tickers'][region]
        if len(region_tickers.get('tilts', [])) != 3:
            raise ValueError(f"Must specify exactly 3 tilt factors, got {len(region_tickers.get('tilts', []))}")

    @property
    def region(self) -> str:
        """Get selected region"""
        return self._config['region']

    @property
    def core_weight(self) -> float:
        """Get core allocation weight"""
        return self._config['weights']['core']

    @property
    def tilt_weight(self) -> float:
        """Get per-tilt allocation weight"""
        return self._config['weights']['tilt_per_factor']

    def get_tickers(self, region: str = None) -> Dict[str, Any]:
        """
        Get tickers for specified region

        Args:
            region: Region to get tickers for (defaults to configured region)

        Returns:
            Dictionary with 'core', 'tilts', and 'cash' tickers
        """
        region = region or self.region
        return self._config['tickers'][region]

    def get_all_tickers(self, region: str = None) -> List[str]:
        """
        Get list of all tickers (core + tilts + cash)

        Args:
            region: Region to get tickers for (defaults to configured region)

        Returns:
            List of all ticker symbols
        """
        tickers = self.get_tickers(region)
        return [tickers['core']] + tickers['tilts'] + [tickers['cash']]

    @property
    def lookback_days(self) -> int:
        """Get trend filter lookback period in days"""
        return self._config['trend_filter']['lookback_days']

    @property
    def rebalance_band_pct(self) -> float:
        """Get rebalance band percentage"""
        return self._config['rebalance']['band_pct']

    @property
    def commission_bps(self) -> float:
        """Get commission in basis points"""
        return self._config['costs']['commission_bps']

    @property
    def slippage_bps(self) -> float:
        """Get slippage in basis points"""
        return self._config['costs']['slippage_bps']

    @property
    def start_date(self) -> str:
        """Get backtest start date"""
        return self._config['backtest']['start_date']

    @property
    def initial_capital(self) -> float:
        """Get initial capital"""
        return self._config['backtest']['initial_capital']

    def get(self, key: str, default=None):
        """Get config value by key (supports nested keys with dot notation)"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


# Global config instance
_config = None


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration (singleton pattern)"""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def get_config() -> Config:
    """Get loaded configuration"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
