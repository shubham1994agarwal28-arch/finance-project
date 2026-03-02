"""
Configuration module for the AI Portfolio Analysis & Recommendation Agent system.

This module centralizes all configuration settings including:
- Risk profiles and their constraints
- Model parameters for local LLM inference
- Database connections
- API endpoints
- Feature flags and thresholds
"""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RiskProfile:
    """
    Data class representing a risk profile with associated constraints.

    Attributes:
        name: Profile identifier (Conservative, Moderate, Aggressive)
        max_volatility: Maximum annual volatility allowed (%)
        min_dividend_yield: Minimum required dividend yield (%)
        max_tech_exposure: Maximum technology sector exposure (%)
        max_single_position: Maximum allocation to a single position (%)
        description: Human-readable profile description
    """

    name: str
    max_volatility: float
    min_dividend_yield: float
    max_tech_exposure: float
    max_single_position: float
    description: str


class Config:
    """
    Central configuration class for the portfolio analysis system.
    Manages all settings and constraints across the application.
    """

    # ============================================================================
    # RISK PROFILES & CONSTRAINTS
    # ============================================================================
    RISK_PROFILES: Dict[str, RiskProfile] = {
        "conservative": RiskProfile(
            name="Conservative",
            max_volatility=10.0,
            min_dividend_yield=2.0,
            max_tech_exposure=20.0,
            max_single_position=5.0,
            description="Low-risk portfolio focused on capital preservation with steady income",
        ),
        "moderate": RiskProfile(
            name="Moderate",
            max_volatility=15.0,
            min_dividend_yield=1.5,
            max_tech_exposure=35.0,
            max_single_position=5.0,
            description="Balanced portfolio with moderate growth and risk tolerance",
        ),
        "aggressive": RiskProfile(
            name="Aggressive",
            max_volatility=25.0,
            min_dividend_yield=0.0,
            max_tech_exposure=50.0,
            max_single_position=10.0,
            description="Growth-focused portfolio accepting higher volatility for potential returns",
        ),
    }

    # ============================================================================
    # MODEL & INFERENCE SETTINGS
    # ============================================================================
    # Ollama local LLM configuration for on-premises deployment
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    PRIMARY_MODEL: str = "mistral:7b"  # Primary model for analysis and reasoning
    NLP_MODEL: str = (
        "distilbert-base-uncased-finetuned-sst-2-english"  # Sentiment analysis
    )

    # Inference constraints and timeouts
    INFERENCE_TIMEOUT_SECONDS: int = 30
    MAX_TOKENS_FOR_ANALYSIS: int = 2000
    TEMPERATURE_FOR_ANALYSIS: float = 0.7  # Balance between creativity and consistency

    # ============================================================================
    # PORTFOLIO ANALYSIS PARAMETERS
    # ============================================================================
    # Portfolio constraints and limits
    MIN_PORTFOLIO_POSITIONS: int = 10
    MAX_PORTFOLIO_POSITIONS: int = 1000
    HISTORICAL_DATA_YEARS: int = 10

    # Analysis requirements
    MIN_CONFIDENCE_THRESHOLD: float = (
        0.60  # Minimum confidence for recommendations (0-1)
    )
    TOP_RECOMMENDATIONS_COUNT: int = 10

    # Risk metrics parameters
    VaR_CONFIDENCE_LEVEL: float = 0.95  # Value-at-Risk confidence level
    CORRELATION_THRESHOLD: float = 0.7  # Threshold for correlation alerts
    SECTOR_CONCENTRATION_THRESHOLD: float = 0.3  # Max sector exposure before alert

    # ============================================================================
    # DATA PROCESSING & SOURCES
    # ============================================================================
    # News and sentiment analysis parameters
    NEWS_ARTICLES_PER_CYCLE: int = 100
    SENTIMENT_UPDATE_FREQUENCY_HOURS: int = 24
    NEWS_LOOKBACK_DAYS: int = 30

    # Data refresh rates
    MARKET_DATA_REFRESH_MINUTES: int = 15  # Real-time price updates
    PORTFOLIO_ANALYSIS_CACHE_MINUTES: int = 60  # Cache analysis for repeated queries
    SENTIMENT_CACHE_HOURS: int = 24

    # ============================================================================
    # DATABASE & STORAGE
    # ============================================================================
    # SQLite for local structured data storage
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./portfolio_analysis.db")

    # Optional: ChromaDB for vector embeddings (sentiment, news)
    EMBEDDINGS_DB_PATH: str = "./chroma_db"

    # ============================================================================
    # API & PERFORMANCE SETTINGS
    # ============================================================================
    # REST API configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RESPONSE_TIMEOUT_SECONDS: int = 3

    # Concurrency settings
    MAX_CONCURRENT_ANALYSES: int = 5
    PORTFOLIO_ANALYSIS_TIMEOUT_SECONDS: int = 300  # 5 minutes max

    # ============================================================================
    # LOGGING & MONITORING
    # ============================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE_PATH: str = "./logs/portfolio_analysis.log"
    ENABLE_AUDIT_LOGGING: bool = True  # Log all recommendations for compliance

    # ============================================================================
    # FEATURE FLAGS
    # ============================================================================
    USE_LOCAL_MODELS_ONLY: bool = True  # Enforce local Ollama models only
    ENABLE_BACKTESTING: bool = True
    ENABLE_PDF_REPORTS: bool = True
    ENABLE_DASHBOARD: bool = False  # Can be enabled for visualization

    @classmethod
    def get_risk_profile(cls, profile_name: str) -> RiskProfile:
        """
        Retrieve risk profile constraints by name.

        Args:
            profile_name: Name of the risk profile (case-insensitive)

        Returns:
            RiskProfile object with all constraints

        Raises:
            ValueError: If profile name is not found
        """
        profile = cls.RISK_PROFILES.get(profile_name.lower())
        if not profile:
            raise ValueError(
                f"Unknown risk profile: {profile_name}. "
                f"Available profiles: {', '.join(cls.RISK_PROFILES.keys())}"
            )
        return profile

    @classmethod
    def validate_portfolio_size(cls, position_count: int) -> None:
        """
        Validate that portfolio size is within acceptable bounds.

        Args:
            position_count: Number of positions in portfolio

        Raises:
            ValueError: If position count is outside acceptable range
        """
        if position_count < cls.MIN_PORTFOLIO_POSITIONS:
            raise ValueError(
                f"Portfolio must have at least {cls.MIN_PORTFOLIO_POSITIONS} positions, "
                f"got {position_count}"
            )
        if position_count > cls.MAX_PORTFOLIO_POSITIONS:
            raise ValueError(
                f"Portfolio exceeds maximum of {cls.MAX_PORTFOLIO_POSITIONS} positions, "
                f"got {position_count}"
            )


# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration with relaxed constraints."""

    DEBUG = True
    TESTING = False
    LOG_LEVEL = "DEBUG"


class TestingConfig(Config):
    """Testing environment configuration with mock data."""

    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///./test_portfolio.db"
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment with strict settings."""

    DEBUG = False
    TESTING = False
    LOG_LEVEL = "WARNING"
    USE_LOCAL_MODELS_ONLY = True


# Configuration factory
def get_config(env: str = "development") -> Config:
    """
    Factory function to retrieve appropriate configuration for environment.

    Args:
        env: Environment name (development, testing, production)

    Returns:
        Configuration object for the specified environment
    """
    configs = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }

    config_class = configs.get(env.lower(), DevelopmentConfig)
    return config_class()


# Initialize default configuration
DEFAULT_CONFIG = get_config(os.getenv("ENV", "development"))
