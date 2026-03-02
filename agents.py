"""
Specialized analysis agents for portfolio evaluation.

Each agent focuses on a specific aspect:
- Risk Assessment Agent: Analyzes portfolio risk, volatility, and downside protection
- Return Optimization Agent: Identifies underperforming assets and growth opportunities
- Diversification Agent: Evaluates concentration and correlation risks
- Market Sentiment Agent: Analyzes market outlook based on news and indicators
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from models import (
    Portfolio,
    Recommendation,
    ActionType,
    RecommendationPriority,
    RecommendationJustification,
    RiskMetrics,
)
from tools import (
    RiskCalculationTools,
    ConcentrationAnalysisTools,
    CorrelationAnalysisTools,
    SentimentAnalysisTools,
)
from config import DEFAULT_CONFIG


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all portfolio analysis agents.

    Defines common interface and logging for all specialized agents.
    Each agent implements its own analysis_type and generate_recommendations method.
    """

    def __init__(self, agent_name: str):
        """
        Initialize agent with name and logger.

        Args:
            agent_name: Name of the agent (e.g., "Risk Assessment Agent")
        """
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")

    @abstractmethod
    def analyze(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Perform specialized analysis on portfolio.

        Args:
            portfolio: Portfolio to analyze

        Returns:
            Dictionary with analysis results specific to this agent
        """
        pass

    @abstractmethod
    def generate_recommendations(
        self, portfolio: Portfolio, analysis_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Generate recommendations based on analysis.

        Args:
            portfolio: Portfolio being analyzed
            analysis_data: Results from analyze() method

        Returns:
            List of actionable recommendations from this agent's perspective
        """
        pass

    def _create_recommendation(
        self,
        action: ActionType,
        target_ticker: str,
        target_sector: str,
        position_sizing: float,
        reasoning: str,
        key_metrics: Dict[str, float],
        confidence: float,
        priority: RecommendationPriority = RecommendationPriority.ONE_WEEK,
    ) -> Recommendation:
        """
        Helper method to create a recommendation with this agent's justification.

        Args:
            action: Type of action recommended
            target_ticker: Target security symbol
            target_sector: Sector of target security
            position_sizing: Recommended position size (%)
            reasoning: Explanation of recommendation
            key_metrics: Supporting metrics
            confidence: Confidence level (0-100)
            priority: Implementation priority

        Returns:
            Recommendation object with agent's justification
        """
        justification = RecommendationJustification(
            agent_name=self.agent_name,
            reasoning=reasoning,
            key_metrics=key_metrics,
            confidence=confidence,
        )

        recommendation = Recommendation(
            recommendation_id=f"{self.agent_name}_{target_ticker}_{datetime.now().timestamp()}",
            action=action,
            target_ticker=target_ticker,
            target_sector=target_sector,
            position_sizing=position_sizing,
            entry_price=0.0,  # To be filled by Return Optimization Agent
            exit_price=0.0,  # To be filled
            justifications=[justification],
            overall_confidence=confidence,
            expected_impact={},  # To be calculated by orchestrator
            priority=priority,
            implementation_notes="",
        )

        return recommendation


class RiskAssessmentAgent(BaseAgent):
    """
    Analyzes portfolio volatility, correlation risks, downside protection, and sector concentration.

    Responsibilities:
    - Calculate portfolio volatility and compare to risk profile limits
    - Compute Value-at-Risk and identify tail risk scenarios
    - Assess concentration risk across individual positions and sectors
    - Flag correlation risks where diversification benefits are limited
    - Recommend risk mitigation through position reduction or hedging
    """

    def __init__(self):
        """Initialize Risk Assessment Agent."""
        super().__init__("Risk Assessment Agent")

    def analyze(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Perform comprehensive risk analysis.

        Args:
            portfolio: Portfolio to analyze

        Returns:
            Dictionary containing:
            - volatility: Annual volatility percentage
            - var_95: Value-at-Risk at 95% confidence
            - concentration_issues: List of concentration problems
            - correlation_risks: High correlation position pairs
            - risk_profile_violations: Constraints exceeded
        """
        self.logger.info(
            f"Starting risk analysis for portfolio {portfolio.portfolio_id}"
        )

        analysis = {
            "volatility": portfolio.metrics.annual_volatility,
            "var_95": portfolio.metrics.var_95,
            "max_drawdown": portfolio.metrics.max_drawdown,
            "sharpe_ratio": portfolio.metrics.sharpe_ratio,
            "sortino_ratio": portfolio.metrics.sortino_ratio,
            "concentration_index": portfolio.metrics.concentration_index,
            "sector_concentration": portfolio.metrics.sector_concentration,
            "correlation_risks": [],
            "concentration_alerts": [],
            "risk_profile_violations": [],
        }

        # Check concentration limits based on risk profile
        risk_profile = DEFAULT_CONFIG.get_risk_profile(portfolio.risk_profile)

        if portfolio.metrics.annual_volatility > risk_profile.max_volatility:
            analysis["risk_profile_violations"].append(
                f"Volatility {portfolio.metrics.annual_volatility:.1f}% exceeds "
                f"limit of {risk_profile.max_volatility}%"
            )

        # Identify concentration risks
        concentration_alerts = (
            ConcentrationAnalysisTools.identify_concentration_violations(
                portfolio,
                risk_profile.max_single_position,
                (
                    risk_profile.max_tech_exposure
                    if portfolio.risk_profile == "aggressive"
                    else 25.0
                ),
            )
        )
        analysis["concentration_alerts"] = concentration_alerts

        self.logger.info(
            f"Risk analysis complete. Volatility: {portfolio.metrics.annual_volatility:.1f}%"
        )

        return analysis

    def generate_recommendations(
        self, portfolio: Portfolio, analysis_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Generate risk reduction recommendations.

        Recommends SELL actions for:
        - Positions creating excessive concentration
        - Highly correlated positions reducing diversification
        - Volatile holdings violating risk constraints

        Args:
            portfolio: Portfolio being analyzed
            analysis_data: Risk analysis results

        Returns:
            List of risk-mitigation recommendations
        """
        recommendations = []

        # Recommend reducing high-concentration positions
        risk_profile = DEFAULT_CONFIG.get_risk_profile(portfolio.risk_profile)
        position_concentration = (
            ConcentrationAnalysisTools.calculate_position_concentration(
                portfolio.positions, portfolio.metrics.total_value
            )
        )

        for position in portfolio.positions:
            allocation = position_concentration.get(position.ticker, 0)

            # If position exceeds maximum, recommend reduction
            if allocation > risk_profile.max_single_position:
                excess_allocation = allocation - risk_profile.max_single_position

                recommendation = self._create_recommendation(
                    action=ActionType.DECREASE,
                    target_ticker=position.ticker,
                    target_sector=position.sector,
                    position_sizing=excess_allocation,
                    reasoning=(
                        f"Position concentration of {allocation:.1f}% exceeds "
                        f"maximum of {risk_profile.max_single_position}% for {portfolio.risk_profile} "
                        f"risk profile. Reduce to limit concentration risk."
                    ),
                    key_metrics={
                        "current_allocation": allocation,
                        "max_allowed": risk_profile.max_single_position,
                        "reduction_needed": excess_allocation,
                    },
                    confidence=85.0,
                    priority=RecommendationPriority.IMMEDIATE,
                )
                recommendations.append(recommendation)

        return recommendations


class ReturnOptimizationAgent(BaseAgent):
    """
    Identifies underperforming assets and high-potential opportunities.

    Responsibilities:
    - Analyze risk-adjusted returns (Sharpe ratio, Sortino ratio)
    - Identify underperforming positions vs. benchmarks
    - Detect high-potential growth opportunities
    - Recommend position increases for outperformers
    - Recommend position decreases for underperformers
    - Optimize portfolio allocation for better returns
    """

    def __init__(self):
        """Initialize Return Optimization Agent."""
        super().__init__("Return Optimization Agent")

    def analyze(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Analyze portfolio return efficiency.

        Args:
            portfolio: Portfolio to analyze

        Returns:
            Dictionary with:
            - sharpe_ratio: Risk-adjusted return metric
            - sortino_ratio: Downside risk-adjusted return
            - underperformers: Positions with negative returns
            - outperformers: Positions with strong returns
            - opportunities: Suggested new positions or increases
        """
        self.logger.info(f"Starting return optimization analysis")

        analysis = {
            "sharpe_ratio": portfolio.metrics.sharpe_ratio,
            "sortino_ratio": portfolio.metrics.sortino_ratio,
            "total_return": portfolio.metrics.total_return_percent,
            "underperformers": [],
            "outperformers": [],
            "opportunities": [],
        }

        # Identify underperformers (negative returns)
        for position in portfolio.positions:
            if position.gain_loss_percent < -5.0:  # More than 5% loss
                analysis["underperformers"].append(
                    {
                        "ticker": position.ticker,
                        "return": position.gain_loss_percent,
                        "sector": position.sector,
                    }
                )
            elif position.gain_loss_percent > 15.0:  # Strong gains
                analysis["outperformers"].append(
                    {
                        "ticker": position.ticker,
                        "return": position.gain_loss_percent,
                        "sector": position.sector,
                    }
                )

        self.logger.info(
            f"Return analysis: {len(analysis['underperformers'])} underperformers, "
            f"{len(analysis['outperformers'])} outperformers"
        )

        return analysis

    def generate_recommendations(
        self, portfolio: Portfolio, analysis_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Generate return optimization recommendations.

        Recommends:
        - SELL for significant underperformers
        - INCREASE for outperformers with strong fundamentals
        - Position sizing adjustments to optimize risk-adjusted returns

        Args:
            portfolio: Portfolio being analyzed
            analysis_data: Return analysis results

        Returns:
            List of return optimization recommendations
        """
        recommendations = []

        # Recommend selling significant underperformers
        for underperformer in analysis_data.get("underperformers", []):
            position = next(
                (
                    p
                    for p in portfolio.positions
                    if p.ticker == underperformer["ticker"]
                ),
                None,
            )
            if position:
                recommendation = self._create_recommendation(
                    action=ActionType.SELL,
                    target_ticker=position.ticker,
                    target_sector=position.sector,
                    position_sizing=position.allocation_percent,
                    reasoning=(
                        f"{position.ticker} has underperformed with a return of "
                        f"{underperformer['return']:.1f}%. Exit underperforming position "
                        f"to redeploy capital to higher-return opportunities."
                    ),
                    key_metrics={
                        "return_percent": underperformer["return"],
                        "holding_period": "Unknown",  # Would come from historical data
                        "relative_performance": "Below expectations",
                    },
                    confidence=75.0,
                    priority=RecommendationPriority.ONE_WEEK,
                )
                recommendations.append(recommendation)

        # Recommend increasing allocation to strong performers
        for outperformer in analysis_data.get("outperformers", [])[:3]:  # Top 3 only
            position = next(
                (p for p in portfolio.positions if p.ticker == outperformer["ticker"]),
                None,
            )
            if position:
                recommendation = self._create_recommendation(
                    action=ActionType.INCREASE,
                    target_ticker=position.ticker,
                    target_sector=position.sector,
                    position_sizing=1.0,  # Increase by 1%
                    reasoning=(
                        f"{position.ticker} has demonstrated strong performance with "
                        f"{outperformer['return']:.1f}% returns. Increase position to capture "
                        f"continued upside while maintaining diversification."
                    ),
                    key_metrics={
                        "return_percent": outperformer["return"],
                        "momentum": "Strong",
                        "risk_adjusted_return": "Above average",
                    },
                    confidence=70.0,
                    priority=RecommendationPriority.ONE_MONTH,
                )
                recommendations.append(recommendation)

        return recommendations


class DiversificationAgent(BaseAgent):
    """
    Evaluates portfolio concentration, sector/geographic exposure, and rebalancing opportunities.

    Responsibilities:
    - Assess portfolio diversification level (Herfindahl index)
    - Analyze sector and geographic concentration
    - Identify correlation redundancies
    - Recommend rebalancing to improve diversification
    - Flag over-concentration in specific themes
    """

    def __init__(self):
        """Initialize Diversification Agent."""
        super().__init__("Diversification Agent")

    def analyze(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Analyze portfolio diversification.

        Args:
            portfolio: Portfolio to analyze

        Returns:
            Dictionary with:
            - concentration_index: HHI index (lower = more diversified)
            - sector_allocations: Allocation by sector
            - high_correlation_pairs: Positions that are too correlated
            - diversification_score: Overall diversification (0-100)
        """
        self.logger.info(f"Starting diversification analysis")

        # Calculate allocations for concentration
        allocations = [p.allocation_percent / 100 for p in portfolio.positions]
        hhi = ConcentrationAnalysisTools.calculate_herfindahl_index(allocations)
        sector_allocations = ConcentrationAnalysisTools.calculate_sector_concentration(
            portfolio
        )

        # Normalize HHI to diversification score (0-100)
        # Min HHI = 1/n, Max HHI = 1
        min_hhi = 1 / len(portfolio.positions) if portfolio.positions else 1
        diversification_score = (1 - hhi) / (1 - min_hhi) * 100 if hhi < 1 else 0
        diversification_score = max(0, min(100, diversification_score))

        analysis = {
            "concentration_index": hhi,
            "diversification_score": diversification_score,
            "sector_allocations": sector_allocations,
            "num_positions": len(portfolio.positions),
            "num_sectors": len(sector_allocations),
            "high_concentration_sectors": [
                sector for sector, alloc in sector_allocations.items() if alloc > 30.0
            ],
        }

        self.logger.info(f"Diversification score: {diversification_score:.1f}")
        return analysis

    def generate_recommendations(
        self, portfolio: Portfolio, analysis_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Generate diversification improvement recommendations.

        Recommends:
        - Selling concentrated positions in over-represented sectors
        - Adding positions in under-represented sectors
        - Reducing correlated holdings
        - Improving geographic diversification

        Args:
            portfolio: Portfolio being analyzed
            analysis_data: Diversification analysis results

        Returns:
            List of diversification recommendations
        """
        recommendations = []
        diversification_score = analysis_data.get("diversification_score", 0)

        # If diversification score is low, recommend sector rebalancing
        if diversification_score < 60:
            high_conc_sectors = analysis_data.get("high_concentration_sectors", [])

            for sector in high_conc_sectors[:2]:  # Top 2 concentrated sectors
                sector_allocation = analysis_data["sector_allocations"][sector]

                # Find largest position in this sector to reduce
                sector_positions = [
                    p for p in portfolio.positions if p.sector == sector
                ]
                sector_positions.sort(key=lambda p: p.current_value, reverse=True)

                if sector_positions:
                    position = sector_positions[0]
                    recommendation = self._create_recommendation(
                        action=ActionType.DECREASE,
                        target_ticker=position.ticker,
                        target_sector=sector,
                        position_sizing=sector_allocation - 25.0,  # Reduce to 25%
                        reasoning=(
                            f"Sector concentration in {sector} is at {sector_allocation:.1f}%, "
                            f"exceeding healthy diversification levels. Reduce {position.ticker} "
                            f"to rebalance sector exposure."
                        ),
                        key_metrics={
                            "sector_allocation": sector_allocation,
                            "target_allocation": 25.0,
                            "diversification_score": diversification_score,
                            "num_positions": analysis_data["num_positions"],
                            "num_sectors": analysis_data["num_sectors"],
                        },
                        confidence=65.0,
                        priority=RecommendationPriority.ONE_MONTH,
                    )
                    recommendations.append(recommendation)

        return recommendations


class MarketSentimentAgent(BaseAgent):
    """
    Analyzes market outlook based on news, earnings, and economic indicators.

    Responsibilities:
    - Process financial news and sentiment (100+ daily articles)
    - Analyze earnings reports and guidance
    - Track economic indicators (interest rates, inflation, GDP)
    - Generate market outlook (bullish/bearish/neutral)
    - Provide sector-specific sentiment analysis
    - Score impact of sentiment on portfolio holdings
    """

    def __init__(self):
        """Initialize Market Sentiment Agent."""
        super().__init__("Market Sentiment Agent")

    def analyze(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Analyze market sentiment and conditions.

        Args:
            portfolio: Portfolio to analyze (for sector-specific sentiment)

        Returns:
            Dictionary with:
            - overall_sentiment: Market sentiment (-1 to 1)
            - market_outlook: Bullish/Neutral/Bearish
            - sector_sentiment: Sentiment by sector
            - economic_indicators: Key economic data
            - news_summary: Summary of recent news impact
        """
        self.logger.info(f"Starting market sentiment analysis")

        # In production, this would analyze real news, earnings, and economic data
        # For now, we provide structure that would be populated by NLP models

        analysis = {
            "overall_sentiment": 0.15,  # Placeholder: slightly positive
            "market_outlook": "MODERATELY_POSITIVE",
            "sentiment_confidence": 0.72,
            "sector_sentiment": {
                "Technology": 0.25,
                "Healthcare": 0.10,
                "Finance": 0.05,
                "Energy": -0.15,
                "Utilities": -0.05,
            },
            "economic_indicators": {
                "interest_rates": "Rising concern",
                "inflation": "Moderating",
                "gdp_growth": "Slowing",
                "unemployment": "Stable",
            },
            "news_articles_analyzed": 125,
            "positive_articles_percent": 55.0,
            "key_themes": [
                "Tech earnings beat expectations",
                "Interest rate hikes continuing",
                "Inflation data improving",
                "Economic growth concerns",
            ],
        }

        self.logger.info(f"Market outlook: {analysis['market_outlook']}")
        return analysis

    def generate_recommendations(
        self, portfolio: Portfolio, analysis_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Generate sentiment-driven recommendations.

        Recommends:
        - Increasing allocation to positively-sentominant sectors
        - Reducing exposure to negatively-sentiment sectors
        - HOLD recommendations for stable sectors

        Args:
            portfolio: Portfolio being analyzed
            analysis_data: Sentiment analysis results

        Returns:
            List of sentiment-based recommendations
        """
        recommendations = []
        sector_sentiment = analysis_data.get("sector_sentiment", {})

        # Find highest sentiment sector and recommend increasing exposure
        if sector_sentiment:
            best_sector = max(sector_sentiment.items(), key=lambda x: x[1])
            if best_sector[1] > 0.15:  # Positive sentiment threshold
                recommendation = self._create_recommendation(
                    action=ActionType.BUY,
                    target_ticker="SECTOR_ROTATION",
                    target_sector=best_sector[0],
                    position_sizing=2.0,  # Add 2% to sector
                    reasoning=(
                        f"{best_sector[0]} sector shows positive sentiment "
                        f"({best_sector[1]:.2f} score). Market analysis suggests "
                        f"strong outlook. Increase sector exposure by adding to "
                        f"high-quality names in this space."
                    ),
                    key_metrics={
                        "sector_sentiment": best_sector[1],
                        "news_analysis": analysis_data.get(
                            "positive_articles_percent", 0
                        ),
                        "economic_backdrop": "Supportive",
                    },
                    confidence=60.0,
                    priority=RecommendationPriority.ONE_WEEK,
                )
                recommendations.append(recommendation)

            # Find worst sentiment sector and recommend decreasing
            worst_sector = min(sector_sentiment.items(), key=lambda x: x[1])
            if worst_sector[1] < -0.10:  # Negative sentiment threshold
                recommendation = self._create_recommendation(
                    action=ActionType.SELL,
                    target_ticker="SECTOR_ROTATION",
                    target_sector=worst_sector[0],
                    position_sizing=1.0,  # Reduce 1%
                    reasoning=(
                        f"{worst_sector[0]} sector shows negative sentiment "
                        f"({worst_sector[1]:.2f} score). Market headwinds suggest "
                        f"caution. Consider reducing exposure to this sector."
                    ),
                    key_metrics={
                        "sector_sentiment": worst_sector[1],
                        "economic_factors": "Headwinds",
                        "recommendation_strength": "Moderate",
                    },
                    confidence=55.0,
                    priority=RecommendationPriority.ONE_MONTH,
                )
                recommendations.append(recommendation)

        return recommendations
