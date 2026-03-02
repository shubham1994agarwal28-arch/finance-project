"""
AI Portfolio Analysis & Recommendation Agent

A sophisticated multi-agent system for institutional portfolio analysis, risk assessment,
and actionable investment recommendations.

Version: 1.0.0
Author: Portfolio Analysis Team
License: MIT

Key Components:
- config: Configuration management and risk profiles
- models: Data models and schemas
- tools: Risk calculation and analysis utilities
- agents: Four specialized analysis agents
- orchestrator: Multi-agent coordination engine
- api: REST API endpoints
- report_generator: Report generation utilities
- utils: Helper functions and data loading
"""

__version__ = "1.0.0"
__author__ = "Portfolio Analysis Team"
__all__ = [
    "config",
    "models",
    "tools",
    "agents",
    "orchestrator",
    "api",
    "report_generator",
    "utils",
]

# Import key components for easy access
from .config import Config, DEFAULT_CONFIG, get_config
from .models import Portfolio, Recommendation, AnalysisResult
from .orchestrator import OrchestratorAgent
from .api import create_app
from .report_generator import ReportGenerator
from .utils import PortfolioLoader, ReportFormatter

__all__.extend(
    [
        "Config",
        "DEFAULT_CONFIG",
        "Portfolio",
        "Recommendation",
        "AnalysisResult",
        "OrchestratorAgent",
        "create_app",
        "ReportGenerator",
        "PortfolioLoader",
        "ReportFormatter",
    ]
)
