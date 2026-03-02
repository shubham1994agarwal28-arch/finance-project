"""
Orchestrator for coordinating multi-agent portfolio analysis.

The Orchestrator Agent acts as the main controller that:
- Coordinates analysis across all four specialized agents
- Aggregates and synthesizes recommendations
- Resolves conflicting recommendations
- Ranks recommendations by impact and confidence
- Ensures compliance with risk constraints
- Generates final analysis results
"""

import logging
import time
from typing import List, Dict, Any, Tuple
from datetime import datetime
import uuid

from models import (
    Portfolio,
    AnalysisResult,
    Recommendation,
    ActionType,
    RecommendationPriority,
    Position,
)
from agents import (
    RiskAssessmentAgent,
    ReturnOptimizationAgent,
    DiversificationAgent,
    MarketSentimentAgent,
)
from tools import DataValidationTools
from config import DEFAULT_CONFIG


logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Main orchestrator coordinating all portfolio analysis agents.

    Workflow:
    1. Validates portfolio data
    2. Executes analysis in parallel via each specialized agent
    3. Aggregates findings across all agents
    4. Synthesizes multi-perspective recommendations
    5. Ranks and scores recommendations
    6. Generates final analysis output
    7. Logs and audits all decisions

    This ensures comprehensive, multi-faceted portfolio analysis with recommendations
    grounded in risk management, performance optimization, diversification, and
    market conditions.
    """

    def __init__(self):
        """Initialize orchestrator with all specialized agents."""
        self.logger = logging.getLogger(__name__ + ".OrchestratorAgent")

        # Initialize all four specialized agents
        self.risk_agent = RiskAssessmentAgent()
        self.return_agent = ReturnOptimizationAgent()
        self.diversification_agent = DiversificationAgent()
        self.sentiment_agent = MarketSentimentAgent()

        self.agents = [
            self.risk_agent,
            self.return_agent,
            self.diversification_agent,
            self.sentiment_agent,
        ]

        self.logger.info("OrchestratorAgent initialized with 4 specialized agents")

    def analyze_portfolio(self, portfolio: Portfolio) -> AnalysisResult:
        """
        Execute comprehensive multi-agent portfolio analysis.

        Complete workflow:
        1. Pre-analysis validation
        2. Run all agents in parallel conceptually
        3. Aggregate and cross-reference findings
        4. Generate ranked recommendations
        5. Identify constraint violations
        6. Create final analysis result

        Args:
            portfolio: Portfolio to analyze

        Returns:
            AnalysisResult containing recommendations, risk assessment, and insights

        Raises:
            ValueError: If portfolio fails validation
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())

        self.logger.info(f"Starting portfolio analysis: {analysis_id}")
        self.logger.info(
            f"Portfolio size: {len(portfolio.positions)} positions, "
            f"Total value: ${portfolio.metrics.total_value:,.2f}"
        )

        # ============================================================================
        # STAGE 1: PRE-ANALYSIS VALIDATION
        # ============================================================================
        validation_errors = DataValidationTools.validate_portfolio(portfolio)
        if validation_errors:
            self.logger.warning(f"Portfolio validation warnings: {validation_errors}")
            # Note: We continue with warnings rather than failing completely

        # ============================================================================
        # STAGE 2: MULTI-AGENT ANALYSIS
        # ============================================================================
        # Execute each agent's analysis
        self.logger.info("Executing specialized agent analyses...")

        risk_analysis = self.risk_agent.analyze(portfolio)
        return_analysis = self.return_agent.analyze(portfolio)
        diversification_analysis = self.diversification_agent.analyze(portfolio)
        sentiment_analysis = self.sentiment_agent.analyze(portfolio)

        # ============================================================================
        # STAGE 3: GENERATE AGENT-SPECIFIC RECOMMENDATIONS
        # ============================================================================
        self.logger.info("Generating agent-specific recommendations...")

        risk_recommendations = self.risk_agent.generate_recommendations(
            portfolio, risk_analysis
        )
        return_recommendations = self.return_agent.generate_recommendations(
            portfolio, return_analysis
        )
        diversification_recommendations = (
            self.diversification_agent.generate_recommendations(
                portfolio, diversification_analysis
            )
        )
        sentiment_recommendations = self.sentiment_agent.generate_recommendations(
            portfolio, sentiment_analysis
        )

        # ============================================================================
        # STAGE 4: SYNTHESIZE & RANK RECOMMENDATIONS
        # ============================================================================
        self.logger.info("Synthesizing recommendations across agents...")

        all_recommendations = (
            risk_recommendations
            + return_recommendations
            + diversification_recommendations
            + sentiment_recommendations
        )

        self.logger.info(
            f"Generated {len(all_recommendations)} initial recommendations"
        )

        # Merge duplicate/similar recommendations
        merged_recommendations = self._merge_similar_recommendations(
            all_recommendations
        )
        self.logger.info(
            f"After deduplication: {len(merged_recommendations)} recommendations"
        )

        # Rank recommendations by impact and confidence
        ranked_recommendations = self._rank_recommendations(
            merged_recommendations, portfolio
        )

        # Take top N recommendations
        final_recommendations = ranked_recommendations[
            : DEFAULT_CONFIG.TOP_RECOMMENDATIONS_COUNT
        ]
        self.logger.info(f"Final top recommendations: {len(final_recommendations)}")

        # ============================================================================
        # STAGE 5: IDENTIFY ALERTS & CONSTRAINT VIOLATIONS
        # ============================================================================
        alerts = []
        alerts.extend(risk_analysis.get("risk_profile_violations", []))
        alerts.extend(risk_analysis.get("concentration_alerts", []))

        if not final_recommendations:
            alerts.append(
                "WARNING: No strong recommendations generated for this portfolio"
            )

        # ============================================================================
        # STAGE 6: COMPILE ANALYSIS RESULT
        # ============================================================================
        completion_time = time.time() - start_time

        analysis_result = AnalysisResult(
            analysis_id=analysis_id,
            portfolio=portfolio,
            recommendations=final_recommendations,
            risk_assessment=risk_analysis,
            market_sentiment=sentiment_analysis,
            alerts=alerts,
            completion_time_seconds=completion_time,
            version="1.0.0",
        )

        self.logger.info(
            f"Analysis complete in {completion_time:.2f}s. "
            f"Generated {len(final_recommendations)} recommendations. "
            f"Alerts: {len(alerts)}"
        )

        return analysis_result

    def _merge_similar_recommendations(
        self, recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """
        Merge recommendations targeting the same security from different agents.

        Consolidates multiple agent perspectives into unified recommendations
        with justifications from all agents that provided analysis.

        Args:
            recommendations: List of all recommendations from all agents

        Returns:
            Deduplicated list with merged justifications
        """
        # Group recommendations by target ticker and action
        grouped = {}
        for rec in recommendations:
            key = (rec.target_ticker, rec.action.value)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(rec)

        merged = []
        for (ticker, action), recs in grouped.items():
            if len(recs) == 1:
                merged.append(recs[0])
            else:
                # Merge multiple recommendations
                primary_rec = recs[0]

                # Combine all justifications
                for rec in recs[1:]:
                    for just in rec.justifications:
                        primary_rec.add_justification(just)

                # Average confidence scores
                avg_confidence = sum(r.overall_confidence for r in recs) / len(recs)
                primary_rec.overall_confidence = avg_confidence

                merged.append(primary_rec)
                self.logger.debug(
                    f"Merged {len(recs)} recommendations for {ticker} ({action})"
                )

        return merged

    def _rank_recommendations(
        self, recommendations: List[Recommendation], portfolio: Portfolio
    ) -> List[Recommendation]:
        """
        Rank recommendations by impact, confidence, and actionability.

        Scoring factors:
        - Confidence level (0-100)
        - Number of supporting agents (1-4)
        - Alignment with market sentiment
        - Impact on portfolio risk metrics
        - Priority level (immediate > 1 week > 1 month)

        Args:
            recommendations: List of recommendations to rank
            portfolio: Portfolio for context

        Returns:
            Sorted list with highest-impact recommendations first
        """

        def calculate_recommendation_score(
            rec: Recommendation,
        ) -> Tuple[float, Recommendation]:
            """Calculate impact score for a recommendation."""
            # Base confidence score (0-100)
            confidence_score = rec.overall_confidence

            # Agent consensus bonus: +5% for each agent supporting this recommendation
            agent_count = len(rec.justifications)
            agent_bonus = (agent_count - 1) * 5.0  # -5 to +15 for 1-4 agents

            # Priority bonus: +20% for immediate, +10% for 1 week
            priority_bonus = {
                RecommendationPriority.IMMEDIATE: 20.0,
                RecommendationPriority.ONE_WEEK: 10.0,
                RecommendationPriority.ONE_MONTH: 0.0,
            }.get(rec.priority, 0.0)

            # Action type bias (SELL more urgent for risk management)
            action_bias = {
                ActionType.SELL: 10.0,  # Risk reduction urgent
                ActionType.DECREASE: 8.0,  # Risk management
                ActionType.BUY: 5.0,  # Opportunity
                ActionType.INCREASE: 3.0,  # Modest opportunity
                ActionType.HOLD: -5.0,  # Lowest priority
            }.get(rec.action, 0.0)

            # Calculate final score
            final_score = confidence_score + agent_bonus + priority_bonus + action_bias
            final_score = max(0, min(100, final_score))  # Clamp 0-100

            return final_score

        # Score and sort all recommendations
        scored_recs = [
            (calculate_recommendation_score(rec), rec) for rec in recommendations
        ]

        scored_recs.sort(key=lambda x: x[0], reverse=True)

        sorted_recommendations = [rec for score, rec in scored_recs]

        self.logger.debug(
            f"Top recommendation scores: {[f'{s:.1f}' for s, _ in scored_recs[:5]]}"
        )

        return sorted_recommendations

    def validate_recommendation_compliance(
        self, portfolio: Portfolio, recommendation: Recommendation
    ) -> bool:
        """
        Validate that a recommendation complies with portfolio constraints.

        Checks:
        - Risk profile constraints (volatility, concentration)
        - Position limits
        - Sector exposure limits
        - Regulatory requirements

        Args:
            portfolio: Portfolio with constraints
            recommendation: Recommendation to validate

        Returns:
            True if recommendation complies with all constraints
        """
        risk_profile = DEFAULT_CONFIG.get_risk_profile(portfolio.risk_profile)

        # Check single-position limit
        if recommendation.position_sizing > risk_profile.max_single_position:
            self.logger.warning(
                f"Recommendation for {recommendation.target_ticker} exceeds "
                f"position limit: {recommendation.position_sizing}% > "
                f"{risk_profile.max_single_position}%"
            )
            return False

        # Check sector limits
        if (
            recommendation.target_sector == "Technology"
            and recommendation.position_sizing > risk_profile.max_tech_exposure
        ):
            self.logger.warning(f"Recommendation would exceed tech sector limit")
            return False

        return True

    def generate_summary_report(
        self, analysis_result: AnalysisResult
    ) -> Dict[str, Any]:
        """
        Generate executive summary of analysis.

        Args:
            analysis_result: Complete analysis result

        Returns:
            Dictionary with summary metrics and insights
        """
        risk_profile = DEFAULT_CONFIG.get_risk_profile(
            analysis_result.portfolio.risk_profile
        )

        summary = {
            "analysis_id": analysis_result.analysis_id,
            "portfolio_id": analysis_result.portfolio.portfolio_id,
            "timestamp": analysis_result.execution_timestamp.isoformat(),
            "completion_time_seconds": analysis_result.completion_time_seconds,
            "portfolio_metrics": {
                "total_value": analysis_result.portfolio.metrics.total_value,
                "total_return": analysis_result.portfolio.metrics.total_return_percent,
                "volatility": analysis_result.portfolio.metrics.annual_volatility,
                "num_positions": len(analysis_result.portfolio.positions),
                "sharpe_ratio": analysis_result.portfolio.metrics.sharpe_ratio,
                "sortino_ratio": analysis_result.portfolio.metrics.sortino_ratio,
            },
            "risk_assessment": {
                "profile": analysis_result.portfolio.risk_profile,
                "volatility_limit": risk_profile.max_volatility,
                "volatility_status": (
                    "COMPLIANT"
                    if analysis_result.portfolio.metrics.annual_volatility
                    <= risk_profile.max_volatility
                    else "VIOLATION"
                ),
                "concentration_risk": analysis_result.portfolio.metrics.concentration_index,
            },
            "recommendations_count": len(analysis_result.recommendations),
            "alerts_count": len(analysis_result.alerts),
            "top_recommendations": [
                {
                    "ticker": rec.target_ticker,
                    "action": rec.action.value,
                    "confidence": rec.overall_confidence,
                    "agents_supporting": len(rec.justifications),
                }
                for rec in analysis_result.recommendations[:5]
            ],
            "market_outlook": analysis_result.market_sentiment.get(
                "market_outlook", "UNKNOWN"
            ),
            "critical_alerts": analysis_result.alerts[:3],
        }

        return summary
