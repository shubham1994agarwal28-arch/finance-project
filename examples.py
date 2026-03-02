"""
Quick Start Guide and Examples

This file demonstrates how to use the AI Portfolio Analysis system
in various common scenarios.
"""

# ============================================================================
# EXAMPLE 1: Simple Portfolio Analysis
# ============================================================================

def example_1_simple_analysis():
    """
    Most basic example: Create a portfolio and analyze it.
    """
    from models import Portfolio, Position, PortfolioMetrics
    from orchestrator import OrchestratorAgent
    from report_generator import ReportGenerator
    
    # Create positions
    positions = [
        Position(ticker="AAPL", shares=100, entry_price=120, current_price=145, 
                allocation_percent=15, sector="Technology"),
        Position(ticker="MSFT", shares=50, entry_price=250, current_price=320,
                allocation_percent=10, sector="Technology"),
        Position(ticker="JNJ", shares=200, entry_price=140, current_price=155,
                allocation_percent=8, sector="Healthcare"),
        # ... add more positions (min 10 required)
    ]
    
    # Create metrics
    metrics = PortfolioMetrics(
        total_value=100000,
        total_return_percent=18.5,
        annual_volatility=12.5,
        sharpe_ratio=1.05,
        sortino_ratio=1.45,
        max_drawdown=-18.5,
        var_95=-2.15,
        concentration_index=0.18,
        sector_concentration=0.32
    )
    
    # Create portfolio
    portfolio = Portfolio(
        positions=positions,
        metrics=metrics,
        risk_profile="moderate",
        constraints={}
    )
    
    # Run analysis
    orchestrator = OrchestratorAgent()
    analysis_result = orchestrator.analyze_portfolio(portfolio)
    
    # Generate report
    report = ReportGenerator.generate_markdown_report(analysis_result)
    print(report)


# ============================================================================
# EXAMPLE 2: Load Portfolio from JSON
# ============================================================================

def example_2_load_from_json():
    """
    Load portfolio from JSON file and analyze it.
    """
    from utils import PortfolioLoader
    from orchestrator import OrchestratorAgent
    from report_generator import ReportGenerator
    
    # Load portfolio
    portfolio = PortfolioLoader.load_from_json("portfolio.json")
    
    # Run analysis
    orchestrator = OrchestratorAgent()
    analysis_result = orchestrator.analyze_portfolio(portfolio)
    
    # Print recommendations
    for idx, rec in enumerate(analysis_result.recommendations[:5], 1):
        print(f"{idx}. {rec.action.value}: {rec.target_ticker}")
        print(f"   Confidence: {rec.overall_confidence:.0f}%")
        print(f"   Sector: {rec.target_sector}")
        print()


# ============================================================================
# EXAMPLE 3: Load Portfolio from CSV
# ============================================================================

def example_3_load_from_csv():
    """
    Load portfolio from CSV file.
    
    CSV format:
    ticker,shares,entry_price,current_price,allocation_percent,sector
    AAPL,100,120.0,145.0,15,Technology
    MSFT,50,250.0,320.0,10,Technology
    """
    from utils import PortfolioLoader
    from orchestrator import OrchestratorAgent
    
    # Load from CSV
    portfolio = PortfolioLoader.load_from_csv("portfolio.csv")
    
    # Analyze
    orchestrator = OrchestratorAgent()
    analysis_result = orchestrator.analyze_portfolio(portfolio)
    
    # Display alerts
    if analysis_result.alerts:
        print("⚠ Alerts:")
        for alert in analysis_result.alerts:
            print(f"  - {alert}")


# ============================================================================
# EXAMPLE 4: Risk Analysis
# ============================================================================

def example_4_risk_analysis():
    """
    Detailed risk metric calculations.
    """
    from tools import RiskCalculationTools
    
    # Sample daily returns
    daily_returns = [0.01, -0.005, 0.015, 0.002, -0.008, 0.012, -0.003, 0.009]
    
    # Calculate risk metrics
    volatility = RiskCalculationTools.calculate_portfolio_volatility(daily_returns)
    sharpe = RiskCalculationTools.calculate_sharpe_ratio(daily_returns)
    sortino = RiskCalculationTools.calculate_sortino_ratio(daily_returns)
    var = RiskCalculationTools.calculate_value_at_risk(daily_returns, confidence_level=0.95)
    cvar = RiskCalculationTools.calculate_conditional_var(daily_returns)
    max_dd = RiskCalculationTools.calculate_maximum_drawdown([100, 101, 98, 102, 99, 95])
    
    print(f"Risk Metrics:")
    print(f"  Volatility (Annual): {volatility:.2f}%")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print(f"  Sortino Ratio: {sortino:.2f}")
    print(f"  VaR (95%): {var:.2f}%")
    print(f("  CVaR (95%): {cvar:.2f}%")
    print(f"  Max Drawdown: {max_dd:.2f}%")


# ============================================================================
# EXAMPLE 5: Concentration Analysis
# ============================================================================

def example_5_concentration_analysis():
    """
    Analyze portfolio concentration and diversification.
    """
    from tools import ConcentrationAnalysisTools
    from models import Portfolio
    
    # Assuming you have a portfolio object
    portfolio = Portfolio(...)  # Your portfolio
    
    # Calculate HHI
    allocations = [p.allocation_percent / 100 for p in portfolio.positions]
    hhi = ConcentrationAnalysisTools.calculate_herfindahl_index(allocations)
    
    # Sector concentration
    sector_conc = ConcentrationAnalysisTools.calculate_sector_concentration(portfolio)
    
    # Check violations
    alerts = ConcentrationAnalysisTools.identify_concentration_violations(
        portfolio,
        max_single_position=5.0,
        max_sector_exposure=25.0
    )
    
    print(f"Concentration Analysis:")
    print(f"  HHI Index: {hhi:.4f}")
    print(f"  Sector Distribution: {sector_conc}")
    print(f"  Violations: {len(alerts)}")
    for alert in alerts:
        print(f"    - {alert}")


# ============================================================================
# EXAMPLE 6: API Usage via CURL
# ============================================================================

def example_6_api_usage():
    """
    Example API calls using curl.
    """
    
    # 1. Start API server
    print("Starting API server:")
    print("  uvicorn api:get_application --reload")
    print()
    
    # 2. Submit portfolio for analysis
    print("Submit portfolio for analysis:")
    print('''
    curl -X POST "http://localhost:8000/api/v1/analyze" \\
      -H "Content-Type: application/json" \\
      -d '{
        "positions": [
          {
            "ticker": "AAPL",
            "shares": 100,
            "entry_price": 120,
            "current_price": 145,
            "allocation_percent": 15,
            "sector": "Technology"
          }
        ],
        "risk_profile": "moderate"
      }'
    ''')
    print()
    
    # 3. Validate portfolio
    print("Validate portfolio:")
    print('''
    curl -X POST "http://localhost:8000/api/v1/validate" \\
      -H "Content-Type: application/json" \\
      -d '{...}'
    ''')
    print()
    
    # 4. Get configuration
    print("Get system configuration:")
    print("  curl http://localhost:8000/api/v1/config")


# ============================================================================
# EXAMPLE 7: Generate Various Reports
# ============================================================================

def example_7_generate_reports():
    """
    Generate different report formats.
    """
    from orchestrator import OrchestratorAgent
    from report_generator import ReportGenerator
    from models import Portfolio
    from utils import ExportUtils
    
    # Your portfolio
    portfolio = Portfolio(...)
    
    # Run analysis
    orchestrator = OrchestratorAgent()
    analysis_result = orchestrator.analyze_portfolio(portfolio)
    
    # Generate markdown report
    markdown_report = ReportGenerator.generate_markdown_report(analysis_result)
    with open("report.md", "w") as f:
        f.write(markdown_report)
    print("✓ Saved: report.md")
    
    # Generate JSON report
    json_report = ReportGenerator.generate_json_report(analysis_result)
    import json
    with open("report.json", "w") as f:
        json.dump(json_report, f, indent=2)
    print("✓ Saved: report.json")
    
    # Summary statistics
    summary = ReportGenerator.get_summary_statistics(analysis_result)
    print(f"Summary: {summary['total_recommendations']} recommendations")
    
    # Export portfolio to Excel
    ExportUtils.export_to_excel(portfolio, "portfolio.xlsx")
    print("✓ Saved: portfolio.xlsx")
    
    # Export to HTML
    ExportUtils.export_to_html(portfolio, "portfolio.html")
    print("✓ Saved: portfolio.html")


# ============================================================================
# EXAMPLE 8: Validate Portfolio Data
# ============================================================================

def example_8_validate_portfolio():
    """
    Validate portfolio before analysis.
    """
    from tools import DataValidationTools
    from models import Portfolio
    
    portfolio = Portfolio(...)
    
    # Validate
    errors = DataValidationTools.validate_portfolio(portfolio)
    
    if errors:
        print("❌ Portfolio validation failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Portfolio is valid")
        
        # Validate individual positions
        for position in portfolio.positions:
            pos_errors = DataValidationTools.validate_position(position)
            if pos_errors:
                print(f"Position {position.ticker}: {pos_errors}")


# ============================================================================
# EXAMPLE 9: Access Agent Analysis Directly
# ============================================================================

def example_9_direct_agent_analysis():
    """
    Access individual agents directly.
    """
    from agents import (RiskAssessmentAgent, ReturnOptimizationAgent,
                       DiversificationAgent, MarketSentimentAgent)
    from models import Portfolio
    
    portfolio = Portfolio(...)
    
    # Risk Agent
    risk_agent = RiskAssessmentAgent()
    risk_analysis = risk_agent.analyze(portfolio)
    risk_recs = risk_agent.generate_recommendations(portfolio, risk_analysis)
    print(f"Risk Agent Recommendations: {len(risk_recs)}")
    
    # Return Agent
    return_agent = ReturnOptimizationAgent()
    return_analysis = return_agent.analyze(portfolio)
    return_recs = return_agent.generate_recommendations(portfolio, return_analysis)
    print(f"Return Agent Recommendations: {len(return_recs)}")
    
    # Diversification Agent
    div_agent = DiversificationAgent()
    div_analysis = div_agent.analyze(portfolio)
    div_recs = div_agent.generate_recommendations(portfolio, div_analysis)
    print(f"Diversification Agent Recommendations: {len(div_recs)}")
    
    # Sentiment Agent
    sent_agent = MarketSentimentAgent()
    sent_analysis = sent_agent.analyze(portfolio)
    sent_recs = sent_agent.generate_recommendations(portfolio, sent_analysis)
    print(f"Sentiment Agent Recommendations: {len(sent_recs)}")


# ============================================================================
# EXAMPLE 10: Custom Configuration
# ============================================================================

def example_10_custom_configuration():
    """
    Using custom configuration settings.
    """
    from config import get_config, DevelopmentConfig, ProductionConfig
    
    # Get configuration for environment
    dev_config = get_config("development")
    prod_config = get_config("production")
    
    print(f"Development Config:")
    print(f"  Log Level: {dev_config.LOG_LEVEL}")
    print(f"  Debug: {dev_config.DEBUG}")
    
    print(f"\nProduction Config:")
    print(f"  Log Level: {prod_config.LOG_LEVEL}")
    print(f"  Debug: {prod_config.DEBUG}")
    
    # Access risk profiles
    from config import DEFAULT_CONFIG
    conservative = DEFAULT_CONFIG.get_risk_profile("conservative")
    print(f"\nConservative Profile:")
    print(f"  Max Volatility: {conservative.max_volatility}%")
    print(f"  Max Position Size: {conservative.max_single_position}%")


# ============================================================================
# MAIN - Run examples
# ============================================================================

if __name__ == "__main__":
    print("AI Portfolio Analysis - Examples\n")
    print("Available examples:")
    print("1. Simple portfolio analysis")
    print("2. Load portfolio from JSON")
    print("3. Load portfolio from CSV")
    print("4. Risk analysis")
    print("5. Concentration analysis")
    print("6. API usage")
    print("7. Generate reports")
    print("8. Validate portfolio")
    print("9. Direct agent analysis")
    print("10. Custom configuration")
    print("\nTo run example 1: python -c 'from examples import example_1_simple_analysis; example_1_simple_analysis()'")
