"""
Tools and utilities module for portfolio analysis calculations.

Provides functions for:
- Risk metric calculations (volatility, VaR, Sharpe ratio, etc.)
- Correlation and concentration analysis
- Sentiment analysis on financial news
- Data validation and transformation
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

from models import Portfolio, Position, RiskMetrics, PortfolioMetrics


logger = logging.getLogger(__name__)


class RiskCalculationTools:
    """
    Suite of risk calculation tools for portfolio analysis.
    All calculations follow institutional portfolio management standards.
    """

    @staticmethod
    def calculate_portfolio_volatility(
        daily_returns: List[float], trading_days_per_year: int = 252
    ) -> float:
        """
        Calculate annualized portfolio volatility (standard deviation of returns).

        Standard formula: σ_annual = σ_daily * sqrt(252)

        Args:
            daily_returns: List of daily portfolio return percentages
            trading_days_per_year: Trading days per year (default: 252 US markets)

        Returns:
            Annualized volatility as percentage (e.g., 15.5 for 15.5%)
        """
        if len(daily_returns) < 2:
            logger.warning("Insufficient data for volatility calculation")
            return 0.0

        daily_volatility = statistics.stdev(daily_returns)
        annual_volatility = daily_volatility * np.sqrt(trading_days_per_year)
        return annual_volatility * 100  # Convert to percentage

    @staticmethod
    def calculate_sharpe_ratio(
        portfolio_returns: List[float],
        risk_free_rate: float = 2.5,
        trading_days_per_year: int = 252,
    ) -> float:
        """
        Calculate Sharpe Ratio: (Return - Risk-Free Rate) / Volatility

        Measures excess return per unit of total risk taken.
        Higher Sharpe ratio indicates better risk-adjusted returns.

        Args:
            portfolio_returns: List of daily portfolio returns (as decimals, e.g., 0.01 for 1%)
            risk_free_rate: Annual risk-free rate in percentage (default: 2.5%)
            trading_days_per_year: Trading days per year

        Returns:
            Sharpe ratio (typically 0.5-2.0 is good, >1.0 is excellent)
        """
        if len(portfolio_returns) < 2:
            return 0.0

        annual_return = statistics.mean(portfolio_returns) * trading_days_per_year * 100
        annual_volatility = (
            statistics.stdev(portfolio_returns) * np.sqrt(trading_days_per_year) * 100
        )

        if annual_volatility == 0:
            return 0.0

        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
        return max(-10, min(10, sharpe_ratio))  # Cap between -10 and 10

    @staticmethod
    def calculate_sortino_ratio(
        portfolio_returns: List[float],
        target_return: float = 0.0,
        trading_days_per_year: int = 252,
    ) -> float:
        """
        Calculate Sortino Ratio: (Return - Target) / Downside Deviation

        Similar to Sharpe but only penalizes downside volatility (losses).
        More relevant for asymmetric risk analysis.

        Args:
            portfolio_returns: List of daily returns (as decimals)
            target_return: Target return threshold (default: 0% - avoid losses)
            trading_days_per_year: Trading days per year

        Returns:
            Sortino ratio (higher is better for downside risk management)
        """
        if len(portfolio_returns) < 2:
            return 0.0

        excess_returns = [
            r - (target_return / trading_days_per_year) for r in portfolio_returns
        ]
        downside_returns = [r for r in excess_returns if r < 0]

        if not downside_returns:
            return 10.0  # No downside risk - maximum score

        downside_deviation = statistics.stdev(downside_returns) * np.sqrt(
            trading_days_per_year
        )
        annual_return = statistics.mean(portfolio_returns) * trading_days_per_year * 100

        if downside_deviation == 0:
            return 0.0

        sortino_ratio = (annual_return - target_return) / (downside_deviation * 100)
        return max(-10, min(10, sortino_ratio))

    @staticmethod
    def calculate_value_at_risk(
        portfolio_returns: List[float],
        confidence_level: float = 0.95,
        return_percentage: bool = True,
    ) -> float:
        """
        Calculate Value-at-Risk (VaR) - maximum expected loss at confidence level.

        VaR represents the worst expected loss over a given time period
        with a specified confidence level (e.g., 95% confident loss won't exceed this).

        Args:
            portfolio_returns: List of daily portfolio returns (as decimals)
            confidence_level: Confidence level (default: 0.95 = 95%)
            return_percentage: Whether to return as percentage

        Returns:
            Value-at-Risk (negative value represents loss)
        """
        if len(portfolio_returns) < 10:
            logger.warning("Insufficient data for VaR calculation")
            return 0.0

        sorted_returns = sorted(portfolio_returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        var = sorted_returns[index]

        return var * 100 if return_percentage else var

    @staticmethod
    def calculate_conditional_var(
        portfolio_returns: List[float], confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional Value-at-Risk (CVaR) / Expected Shortfall.

        Average of all losses worse than the VaR threshold.
        More conservative than VaR for risk management.

        Args:
            portfolio_returns: List of daily returns
            confidence_level: Confidence level

        Returns:
            Conditional VaR (average of worst returns beyond VaR)
        """
        if len(portfolio_returns) < 10:
            return 0.0

        var = RiskCalculationTools.calculate_value_at_risk(
            portfolio_returns, confidence_level, return_percentage=False
        )
        worst_returns = [r for r in portfolio_returns if r <= var]

        if not worst_returns:
            return var * 100

        cvar = statistics.mean(worst_returns) * 100
        return cvar

    @staticmethod
    def calculate_maximum_drawdown(cumulative_returns: List[float]) -> float:
        """
        Calculate Maximum Drawdown - largest peak-to-trough decline.

        Represents the worst timing - buying at peak and selling at trough.
        Important for understanding worst-case historical scenario.

        Args:
            cumulative_returns: List of cumulative return values over time

        Returns:
            Maximum drawdown as percentage (e.g., -25.5 for -25.5% drop)
        """
        if len(cumulative_returns) < 2:
            return 0.0

        peak = cumulative_returns[0]
        max_drawdown = 0.0

        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = (value - peak) / peak if peak != 0 else 0
            if drawdown < max_drawdown:
                max_drawdown = drawdown

        return max_drawdown * 100

    @staticmethod
    def calculate_beta(
        asset_returns: List[float], market_returns: List[float]
    ) -> float:
        """
        Calculate Beta - systematic risk relative to market.

        Beta = Cov(Asset, Market) / Var(Market)
        Beta > 1: More volatile than market (riskier)
        Beta < 1: Less volatile than market (more stable)
        Beta = 1: Moves exactly with market

        Args:
            asset_returns: Daily returns of asset/portfolio
            market_returns: Daily returns of market benchmark

        Returns:
            Beta coefficient
        """
        if len(asset_returns) != len(market_returns) or len(asset_returns) < 2:
            return 1.0  # Return neutral beta

        asset_array = np.array(asset_returns)
        market_array = np.array(market_returns)

        covariance = np.cov(asset_array, market_array)[0, 1]
        market_variance = np.var(market_array)

        if market_variance == 0:
            return 1.0

        beta = covariance / market_variance
        return beta


class ConcentrationAnalysisTools:
    """
    Tools for analyzing portfolio concentration risks.
    """

    @staticmethod
    def calculate_herfindahl_index(allocations: List[float]) -> float:
        """
        Calculate Herfindahl-Hirschman Index (HHI) - concentration metric.

        HHI = Sum(allocation_i^2)
        Range: 1/n to 1 (where n = number of positions)
        Lower = more diversified, Higher = more concentrated

        Args:
            allocations: List of allocation percentages (as decimals, e.g., 0.05 for 5%)

        Returns:
            HHI concentration index (0-1, higher = more concentrated)
        """
        if not allocations:
            return 0.0

        hhi = sum(a**2 for a in allocations)
        return hhi

    @staticmethod
    def calculate_position_concentration(
        positions: List[Position], portfolio_value: float
    ) -> Dict[str, float]:
        """
        Calculate concentration for each position.

        Args:
            positions: List of portfolio positions
            portfolio_value: Total portfolio value

        Returns:
            Dictionary mapping ticker to allocation percentage
        """
        if portfolio_value == 0:
            return {}

        concentration = {}
        for position in positions:
            allocation = (position.current_value / portfolio_value) * 100
            concentration[position.ticker] = allocation

        return concentration

    @staticmethod
    def calculate_sector_concentration(portfolio: Portfolio) -> Dict[str, float]:
        """
        Calculate sector-level concentration.

        Args:
            portfolio: Portfolio object with positions

        Returns:
            Dictionary mapping sector to allocation percentage
        """
        sector_values = defaultdict(float)

        for position in portfolio.positions:
            sector_values[position.sector] += position.current_value

        total_value = portfolio.metrics.total_value
        if total_value == 0:
            return {}

        sector_concentration = {
            sector: (value / total_value) * 100
            for sector, value in sector_values.items()
        }

        return sector_concentration

    @staticmethod
    def identify_concentration_violations(
        portfolio: Portfolio, max_single_position: float, max_sector_exposure: float
    ) -> List[str]:
        """
        Identify positions exceeding concentration limits.

        Args:
            portfolio: Portfolio to analyze
            max_single_position: Maximum allowed position size (%)
            max_sector_exposure: Maximum allowed sector exposure (%)

        Returns:
            List of concentration violation alerts
        """
        alerts = []
        position_concentration = (
            ConcentrationAnalysisTools.calculate_position_concentration(
                portfolio.positions, portfolio.metrics.total_value
            )
        )
        sector_concentration = (
            ConcentrationAnalysisTools.calculate_sector_concentration(portfolio)
        )

        # Check individual positions
        for ticker, allocation in position_concentration.items():
            if allocation > max_single_position:
                alerts.append(
                    f"CONCENTRATION ALERT: {ticker} at {allocation:.2f}% exceeds limit of {max_single_position}%"
                )

        # Check sectors
        for sector, allocation in sector_concentration.items():
            if allocation > max_sector_exposure:
                alerts.append(
                    f"SECTOR ALERT: {sector} at {allocation:.2f}% exceeds limit of {max_sector_exposure}%"
                )

        return alerts


class CorrelationAnalysisTools:
    """
    Tools for analyzing correlation and diversification benefits.
    """

    @staticmethod
    def calculate_correlation_matrix(
        returns_data: Dict[str, List[float]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix between all assets.

        Args:
            returns_data: Dictionary mapping ticker to list of returns

        Returns:
            Correlation matrix as nested dictionaries
        """
        tickers = list(returns_data.keys())
        n = len(tickers)
        correlation_matrix = {}

        for i in range(n):
            ticker1 = tickers[i]
            correlation_matrix[ticker1] = {}

            for j in range(n):
                ticker2 = tickers[j]
                if i == j:
                    correlation_matrix[ticker1][ticker2] = 1.0
                else:
                    returns1 = np.array(returns_data[ticker1])
                    returns2 = np.array(returns_data[ticker2])

                    correlation = np.corrcoef(returns1, returns2)[0, 1]
                    correlation_matrix[ticker1][ticker2] = (
                        correlation if not np.isnan(correlation) else 0.0
                    )

        return correlation_matrix

    @staticmethod
    def identify_high_correlation_pairs(
        correlation_matrix: Dict[str, Dict[str, float]], threshold: float = 0.7
    ) -> List[Tuple[str, str, float]]:
        """
        Identify highly correlated position pairs that reduce diversification.

        Args:
            correlation_matrix: Correlation matrix
            threshold: Correlation threshold for flagging (default: 0.7)

        Returns:
            List of (ticker1, ticker2, correlation) tuples exceeding threshold
        """
        pairs = []
        tickers = list(correlation_matrix.keys())

        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                ticker1, ticker2 = tickers[i], tickers[j]
                correlation = correlation_matrix[ticker1][ticker2]

                if abs(correlation) > threshold:
                    pairs.append((ticker1, ticker2, correlation))

        return pairs


class SentimentAnalysisTools:
    """
    Tools for analyzing financial news and market sentiment.
    """

    @staticmethod
    def parse_sentiment_score(score: float) -> str:
        """
        Convert numerical sentiment score to category.

        Args:
            score: Sentiment score (-1 to 1, typically from NLP model)

        Returns:
            Sentiment category: POSITIVE, NEUTRAL, or NEGATIVE
        """
        if score > 0.1:
            return "POSITIVE"
        elif score < -0.1:
            return "NEGATIVE"
        else:
            return "NEUTRAL"

    @staticmethod
    def aggregate_sentiment(
        sentiment_scores: List[float], weights: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Aggregate multiple sentiment scores into summary metrics.

        Args:
            sentiment_scores: List of individual sentiment scores
            weights: Optional weights for each score (e.g., by recency)

        Returns:
            Dictionary with aggregated sentiment metrics
        """
        if not sentiment_scores:
            return {"overall_sentiment": 0.0, "confidence": 0.0}

        if weights is None:
            weights = [1.0] * len(sentiment_scores)

        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        # Calculate weighted average
        weighted_sentiment = sum(s * w for s, w in zip(sentiment_scores, weights))

        # Calculate confidence as standard deviation (lower = more consensus)
        variance = sum(
            w * (s - weighted_sentiment) ** 2 for s, w in zip(sentiment_scores, weights)
        )
        confidence = 1.0 - (abs(variance) ** 0.5)  # Normalize to 0-1

        return {
            "overall_sentiment": weighted_sentiment,
            "confidence": max(0, confidence),
            "category": SentimentAnalysisTools.parse_sentiment_score(
                weighted_sentiment
            ),
            "sample_size": len(sentiment_scores),
        }


class DataValidationTools:
    """
    Tools for validating portfolio and market data.
    """

    @staticmethod
    def validate_position(position: Position) -> List[str]:
        """
        Validate position data for consistency and reasonableness.

        Args:
            position: Position object to validate

        Returns:
            List of validation warnings/errors (empty if valid)
        """
        errors = []

        if position.shares <= 0:
            errors.append(f"{position.ticker}: Shares must be positive")

        if position.current_price <= 0:
            errors.append(f"{position.ticker}: Current price must be positive")

        if position.entry_price <= 0:
            errors.append(f"{position.ticker}: Entry price must be positive")

        if position.allocation_percent < 0 or position.allocation_percent > 100:
            errors.append(f"{position.ticker}: Allocation must be 0-100%")

        if not position.sector:
            errors.append(f"{position.ticker}: Sector is required")

        return errors

    @staticmethod
    def validate_portfolio(portfolio: Portfolio) -> List[str]:
        """
        Validate complete portfolio data.

        Args:
            portfolio: Portfolio object to validate

        Returns:
            List of validation issues
        """
        errors = []

        # Validate each position
        for position in portfolio.positions:
            errors.extend(DataValidationTools.validate_position(position))

        # Validate allocation sums to approximately 100%
        total_allocation = sum(p.allocation_percent for p in portfolio.positions)
        if abs(total_allocation - 100.0) > 0.1:
            errors.append(
                f"Portfolio allocation sums to {total_allocation:.2f}%, expected ~100%"
            )

        # Validate metrics
        if portfolio.metrics.total_value < 0:
            errors.append("Portfolio total value cannot be negative")

        return errors
