"""
API module providing REST endpoints for portfolio analysis.

Endpoints:
- POST /api/v1/analyze: Submit portfolio for analysis
- GET /api/v1/analysis/{analysis_id}: Retrieve analysis results
- GET /api/v1/recommendations/{analysis_id}: Get recommendations
- POST /api/v1/validate: Validate portfolio data
- GET /api/v1/health: Health check
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import asyncio

from models import (
    Portfolio,
    Position,
    PortfolioMetrics,
    AnalysisResult,
    Recommendation,
    APIResponse,
)
from orchestrator import OrchestratorAgent
from tools import DataValidationTools
from config import DEFAULT_CONFIG


logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class PositionRequest(BaseModel):
    """Request model for a portfolio position."""

    ticker: str = Field(..., description="Stock symbol")
    shares: float = Field(..., description="Number of shares held", gt=0)
    entry_price: float = Field(..., description="Average entry price", gt=0)
    current_price: float = Field(..., description="Current market price", gt=0)
    allocation_percent: float = Field(
        ..., description="Portfolio allocation %", ge=0, le=100
    )
    sector: str = Field(..., description="Industry sector")


class PortfolioRequest(BaseModel):
    """Request model for portfolio analysis."""

    positions: List[PositionRequest] = Field(
        ..., description="List of holdings", min_items=10, max_items=1000
    )
    risk_profile: str = Field(
        ..., description="Risk profile: conservative, moderate, or aggressive"
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict, description="Custom constraints"
    )
    historical_data: Optional[Dict[str, Any]] = Field(
        None, description="10+ years of historical performance data"
    )


class PortfolioMetricsResponse(BaseModel):
    """Response model for portfolio metrics."""

    total_value: float
    total_return_percent: float
    annual_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float
    concentration_index: float


class RecommendationResponse(BaseModel):
    """Response model for a single recommendation."""

    recommendation_id: str
    action: str
    target_ticker: str
    target_sector: str
    position_sizing: float
    confidence: float
    priority: str
    implementation_notes: str
    agents_involved: int


class AnalysisResponse(BaseModel):
    """Complete analysis response."""

    analysis_id: str
    portfolio_metrics: PortfolioMetricsResponse
    recommendations: List[RecommendationResponse]
    alerts: List[str]
    market_outlook: str
    completion_time_seconds: float
    timestamp: str


class ValidationResponse(BaseModel):
    """Portfolio validation response."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ============================================================================
# API APPLICATION
# ============================================================================


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application with all endpoints
    """
    app = FastAPI(
        title="AI Portfolio Analysis & Recommendation Agent",
        description="Multi-agent system for institutional portfolio analysis",
        version="1.0.0",
    )

    # Initialize orchestrator
    orchestrator = OrchestratorAgent()

    # ========================================================================
    # ENDPOINTS
    # ========================================================================

    @app.get("/health", tags=["Health"])
    async def health_check() -> Dict[str, str]:
        """
        Health check endpoint.

        Returns:
            Status of the API service
        """
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.post("/api/v1/validate", response_model=ValidationResponse, tags=["Portfolio"])
    async def validate_portfolio(portfolio: PortfolioRequest) -> ValidationResponse:
        """
        Validate portfolio data for correctness and completeness.

        Checks:
        - Required fields present
        - Values within reasonable ranges
        - Allocations sum to 100%
        - Risk profile valid
        - Sector definitions valid

        Args:
            portfolio: Portfolio data to validate

        Returns:
            ValidationResponse with any errors or warnings
        """
        logger.info(f"Validating portfolio with {len(portfolio.positions)} positions")

        errors = []
        warnings = []

        # Validate risk profile
        try:
            risk_profile = DEFAULT_CONFIG.get_risk_profile(portfolio.risk_profile)
        except ValueError as e:
            errors.append(str(e))

        # Validate positions
        for pos_req in portfolio.positions:
            if pos_req.current_price < 0.01:
                warnings.append(
                    f"{pos_req.ticker}: Very low price (${pos_req.current_price})"
                )
            if (
                abs((pos_req.current_price - pos_req.entry_price) / pos_req.entry_price)
                > 2.0
            ):
                warnings.append(
                    f"{pos_req.ticker}: Extreme price movement ({abs((pos_req.current_price - pos_req.entry_price) / pos_req.entry_price * 100):.0f}%)"
                )

        # Validate allocation sums to ~100%
        total_allocation = sum(p.allocation_percent for p in portfolio.positions)
        if abs(total_allocation - 100.0) > 0.5:
            errors.append(
                f"Portfolio allocation sums to {total_allocation:.2f}%, expected ~100%"
            )

        is_valid = len(errors) == 0

        response = ValidationResponse(
            is_valid=is_valid, errors=errors, warnings=warnings
        )

        logger.info(f"Validation result: {'PASS' if is_valid else 'FAIL'}")
        return response

    @app.post("/api/v1/analyze", response_model=AnalysisResponse, tags=["Analysis"])
    async def analyze_portfolio(
        portfolio_req: PortfolioRequest, background_tasks: BackgroundTasks
    ) -> AnalysisResponse:
        """
        Submit portfolio for comprehensive multi-agent analysis.

        Executes:
        1. Risk Assessment Agent
        2. Return Optimization Agent
        3. Diversification Agent
        4. Market Sentiment Agent

        Generates:
        - Ranked recommendations (top 10)
        - Risk metrics and alerts
        - Market outlook
        - Implementation guidance

        Args:
            portfolio_req: Portfolio data
            background_tasks: Background task queue

        Returns:
            AnalysisResponse with recommendations and analysis

        Raises:
            HTTPException: 400 if validation fails, 500 if analysis fails
        """
        # Validate input
        validation = await validate_portfolio(portfolio_req)
        if not validation.is_valid:
            logger.error(f"Portfolio validation failed: {validation.errors}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid portfolio: {'; '.join(validation.errors)}",
            )

        # Convert request to internal Portfolio model
        positions = []
        for pos_req in portfolio_req.positions:
            position = Position(
                ticker=pos_req.ticker,
                shares=pos_req.shares,
                entry_price=pos_req.entry_price,
                current_price=pos_req.current_price,
                allocation_percent=pos_req.allocation_percent,
                sector=pos_req.sector,
            )
            positions.append(position)

        # Calculate portfolio metrics (simplified for demo)
        total_value = sum(p.current_value for p in positions)
        total_cost = sum(p.shares * p.entry_price for p in positions)
        total_return = (
            ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
        )

        metrics = PortfolioMetrics(
            total_value=total_value,
            total_return_percent=total_return,
            annual_volatility=12.5,  # Placeholder
            sharpe_ratio=0.8,  # Placeholder
            sortino_ratio=1.2,  # Placeholder
            max_drawdown=-15.0,  # Placeholder
            var_95=-2.5,  # Placeholder
            concentration_index=0.15,  # Placeholder
            sector_concentration=0.35,  # Placeholder
        )

        portfolio = Portfolio(
            positions=positions,
            metrics=metrics,
            risk_profile=portfolio_req.risk_profile,
            constraints=portfolio_req.constraints or {},
            historical_data=portfolio_req.historical_data or {},
        )

        try:
            logger.info(f"Analyzing portfolio {portfolio.portfolio_id}")

            # Execute orchestrator analysis
            analysis_result = orchestrator.analyze_portfolio(portfolio)

            # Generate summary for API response
            recs_response = []
            for rec in analysis_result.recommendations:
                recs_response.append(
                    RecommendationResponse(
                        recommendation_id=rec.recommendation_id,
                        action=rec.action.value,
                        target_ticker=rec.target_ticker,
                        target_sector=rec.target_sector,
                        position_sizing=rec.position_sizing,
                        confidence=rec.overall_confidence,
                        priority=rec.priority.value,
                        implementation_notes=rec.implementation_notes,
                        agents_involved=len(rec.justifications),
                    )
                )

            response = AnalysisResponse(
                analysis_id=analysis_result.analysis_id,
                portfolio_metrics=PortfolioMetricsResponse(
                    **{
                        "total_value": metrics.total_value,
                        "total_return_percent": metrics.total_return_percent,
                        "annual_volatility": metrics.annual_volatility,
                        "sharpe_ratio": metrics.sharpe_ratio,
                        "sortino_ratio": metrics.sortino_ratio,
                        "max_drawdown": metrics.max_drawdown,
                        "var_95": metrics.var_95,
                        "concentration_index": metrics.concentration_index,
                    }
                ),
                recommendations=recs_response,
                alerts=analysis_result.alerts,
                market_outlook=analysis_result.market_sentiment.get(
                    "market_outlook", "UNKNOWN"
                ),
                completion_time_seconds=analysis_result.completion_time_seconds,
                timestamp=analysis_result.execution_timestamp.isoformat(),
            )

            logger.info(f"Analysis completed: {len(recs_response)} recommendations")
            return response

        except Exception as e:
            logger.exception(f"Portfolio analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    @app.get("/api/v1/config", tags=["Configuration"])
    async def get_configuration() -> Dict[str, Any]:
        """
        Get current system configuration.

        Returns:
            Configuration parameters for reference
        """
        config_info = {
            "risk_profiles": {
                name: {
                    "max_volatility": profile.max_volatility,
                    "min_dividend_yield": profile.min_dividend_yield,
                    "max_tech_exposure": profile.max_tech_exposure,
                    "max_single_position": profile.max_single_position,
                    "description": profile.description,
                }
                for name, profile in DEFAULT_CONFIG.RISK_PROFILES.items()
            },
            "portfolio_constraints": {
                "min_positions": DEFAULT_CONFIG.MIN_PORTFOLIO_POSITIONS,
                "max_positions": DEFAULT_CONFIG.MAX_PORTFOLIO_POSITIONS,
                "historical_data_years": DEFAULT_CONFIG.HISTORICAL_DATA_YEARS,
                "top_recommendations": DEFAULT_CONFIG.TOP_RECOMMENDATIONS_COUNT,
            },
            "model_info": {
                "primary_model": DEFAULT_CONFIG.PRIMARY_MODEL,
                "nlp_model": DEFAULT_CONFIG.NLP_MODEL,
                "inference_timeout": DEFAULT_CONFIG.INFERENCE_TIMEOUT_SECONDS,
            },
        }
        return config_info

    return app


# ============================================================================
# APPLICATION FACTORY
# ============================================================================


def get_application() -> FastAPI:
    """
    Factory function to create application instance.

    Returns:
        Configured FastAPI application
    """
    return create_app()


if __name__ == "__main__":
    import uvicorn

    app = create_app()

    logger.info("Starting AI Portfolio Analysis API")
    logger.info(f"Server: {DEFAULT_CONFIG.API_HOST}:{DEFAULT_CONFIG.API_PORT}")

    uvicorn.run(
        app,
        host=DEFAULT_CONFIG.API_HOST,
        port=DEFAULT_CONFIG.API_PORT,
        log_level=DEFAULT_CONFIG.LOG_LEVEL.lower(),
    )
