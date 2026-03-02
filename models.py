"""
Data models and schemas for the portfolio analysis system.

Defines core data structures used throughout the application:
- Portfolio holdings and allocation
- Recommendations and analysis results
- Risk metrics and performance indicators
- Audit and logging records
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid


class ActionType(Enum):
    """Enumeration of possible recommendation actions."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"


class RecommendationPriority(Enum):
    """Urgency level for implementing recommendations."""

    IMMEDIATE = "immediate"
    ONE_WEEK = "1_week"
    ONE_MONTH = "1_month"


@dataclass
class Position:
    """
    Represents a single holding in the portfolio.

    Attributes:
        ticker: Stock symbol/ticker
        shares: Number of shares held
        entry_price: Average purchase price per share
        current_price: Current market price per share
        allocation_percent: Percentage of portfolio value
        sector: Industry sector (e.g., Technology, Healthcare)
        current_value: Total current position value
        gain_loss: Unrealized gain/loss
        gain_loss_percent: Unrealized gain/loss percentage
    """

    ticker: str
    shares: float
    entry_price: float
    current_price: float
    allocation_percent: float
    sector: str
    current_value: float = 0.0
    gain_loss: float = 0.0
    gain_loss_percent: float = 0.0

    def __post_init__(self):
        """Calculate derived metrics after initialization."""
        self.current_value = self.shares * self.current_price
        self.gain_loss = self.current_value - (self.shares * self.entry_price)
        original_value = self.shares * self.entry_price
        if original_value != 0:
            self.gain_loss_percent = (self.gain_loss / original_value) * 100


@dataclass
class PortfolioMetrics:
    """
    Aggregated portfolio performance and risk metrics.

    Attributes:
        total_value: Total portfolio value in base currency
        total_return_percent: Overall portfolio return percentage
        annual_volatility: Annualized volatility (standard deviation)
        sharpe_ratio: Risk-adjusted return metric
        sortino_ratio: Downside risk-adjusted return metric
        max_drawdown: Largest peak-to-trough decline
        var_95: Value-at-Risk at 95% confidence level
        concentration_index: Herfindahl index of position concentration
        sector_concentration: Maximum sector exposure
    """

    total_value: float
    total_return_percent: float
    annual_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float  # Value-at-Risk
    concentration_index: float
    sector_concentration: float


@dataclass
class Portfolio:
    """
    Complete portfolio data with all holdings and metadata.

    Attributes:
        positions: List of current holdings
        metrics: Aggregated portfolio metrics
        risk_profile: Risk tolerance level (conservative/moderate/aggressive)
        constraints: Custom portfolio constraints and restrictions
        historical_data: Historical performance data (last 10 years)
        created_at: Portfolio creation timestamp
        portfolio_id: Unique identifier
    """

    positions: List[Position]
    metrics: PortfolioMetrics
    risk_profile: str
    constraints: Dict[str, Any]
    historical_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    portfolio_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def get_sector_allocation(self) -> Dict[str, float]:
        """
        Calculate allocation percentage by sector.

        Returns:
            Dictionary mapping sectors to their allocation percentages
        """
        sector_values = {}
        for position in self.positions:
            sector_values[position.sector] = (
                sector_values.get(position.sector, 0) + position.current_value
            )

        total_value = self.metrics.total_value
        return {
            sector: (value / total_value * 100) if total_value > 0 else 0
            for sector, value in sector_values.items()
        }


@dataclass
class RecommendationJustification:
    """
    Detailed reasoning behind a recommendation from one analysis perspective.

    Attributes:
        agent_name: Name of the agent providing analysis (e.g., Risk Assessment)
        reasoning: Detailed explanation of the recommendation
        key_metrics: Relevant metrics supporting the recommendation
        data_sources: Sources of data used for analysis
        confidence: Confidence score (0-100)
    """

    agent_name: str
    reasoning: str
    key_metrics: Dict[str, float]
    data_sources: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class Recommendation:
    """
    Single actionable portfolio recommendation.

    Attributes:
        recommendation_id: Unique identifier
        action: Type of action (BUY/SELL/HOLD/etc)
        target_ticker: Security symbol for the recommendation
        target_sector: Sector of recommended security
        position_sizing: Recommended allocation percentage or share count
        entry_price: Suggested entry price for BUY/INCREASE actions
        exit_price: Suggested exit price for SELL/DECREASE actions
        justifications: Analysis from each agent perspective
        overall_confidence: Aggregate confidence score (0-100)
        expected_impact: Expected portfolio impact metrics
        priority: Implementation timeline suggestion
        implementation_notes: Specific guidance on how to execute
        created_at: Timestamp when recommendation was generated
    """

    recommendation_id: str
    action: ActionType
    target_ticker: str
    target_sector: str
    position_sizing: float
    entry_price: float
    exit_price: float
    justifications: List[RecommendationJustification]
    overall_confidence: float
    expected_impact: Dict[str, float]  # return_pct, risk_reduction_pct, etc
    priority: RecommendationPriority
    implementation_notes: str
    created_at: datetime = field(default_factory=datetime.now)

    def add_justification(self, justification: RecommendationJustification) -> None:
        """
        Add analysis justification from an agent.

        Args:
            justification: RecommendationJustification object with agent reasoning
        """
        self.justifications.append(justification)


@dataclass
class AnalysisResult:
    """
    Complete analysis output with recommendations and detailed analysis.

    Attributes:
        analysis_id: Unique identifier for this analysis run
        portfolio: Portfolio that was analyzed
        recommendations: Ranked list of actionable recommendations
        risk_assessment: Detailed risk analysis results
        market_sentiment: Current market outlook and sentiment analysis
        alerts: Any constraint violations or risk warnings
        completion_time_seconds: Total analysis completion time
        execution_timestamp: When analysis was performed
        version: System version used for analysis
    """

    analysis_id: str
    portfolio: Portfolio
    recommendations: List[Recommendation]
    risk_assessment: Dict[str, Any]
    market_sentiment: Dict[str, Any]
    alerts: List[str] = field(default_factory=list)
    completion_time_seconds: float = 0.0
    execution_timestamp: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

    def add_alert(self, alert: str) -> None:
        """
        Add a constraint violation or risk alert.

        Args:
            alert: Alert message describing the issue
        """
        self.alerts.append(alert)


@dataclass
class RiskMetrics:
    """
    Comprehensive risk analysis metrics for a portfolio.

    Attributes:
        volatility: Annual volatility (standard deviation of returns)
        beta: Systematic risk relative to market
        var_95: Value-at-Risk at 95% confidence
        cvar_95: Conditional Value-at-Risk (expected shortfall)
        max_drawdown: Largest peak-to-trough decline
        sortino_ratio: Downside risk-adjusted return
        treynor_ratio: Return per unit of systematic risk
        correlation_matrix: Correlations between holdings
        sector_concentration: Concentration by sector
        position_concentration: Concentration by individual position
    """

    volatility: float
    beta: float
    var_95: float
    cvar_95: float
    max_drawdown: float
    sortino_ratio: float
    treynor_ratio: float
    correlation_matrix: Dict[str, Dict[str, float]]
    sector_concentration: Dict[str, float]
    position_concentration: Dict[str, float]


@dataclass
class AuditLog:
    """
    Audit trail entry for compliance and tracking.

    Attributes:
        log_id: Unique log identifier
        portfolio_id: Associated portfolio
        analysis_id: Associated analysis run
        action: What operation was performed
        agent_name: Which agent performed the action
        timestamp: When the action occurred
        reasoning: Explanation of the action
        affected_data: What data was affected
    """

    log_id: str
    portfolio_id: str
    analysis_id: str
    action: str
    agent_name: str
    timestamp: datetime
    reasoning: str
    affected_data: Dict[str, Any]


# Response model for API endpoints
@dataclass
class APIResponse:
    """
    Standardized API response wrapper.

    Attributes:
        success: Whether operation succeeded
        data: Response payload
        error: Error message if operation failed
        timestamp: Response generation timestamp
    """

    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
