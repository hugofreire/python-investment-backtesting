#!/usr/bin/env python3
"""
80/20 Portfolio Backtesting System
Command-line interface
"""

import argparse
import logging
import sys
from pathlib import Path

# Add portfolio to path
sys.path.insert(0, str(Path(__file__).parent))

from portfolio.config import load_config
from portfolio.backtest.runner import BacktestRunner


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def cmd_backtest(args):
    """Run backtest command"""
    setup_logging(args.verbose)

    # Load config
    config = load_config(args.config)

    # Override config with CLI args
    region = args.region or config.region
    start_date = args.start or config.start_date
    initial_capital = args.capital or config.initial_capital

    # Run backtest
    runner = BacktestRunner(config)
    results = runner.run(
        start_date=start_date,
        end_date=args.end,
        region=region,
        initial_capital=initial_capital,
        include_benchmark=not args.no_benchmark,
        use_cache=not args.no_cache
    )

    # Display results
    print("\n" + "="*80)
    print("BACKTEST RESULTS")
    print("="*80 + "\n")

    results.display()

    print("\n" + "="*80)

    # Plot if requested
    if args.plot:
        print("\nGenerating plots...")
        results.plot(figsize=(12, 6))
        print("Close the plot window to continue...")

    # Show transactions if requested
    if args.show_trades:
        print("\n" + "="*80)
        print("TRANSACTION LOG")
        print("="*80 + "\n")
        txns = results.get_transactions()
        print(txns.to_string())

    return results


def cmd_compare(args):
    """Run comparison command"""
    setup_logging(args.verbose)

    config = load_config(args.config)

    region = args.region or config.region
    start_date = args.start or config.start_date

    runner = BacktestRunner(config)
    results = runner.run_comparison(
        start_date=start_date,
        end_date=args.end,
        region=region
    )

    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80 + "\n")

    results.display()

    if args.plot:
        results.plot(figsize=(12, 6))

    return results


def cmd_info(args):
    """Show configuration info"""
    config = load_config(args.config)

    print("\n" + "="*80)
    print("CONFIGURATION")
    print("="*80 + "\n")

    print(f"Region: {config.region}")
    print(f"Start Date: {config.start_date}")
    print(f"Initial Capital: ${config.initial_capital:,.0f}")
    print()

    print("Portfolio Allocation:")
    print(f"  Core: {config.core_weight:.1%}")
    print(f"  Tilt (per factor): {config.tilt_weight:.2%}")
    print()

    tickers = config.get_tickers()
    print(f"Tickers ({config.region}):")
    print(f"  Core: {tickers['core']}")
    print(f"  Tilts: {', '.join(tickers['tilts'])}")
    print(f"  Cash: {tickers['cash']}")
    print()

    print("Strategy Parameters:")
    print(f"  Trend Lookback: {config.lookback_days} days (~10 months)")
    print(f"  Rebalance Band: {config.rebalance_band_pct:.1%}")
    print(f"  Commission: {config.commission_bps} bps")
    print(f"  Slippage: {config.slippage_bps} bps")
    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='80/20 Portfolio Backtesting System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run backtest with defaults from config.yaml
  python main.py backtest

  # Run backtest for specific period
  python main.py backtest --start 2015-01-01 --end 2023-12-31

  # Run backtest for EU region
  python main.py backtest --region EU

  # Show configuration
  python main.py info

  # Compare strategies
  python main.py compare --plot
        """
    )

    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest')
    backtest_parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('--region', choices=['US', 'EU'], help='Region')
    backtest_parser.add_argument('--capital', type=float, help='Initial capital')
    backtest_parser.add_argument('--no-benchmark', action='store_true', help='Skip benchmark')
    backtest_parser.add_argument('--no-cache', action='store_true', help='Disable data caching')
    backtest_parser.add_argument('--plot', action='store_true', help='Show plots')
    backtest_parser.add_argument('--show-trades', action='store_true', help='Show transaction log')
    backtest_parser.set_defaults(func=cmd_backtest)

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare strategies')
    compare_parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    compare_parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    compare_parser.add_argument('--region', choices=['US', 'EU'], help='Region')
    compare_parser.add_argument('--plot', action='store_true', help='Show plots')
    compare_parser.set_defaults(func=cmd_compare)

    # Info command
    info_parser = subparsers.add_parser('info', help='Show configuration')
    info_parser.set_defaults(func=cmd_info)

    # Parse and execute
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    try:
        args.func(args)
        return 0
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
