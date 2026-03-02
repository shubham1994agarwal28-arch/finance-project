"""
Report generation module for creating comprehensive analysis outputs.

Generates:
- Text/Markdown reports with analysis summary
- Detailed recommendation documentation
- Portfolio metrics and risk assessment details
- Audit trail and compliance documentation
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from io import StringIO

from models import AnalysisResult, Recommendation
from config import DEFAULT_CONFIG


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive reports from analysis results.
    Supports multiple output formats: Markdown, HTML, JSON.
    """

    @staticmethod
    def generate_markdown_report(analysis_result: AnalysisResult) -> str:
        """
        Generate comprehensive Markdown report.

        Includes:
        - Executive summary
        - Portfolio metrics
        - Risk assessment
        - Detailed recommendations
        - Market outlook
        - Alerts and violations
        - Appendix with methodology

        Args:
            analysis_result: Complete analysis result

        Returns:
            Markdown-formatted report as string
        """
        report = StringIO()

        # ====================================================================
        # TITLE & EXECUTIVE SUMMARY
        # ====================================================================
        report.write("# AI Portfolio Analysis Report\n\n")
        report.write(f"**Analysis ID:** {analysis_result.analysis_id}\n")
        report.write(f"**Portfolio ID:** {analysis_result.portfolio.portfolio_id}\n")
        report.write(
            f"**Generated:** {analysis_result.execution_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        report.write(
            f"**Analysis Duration:** {analysis_result.completion_time_seconds:.2f} seconds\n\n"
        )

        # Executive Summary
        report.write("## Executive Summary\n\n")

        portfolio = analysis_result.portfolio
        report.write(
            f"This report presents a comprehensive multi-agent analysis of your institutional portfolio.\n\n"
        )
        report.write(f"**Portfolio Overview:**\n")
        report.write(f"- Total Value: ${portfolio.metrics.total_value:,.2f}\n")
        report.write(f"- Number of Positions: {len(portfolio.positions)}\n")
        report.write(f"- Risk Profile: {portfolio.risk_profile.upper()}\n")
        report.write(
            f"- Total Return: {portfolio.metrics.total_return_percent:+.2f}%\n\n"
        )

        report.write(f"**Analysis Highlights:**\n")
        report.write(
            f"- Recommendations Generated: {len(analysis_result.recommendations)}\n"
        )
        report.write(f"- Agents Involved: 4 specialized agents\n")
        report.write(f"- Critical Alerts: {len(analysis_result.alerts)}\n")
        report.write(
            f"- Market Outlook: {analysis_result.market_sentiment.get('market_outlook', 'NEUTRAL')}\n\n"
        )

        # ====================================================================
        # PORTFOLIO METRICS
        # ====================================================================
        report.write("## Portfolio Metrics\n\n")

        metrics = portfolio.metrics

        report.write("### Risk Metrics\n\n")
        report.write(f"| Metric | Value | Assessment |\n")
        report.write(f"|--------|-------|------------|\n")
        report.write(f"| Annual Volatility | {metrics.annual_volatility:.2f}% | ")

        risk_profile = DEFAULT_CONFIG.get_risk_profile(portfolio.risk_profile)
        if metrics.annual_volatility <= risk_profile.max_volatility:
            report.write("✓ Within Profile Limits |\n")
        else:
            report.write("⚠ Exceeds Limits |\n")

        report.write(
            f"| Value-at-Risk (95%) | {metrics.var_95:.2f}% | Maximum expected loss |\n"
        )
        report.write(
            f"| Maximum Drawdown | {metrics.max_drawdown:.2f}% | Worst historical decline |\n"
        )
        report.write(
            f"| Sharpe Ratio | {metrics.sharpe_ratio:.2f} | Risk-adjusted returns |\n"
        )
        report.write(
            f"| Sortino Ratio | {metrics.sortino_ratio:.2f} | Downside risk-adjusted returns |\n"
        )
        report.write(
            f"| Concentration Index | {metrics.concentration_index:.4f} | Diversification level |\n\n"
        )

        report.write("### Performance Metrics\n\n")
        report.write(f"| Metric | Value |\n")
        report.write(f"|--------|-------|\n")
        report.write(f"| Total Return | {metrics.total_return_percent:+.2f}% |\n")
        report.write(
            f"| Allocation Sectors | {len(set(p.sector for p in portfolio.positions))} |\n"
        )
        report.write(
            f"| Largest Position | {max((p.allocation_percent for p in portfolio.positions), default=0):.2f}% |\n\n"
        )

        # ====================================================================
        # RISK ASSESSMENT
        # ====================================================================
        report.write("## Risk Assessment\n\n")

        risk_assessment = analysis_result.risk_assessment
        report.write(f"**Current Status:** ")
        if not analysis_result.alerts:
            report.write("✓ No critical violations\n\n")
        else:
            report.write("⚠ Constraint violations detected\n\n")

        report.write("### Constraints vs Limits\n\n")
        report.write(f"| Constraint | Current | Limit | Status |\n")
        report.write(f"|-----------|---------|-------|--------|\n")
        report.write(
            f"| Volatility | {metrics.annual_volatility:.1f}% | {risk_profile.max_volatility}% | "
        )
        report.write(
            "✓\n" if metrics.annual_volatility <= risk_profile.max_volatility else "⚠\n"
        )

        report.write(
            f"| Max Position | {max((p.allocation_percent for p in portfolio.positions), default=0):.1f}% | {risk_profile.max_single_position}% | "
        )
        max_pos = max((p.allocation_percent for p in portfolio.positions), default=0)
        report.write("✓\n" if max_pos <= risk_profile.max_single_position else "⚠\n\n")

        # ====================================================================
        # RECOMMENDATIONS
        # ====================================================================
        report.write("## Top Recommendations\n\n")
        report.write(
            f"**Total Recommendations:** {len(analysis_result.recommendations)}\n\n"
        )

        for idx, rec in enumerate(analysis_result.recommendations[:10], 1):
            report.write(f"### {idx}. {rec.action.value}: {rec.target_ticker}\n\n")
            report.write(f"- **Sector:** {rec.target_sector}\n")
            report.write(f"- **Position Sizing:** {rec.position_sizing:.2f}%\n")
            report.write(f"- **Confidence:** {rec.overall_confidence:.0f}%\n")
            report.write(f"- **Priority:** {rec.priority.value}\n")
            report.write(f"- **Agents Supporting:** {len(rec.justifications)}\n\n")

            report.write("**Justifications:**\n\n")
            for just in rec.justifications:
                report.write(f"- **{just.agent_name}:**\n")
                report.write(f"  - Reasoning: {just.reasoning}\n")
                report.write(f"  - Confidence: {just.confidence:.0f}%\n")
                if just.key_metrics:
                    report.write(
                        f"  - Key Metrics: {', '.join(f'{k}: {v}' for k, v in just.key_metrics.items())}\n\n"
                    )

        # ====================================================================
        # ALERTS & VIOLATIONS
        # ====================================================================
        report.write("## Alerts & Constraint Violations\n\n")

        if analysis_result.alerts:
            for idx, alert in enumerate(analysis_result.alerts, 1):
                report.write(f"{idx}. ⚠ {alert}\n")
            report.write("\n")
        else:
            report.write("✓ No alerts or violations\n\n")

        # ====================================================================
        # MARKET SENTIMENT
        # ====================================================================
        report.write("## Market Sentiment & Outlook\n\n")

        sentiment = analysis_result.market_sentiment
        report.write(
            f"**Overall Sentiment:** {sentiment.get('overall_sentiment', 0):.2f}\n"
        )
        report.write(
            f"**Market Outlook:** {sentiment.get('market_outlook', 'NEUTRAL')}\n"
        )
        report.write(
            f"**Sentiment Confidence:** {sentiment.get('sentiment_confidence', 0):.0%}\n"
        )
        report.write(
            f"**News Articles Analyzed:** {sentiment.get('news_articles_analyzed', 0)}\n"
        )
        report.write(
            f"**Positive Articles:** {sentiment.get('positive_articles_percent', 0):.0f}%\n\n"
        )

        report.write("### Sector Sentiment\n\n")
        for sector, sentiment_score in sentiment.get("sector_sentiment", {}).items():
            sentiment_label = (
                "🟢 Positive"
                if sentiment_score > 0.1
                else "🔴 Negative"
                if sentiment_score < -0.1
                else "🟡 Neutral"
            )
            report.write(f"- {sector}: {sentiment_score:+.2f} {sentiment_label}\n")

        report.write("\n")

        # ====================================================================
        # METHODOLOGY
        # ====================================================================
        report.write("## Methodology & Architecture\n\n")

        report.write("### Multi-Agent Framework\n\n")
        report.write("This analysis leverages four specialized agents:\n\n")
        report.write("1. **Risk Assessment Agent**\n")
        report.write("   - Evaluates portfolio volatility and downside risk\n")
        report.write("   - Analyzes concentration risks\n")
        report.write("   - Monitors compliance with risk profile constraints\n\n")

        report.write("2. **Return Optimization Agent**\n")
        report.write("   - Identifies underperforming positions\n")
        report.write("   - Detects high-potential opportunities\n")
        report.write("   - Optimizes allocation for risk-adjusted returns\n\n")

        report.write("3. **Diversification Agent**\n")
        report.write("   - Assesses portfolio diversification (Herfindahl index)\n")
        report.write("   - Analyzes sector and position concentration\n")
        report.write("   - Recommends rebalancing for improved diversification\n\n")

        report.write("4. **Market Sentiment Agent**\n")
        report.write("   - Analyzes financial news and sentiment\n")
        report.write("   - Tracks economic indicators\n")
        report.write("   - Provides market outlook and sector perspectives\n\n")

        report.write("### Technologies\n\n")
        report.write(f"- **LLM Inference:** Ollama ({DEFAULT_CONFIG.PRIMARY_MODEL})\n")
        report.write("- **NLP Analysis:** Hugging Face Transformers, BERT sentiment\n")
        report.write("- **Risk Calculations:** NumPy, Pandas, SciPy\n")
        report.write("- **Framework:** FastAPI, Python 3.8+\n\n")

        # ====================================================================
        # FOOTER
        # ====================================================================
        report.write("---\n\n")
        report.write(
            "*Report Generated by AI Portfolio Analysis & Recommendation Agent v1.0*\n"
        )
        report.write(
            "*For compliance and audit purposes, all recommendations and reasoning are logged.*\n"
        )

        return report.getvalue()

    @staticmethod
    def generate_json_report(analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Generate JSON-formatted report for programmatic access.

        Args:
            analysis_result: Complete analysis result

        Returns:
            Dictionary suitable for JSON serialization
        """
        portfolio = analysis_result.portfolio

        return {
            "analysis_id": analysis_result.analysis_id,
            "timestamp": analysis_result.execution_timestamp.isoformat(),
            "completion_time_seconds": analysis_result.completion_time_seconds,
            "portfolio": {
                "id": portfolio.portfolio_id,
                "risk_profile": portfolio.risk_profile,
                "num_positions": len(portfolio.positions),
                "metrics": {
                    "total_value": portfolio.metrics.total_value,
                    "total_return_percent": portfolio.metrics.total_return_percent,
                    "annual_volatility": portfolio.metrics.annual_volatility,
                    "sharpe_ratio": portfolio.metrics.sharpe_ratio,
                    "sortino_ratio": portfolio.metrics.sortino_ratio,
                    "max_drawdown": portfolio.metrics.max_drawdown,
                    "var_95": portfolio.metrics.var_95,
                    "concentration_index": portfolio.metrics.concentration_index,
                },
            },
            "recommendations": [
                {
                    "id": rec.recommendation_id,
                    "action": rec.action.value,
                    "ticker": rec.target_ticker,
                    "sector": rec.target_sector,
                    "position_sizing": rec.position_sizing,
                    "confidence": rec.overall_confidence,
                    "priority": rec.priority.value,
                    "agents": [j.agent_name for j in rec.justifications],
                    "justifications": [
                        {
                            "agent": j.agent_name,
                            "reasoning": j.reasoning,
                            "confidence": j.confidence,
                            "metrics": j.key_metrics,
                        }
                        for j in rec.justifications
                    ],
                }
                for rec in analysis_result.recommendations
            ],
            "risk_assessment": analysis_result.risk_assessment,
            "market_sentiment": analysis_result.market_sentiment,
            "alerts": analysis_result.alerts,
            "version": analysis_result.version,
        }

    @staticmethod
    def get_summary_statistics(analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Generate summary statistics for quick overview.

        Args:
            analysis_result: Complete analysis result

        Returns:
            Dictionary with key statistics
        """
        recommendations = analysis_result.recommendations

        # Count recommendations by action type
        action_counts = {}
        for rec in recommendations:
            action = rec.action.value
            action_counts[action] = action_counts.get(action, 0) + 1

        # Count by priority
        priority_counts = {}
        for rec in recommendations:
            priority = rec.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Average confidence
        avg_confidence = (
            sum(r.overall_confidence for r in recommendations) / len(recommendations)
            if recommendations
            else 0
        )

        return {
            "total_recommendations": len(recommendations),
            "recommendations_by_action": action_counts,
            "recommendations_by_priority": priority_counts,
            "average_confidence": avg_confidence,
            "alerts_count": len(analysis_result.alerts),
            "market_outlook": analysis_result.market_sentiment.get(
                "market_outlook", "UNKNOWN"
            ),
            "completion_time_seconds": analysis_result.completion_time_seconds,
            "portfolio_metrics": {
                "total_value": analysis_result.portfolio.metrics.total_value,
                "volatility": analysis_result.portfolio.metrics.annual_volatility,
                "sharpe_ratio": analysis_result.portfolio.metrics.sharpe_ratio,
                "num_positions": len(analysis_result.portfolio.positions),
            },
        }
