"""
Main application entry point and example usage.

Demonstrates:
- Creating a portfolio from sample data
- Running the multi-agent analysis
- Generating reports
- Starting the API server
"""

import logging
import json
from datetime import datetime
from typing import List

from models import Portfolio, Position, PortfolioMetrics
from orchestrator import OrchestratorAgent
from report_generator import ReportGenerator
from config import DEFAULT_CONFIG, get_config


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=DEFAULT_CONFIG.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(DEFAULT_CONFIG.LOG_FILE_PATH),
            logging.StreamHandler(),
        ],
    )


logger = logging.getLogger(__name__)


# ============================================================================
# SAMPLE DATA
# ============================================================================


def create_sample_portfolio() -> Portfolio:
    """
    Create a sample portfolio for demonstration.

    Generates a moderately diversified portfolio with:
    - 25 positions across multiple sectors
    - Mix of gainers and losers
    - Varied position sizes
    - Real-world allocation patterns

    Returns:
        Sample Portfolio object with realistic data
    """

    # Define sample holdings with realistic data
    holdings_data = [
        # Technology (30% of portfolio)
        {
            "ticker": "AAPL",
            "shares": 500,
            "entry": 120,
            "current": 145,
            "sector": "Technology",
        },
        {
            "ticker": "MSFT",
            "shares": 300,
            "entry": 250,
            "current": 320,
            "sector": "Technology",
        },
        {
            "ticker": "GOOGL",
            "shares": 100,
            "entry": 2000,
            "current": 2350,
            "sector": "Technology",
        },
        {
            "ticker": "META",
            "shares": 250,
            "entry": 150,
            "current": 280,
            "sector": "Technology",
        },
        {
            "ticker": "NFLX",
            "shares": 150,
            "entry": 200,
            "current": 420,
            "sector": "Technology",
        },
        {
            "ticker": "CRM",
            "shares": 200,
            "entry": 150,
            "current": 220,
            "sector": "Technology",
        },
        {
            "ticker": "MU",
            "shares": 400,
            "entry": 50,
            "current": 65,
            "sector": "Technology",
        },
        # Healthcare (20% of portfolio)
        {
            "ticker": "JNJ",
            "shares": 200,
            "entry": 140,
            "current": 155,
            "sector": "Healthcare",
        },
        {
            "ticker": "PFE",
            "shares": 400,
            "entry": 30,
            "current": 28,
            "sector": "Healthcare",
        },
        {
            "ticker": "UNH",
            "shares": 100,
            "entry": 380,
            "current": 520,
            "sector": "Healthcare",
        },
        {
            "ticker": "AZN",
            "shares": 150,
            "entry": 60,
            "current": 85,
            "sector": "Healthcare",
        },
        # Financials (15% of portfolio)
        {
            "ticker": "JPM",
            "shares": 250,
            "entry": 120,
            "current": 185,
            "sector": "Financials",
        },
        {
            "ticker": "BAC",
            "shares": 600,
            "entry": 25,
            "current": 32,
            "sector": "Financials",
        },
        {
            "ticker": "GS",
            "shares": 100,
            "entry": 300,
            "current": 380,
            "sector": "Financials",
        },
        # Industrials (15% of portfolio)
        {
            "ticker": "BA",
            "shares": 150,
            "entry": 180,
            "current": 185,
            "sector": "Industrials",
        },
        {
            "ticker": "GE",
            "shares": 500,
            "entry": 70,
            "current": 85,
            "sector": "Industrials",
        },
        {
            "ticker": "CAT",
            "shares": 100,
            "entry": 200,
            "current": 245,
            "sector": "Industrials",
        },
        # Energy (10% of portfolio)
        {
            "ticker": "XOM",
            "shares": 300,
            "entry": 90,
            "current": 105,
            "sector": "Energy",
        },
        {
            "ticker": "CVX",
            "shares": 200,
            "entry": 110,
            "current": 155,
            "sector": "Energy",
        },
        # Utilities (5% of portfolio)
        {
            "ticker": "NEE",
            "shares": 150,
            "entry": 70,
            "current": 88,
            "sector": "Utilities",
        },
        {
            "ticker": "DUK",
            "shares": 200,
            "entry": 85,
            "current": 92,
            "sector": "Utilities",
        },
        # Consumer (5% of portfolio)
        {
            "ticker": "KO",
            "shares": 300,
            "entry": 50,
            "current": 58,
            "sector": "Consumer",
        },
        {
            "ticker": "MCD",
            "shares": 100,
            "entry": 250,
            "current": 285,
            "sector": "Consumer",
        },
    ]

    # Create Position objects and calculate metrics
    positions = []
    total_current_value = 0
    total_entry_value = 0

    for holding in holdings_data:
        entry_value = holding["shares"] * holding["entry"]
        current_value = holding["shares"] * holding["current"]

        position = Position(
            ticker=holding["ticker"],
            shares=holding["shares"],
            entry_price=holding["entry"],
            current_price=holding["current"],
            allocation_percent=0.0,  # Will be calculated
            sector=holding["sector"],
        )

        positions.append(position)
        total_current_value += current_value
        total_entry_value += entry_value

    # Calculate allocation percentages
    for position in positions:
        position.allocation_percent = (
            position.current_value / total_current_value
        ) * 100

    # Create portfolio metrics
    total_return = (
        ((total_current_value - total_entry_value) / total_entry_value) * 100
        if total_entry_value > 0
        else 0
    )

    metrics = PortfolioMetrics(
        total_value=total_current_value,
        total_return_percent=total_return,
        annual_volatility=12.5,  # Realistic moderate volatility
        sharpe_ratio=1.05,  # Good risk-adjusted return
        sortino_ratio=1.45,  # Better downside risk-adjusted return
        max_drawdown=-18.5,  # Historical worst drawdown
        var_95=-2.15,  # 95% confidence max daily loss
        concentration_index=0.18,  # Reasonably diversified
        sector_concentration=0.32,  # Tech sector largest at ~32%
    )

    # Create portfolio
    portfolio = Portfolio(
        positions=positions,
        metrics=metrics,
        risk_profile="moderate",
        constraints={
            "max_sector_exposure": 0.35,
            "min_quality_rating": "A-",
            "geographic_restriction": "US only",
        },
        historical_data={
            "1_year_return": 18.5,
            "3_year_return": 42.0,
            "5_year_return": 85.5,
            "10_year_return": 180.0,
            "inception_date": "2000-01-01",
        },
    )

    logger.info(
        f"Created sample portfolio with {len(positions)} positions, value: ${total_current_value:,.2f}"
    )

    return portfolio


def run_analysis_example():
    """
    Execute complete analysis on sample portfolio.

    Demonstrates the full workflow:
    1. Create/load portfolio
    2. Run multi-agent analysis
    3. Generate reports
    4. Display results
    """

    logger.info("=" * 70)
    logger.info("AI PORTFOLIO ANALYSIS & RECOMMENDATION AGENT - EXAMPLE RUN")
    logger.info("=" * 70)

    # Create sample portfolio
    logger.info("Step 1: Creating sample portfolio...")
    portfolio = create_sample_portfolio()
    print(f"\n✓ Sample portfolio created")
    print(f"  Positions: {len(portfolio.positions)}")
    print(f"  Total Value: ${portfolio.metrics.total_value:,.2f}")
    print(f"  Total Return: {portfolio.metrics.total_return_percent:+.2f}%")
    print(f"  Risk Profile: {portfolio.risk_profile.upper()}")

    # Run analysis
    logger.info("\nStep 2: Running multi-agent analysis...")
    orchestrator = OrchestratorAgent()
    analysis_result = orchestrator.analyze_portfolio(portfolio)

    print(
        f"\n✓ Analysis completed in {analysis_result.completion_time_seconds:.2f} seconds"
    )
    print(f"  Recommendations: {len(analysis_result.recommendations)}")
    print(f"  Alerts: {len(analysis_result.alerts)}")
    print(
        f"  Market Outlook: {analysis_result.market_sentiment.get('market_outlook', 'UNKNOWN')}"
    )

    # Generate reports
    logger.info("\nStep 3: Generating reports...")

    # Markdown report
    markdown_report = ReportGenerator.generate_markdown_report(analysis_result)

    # JSON report
    json_report = ReportGenerator.generate_json_report(analysis_result)

    # Summary statistics
    summary_stats = ReportGenerator.get_summary_statistics(analysis_result)

    print(f"\n✓ Reports generated")

    # Display Summary
    print(f"\n" + "=" * 70)
    print(f"ANALYSIS SUMMARY")
    print(f"=" * 70)

    print(f"\nPortfolio Metrics:")
    print(f"  Total Value: ${portfolio.metrics.total_value:,.2f}")
    print(f"  Annual Volatility: {portfolio.metrics.annual_volatility:.2f}%")
    print(f"  Sharpe Ratio: {portfolio.metrics.sharpe_ratio:.2f}")
    print(f"  Return: {portfolio.metrics.total_return_percent:+.2f}%")

    print(f"\nRecommendations by Action:")
    for action, count in summary_stats.get("recommendations_by_action", {}).items():
        print(f"  {action}: {count}")

    print(f"\nRecommendations by Priority:")
    for priority, count in summary_stats.get("recommendations_by_priority", {}).items():
        print(f"  {priority}: {count}")

    print(f"\nTop Recommendations:")
    for idx, rec in enumerate(analysis_result.recommendations[:5], 1):
        print(f"\n  {idx}. {rec.action.value}: {rec.target_ticker}")
        print(f"     Sector: {rec.target_sector}")
        print(f"     Confidence: {rec.overall_confidence:.0f}%")
        print(f"     Priority: {rec.priority.value}")
        print(f"     Agents: {len(rec.justifications)}")

    if analysis_result.alerts:
        print(f"\nAlerts ({len(analysis_result.alerts)}):")
        for alert in analysis_result.alerts[:3]:
            print(f"  ⚠ {alert}")
    else:
        print(f"\n✓ No alerts or violations")

    print(f"\n" + "=" * 70)

    # Save reports to files
    logger.info("\nStep 4: Saving reports to files...")

    # Save markdown report
    report_path = f"portfolio_analysis_{analysis_result.analysis_id[:8]}.md"
    with open(report_path, "w") as f:
        f.write(markdown_report)
    logger.info(f"Markdown report saved to: {report_path}")
    print(f"✓ Markdown report: {report_path}")

    # Save JSON report
    json_path = f"portfolio_analysis_{analysis_result.analysis_id[:8]}.json"
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2, default=str)
    logger.info(f"JSON report saved to: {json_path}")
    print(f"✓ JSON report: {json_path}")

    print(f"\n✓ Analysis complete!")

    return analysis_result


def start_api_server():
    """
    Start the FastAPI server for REST endpoint access.

    Provides endpoints for portfolio analysis, validation, etc.
    """

    logger.info("Starting API server...")
    print("\nTo start the API server, run:")
    print("  python -m uvicorn api:get_application --reload")
    print("\nAPI endpoints:")
    print("  POST /api/v1/analyze - Analyze portfolio")
    print("  POST /api/v1/validate - Validate portfolio data")
    print("  GET /api/v1/config - Get system configuration")
    print("  GET /health - Health check")
    print("\nAPI documentation:")
    print("  http://localhost:8000/docs")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """
    Main entry point for the application.

    Provides menu for:
    - Running example analysis
    - Starting API server
    - Displaying configuration
    """

    # Setup logging
    setup_logging()

    logger.info("AI Portfolio Analysis & Recommendation Agent Starting")
    logger.info(f"Environment: {DEFAULT_CONFIG.__class__.__name__}")

    print("\n" + "=" * 70)
    print("AI PORTFOLIO ANALYSIS & RECOMMENDATION AGENT v1.0")
    print("=" * 70)
    print("\nOptions:")
    print("  1. Run example portfolio analysis")
    print("  2. Start API server")
    print("  3. Display configuration")
    print("  4. Exit")
    print("\n" + "-" * 70)

    choice = input("\nSelect option (1-4): ").strip()

    if choice == "1":
        print()
        run_analysis_example()
    elif choice == "2":
        print()
        start_api_server()
    elif choice == "3":
        print("\nSystem Configuration:")
        print(f"  Model: {DEFAULT_CONFIG.PRIMARY_MODEL}")
        print(f"  Risk Profiles: {', '.join(DEFAULT_CONFIG.RISK_PROFILES.keys())}")
        print(f"  Min Positions: {DEFAULT_CONFIG.MIN_PORTFOLIO_POSITIONS}")
        print(f"  Max Positions: {DEFAULT_CONFIG.MAX_PORTFOLIO_POSITIONS}")
        print(f"  API Host: {DEFAULT_CONFIG.API_HOST}:{DEFAULT_CONFIG.API_PORT}")
        print(f"  DB: {DEFAULT_CONFIG.DATABASE_URL}")
    elif choice == "4":
        print("\nExiting...")
    else:
        print("\nInvalid selection")

    print()


if __name__ == "__main__":
    main()
