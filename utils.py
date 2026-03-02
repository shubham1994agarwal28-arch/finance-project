"""
Utility functions and helpers for the portfolio analysis system.

Provides:
- Data loading and parsing from various formats
- Portfolio JSON serialization/deserialization
- File I/O helpers
- Formatting utilities for display
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from models import Portfolio, Position, PortfolioMetrics


logger = logging.getLogger(__name__)


class PortfolioLoader:
    """Load and manage portfolio data from various sources."""

    @staticmethod
    def load_from_json(file_path: str) -> Portfolio:
        """
        Load portfolio from JSON file.

        Expected JSON format:
        {
          "risk_profile": "moderate",
          "constraints": {},
          "positions": [
            {
              "ticker": "AAPL",
              "shares": 100,
              "entry_price": 120.0,
              "current_price": 145.0,
              "allocation_percent": 12.5,
              "sector": "Technology"
            }
          ],
          "metrics": {
            "total_value": 1000000,
            "total_return_percent": 18.5,
            "annual_volatility": 12.5,
            ...
          }
        }

        Args:
            file_path: Path to JSON file

        Returns:
            Portfolio object

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
            ValueError: If required fields are missing
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Portfolio file not found: {file_path}")

        logger.info(f"Loading portfolio from JSON: {file_path}")

        with open(file_path, "r") as f:
            data = json.load(f)

        # Parse positions
        positions = []
        for pos_data in data.get("positions", []):
            position = Position(
                ticker=pos_data["ticker"],
                shares=pos_data["shares"],
                entry_price=pos_data["entry_price"],
                current_price=pos_data["current_price"],
                allocation_percent=pos_data["allocation_percent"],
                sector=pos_data["sector"],
            )
            positions.append(position)

        # Parse metrics
        metrics_data = data.get("metrics", {})
        metrics = PortfolioMetrics(
            total_value=metrics_data.get("total_value", 0),
            total_return_percent=metrics_data.get("total_return_percent", 0),
            annual_volatility=metrics_data.get("annual_volatility", 0),
            sharpe_ratio=metrics_data.get("sharpe_ratio", 0),
            sortino_ratio=metrics_data.get("sortino_ratio", 0),
            max_drawdown=metrics_data.get("max_drawdown", 0),
            var_95=metrics_data.get("var_95", 0),
            concentration_index=metrics_data.get("concentration_index", 0),
            sector_concentration=metrics_data.get("sector_concentration", 0),
        )

        # Create portfolio
        portfolio = Portfolio(
            positions=positions,
            metrics=metrics,
            risk_profile=data.get("risk_profile", "moderate"),
            constraints=data.get("constraints", {}),
        )

        logger.info(f"Portfolio loaded: {len(positions)} positions")
        return portfolio

    @staticmethod
    def save_to_json(portfolio: Portfolio, file_path: str) -> None:
        """
        Save portfolio to JSON file.

        Args:
            portfolio: Portfolio object to save
            file_path: Path where to save JSON file
        """
        logger.info(f"Saving portfolio to JSON: {file_path}")

        portfolio_data = {
            "portfolio_id": portfolio.portfolio_id,
            "created_at": portfolio.created_at.isoformat(),
            "risk_profile": portfolio.risk_profile,
            "constraints": portfolio.constraints,
            "positions": [
                {
                    "ticker": p.ticker,
                    "shares": p.shares,
                    "entry_price": p.entry_price,
                    "current_price": p.current_price,
                    "allocation_percent": p.allocation_percent,
                    "sector": p.sector,
                    "current_value": p.current_value,
                    "gain_loss": p.gain_loss,
                    "gain_loss_percent": p.gain_loss_percent,
                }
                for p in portfolio.positions
            ],
            "metrics": {
                "total_value": portfolio.metrics.total_value,
                "total_return_percent": portfolio.metrics.total_return_percent,
                "annual_volatility": portfolio.metrics.annual_volatility,
                "sharpe_ratio": portfolio.metrics.sharpe_ratio,
                "sortino_ratio": portfolio.metrics.sortino_ratio,
                "max_drawdown": portfolio.metrics.max_drawdown,
                "var_95": portfolio.metrics.var_95,
                "concentration_index": portfolio.metrics.concentration_index,
                "sector_concentration": portfolio.metrics.sector_concentration,
            },
        }

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(portfolio_data, f, indent=2)

        logger.info(f"Portfolio saved successfully")

    @staticmethod
    def load_from_csv(file_path: str) -> Portfolio:
        """
        Load portfolio from CSV file.

        CSV format (header required):
        ticker,shares,entry_price,current_price,allocation_percent,sector
        AAPL,100,120.0,145.0,12.5,Technology
        MSFT,50,250.0,320.0,8.2,Technology

        Args:
            file_path: Path to CSV file

        Returns:
            Portfolio object
        """
        import csv

        if not Path(file_path).exists():
            raise FileNotFoundError(f"Portfolio file not found: {file_path}")

        logger.info(f"Loading portfolio from CSV: {file_path}")

        positions = []
        total_value = 0
        total_cost = 0

        with open(file_path, "r") as f:
            reader = csv.DictReader(f)

            for row in reader:
                position = Position(
                    ticker=row["ticker"],
                    shares=float(row["shares"]),
                    entry_price=float(row["entry_price"]),
                    current_price=float(row["current_price"]),
                    allocation_percent=float(row["allocation_percent"]),
                    sector=row["sector"],
                )
                positions.append(position)
                total_value += position.current_value
                total_cost += position.shares * position.entry_price

        # Create metrics
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

        # Create portfolio
        portfolio = Portfolio(
            positions=positions,
            metrics=metrics,
            risk_profile="moderate",
            constraints={},
        )

        logger.info(f"Portfolio loaded: {len(positions)} positions")
        return portfolio


class ReportFormatter:
    """Format data for display and output."""

    @staticmethod
    def format_currency(value: float, decimals: int = 2) -> str:
        """Format value as currency string."""
        return f"${value:,.{decimals}f}"

    @staticmethod
    def format_percentage(
        value: float, decimals: int = 2, include_sign: bool = False
    ) -> str:
        """Format value as percentage string."""
        return f"{value:+.{decimals}f}%" if include_sign else f"{value:.{decimals}f}%"

    @staticmethod
    def format_ratio(value: float, decimals: int = 2) -> str:
        """Format value as ratio."""
        return f"{value:.{decimals}f}"

    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime object."""
        return dt.strftime(format_str)

    @staticmethod
    def create_table(headers: List[str], rows: List[List[str]]) -> str:
        """
        Create formatted ASCII table.

        Args:
            headers: Column headers
            rows: List of row data (each row is list of values)

        Returns:
            Formatted ASCII table string
        """
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Create separator line
        separator = "+" + "+".join(f"-{w + 2}-" for w in col_widths) + "+"

        # Create header
        table = separator + "\n"
        header_line = (
            "|"
            + "|".join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers))
            + "|\n"
        )
        table += header_line
        table += separator + "\n"

        # Add rows
        for row in rows:
            row_line = (
                "|"
                + "|".join(
                    f" {str(cell):<{col_widths[i]}} " for i, cell in enumerate(row)
                )
                + "|\n"
            )
            table += row_line

        table += separator

        return table


class DataValidationUtils:
    """Additional data validation utilities."""

    @staticmethod
    def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """
        Validate JSON data against schema.

        Args:
            data: Data to validate
            schema: JSON schema definition

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Basic schema validation
        if isinstance(schema, dict) and "required" in schema:
            for field in schema["required"]:
                if field not in data:
                    errors.append(f"Required field missing: {field}")

        return errors

    @staticmethod
    def sanitize_ticker(ticker: str) -> str:
        """Sanitize ticker symbol."""
        return ticker.strip().upper()

    @staticmethod
    def validate_ticker_format(ticker: str) -> bool:
        """Validate ticker symbol format."""
        # Basic validation: 1-5 alphanumeric characters
        return 1 <= len(ticker) <= 5 and ticker.replace(".", "").isalnum()

    @staticmethod
    def validate_sector(sector: str) -> bool:
        """
        Validate sector name against known sectors.

        Args:
            sector: Sector name to validate

        Returns:
            True if valid sector
        """
        valid_sectors = {
            "Technology",
            "Healthcare",
            "Financials",
            "Industrials",
            "Energy",
            "Utilities",
            "Consumer",
            "Materials",
            "Real Estate",
            "Communication",
            "Discretionary",
            "Staples",
        }
        return sector in valid_sectors


class ExportUtils:
    """Export portfolio data to various formats."""

    @staticmethod
    def export_to_excel(portfolio: Portfolio, file_path: str) -> None:
        """
        Export portfolio to Excel file.

        Args:
            portfolio: Portfolio to export
            file_path: Path to Excel file
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            logger.error("openpyxl not installed. Install with: pip install openpyxl")
            return

        logger.info(f"Exporting portfolio to Excel: {file_path}")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Portfolio"

        # Add headers
        headers = [
            "Ticker",
            "Shares",
            "Entry Price",
            "Current Price",
            "Position Value",
            "Gain/Loss $",
            "Gain/Loss %",
            "Allocation %",
            "Sector",
        ]
        ws.append(headers)

        # Format header row
        header_fill = PatternFill(
            start_color="4472C4", end_color="4472C4", fill_type="solid"
        )
        header_font = Font(bold=True, color="FFFFFF")

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font

        # Add data rows
        for position in portfolio.positions:
            ws.append(
                [
                    position.ticker,
                    position.shares,
                    position.entry_price,
                    position.current_price,
                    position.current_value,
                    position.gain_loss,
                    position.gain_loss_percent,
                    position.allocation_percent,
                    position.sector,
                ]
            )

        # Adjust column widths
        ws.column_dimensions["A"].width = 10
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["I"].width = 15

        wb.save(file_path)
        logger.info(f"Portfolio exported to Excel: {file_path}")

    @staticmethod
    def export_to_html(portfolio: Portfolio, file_path: str) -> None:
        """
        Export portfolio to HTML file.

        Args:
            portfolio: Portfolio to export
            file_path: Path to HTML file
        """
        logger.info(f"Exporting portfolio to HTML: {file_path}")

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Portfolio Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: right; }
                th { background-color: #4472C4; color: white; text-align: left; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .summary { margin: 20px 0; }
                .metric { display: inline-block; margin-right: 30px; }
            </style>
        </head>
        <body>
            <h1>Portfolio Report</h1>
            <div class="summary">
                <div class="metric"><strong>Total Value:</strong> ${portfolio.metrics.total_value:,.2f}</div>
                <div class="metric"><strong>Total Return:</strong> {portfolio.metrics.total_return_percent:+.2f}%</div>
                <div class="metric"><strong>Volatility:</strong> {portfolio.metrics.annual_volatility:.2f}%</div>
                <div class="metric"><strong>Positions:</strong> {len(portfolio.positions)}</div>
            </div>
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Shares</th>
                    <th>Entry Price</th>
                    <th>Current Price</th>
                    <th>Position Value</th>
                    <th>Gain/Loss</th>
                    <th>Return %</th>
                    <th>Allocation %</th>
                    <th>Sector</th>
                </tr>
        """

        for position in portfolio.positions:
            html += f"""
                <tr>
                    <td>{position.ticker}</td>
                    <td>{position.shares:.0f}</td>
                    <td>${position.entry_price:.2f}</td>
                    <td>${position.current_price:.2f}</td>
                    <td>${position.current_value:,.2f}</td>
                    <td>${position.gain_loss:+,.2f}</td>
                    <td>{position.gain_loss_percent:+.2f}%</td>
                    <td>{position.allocation_percent:.2f}%</td>
                    <td>{position.sector}</td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        Path(file_path).write_text(html)
        logger.info(f"Portfolio exported to HTML: {file_path}")
